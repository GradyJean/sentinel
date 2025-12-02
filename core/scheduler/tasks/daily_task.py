from core.scheduler.task_runner import TaskRunner
from service.offset_service import OffsetsService


class DailyTask(TaskRunner):
    """
    每天定时任务
    """
    task_id = "daily_task"
    offset_service = OffsetsService()

    async def run(self):
        pass
