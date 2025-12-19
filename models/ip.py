import ipaddress
from datetime import datetime
from typing import Optional, Self, List

from pydantic import model_validator, BaseModel, Field

from models.storage.document import ElasticSearchModel


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


class IpEnrich(BaseModel):
    allowed: bool = False
    org_name: str = ""
    city_name: str = ""
    country_name: str = ""
    country_code: str = ""
    continent_name: str = ""
    continent_code: str = ""


class Score(BaseModel):
    fixed: float = 0  # 固定评分
    dynamic: float = 0  # 动态评分
    feature: float = 0  # 特征评分
    total: float = Field(default=0, exclude=True)

    @model_validator(mode="after")
    def auto_fix(self) -> Self:
        self.total = self.fixed + self.dynamic + self.feature


class History(BaseModel):
    count: int = 0  # 请求次数
    body_bytes_sent: float = 0  # 发送字节数
    response_bytes: float = 0  # 响应字节数
    request_time: float = 0  # 请求处理时间
    active_days: int = 0  # 活跃天数


class IpProfile(ElasticSearchModel):
    """
    评分聚合
    """
    ip: str  # IP
    score: Score = Field(default_factory=Score)  # 评分
    # total_metadata: TotalMetadata = Field(default_factory=TotalMetadata)  # 总数据
    feature_tags: List[str] = Field(default_factory=list)  # 特征标签
    ip_enrich: IpEnrich = Field(default_factory=IpEnrich)  # IP 地址信息
    create_at: datetime = Field(default=datetime.now())
    update_at: datetime = Field(default=datetime.now())

    @model_validator(mode="after")
    def auto_fix(self) -> Self:
        self.id = self.ip
        return self
