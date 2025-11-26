from datetime import datetime
from enum import Enum
from typing import Optional

from models.elasticsearch import ElasticsearchModel


class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    FAILED = "failed"
    SUCCESS = "success"
    SKIPPED = "skipped"
    CANCELED = "canceled"


class TaskScheduler(ElasticsearchModel):
    """
    任务调度配置模型
    对应 ES task_scheduler 索引
    """
    task_id: str  # 任务唯一 ID
    task_name: Optional[str] = None  # 任务名称（展示用）
    enabled: bool = True  # 是否启用任务
    cron: Optional[str] = None  # Cron 表达式
    description: Optional[str] = None  # 任务描述
    start_time: Optional[datetime] = None  # 最近执行时间
    end_time: Optional[datetime] = None  # 最近执行时间
    status: Optional[TaskStatus] = None  # 执行状态：success/failed/skipped
    message: Optional[str] = None  # 错误信息或执行信息
    batch_id: Optional[str] = None  # 批次号
