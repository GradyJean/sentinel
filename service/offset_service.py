from datetime import datetime

from models import OffsetConfig
from storage.database import DatabaseRepository


class OffsetsService(DatabaseRepository[OffsetConfig]):
    """
    日志采集任务服务
    """
    offsets_id: str = "log_collect"

    def __init__(self):
        super().__init__(OffsetConfig)

    def get(self) -> OffsetConfig:
        """
        获取日志文件偏移量
        """
        return self.get_by_id(self.offsets_id)

    def update(self, file_path: str, offset: int = 0):
        """
        保存日志文件偏移量
        """

        now = datetime.now()
        self.merge(OffsetConfig(
            id=self.offsets_id,
            file_path=file_path,
            offset=offset,
            update_time=now,
            collect_date=now.strftime("%Y-%m-%d")
        ))
