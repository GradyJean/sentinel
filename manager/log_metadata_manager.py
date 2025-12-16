from datetime import datetime, timedelta
from typing import List

from loguru import logger

from models.log import LogMetaData, LogMetaDataBatch, BatchStatus
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

    def get_all_by_batch_id(self, batch_id: str) -> List[LogMetaData]:
        """
        通过批次ID查询
        :param batch_id:
        :return:
        """
        index_name = f"{self.PREFIX}{batch_id[:10]}"
        query = {
            "query": {
                "term": {
                    "batch_id": batch_id
                }
            }
        }
        return self.get_all(query=query, index=index_name)

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

    def get_all_by_status(self, status: BatchStatus) -> List[LogMetaDataBatch]:
        query = {
            "query": {
                "term": {
                    "status": f"{status.value}"
                }
            }, "sort": [
                {
                    "batch_id": {
                        "order": "asc"
                    }
                }]
        }
        return self.get_all(query=query)

    def cleanup_records(self, keep_days: int = 7):
        cutoff_date = datetime.now() - timedelta(days=keep_days)
        cutoff_str = cutoff_date.strftime("%Y_%m_%d")
        # 查询所有批次记录，使用通配符匹配日期前缀
        query = {
            "query": {
                "range": {
                    "batch_id": {
                        "lt": f"{cutoff_str}_23:59"  # 使用截止日期的最大时间
                    }
                }
            }
        }
        # 删除符合条件的记录
        try:
            self.get_client().delete_by_query(
                index=self.index,
                body=query,
                conflicts="proceed"
            )
            logger.info(f"Deleted records older than {keep_days} days")
        except Exception as e:
            logger.error(f"Error deleting old records: {e}")
