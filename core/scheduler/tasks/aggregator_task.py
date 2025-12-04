from core.scheduler.task_runner import TaskRunner
from service.aggregator_service import AccessIpAggregationService
from service.log_metadata_service import LogMetaDataService


class LogAggregatorTask(TaskRunner):
    task_id: str = "log_aggregator"
    log_metadata_service = LogMetaDataService()
    access_ip_aggregation_service = AccessIpAggregationService()

    async def run(self):
        pass

