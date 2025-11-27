from datetime import datetime

from elasticsearch import Elasticsearch, helpers
from loguru import logger
from typing import List
from models.scheduler import TaskScheduler
from config import settings
from models.elasticsearch import *

es_client: Elasticsearch = Elasticsearch(settings.elasticsearch.url,
                                         http_auth=(settings.elasticsearch.username,
                                                    settings.elasticsearch.password))

index_template_dict = {
    "nginx_log_metadata": daily_nginx_metadata_template,
    "allowed_ip_segment": allowed_ip_segment_template,
    "ip_record": ip_record_template,
    "ip_policy": ip_policy_template,
    "task_scheduler": task_scheduler_template
}


def elasticsearch_index_init():
    """
    初始化索引
    :return:
    """
    # 索引初始化
    current_date = datetime.now().strftime("%Y_%m_%d")
    for index_name, template in index_template_dict.items():
        if index_name == "nginx_log_metadata":
            index_name = f"{index_name}_{current_date}"
        if es_client.indices.exists(index=index_name):
            continue
        else:
            res = es_client.indices.create(index=index_name, body=template)
            acknowledged = res.get('acknowledged')
            if acknowledged:
                logger.info(f"{index_name} index init: {acknowledged}")
            else:
                raise Exception(f"{index_name} index init error: {res}")
    # 定时任务初始化
    task_scheduler_init()


def task_scheduler_init():
    """
        定时调度初始化
    """
    configs: List[TaskScheduler] = [
        TaskScheduler(
            task_id="log_collector",
            task_name="Nginx日志采集",
            enabled=True,
            cron="*/30 * * * *",
            description="Nginx日志采集 每30分钟执行一次"
        ),
    ]
    data_init("task_scheduler", configs)


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
            "_index": index_name,
            "_source": record.model_dump(exclude_none=True)
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
