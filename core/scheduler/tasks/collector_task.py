from datetime import datetime
from typing import List

from loguru import logger

from config import settings
from core.collector.log_collector import Collector
from core.scheduler.task_runner import TaskRunner
from models.nginx import LogMetaData
from service.log_metadata_service import LogMetaDataService
from service.offset_service import OffsetsService


class LogCollectorTask(TaskRunner):
    """
    日志采集任务
    """
    task_id: str = "log_collector"

    def __init__(self):
        self.offset_service = OffsetsService()
        self.log_metadata_service = LogMetaDataService()
        self.collector = Collector(
            call_back=self.metadata_callback,
        )

    async def run(self):
        file_path = settings.nginx.get_log_path()
        # 文件偏移量
        offset = 0
        curr_date = datetime.now().strftime("%Y-%m-%d")
        # 获取文件偏移量配置
        offset_config = self.offset_service.get()
        # 不是今天的文件直接偏移量归零
        if offset_config and offset_config.collect_date == curr_date:
            offset = offset_config.offset
        # 文件采集并返回偏移量
        offset = self.collector.start(file_path=file_path, offset=offset)
        # 保存文件偏移量
        self.offset_service.update(file_path=file_path, offset=offset)

    def metadata_callback(self, metadata_list: List[LogMetaData], file_path: str, offset: int) -> bool:
        save_status = self.log_metadata_service.batch_insert(metadata_list)
        if save_status:
            # 保存文件偏移量
            self.offset_service.update(file_path=file_path, offset=offset)
            logger.info(f"log metadata save success: {len(metadata_list)}")
            return True
        return False
