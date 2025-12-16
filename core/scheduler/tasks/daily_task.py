from core.scheduler.task_runner import TaskRunner
from manager.log_metadata_manager import LogMetaDataManager, LogMetaDataBatchManager
from manager.ip_aggregator_manager import AccessIpAggregationManager
from manager.ip_score_manager import ScoreRecordManager
from manager.system_config_manager import SystemConfigManager


class DailyTask(TaskRunner):
    """
    每天定时任务
    """
    task_id = "daily_task"
    system_config_manager = SystemConfigManager()
    log_metadata_manager = LogMetaDataManager()
    access_ip_aggregation_manager = AccessIpAggregationManager()
    log_meta_data_batch_manager = LogMetaDataBatchManager()
    score_record_manager = ScoreRecordManager()

    def run(self):
        days = self.system_config_manager.system_config["record_keep_days"]
        if not days or days <= 0:
            days = 7
        self.log_metadata_manager.cleanup_indices(keep_days=days)
        self.access_ip_aggregation_manager.cleanup_indices(keep_days=days)
        self.score_record_manager.cleanup_indices(keep_days=days)
        self.log_meta_data_batch_manager.cleanup_records(keep_days=days)
