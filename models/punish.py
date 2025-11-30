from datetime import datetime
from enum import Enum
from typing import Optional, List

from pydantic import BaseModel, Field

from models import ElasticSearchModel


class ScoreType(Enum):
    """
    评分类型
    """
    DEDUCTIBLE = "DEDUCTIBLE"  # 可扣除规则
    PERMANENT = "PERMANENT"  # 不可扣除规则


class ScoreRule(ElasticSearchModel):
    """
    评分规则
    """
    rule_name: str  # 规则名称
    score_type: ScoreType  # 评分类型
    condition: str  # 条件
    formula: str  # 公式
    description: str  # 描述
    created_at: Optional[datetime] = None  # 创建时间
    updated_at: Optional[datetime] = None  # 更新时间
    enabled: bool = True  # 是否启用


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
    created_at: Optional[datetime] = None  # 创建时间
    expire_at: Optional[datetime] = None  # 过期时间
    enabled: bool = True  # 是否启用


class ScoreDetail(BaseModel):
    """
    评分详情
    """
    score_rule: ScoreRule
    score: float
    description: str
    created_at: Optional[datetime] = None


class ScoreRecord(ElasticSearchModel):
    """
    评分记录
    """
    ip: str  # IP
    deductible_score: float = 0  # 可扣除分数
    permanent_score: float = 0  # 不可扣除分数
    score_details: List[ScoreDetail] = Field(default_factory=list)  # 评分详情
