import asyncio
import time
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from service.task_scheduler_service import TaskSchedulerService


async def aggregate_ip():
    start = time.time()
    print(f"[{datetime.now()}] 开始聚合 IP...")

    # 模拟任务
    await asyncio.sleep(1)

    cost = int((time.time() - start) * 1000)
    print(f"[{datetime.now()}] IP 聚合完成，耗时 {cost} ms")


class TaskScheduler:
    def __init__(self):
        self.task_scheduler_service = TaskSchedulerService()
        self.task_schedulers = self.task_scheduler_service.load_task_scheduler()
        self.scheduler = AsyncIOScheduler()
        self.__add_tasks()

    def start(self):
        self.scheduler.start()

    def stop(self):
        self.scheduler.shutdown()

    def configure_reload(self):
        self.task_schedulers = self.task_scheduler_service.load_task_scheduler()

    def __add_tasks(self):
        self.scheduler.add_job(aggregate_ip,
                               trigger=CronTrigger.from_crontab("0 4 * * *"),
                               id="ip_aggregator",
                               replace_existing=True)

if __name__ == "__main__":
    task = TaskScheduler()
