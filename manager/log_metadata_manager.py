from datetime import datetime, timedelta

from loguru import logger

from models.log import LogMetaData, LogMetaDataBatch
from storage.document import ElasticSearchRepository


class LogMetaDataManager(ElasticSearchRepository[LogMetaData]):
    """
    日志服务
    """
    PREFIX = "log_metadata_"
    TEMPLATE_NAME = "nginx_log_metadata"

    def __init__(self):
        super().__init__("nginx_log_metadata", LogMetaData)

    def cleanup_indices(self, keep_days: int = 7):
        cutoff = datetime.now() - timedelta(days=keep_days)
        indices = self.get_client().indices.get(index=f"{self.PREFIX}*")
        for index in indices:
            try:
                date_str = index.replace(self.PREFIX, "")
                index_date = datetime.strptime(date_str, "%Y_%m_%d")
                if index_date < cutoff:
                    logger.info(f"Deleting index: {index}")
                    self.get_client().indices.delete(index=index)
            except Exception as e:
                logger.error(f"Error deleting index: {index}: {e}")
                continue

    def create_daily_index(self, index_stuff: str):
        index_name = f"{self.PREFIX}{index_stuff}"
        template = self.get_index_template(index_name=self.TEMPLATE_NAME)
        self.create_index(index_name, template)


class LogMetaDataBatchManager(ElasticSearchRepository[LogMetaDataBatch]):
    """
    日志服务
    """

    def __init__(self):
        super().__init__("log_metadata_batch", LogMetaDataBatch)
