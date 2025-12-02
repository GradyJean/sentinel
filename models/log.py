from datetime import datetime
from typing import Optional, Self, Any

from pydantic import model_validator, BaseModel
from sqlalchemy import func
from sqlmodel import Field
from enum import Enum
from models.storage.document import ElasticSearchModel
from models.storage.database import DatabaseModel


class OffsetConfig(DatabaseModel, table=True):
    """
    日志采集任务配置
    """
    __tablename__ = "offset_config"
    offset: int = Field(0, description="日志文件偏移量")
    update_time: datetime = Field(default=func.now(), description="更新时间")


class LogMetaData(ElasticSearchModel):
    """
    Log 用于保存 Nginx 日志信息
    示例如下:
    log_format sentinel '$remote_addr||$remote_user||$time_local||$request||$status||'
                    '$request_length||$body_bytes_sent||$http_referer||$http_user_agent||$request_time';
    """
    remote_addr: Optional[str]  # 客户端IP地址
    remote_user: Optional[str]  # 远程用户标识
    time_local: Optional[datetime]  # 请求时间
    request: Optional[str]  # 请求行（方法、URL、协议）
    status: Optional[int]  # 响应状态码
    request_length: Optional[int]  # 请求长度
    body_bytes_sent: Optional[int]  # 发送给客户端的字节数
    http_referer: Optional[str]  # 引用页URL
    http_user_agent: Optional[str]  # 用户代理信息
    request_time: Optional[int]  # 请求处理时间（毫秒）
    batch_id: Optional[str]  # 批次ID

    @classmethod
    def parse(cls, log_line: str, delimiter: str = "||") -> Self:
        """
        解析日志行，按 Nginx log_format sentinel格式
        Args:
            log_line 日志行
            delimiter 分隔符 默认 ||
        """
        log_line = log_line.strip()
        parts = log_line.split(delimiter)

        # 必须正好 10 个（允许为空但必须存在）
        if len(parts) != 10:
            raise ValueError(f"日志格式错误：字段数量应为 10 个，实际为 {len(parts)} —— {log_line}")

        # 不允许缺失字段（必须是 "" 或实际值）
        for idx, p in enumerate(parts):
            if p is None:
                raise ValueError(f"日志第 {idx} 个字段缺失（None），日志内容：{log_line}")

        return LogMetaData(
            remote_addr=parts[0] if parts[0] != "" else None,
            remote_user=parts[1] if parts[1] != "" else None,
            time_local=(
                datetime.strptime(parts[2], "%d/%b/%Y:%H:%M:%S %z")
                if parts[2] != "" else None
            ),
            request=parts[3] if parts[3] != "" else None,
            status=int(parts[4]) if parts[4] != "" else None,
            request_length=int(parts[5]) if parts[5] != "" else None,
            body_bytes_sent=int(parts[6]) if parts[6] != "" else None,
            http_referer=parts[7] if parts[7] != "" else None,
            http_user_agent=parts[8] if parts[8] != "" else None,
            request_time=int(float(parts[9]) * 1000) if parts[9] != "" else None,
            batch_id=None
        )

    @model_validator(mode="after")
    def auto_fix(self) -> Self:
        self.batch_id = self.get_batch_id(self.time_local)
        return self

    @staticmethod
    def get_batch_id(time: datetime, interval: int = 5) -> str:
        total_minutes = time.hour * 60 + time.minute
        rounded_minutes = (total_minutes // interval) * interval
        # 生成取整后的datetime对象（保留原日期，截断秒和微秒）
        rounded_datetime = time.replace(
            hour=rounded_minutes // 60,
            minute=rounded_minutes % 60,
            second=0,
            microsecond=0
        )
        return rounded_datetime.strftime("%Y_%m_%d%H%M")


class CollectEventType(Enum):
    """
    日志采集事件类型
    """
    DATE_CHANGED = "DATE_CHANGED"  # 日期改变
    BATCH_CHANGED = "BATCH_CHANGED"  # 批次改变


class CollectEventData(BaseModel):
    """
    日志采集事件数据
    """
    last: Optional[Any]  # 上一次数据
    current: Optional[Any]  # 当前数据


class CollectEvent(BaseModel):
    """
    日志采集事件
    """
    event_type: CollectEventType
    data: CollectEventData


class BatchStatus(Enum):
    """
    批次状态
    """
    COLLECTING = "COLLECTING"  # 正在采集
    COLLECTED = "COLLECTED"  # 已采集
    PROCESSING = "PROCESSING"  # 处理中
    COMPLETED = "COMPLETED"  # 处理完成
    FAILED = "FAILED"  # 处理失败


class LogMetaDataBatch(ElasticSearchModel):
    """
    日志批次信息
    """
    batch_id: str  # 批次ID
    status: BatchStatus  # 批次状态
