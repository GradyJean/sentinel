from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel, Field


class IPRecord(SQLModel, table=True):
    """
    数据库表模型：IP 检测结果记录
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    ip: str
    req_count: int
    uri_count: int
    status_404_ratio: float
    score: float
    is_anomaly: bool
    timestamp: datetime
