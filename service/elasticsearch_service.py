from typing import List, TypeVar, Generic, Type, Optional

from loguru import logger
from elasticsearch import helpers
from models.elasticsearch import ElasticsearchModel
from storage import es_client

E = TypeVar("E", bound=ElasticsearchModel)


class ElasticsearchService(Generic[E]):
    """
    ElasticsearchService class
    """

    def __init__(self, index: str, model: Type[E]):
        """
        :param index:
        """
        self.es_client = es_client
        self.index = index
        self.model = model

    def get_all(self) -> List[E]:
        """
        Get all
        """
        records: List[E] = []
        res = self.es_client.search(index=self.index, body={"query": {"match_all": {}}})
        if "hits" not in res:
            return records
        for hit in res["hits"]["hits"]:
            record = self.model(**hit["_source"])
            record.id = hit["_id"]
            records.append(record)
        return records

    def query_list(self, query: dict) -> List[E]:
        """
            列表查询
        """
        records: List[E] = []
        res = self.es_client.search(index=self.index, body=query)
        if "hits" not in res:
            return records
        for hit in res["hits"]["hits"]:
            record = self.model(**hit["_source"])
            record.id = hit["_id"]
            records.append(record)
        return records

    def get_by_id(self, id: str) -> Optional[E]:
        """
        Get record by id
        """
        try:
            res = self.es_client.get(index=self.index, id=id)
        except Exception as e:
            logger.error(e)
            return None

        # ES may return {"found": False}
        if not res.get("found", True) or "_source" not in res:
            return None

        record = self.model(**res["_source"])
        record.id = res["_id"]
        return record

    def delete_by_id(self, id: str) -> bool:
        """
        Delete record by id
        """
        try:
            res = self.es_client.delete(index=self.index, id=id)
        except Exception as e:
            logger.error(e)
            return False
        return res.get("result") == "deleted"

    def save(self, record: E):
        """
        Save record
        """
        try:
            res = self.es_client.index(index=self.index, id=record.id, body=record.model_dump(exclude_none=True))
            return res["result"] in ("created", "updated", "noop")
        except Exception as e:
            logger.error(e)
            return False

    def batch_save(self, records: List[E]) -> bool:
        """
        Batch save records
        """
        try:
            actions = (
                {
                    "_index": self.index,
                    "_source": record.model_dump(exclude_none=True)
                }
                for record in records
            )

            success_count, error = helpers.bulk(
                es_client,
                actions,
                request_timeout=60
            )
            if error:
                logger.error(error)
                return False
            return success_count > 0
        except Exception as e:
            logger.error(e)
            return False

    def count(self, query=None):
        """
        Count records
        """
        if query is None:
            query = {"query": {"match_all": {}}}
        res = self.es_client.count(index=self.index, body=query)
        return res.get("count", 0)
