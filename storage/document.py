from datetime import datetime
from typing import List, TypeVar, Any, Optional, Type

from elasticsearch import Elasticsearch, helpers
from loguru import logger
from pydantic import BaseModel

from config import settings
from models.elasticsearch import *
from models.scheduler import TaskScheduler
from models.score import ScoreRule, ScoreType
from models.storage.document import ElasticSearchModel
from storage.repository import IRepository

http_auth = None
if settings.elasticsearch.username and settings.elasticsearch.password:
    http_auth = (settings.elasticsearch.username, settings.elasticsearch.password)
es_client: Elasticsearch = Elasticsearch(settings.elasticsearch.url,
                                         http_auth=http_auth)

E = TypeVar("E", bound=ElasticSearchModel)


class ElasticSearchRepository(IRepository[E]):
    def __init__(self, index: str, model: Type[E]):
        """
        :param index:
        """
        super().__init__(model)
        if index is None:
            raise ValueError("Repository must specify a index")
        self.index = index

    def get_all(self, query: Optional[dict] = None, index: str = None) -> List[E]:
        records: List[E] = []
        page_size = 1000

        # if user didn't pass query, default to match_all
        if query is None:
            query = {"query": {"match_all": {}}}

        # initial search with scroll
        resp = es_client.search(
            index=self.index if index is None else index,
            body=query,
            scroll="1m",
            size=page_size
        )

        scroll_id = resp.get("_scroll_id")
        hits = resp["hits"]["hits"]

        while hits:
            for hit in hits:
                record = self.model(**hit["_source"])
                record.id = hit["_id"]
                records.append(record)

            resp = es_client.scroll(scroll_id=scroll_id, scroll="1m")
            scroll_id = resp.get("_scroll_id")
            hits = resp["hits"]["hits"]

        # clear scroll context
        try:
            es_client.clear_scroll(scroll_id=scroll_id)
        except Exception as e:
            logger.error(e)

        return records

    def query_list(self, query: Any, index: str = None) -> List[E]:
        records: List[E] = []
        res = es_client.search(index=self.index if index is None else index, body=query)
        if "hits" not in res:
            return records
        for hit in res["hits"]["hits"]:
            record = self.model(**hit["_source"])
            record.id = hit["_id"]
            records.append(record)
        return records

    def get_by_id(self, id: str, index: str = None) -> Optional[E]:
        try:
            res = es_client.get(index=self.index if index is None else index, id=id)
        except Exception as e:
            logger.error(e)
            return None

        # ES may return {"found": False}
        if not res.get("found", True) or "_source" not in res:
            return None

        record = self.model(**res["_source"])
        record.id = res["_id"]
        return record

    def delete_by_id(self, id: str, index: str = None) -> bool:
        try:
            res = es_client.delete(index=self.index if index is None else index, id=id)
        except Exception as e:
            logger.error(e)
            return False
        return res.get("result") == "deleted"

    def merge(self, record: E, index: str = None) -> bool:
        try:
            res = es_client.update(
                index=self.index if index is None else index,
                id=record.id,
                doc=record.model_dump(exclude_none=True, mode="json"),
                doc_as_upsert=True,
                retry_on_conflict=3
            )
            return res["result"] in ("created", "updated", "noop")
        except Exception as e:
            logger.error(e)
            return False

    def batch_insert(self, records: List[E], index: str = None) -> bool:
        """
        批量添加IP记录
        """
        if len(records) == 0:
            return True
        try:
            actions = (
                {
                    "_index": self.index if index is None else index,
                    "_source": record.model_dump(exclude_none=True)
                }
                for record in records
            )

            success_count, error = helpers.bulk(
                es_client,
                actions,
                chunk_size=1000,
                request_timeout=60,
                raise_on_error=True,
                raise_on_exception=True,
                error_trace=True
            )
            if error:
                logger.error(error)
                return False
            return success_count > 0
        except Exception as e:
            logger.error(f"{self.index} batch insert error: {e}")
            return False

    def batch_merge(self, records: List[E], index: str = None) -> bool:
        """
          批量添加IP记录
          """
        try:
            actions = (
                {
                    "_op_type": "update",
                    "_index": self.index if index is None else index,
                    "_id": record.id,
                    "doc": record.model_dump(exclude_none=True, mode="json"),
                    "doc_as_upsert": True
                }
                for record in records
            )

            success_count, error = helpers.bulk(
                self.get_client(),
                actions,
                chunk_size=1000,
                request_timeout=60
            )
            if error:
                logger.error(error)
                return False
            return success_count > 0
        except Exception as e:
            logger.error(e)
            return False

    def count(self, query: Any = None, index: str = None) -> int:
        if query is None:
            query = {"query": {"match_all": {}}}
        res = es_client.count(index=self.index if index is None else index, body=query)
        return res.get("count", 0)

    def create_index(self, index_name: str, index_template: dict):
        """
        创建索引
        :param index_name:
        :param index_template:
        :return:
        """
        self.index = index_name
        if es_client.indices.exists(index=index_name):
            return
        res = es_client.indices.create(index=index_name, body=index_template)
        acknowledged = res.get('acknowledged')
        if acknowledged:
            logger.info(f"{index_name} index create: {acknowledged}")
        else:
            raise Exception(f"{index_name} index create error: {res}")

    @staticmethod
    def get_index_template(index_name: str) -> dict:
        """
        获取索引模板
        :param index_name:
        :return:
        """
        return index_template_dict[index_name]["value"]

    @staticmethod
    def get_client():
        return es_client


