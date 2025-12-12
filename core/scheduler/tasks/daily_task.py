from core.scheduler.task_runner import TaskRunner
from manager.log_metadata_manager import LogMetaDataManager


class DailyTask(TaskRunner):
    """
    每天定时任务
    """
    task_id = "daily_task"
    log_metadata_manager = LogMetaDataManager()

    def run(self):
        self.log_metadata_manager.cleanup_indices(keep_days=7)
