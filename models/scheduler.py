from datetime import datetime
from typing import Optional
from models.elasticsearch import ElasticsearchModel
from typing import Optional

from models.elasticsearch import ElasticsearchModel


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
    last_run_at: Optional[datetime] = None  # 最近执行时间
    last_status: Optional[str] = None  # 执行状态：success/failed/skipped
    last_message: Optional[str] = None  # 错误信息或执行信息
    last_cost: Optional[int] = None  # 执行时间（秒）
    run_count: Optional[int] = 0  # 执行次数
