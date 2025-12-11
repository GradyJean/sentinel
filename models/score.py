from datetime import datetime
from enum import Enum
from typing import Optional, List, Self

from pydantic import BaseModel, Field, model_validator

from models.storage.document import ElasticSearchModel


class ScoreType(Enum):
    """
    评分类型
    """
    FIXED = "FIXED"  # 固定
    DYNAMIC = "DYNAMIC"  # 动态
    FEATURE = "FEATURE"  # 特征


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


class ScoreDetail(BaseModel):
    """
    评分详情
    """
    score_rule_name: str
    score: float
    description: str


class ScoreRecord(ElasticSearchModel):
    """
    评分记录
    """
    ip: str  # IP
    score_fixed: float = 0  # 固定评分
    score_dynamic: float = 0  # 动态评分
    score_feature: float = 0  # 特征评分
    score_details: List[ScoreDetail] = Field(default_factory=list)  # 评分详情
    batch_id: str = Field(default="")  # 批次ID


class ScoreAggregate(ElasticSearchModel):
    """
    评分聚合
    """
    ip: str  # IP
    score_fixed: float = 0  # 固定评分
    score_dynamic: float = 0  # 动态评分
    score_feature: float = 0  # 特征评分
    score_total: float = 0  # 总评分
    last_update: datetime = Field(default=datetime.now())

    @model_validator(mode="after")
    def auto_fix(self) -> Self:
        self.score_total = self.score_fixed + self.score_dynamic + self.score_feature