index_template_dict = {
    "nginx_log_metadata": {"value": daily_nginx_metadata_template, "init": False},
    "allowed_ip_segment": {"value": allowed_ip_segment_template, "init": True},
    "log_metadata_batch": {"value": log_metadata_batch_template, "init": True},
    "task_scheduler": {"value": task_scheduler_template, "init": True},
    "access_ip_aggregation": {"value": access_ip_aggregation_template, "init": False},
    "score_rule": {"value": score_rule_template, "init": True},
    "score_record": {"value": score_record_template, "init": True},
    "score_aggregate": {"value": score_aggregate_template, "init": True},
    "punish_level": {"value": punish_level_template, "init": True},
    "punish_record": {"value": punish_record_template, "init": True}
}


def init_elasticsearch():
    """
    初始化索引
    :return:
    """
    # 索引初始化
    for index_name, template in index_template_dict.items():
        if es_client.indices.exists(index=index_name):
            continue
        else:
            if not template["init"]:
                continue
            res = es_client.indices.create(index=index_name, body=template["value"])
            acknowledged = res.get('acknowledged')
            if acknowledged:
                logger.info(f"{index_name} index init: {acknowledged}")
            else:
                raise Exception(f"{index_name} index init error: {res}")
    # 定时任务初始化
    __init_task_scheduler()
    # 评分规则初始化
    __score_role_init()


def __init_task_scheduler():
    """
        定时调度初始化
    """
    configs: List[TaskScheduler] = [
        TaskScheduler(
            id="daily_task",
            task_id="daily_task",
            task_name="每日定时任务",
            enabled=True,
            cron="30 0 * * *",
            description="每日定时任务,用于做一些日常任务"
        ),
        TaskScheduler(
            id="log_collector",
            task_id="log_collector",
            task_name="Nginx日志采集",
            enabled=True,
            cron="*/5 * * * *",
            description="Nginx日志采集 每5分钟执行一次 0开始触发"
        ),
        TaskScheduler(
            id="log_aggregator",
            task_id="log_aggregator",
            task_name="聚合日志任务",
            enabled=True,
            cron="1-59/5 * * * *",
            description="Nginx 元数据聚合任务 每5分钟执行一次 从第一分钟开始触发 延时于采集任务"
        ),
        TaskScheduler(
            id="score_task",
            task_id="score_task",
            task_name="ip评分任务",
            enabled=True,
            cron="2-59/5 * * * *",
            description="评分任务 每5分钟执行一次 从第二分钟开始触发 延时于聚合任务"
        ),
        TaskScheduler(
            id="punish_task",
            task_id="punish_task",
            task_name=" ip 惩处任务",
            enabled=True,
            cron="3-59/5 * * * *",
            description="惩处任务 每5分钟执行一次 从第三分钟开始触发 延时于评分任务"
        ),
    ]
    data_init("task_scheduler", configs)


