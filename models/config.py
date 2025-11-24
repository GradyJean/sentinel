from pydantic import BaseModel

"""
配置类
"""


class ServerConfig(BaseModel):
    """
    服务配置
    """
    host: str
    port: int
    base_path: str
    static_path: str


class NginxConfig(BaseModel):
    """
    Nginx 配置
    """
    base_path: str
    log_path: str
    conf_path: str


class ElasticsearchConfig(BaseModel):
    """
    Elasticsearch 配置
    """
    host: str
    port: int
    username: str
    password: str
