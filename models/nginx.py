from datetime import datetime
from typing import Optional, Any, Self

from pydantic import BaseModel


class Log(BaseModel):
    """
    Log 用于保存 Nginx 日志信息
    示例如下:
    log_format sentinel '$remote_addr||$remote_user||$time_local||$request||$status||'
                    '$request_length||$body_bytes_sent||$http_referer||$http_user_agent||$request_time';
    """
    remote_addr: Optional[str]
    remote_user: Optional[str]
    time_local: Optional[datetime]
    request: Optional[str]
    status: Optional[int]
    request_length: Optional[int]
    body_bytes_sent: Optional[int]
    http_referer: Optional[str]
    http_user_agent: Optional[str]
    request_time: Optional[float]

    def parse(self, log_line: str) -> Self:
        """
        解析日志行，按 Nginx log_format sentinel 中的 || 分隔顺序解析字段。
        严格校验字段数量和内容。
        """
        log_line = log_line.strip()
        parts = log_line.split("||")

        # 严格校验字段数量：必须正好 10 个（允许为空但必须存在）
        if len(parts) != 10:
            raise ValueError(f"日志格式错误：字段数量应为 10 个，实际为 {len(parts)} —— {log_line}")

        # 不允许缺失字段（必须是 "" 或实际值）
        for idx, p in enumerate(parts):
            if p is None:
                raise ValueError(f"日志第 {idx} 个字段缺失（None），日志内容：{log_line}")

        return Log(
            remote_addr=parts[0],
            remote_user=parts[1],
            time_local=(
                datetime.strptime(parts[2], "%d/%b/%Y:%H:%M:%S %z")
                if parts[2] != "" else None
            ),
            request=parts[3],
            status=int(parts[4]) if parts[4] != "" else None,
            request_length=int(parts[5]) if parts[5] != "" else None,
            body_bytes_sent=int(parts[6]) if parts[6] != "" else None,
            http_referer=parts[7],
            http_user_agent=parts[8],
            request_time=float(parts[9]) if parts[9] != "" else None
        )
