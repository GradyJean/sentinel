from core.scheduler.task_runner import TaskRunner
from models.log import BatchStatus
from manager.ip_aggregator_manager import AccessIpAggregationManager
from manager.log_metadata_manager import LogMetaDataBatchManager


class LogAggregatorTask(TaskRunner):
    task_id: str = "log_aggregator"
    log_metadata_batch_manager = LogMetaDataBatchManager()
    access_ip_aggregation_manager = AccessIpAggregationManager()

    def run(self):
        query = {
            "query": {
                "term": {
                    "status": "COLLECTED"
                }
            }, "sort": [
                {
                    "batch_id": {
                        "order": "asc"
                    }
                }]
        }
        batches = self.log_metadata_batch_manager.get_all(query=query)
        for batch in batches:
            batch_id = batch.batch_id
            # 批次状态更新
            batch.status = BatchStatus.AGGREGATING
            self.log_metadata_batch_manager.merge(batch)
            access_ip_aggregation = self.access_ip_aggregation_manager.query_access_ip_aggregation(batch_id)
            # 创建索引
            self.access_ip_aggregation_manager.create_daily_index(batch_id[:10])
            # 批量插入
            self.access_ip_aggregation_manager.batch_insert(access_ip_aggregation)
            # 批次状态更新
            batch.status = BatchStatus.AGGREGATED
            self.log_metadata_batch_manager.merge(batch)
