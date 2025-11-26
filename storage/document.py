from datetime import datetime

from elasticsearch import Elasticsearch
from loguru import logger

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
    current_date = datetime.now().strftime("%Y_%m_%d")
    for index_name, template in index_template_dict.items():
        if index_name == "nginx_log_metadata":
            index_name = f"{index_name}_{current_date}"
        if es_client.indices.exists(index=index_name):
            continue
        else:
            res = es_client.indices.create(index=index_name, body=template)
            if res.get('acknowledged'):
                logger.info(f"{index_name} index init: {res}")
            else:
                raise Exception(f"{index_name} index init error: {res}")
