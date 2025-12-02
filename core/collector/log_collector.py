import os
from typing import Callable, List

from loguru import logger

from models.log import LogMetaData, CollectEvent, CollectEventType, CollectEventData


class Collector:
    """
    日志采集类

    """
    __enabled: bool = False
    __data_callback: Callable[[List[LogMetaData], int], bool]
    __event_callback: Callable[[CollectEvent], None]
    __batch_size: int = 1000
    __log_batch_id: str = None
    __log_date: str = None

    def __init__(self,
                 data_callback: Callable[[List[LogMetaData], int], bool],
                 event_callback: Callable[[CollectEvent], None] = None,
                 batch_size: int = 1000):
        """
        初始化日志采集类
        Args:
            data_callback:   日志数据回调函数
            event_callback: 事件回调函数
            batch_size 批量写入大小
        """

        if not data_callback:
            raise ValueError("data_callback is empty")

        self.__data_callback = data_callback
        self.__event_callback = event_callback
        self.__batch_size = batch_size

    def start(self, file_path: str, offset: int = 0):
        """
            运行日志采集
            callback 也返回偏移量 防止程序中断丢数据
            return offset
        """
        if not file_path or not os.path.exists(file_path):
            raise ValueError(f"{file_path} is empty or file does not exist")
        # 状态开启
        self.__enabled = True
        batch_log_metadata: List[LogMetaData] = []
        with open(file_path, 'r', encoding="utf-8") as file:
            # 定位到指定偏移量
            file.seek(offset)
            # 使用 readline() 替代迭代器，避免 tell() 冲突
            while self.__enabled:
                line = file.readline()
                if not line:  # 文件结束
                    break
                try:
                    # 解析日志
                    log_metadata = LogMetaData.parse(line)
                except Exception as e:
                    logger.warning(f"{line} parse error: {e}")
                    continue
                # 获取当前行的日期
                log_date = log_metadata.time_local.strftime("%Y_%m_%d")
                # 日期改变添加事件
                if self.__log_date != log_date:
                    self.__event_callback_invoke(CollectEvent(
                        event_type=CollectEventType.DATE_CHANGED,
                        data=CollectEventData(last=self.__log_date, current=log_date)
                    ))
                    self.__log_date = log_date
                    # 日期改变直接返回批次数据 并返回偏移量 重新开始一下一批次
                    if len(batch_log_metadata) > 0:
                        self.__data_callback_invoke(batch_log_metadata, file.tell())
                        batch_log_metadata.clear()
                # 获取当前行日志批次
                log_batch_id = log_metadata.batch_id
                # 批次改变添加事件
                if self.__log_batch_id != log_batch_id:
                    self.__event_callback_invoke(CollectEvent(
                        event_type=CollectEventType.BATCH_CHANGED,
                        data=CollectEventData(last=self.__log_batch_id, current=log_batch_id)
                    ))
                    self.__log_batch_id = log_batch_id
                batch_log_metadata.append(log_metadata)

                # 批量写入
                if len(batch_log_metadata) >= self.__batch_size:
                    self.__data_callback_invoke(batch_log_metadata, file.tell())
                    batch_log_metadata.clear()

            # 写入剩余数据
            if len(batch_log_metadata) > 0:
                self.__data_callback_invoke(batch_log_metadata, file.tell())
                batch_log_metadata.clear()

    def stop(self):
        """
        停止日志采集
        :return:
        """
        self.__enabled = False

    def __data_callback_invoke(self, log_metadata_list: List[LogMetaData], offset: int):
        """
            数据回调执行
        """
        callback_status = self.__data_callback(log_metadata_list, offset)
        if not callback_status:
            self.stop()
            raise RuntimeError(f"collect error callback status is False")

    def __event_callback_invoke(self, event: CollectEvent):
        """
            事件回调执行
        """
        if self.__event_callback:
            self.__event_callback(event)
