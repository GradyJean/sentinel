from datetime import datetime

from sqlalchemy import func
from sqlmodel import Field

from models.storage.database import DatabaseModel


class OffsetConfig(DatabaseModel, table=True):
    """
    日志采集任务配置
    """
    __tablename__ = "offset_config"
    file_path: str = Field(..., description="日志文件路径", unique=True)
    offset: int = Field(0, description="日志文件偏移量")
    update_time: datetime = Field(default=func.now(), description="更新时间")
    collect_date: str = Field(default="", description="采集日期")
    count: int = Field(default=0, description="计数")