def __score_role_init():
    """
    初始化评分规则
    :return:
    """
    score_rules: List[ScoreRule] = [
        ScoreRule(
            id="dynamic_count_high",
            rule_name="high_request_count",
            score_type=ScoreType.DYNAMIC,
            condition="count > 500",
            formula="2",
            description="count 大于 500 加分",
            enabled=True,
            created_at=datetime.now(),
            updated_at=datetime.now()
        ),
        ScoreRule(
            id="dynamic_static_zero",
            rule_name="no_static_requests",
            score_type=ScoreType.DYNAMIC,
            condition="path_categories_STATIC == 0",
            formula="2",
            description="静态页面为0",
            enabled=True,
            created_at=datetime.now(),
            updated_at=datetime.now()
        ),
        ScoreRule(
            id="dynamic_path_size_low",
            rule_name="few_paths_accessed",
            score_type=ScoreType.DYNAMIC,
            condition="path_size <= 2",
            formula="2",
            description="路径数量小于等于2",
            enabled=True,
            created_at=datetime.now(),
            updated_at=datetime.now()
        ),
        ScoreRule(
            id="dynamic_ua_count_high",
            rule_name="many_user_agents",
            score_type=ScoreType.DYNAMIC,
            condition="http_user_agent_size >= 5",
            formula="2",
            description="ua 多于5个",
            enabled=True,
            created_at=datetime.now(),
            updated_at=datetime.now()
        ),
        ScoreRule(
            id="dynamic_referer_low",
            rule_name="low_referer_usage",
            score_type=ScoreType.DYNAMIC,
            condition="referer_categories_non_empty_referer <= 1",
            formula="2",
            description="referer 有值的小于等于1",
            enabled=True,
            created_at=datetime.now(),
            updated_at=datetime.now()
        ),
        ScoreRule(
            id="dynamic_status_200_zero",
            rule_name="no_successful_requests",
            score_type=ScoreType.DYNAMIC,
            condition="status_200 <= 0",
            formula="5",
            description="状态码200等于0",
            enabled=True,
            created_at=datetime.now(),
            updated_at=datetime.now()
        ),
        ScoreRule(
            id="dynamic_status_200_ratio_low",
            rule_name="low_success_rate",
            score_type=ScoreType.DYNAMIC,
            condition="status_200 / count <= 0.5",
            formula="5",
            description="请求状态码200比例小于0.5",
            enabled=True,
            created_at=datetime.now(),
            updated_at=datetime.now()
        ),
        ScoreRule(
            id="dynamic_normal_path_ratio_high",
            rule_name="high_normal_path_ratio",
            score_type=ScoreType.DYNAMIC,
            condition="path_categories_NORMAL / count >=0.7",
            formula="5",
            description="NORMAL 比例大于0.7",
            enabled=True,
            created_at=datetime.now(),
            updated_at=datetime.now()
        ),
    ]

    data_init("score_rule", score_rules)


def data_init(index_name: str, data: List[BaseModel]):
    """
    初始化数据
    :param index_name:
    :param data:
    :return:
    """
    res = es_client.count(index=index_name, body={"query": {"match_all": {}}})
    if res.get("count") > 0:
        return

    actions = (
        {
            "_op_type": "update",
            "_index": index_name,
            "_id": record.id,
            "doc": record.model_dump(exclude_none=True, mode="json"),
            "doc_as_upsert": True
        }
        for record in data
    )

    success_count, error = helpers.bulk(
        es_client,
        actions,
        request_timeout=60
    )
    es_client.indices.refresh(index=index_name)
    if error:
        raise Exception(error)
