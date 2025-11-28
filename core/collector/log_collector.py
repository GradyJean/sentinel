import os
from typing import Callable, List
from loguru import logger
from models.nginx import LogMetaData


class Collector:
    """
    日志采集类

    """
    __enabled: bool = False
    __call_back: Callable[[List[LogMetaData], str, int], bool]
    __batch_size: int = 1000

    def __init__(self, call_back: Callable[[List[LogMetaData], str, int], bool], batch_size: int = 1000):
        """
        初始化日志采集类
        Args:
            log_path 日志文件路径
            call_back:    日志回调函数
                arg1:log_metadata_list
                arg2:file_path
                arg3:offset
            batch_size 批量写入大小
        """

        if not call_back:
            raise ValueError("call_back is empty")

        self.__call_back = call_back
        self.__batch_size = batch_size

    def start(self, file_path: str, offset: int = 0) -> int:
        """
            运行日志采集
            callback 也返回偏移量 防止程序中断丢数据
            return offset
        """
        if not file_path or not os.path.exists(file_path):
            raise ValueError(f"{file_path} is empty or file does not exist")

        def callback(log_metadata_list: List[LogMetaData], file_path: str, offset: int):
            callback_status = self.__call_back(log_metadata_list, file_path, offset)
            if not callback_status:
                self.stop()
                raise RuntimeError(f"collect error callback status is False [{file_path}]")

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
                    log_metadata = LogMetaData.parse(line)
                except Exception as e:
                    logger.warning(f"{line} parse error: {e}")
                    continue
                batch_log_metadata.append(log_metadata)

                # 批量写入
                if len(batch_log_metadata) >= self.__batch_size:
                    callback(batch_log_metadata, file_path, file.tell())
                    batch_log_metadata.clear()

            # 写入剩余数据
            if len(batch_log_metadata) > 0:
                callback(batch_log_metadata, file_path, file.tell())
                batch_log_metadata.clear()
            return file.tell()

    def stop(self):
        """
        停止日志采集
        :return:
        """
        self.__enabled = False
