import ipaddress
from typing import Optional, Self

from pydantic import model_validator

from models import ElasticSearchModel


def ip_range_to_cidr(start_ip: str, end_ip: str) -> str:
    """
    将 IP 范围转换为 CIDR 格式
    """
    networks = ipaddress.summarize_address_range(
        ipaddress.ip_address(start_ip),
        ipaddress.ip_address(end_ip)
    )
    return str(list(networks)[0])


class AllowedIpSegment(ElasticSearchModel):
    """
    允许的 IP 段
    """
    org_name: Optional[str] = None  # 机构名称
    is_internal: Optional[bool] = None  # 是否院内机构
    start_ip: str  # 起始 IP
    end_ip: str  # 结束 IP
    cidr: Optional[str] = None  # CIDR 格式（可选）

    @model_validator(mode="after")
    def auto_fix(self) -> Self:
        start = int(ipaddress.ip_address(self.start_ip))
        end = int(ipaddress.ip_address(self.end_ip))
        if start > end:
            self.start_ip, self.end_ip = self.end_ip, self.start_ip
        self.cidr = ip_range_to_cidr(self.start_ip, self.end_ip)
        return self
