from datetime import datetime, timedelta

from loguru import logger

class LogTailer:
    """
    LogTailer 用于从 Nginx access.log 中实时读取新增日志内容
    """

    def collect_recent(self, log_path: str, duration: int) -> list:
        """
        从日志文件中读取最近 duration 秒的日志内容
        :param log_path: 日志文件路径（支持每日不同文件）
        :param duration: 时间间隔，单位为秒
        :return: list of dict，每条日志为结构化对象（不完整行也会保留）
        """
        pass


class Log:
    """
    Log 用于保存 Nginx 日志信息
    """
    remote_addr: str
    remote_user: str
    time_local: str
    request: str
    status: int
    body_bytes_sent: int
    http_referer: str
    http_user_agent: str
