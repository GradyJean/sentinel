from datetime import datetime, timedelta
from typing import List

from loguru import logger

from models.score import ScoreRule, ScoreRecord, ScoreAggregate
from storage.document import ElasticSearchRepository


class ScoreRuleManager(ElasticSearchRepository[ScoreRule]):
    """
    分数规则服务
    """

    def __init__(self):
        super().__init__("score_rule", ScoreRule)


class ScoreRecordManager(ElasticSearchRepository[ScoreRecord]):
    """
    分数记录服务
    """
    PREFIX = "score_record_"
    TEMPLATE_NAME = "score_record_template"

    def __init__(self):
        super().__init__("score_record", ScoreRecord)

    def create_daily_index(self, index_stuff: str):
        index_name = f"{self.PREFIX}{index_stuff}"
        template = self.get_index_template(index_name=self.TEMPLATE_NAME)
        self.create_index(index_name, template)

    def get_all_by_batch_id(self, batch_id: str) -> List[ScoreRecord]:
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


class ScoreAggregateManager(ElasticSearchRepository[ScoreAggregate]):
    """
    分数聚合服务
    """

    def __init__(self):
        super().__init__("score_aggregate", ScoreAggregate)
