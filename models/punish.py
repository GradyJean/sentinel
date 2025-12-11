from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import Field

from models.storage.document import ElasticSearchModel


class PunishType(Enum):
    """
    处罚类型
    """
    RATE_LIMIT = "RATE_LIMIT"  # 限速
    NGINX_BAN = "NGINX_BAN"  # Nginx 封禁
    FIREWALL_BAN = "FIREWALL_BAN"  # 防火墙封禁


class PunishLevel(ElasticSearchModel):
    """
    处罚等级
    """
    name: str  # 等级名称
    level: int  # 等级
    level_type: PunishType  # 处罚类型
    score: float  # 评分
    description: str  # 描述
    created_at: Optional[datetime] = None  # 创建时间


class PunishRecord(ElasticSearchModel):
    """
    处罚记录
    """
    ip: str  # IP
    punish_level: PunishLevel  # 处罚等级
    description: str  # 描述
    last_update: Optional[datetime] = Field(default=datetime.now())  # 最后更新时间
