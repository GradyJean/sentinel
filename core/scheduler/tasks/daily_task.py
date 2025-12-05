from core.scheduler.task_runner import TaskRunner
from service.log_metadata_service import LogMetaDataService


class DailyTask(TaskRunner):
    """
    每天定时任务
    """
    task_id = "daily_task"
    log_metadata_service = LogMetaDataService()

    def run(self):
        self.log_metadata_service.cleanup_indices(keep_days=7)
