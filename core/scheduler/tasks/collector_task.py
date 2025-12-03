from typing import List

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

    def __init__(self):
        self.offset_service = OffsetsService()
        self.log_metadata_service = LogMetaDataService()
        self.log_metadata_batch_service = LogMetaDataBatchService()
        self.collector = Collector(
            data_callback=self.log_metadata_callback,
            event_callback=self.event_listener
        )

    async def run(self):
        """
            初始计数 从1开始 1表示从今天的文件开始
            0表示昨天日志 用于收尾昨天日志
            count =1 的时候offset 为0 表示从文件头开始
            count 字段 由daily_task 任务更新
        """
        file_path = settings.nginx.get_log_path()
        # 获取文件偏移量配置
        offset_config = self.offset_service.get()
        offset = offset_config.offset
        # 文件路径改变
        # 每天只发生一次
        # 用来采集昨天尾部
        # 下一次调度就切换文件了 偏移量需要归0
        if file_path != self.current_file_path:
            logger.info(f"file path changed: {file_path}")
            file_path = self.current_file_path
            self.offset_service.save_offset(0)
            # 更新当前文件路径
            self.current_file_path = settings.nginx.get_log_path()
        # 文件采集并返回偏移量
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
        if save_status:
            return self.offset_service.save_offset(offset)
        return False

    def event_listener(self, event: CollectEvent):
        match event.event_type:
            case CollectEventType.DATE_CHANGED:
                # 日期改变事件
                # 创建索引(如果不存在)
                index_stuff = event.data.current
                index_name = f"log_metadata_{index_stuff}"
                template = self.log_metadata_service.get_index_template("nginx_log_metadata")
                self.log_metadata_service.create_index(index_name, template)
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
