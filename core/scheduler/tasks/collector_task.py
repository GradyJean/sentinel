from core.scheduler.task_runner import TaskRunner


class LogCollectorTask(TaskRunner):
    """
    日志采集任务
    """
    task_id: str = "log_collector"

    async def run(self):
        print("LogCollectorTask run")
