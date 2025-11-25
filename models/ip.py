import ipaddress
from enum import Enum

from pydantic import BaseModel, model_validator, Field
from typing import Optional, List, Self


def ip_range_to_cidr(start_ip: str, end_ip: str) -> str:
    """
    将 IP 范围转换为 CIDR 格式
    """
    networks = ipaddress.summarize_address_range(
        ipaddress.ip_address(start_ip),
        ipaddress.ip_address(end_ip)
    )
    return str(list(networks)[0])


class AllowedIpSegment(BaseModel):
    """
    允许的 IP 段
    """
    id: Optional[str] = Field(default=None, exclude=True)  # 可选的ID字段，序列化时排除
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


class IpRecord(BaseModel):
    """
    IP 记录
    """
    id: Optional[str] = Field(default=None, exclude=True)  # 可选的ID字段，序列化时排除
    ip: str  # IP
    location: str  # 地理位置
    isp: str  # 运营商
    scene: str  # 使用场景
    risk_tags: List[str]  # 风险标签


class PolicyType(Enum):
    """
    策略类型枚举
    """
    BLACKLIST = "BLACKLIST"  # 黑名单
    RATELIMIT = "RATELIMIT"  # 限速


class IpPolicy(BaseModel):
    """
    IP 策略
    """
    id: Optional[str] = Field(default=None, exclude=True)  # 可选的ID字段，序列化时排除
    policy_type: PolicyType  # 策略类型
    start_ip: Optional[str] = None  # 起始 IP
    end_ip: Optional[str] = None  # 结束 IP
    cidr: Optional[str] = None  # CIDR 形式
    reason: str  # 原因
    manual: bool  # 是否手动添加
    rate_limit: Optional[int] = None  # 限速
    created_at: Optional[str] = None  # 创建时间
    expire_at: Optional[str] = None  # 过期时间

    @model_validator(mode="after")
    def auto_fix(self) -> Self:
        self.cidr = ip_range_to_cidr(self.start_ip, self.end_ip)
        return self
