import importlib
import pkgutil
from datetime import datetime
from typing import Dict, List

from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from loguru import logger

from core.scheduler import tasks
from core.scheduler.task_runner import TaskRunner
from models.scheduler import TaskScheduler, TaskStatus
from service import task_scheduler_service


class SchedulerManager:
    def __init__(self):
        self.scheduler = AsyncIOScheduler(
            executors={
                "default": ThreadPoolExecutor(20),
            },
            job_defaults={
                "max_instances": 1,  # 同类型job运行一次
                "coalesce": True,  # 错过的调度不补偿
            }
        )
        self.task_runners: List[TaskRunner] = self.__load_task_runners()
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
    def __load_task_runners() -> List[TaskRunner]:
        """
        加载所有任务
        """
        logger.info("Loading tasks...")
        for module_info in pkgutil.walk_packages(tasks.__path__, tasks.__name__ + "."):
            logger.info(f"Importing task: {module_info.name}")
            importlib.import_module(module_info.name)

        task_runners: List[TaskRunner] = []
        for cls in TaskRunner.__subclasses__():
            task_runners.append(cls())
        return task_runners

    def reload_tasks(self):
        """
        注册任务
        :return:
        """
        # 获取配置
        config_dict: Dict[str, TaskScheduler] = self.__load_config()
        # 遍历所有任务
        for runner in self.task_runners:
            task_id = runner.task_id
            # 不存在任务配置，跳过
            if task_id not in config_dict:
                logger.warning(f"Task [{task_id}] not found in config")
                continue
            # 获取任务配置
            config: TaskScheduler = config_dict[task_id]
            # 获取任务
            job = self.scheduler.get_job(task_id)
            if job:
                # 任务已存在,直接更新
                self.scheduler.modify_job(
                    job_id=task_id,
                    trigger=CronTrigger.from_crontab(config.cron)
                )
                logger.info(f"Task [{task_id}] updated")
            else:
                # 任务不存在,创建任务
                self.scheduler.add_job(
                    func=self.__task_runner_wrapper,
                    args=(runner,),
                    trigger=CronTrigger.from_crontab(config.cron),
                    id=task_id,
                    replace_existing=True
                )
                logger.info(f"Task [{task_id}] created cron: {config.cron}")

    @staticmethod
    def __task_runner_wrapper(task_runner: TaskRunner):
        """
           通用包装器：执行前后自动更新状态、捕获异常
        """
        config: TaskScheduler = task_scheduler_service.get_by_id(task_runner.task_id)
        # 配置不存在 或者 禁用 跳过
        if not config or not config.enabled:
            return
        now = datetime.now()
        # 批次ID
        batch_id = now.strftime("%Y%m%d%H%M")
        # 判断是否重复执行
        if batch_id == config.batch_id:
            return
        logger.info(f"Task [{task_runner.task_id}] started")
        # 更新状态 RUNNING
        config.start_time = now
        config.end_time = now
        config.status = TaskStatus.RUNNING
        config.message = ""
        config.batch_id = batch_id
        task_scheduler_service.merge(config)
        try:
            # 运行任务
            task_runner.run()
            config.status = TaskStatus.SUCCESS
            logger.info(f"Task [{task_runner.task_id}] completed")
        except Exception as e:
            config.status = TaskStatus.FAILED
            config.message = str(e)
            logger.error(f"Task [{task_runner.task_id}] failed: {e}")
        finally:
            #  更新状态
            config.end_time = datetime.now()
            task_scheduler_service.merge(config)
