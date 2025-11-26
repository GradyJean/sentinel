import importlib
import pkgutil
import traceback
from datetime import datetime
from typing import Dict, List

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from loguru import logger

import tasks
from core.scheduler.task_runner import TaskRunner
from models.scheduler import TaskScheduler
from service import task_scheduler_service


class SchedulerManager:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.task_runners: List[type[TaskRunner]] = self.__load_task_runners()
        self.reload_tasks()

    def start(self):
        self.scheduler.start()

    def stop(self):
        self.scheduler.shutdown()

    @staticmethod
    def __load_config() -> Dict[str, TaskScheduler]:
        """
        加载配置
        :return:
        """
        config: Dict[str, TaskScheduler] = {}
        records = task_scheduler_service.get_all()
        if records:
            for record in records:
                config[record.task_id] = record
        return config

    @staticmethod
    def __load_task_runners() -> List[type[TaskRunner]]:
        """
        加载所有任务
        """
        logger.info("Loading tasks...")
        for module_info in pkgutil.walk_packages(tasks.__path__, tasks.__name__ + "."):
            logger.info(f"Importing task: {module_info.name}")
            importlib.import_module(module_info.name)

        task_runners: List[type[TaskRunner]] = []
        for cls in TaskRunner.__subclasses__():
            task_runners.append(cls)
        return task_runners

    def reload_tasks(self):
        """
        注册任务
        :return:
        """
        # 获取配置
        config_dict: Dict[str, TaskScheduler] = self.__load_config()
        # 遍历所有任务
        for runner_cls in self.task_runners:
            task_id = runner_cls.task_id
            # 不存在任务配置，跳过
            if task_id not in config_dict:
                logger.warning(f"Task {task_id} not found in config")
                continue
            # 获取任务配置
            config: TaskScheduler = config_dict[task_id]
            # 获取任务
            job = self.scheduler.get_job(task_id)
            if job:
                # 任务已存在
                if config.enabled:
                    # 配置已启用，更新任务
                    self.scheduler.modify_job(
                        job_id=task_id,
                        trigger=CronTrigger.from_crontab(config.cron)
                    )
                    logger.info(f"Task {task_id} updated")
                else:
                    # 配置禁用，删除任务
                    self.scheduler.remove_job(task_id)
                    logger.info(f"Task {task_id} disabled")
            else:
                # 任务不存在
                if config.enabled:
                    # 配置启用 创建任务
                    self.scheduler.add_job(
                        func=self.__task_runner_wrapper,
                        args=(runner_cls, config),
                        trigger=CronTrigger.from_crontab(config.cron),
                        id=task_id,
                        replace_existing=True
                    )
                    logger.info(f"Task {task_id} enabled")
                else:
                    # 配置禁用 跳过
                    continue

    @staticmethod
    async def __task_runner_wrapper(task_runner: TaskRunner, config: TaskScheduler):
        """
           通用包装器：执行前后自动更新状态、捕获异常
        """
        logger.info(f"Task [{task_runner.task_id}] started")
        # 更新状态
        start_time = datetime.now()
        config.last_run_at = start_time
        config.last_status = "running"
        task_scheduler_service.save(config)
        try:
            # 运行任务
            await task_runner.run()
            #  更新状态
            cost_seconds = (datetime.now() - start_time).total_seconds()
            config.last_cost = int(cost_seconds)
            config.last_status = "successful"
            config.run_count += 1
            task_scheduler_service.save(config)
            logger.info(f"Task [{task_runner.task_id}] completed")
        except Exception as e:

            config.last_status = "failed"
            config.run_count += 1
            tb = "".join(traceback.format_exception(e))
            config.last_message = tb
            task_scheduler_service.save(config)
            logger.error(f"Task [{task_runner.task_id}] failed: {e}\n{tb}")
