from typing import Dict, Optional

from pydantic import BaseModel, Field


class ElasticsearchModel(BaseModel):
    """
    ElasticsearchModel 用于查询 ES 库继承
    """
    id: Optional[str] = Field(default=None, exclude=True)


"""
    每天生成新索引
    nginx日志格式如下:
    log_format sentinel '$remote_addr||$remote_user||$time_local||$request||$status||'
                '$request_length||$body_bytes_sent||$http_referer||$http_user_agent||$request_time';

    详情请参考: models.nginx.LogMetaData

    remote_addr: Optional[str]      # 客户端IP地址
    remote_user: Optional[str]      # 远程用户标识
    time_local: Optional[datetime]  # 请求时间
    request: Optional[str]          # 请求行（方法、URL、协议）
    status: Optional[int]           # 响应状态码
    request_length: Optional[int]   # 请求长度
    body_bytes_sent: Optional[int]  # 发送给客户端的字节数
    http_referer: Optional[str]     # 引用页URL
    http_user_agent: Optional[str]  # 用户代理信息
    request_time: Optional[int]     # 请求处理时间（毫秒）
"""

daily_nginx_metadata_template: Dict = {
    "settings": {
        "number_of_shards": 5,
        "number_of_replicas": 0
    },
    "mappings": {
        "dynamic": "strict",
        "properties": {
            "remote_addr": {
                "type": "ip"
            },
            "remote_user": {
                "type": "keyword",
                "ignore_above": 256
            },
            "time_local": {
                "type": "date",
                "format": "strict_date_optional_time||epoch_millis||yyyy-MM-dd HH:mm:ss||yyyy-MM-dd'T'HH:mm:ss.SSSZ"
            },
            "request": {
                "type": "text",
                "fields": {
                    "keyword": {
                        "type": "keyword",
                        "ignore_above": 1024
                    }
                }
            },
            "status": {
                "type": "integer"
            },
            "request_length": {
                "type": "integer"
            },
            "body_bytes_sent": {
                "type": "long"
            },
            "http_referer": {
                "type": "text",
                "fields": {
                    "keyword": {
                        "type": "keyword",
                        "ignore_above": 1024
                    }
                }
            },
            "http_user_agent": {
                "type": "text",
                "fields": {
                    "keyword": {
                        "type": "keyword",
                        "ignore_above": 1024
                    }
                }
            },
            "request_time": {
                "type": "integer"
            }
        }
    }
}
"""
    例:
    "org_name": "扬州大学图书馆",  #机构名称
    "is_internal": false,       #是否内网
    "start_ip": "202.195.48.0", #起始ip
    "end_ip": "202.195.63.255", #结束ip
    "cidr": "202.195.48.0/20",  #CIDR ip段
    "tags": ["university"]      #标签
    
    详情请参考: models.ip.AllowedIpSegment
    
"""
allowed_ip_segment_template: Dict = {
    "settings": {
        "number_of_shards": 5,
        "number_of_replicas": 0
    },
    "mappings": {
        "dynamic": "strict",
        "properties": {
            "org_name": {
                "type": "keyword"
            },
            "is_internal": {
                "type": "boolean"
            },
            "start_ip": {
                "type": "ip"
            },
            "end_ip": {
                "type": "ip"
            },
            "cidr": {
                "type": "keyword"
            }
        }
    }
}
"""
    ip 记录索引
    用于存储涉及到的ip信息
    models.ip.IpRecord
"""
ip_record_template: Dict = {
    "settings": {
        "number_of_shards": 5,
        "number_of_replicas": 0
    },
    "mappings": {
        "dynamic": "strict",
        "properties": {

            "ip": {
                "type": "ip"
            },

            "location": {
                "type": "keyword"
            },

            "isp": {
                "type": "keyword"
            },

            "scene": {
                "type": "keyword"
            },

            "risk_tags": {
                "type": "keyword"
            }
        }
    }
}
"""
    ip 策略
    用于存储限速和黑名单
    models.ip.IpPolicy
"""
ip_policy_template = {
    "settings": {
        "number_of_shards": 5,
        "number_of_replicas": 0
    },
    "mappings": {
        "dynamic": "strict",
        "properties": {

            "policy_type": {
                "type": "keyword"
            },

            "start_ip": {
                "type": "ip"
            },
            "end_ip": {
                "type": "ip"
            },
            "cidr": {
                "type": "keyword"
            },

            "reason": {
                "type": "text"
            },
            "manual": {
                "type": "boolean"
            },

            "rate_limit": {
                "type": "integer"
            },
            "created_at": {
                "type": "date",
                "format": "strict_date_optional_time||epoch_millis"
            },
            "expire_at": {
                "type": "date",
                "format": "strict_date_optional_time||epoch_millis"
            },

            "tags": {
                "type": "keyword"
            }
        }
    }
}
"""
    任务调度模板
    详情参考: models.scheduler.TaskScheduler
"""
task_scheduler_template = {
    "settings": {
        "number_of_shards": 5,
        "number_of_replicas": 0
    },
    "mappings": {
        "dynamic": "strict",
        "properties": {

            "task_id": {
                "type": "keyword"
            },
            "task_name": {
                "type": "keyword"
            },
            "enabled": {
                "type": "boolean"
            },

            "cron": {
                "type": "keyword"
            },
            "description": {
                "type": "text"
            },
            "start_time": {
                "type": "date",
                "format": "strict_date_optional_time||epoch_millis"
            },
            "end_time": {
                "type": "date",
                "format": "strict_date_optional_time||epoch_millis"
            },
            "status": {
                "type": "keyword"
            },

            "message": {
                "type": "text"
            },
            "batch_id": {
                "type": "keyword"
            }
        }
    }
}
