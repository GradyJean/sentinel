from typing import List
from threading import Lock
from loguru import logger

from config import settings
from core.collector.log_collector import Collector
from core.scheduler.task_runner import TaskRunner
from models.log import LogMetaData, LogMetaDataBatch, BatchStatus, CollectEvent, CollectEventType
from service.log_metadata_service import LogMetaDataService, LogMetaDataBatchService
from service.offset_service import OffsetsService


class LogCollectorTask(TaskRunner):
    """
    日志采集任务
    """
    task_id: str = "log_collector"
    current_file_path: str = settings.nginx.get_log_path()
    file_path_changed: bool = False
    _lock = Lock()  # 类级别锁

    def __init__(self):
        self.offset_service = OffsetsService()
        self.log_metadata_service = LogMetaDataService()
        self.log_metadata_batch_service = LogMetaDataBatchService()
        self.collector = Collector(
            data_callback=self.log_metadata_callback,
            event_callback=self.event_listener
        )

    def run(self):
        with self._lock:
            self._run_safe()

    def _run_safe(self):
        file_path = settings.nginx.get_log_path()
        offset_config = self.offset_service.get()
        offset = offset_config.offset

        if file_path != self.current_file_path:
            logger.info(f"file path change to: {file_path}")
            file_path = self.current_file_path
            logger.info(f"reset file path: {file_path}")
            self.file_path_changed = True
            logger.info(f"set file path change status:{self.file_path_changed}")
            self.current_file_path = settings.nginx.get_log_path()
            logger.info(f"current file path update: {self.current_file_path}")
        logger.info(f"current collecting file path: {file_path}:[{offset}]:[{self.log_metadata_service.index}]")
        self.collector.start(file_path=file_path, offset=offset)

    def log_metadata_callback(self, metadata_list: List[LogMetaData], offset: int) -> bool:
        """
        日志数据回调
        :param metadata_list:
        :param offset:
        :return:
        """
        if not metadata_list:
            return True
        save_status = self.log_metadata_service.batch_insert(metadata_list)
        logger.info(f"save log meta data: {len(metadata_list)} status: {save_status} current offset:{offset}")
        if self.file_path_changed:
            # 文件改变时 重置偏移量
            offset = 0
            self.file_path_changed = False
            logger.info(f"file path change, reset offset, set file path change status:{self.file_path_changed}")
        if save_status:
            logger.info(f"offset update: {offset}")
            return self.offset_service.save_offset(offset)
        return False

    def event_listener(self, event: CollectEvent):
        match event.event_type:
            case CollectEventType.DATE_CHANGED:
                # 日期改变事件
                # 创建索引(如果不存在)
                index_stuff = event.data.current
                self.log_metadata_service.create_daily_index(index_stuff)
            case CollectEventType.BATCH_CHANGED:
                # 批次改变新增或修改批次
                log_batches: List[LogMetaDataBatch] = []
                last_batch_id = event.data.last
                current_batch_id = event.data.current
                if last_batch_id:
                    log_batches.append(LogMetaDataBatch(
                        id=last_batch_id,
                        batch_id=last_batch_id,
                        status=BatchStatus.COLLECTED
                    ))
                if current_batch_id:
                    log_batches.append(LogMetaDataBatch(
                        id=current_batch_id,
                        batch_id=current_batch_id,
                        status=BatchStatus.COLLECTING
                    ))
                self.log_metadata_batch_service.batch_merge(log_batches)
