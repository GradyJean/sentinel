from core.scheduler.task_runner import TaskRunner
from models.log import BatchStatus
from service.aggregator_service import AccessIpAggregationService
from service.log_metadata_service import LogMetaDataBatchService


class LogAggregatorTask(TaskRunner):
    task_id: str = "log_aggregator"
    log_metadata_batch_service = LogMetaDataBatchService()
    access_ip_aggregation_service = AccessIpAggregationService()

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
        batches = self.log_metadata_batch_service.get_all(query=query)
        for batch in batches:
            batch.status = BatchStatus.AGGREGATING
            self.log_metadata_batch_service.merge(batch)
            access_ip_aggregation = self.access_ip_aggregation_service.query_access_ip_aggregation(batch.batch_id)
            self.access_ip_aggregation_service.batch_insert(access_ip_aggregation)
            batch.status = BatchStatus.AGGREGATED
            self.log_metadata_batch_service.merge(batch)
