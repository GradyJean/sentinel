from models.aggregator import AccessIpAggregation
from storage.document import ElasticSearchRepository


class AccessIpAggregationService(ElasticSearchRepository[AccessIpAggregation]):
    """
    访问IP聚合服务
    """
    PREFIX = "log_metadata_"

    def __init__(self):
        super().__init__("access_ip_aggregation", AccessIpAggregation)

    def query_access_ip_aggregation(self, batch_id: str):
        """
        查询指定IP的访问聚合信息
        """
        index_name = f"{self.PREFIX}{batch_id[:10]}"
        query = {
            "from": 0,
            "size": 0,
            "query": {
                "term": {
                    "batch_id": f"{batch_id}"
                }
            },
            "aggregations": {
                "ip": {
                    "composite": {
                        "size": 1000,
                        "sources": [
                            {
                                "remote_addr": {
                                    "terms": {
                                        "field": "remote_addr"
                                    }
                                }
                            }
                        ]
                    },
                    "aggregations": {
                        "status": {
                            "terms": {
                                "field": "status"
                            }
                        },
                        "path": {
                            "terms": {
                                "field": "path"
                            }
                        },
                        "path_categories": {
                            "terms": {
                                "field": "path_type"
                            }
                        },
                        "request_length": {
                            "extended_stats": {
                                "field": "request_length"
                            }
                        },
                        "body_bytes_sent": {
                            "extended_stats": {
                                "field": "body_bytes_sent"
                            }
                        },
                        "request_time": {
                            "extended_stats": {
                                "field": "request_time"
                            }
                        },
                        "referer_categories": {
                            "filters": {
                                "filters": {
                                    "empty_referer": {
                                        "term": {
                                            "http_referer.keyword": "-"
                                        }
                                    },
                                    "non_empty_referer": {
                                        "bool": {
                                            "must_not": {
                                                "term": {
                                                    "http_referer.keyword": "-"
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        },
                        "http_user_agent": {
                            "terms": {
                                "field": "http_user_agent.keyword"
                            }
                        }
                    }
                }
            }
        }
        res = self.get_client().search(index=index_name, body=query)
        print(res)
