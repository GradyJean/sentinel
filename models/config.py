import re
from datetime import datetime

from pydantic import BaseModel, Field

"""
配置类
"""


class ServerConfig(BaseModel):
    """
    服务配置
    """
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8080)
    base_path: str = Field(default="")
    static_path: str = Field(default="./static")


class NginxConfig(BaseModel):
    """
    Nginx 配置
    """
    base_path: str = Field(...)
    log_path: str = Field(...)
    conf_path: str = Field(...)
    black_list_file: str = Field(...)
    rate_limit_file: str = Field(...)

    def get_log_path(self) -> str:
        # 检查是否包含 ${} 模式
        pattern = r'\$\{([^}]+)\}'
        match = re.search(pattern, self.log_path)

        if match:
            # 提取 ${} 中的内容
            date_format = match.group(1)
            try:
                formatted_date = datetime.now().strftime(date_format)
                return re.sub(pattern, formatted_date, self.log_path)
            except Exception as e:
                raise ValueError("Invalid date format", e)
        else:
            # 不包含 ${} 直接返回
            return self.log_path


class ElasticsearchConfig(BaseModel):
    """
    Elasticsearch 配置
    """
    url: str = Field(default="http://127.0.0.1:9200")
    username: str = Field(default="elastic")
    password: str = Field(None)


class DatabaseConfig(BaseModel):
    """
    数据库配置
    """
    url: str = Field(default="sqlite:///./data/sentinel.db")


class GeoIpConfig(BaseModel):
    """
    geoip 配置
    """
    data_path: str = Field(default="./data/GeoLite2-City.mmdb")
