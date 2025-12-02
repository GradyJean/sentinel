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

    def save_offset(self, offset: int) -> bool:
        """
        更新日志文件偏移量
        """
        return self.merge(OffsetConfig(id=self.offsets_id, offset=offset))
