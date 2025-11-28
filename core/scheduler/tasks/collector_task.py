import os
from datetime import datetime
from typing import List

from loguru import logger
from sqlmodel import select

from config import settings
from core.collector.log_collector import Collector
from core.scheduler.task_runner import TaskRunner
from models.log import OffsetConfig
from models.nginx import LogMetaData
from storage.database import DatabaseRepository
from storage.document import ElasticSearchRepository, E


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
        save_status = self.log_metadata_service.metadata_list_save(metadata_list)
        if save_status:
            # 保存文件偏移量
            self.offset_service.update(file_path=file_path, offset=offset)
            logger.info(f"log metadata save success: {len(metadata_list)}")
            return True
        return False


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


class LogMetaDataService(ElasticSearchRepository[LogMetaData]):
    """
    日志服务
    """

    def __init__(self):
        super().__init__("nginx_log_metadata", LogMetaData)

    def metadata_list_save(self, metadata_list: List[LogMetaData]) -> bool:
        now = datetime.now()
        index_name = f"nginx_log_metadata_{now.strftime('%Y_%m_%d')}"
        # 创建索引
        self.acquire_index(index_name, self.get_index_template("nginx_log_metadata"))
        return self.batch_save(metadata_list)
