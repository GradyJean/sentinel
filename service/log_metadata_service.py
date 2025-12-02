from datetime import datetime

from models.log import LogMetaData, LogMetaDataBatch
from storage.document import ElasticSearchRepository


class LogMetaDataService(ElasticSearchRepository[LogMetaData]):
    """
    日志服务
    """

    def __init__(self):
        super().__init__("nginx_log_metadata", LogMetaData)


class LogMetaDataBatchService(ElasticSearchRepository[LogMetaDataBatch]):
    """
    日志服务
    """

    def __init__(self):
        super().__init__("log_metadata_batch", LogMetaDataBatch)
