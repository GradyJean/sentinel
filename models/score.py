from datetime import datetime
from enum import Enum
from typing import Dict, Any
from typing import Optional, List, Self

from pydantic import BaseModel, Field, model_validator

from models.aggregator import AccessIpAggregation, KeyValue, ExtendedStats
from models.storage.document import ElasticSearchModel


class ScoreType(Enum):
    """
    评分类型
    """
    FIXED = "FIXED"  # 固定
    DYNAMIC = "DYNAMIC"  # 动态
    FEATURE = "FEATURE"  # 特征


class ScoreRule(ElasticSearchModel):
    """
    评分规则
    """
    rule_name: str  # 规则名称
    score_type: ScoreType  # 评分类型
    condition: str  # 条件
    formula: str  # 公式
    description: str  # 描述
    created_at: Optional[datetime] = None  # 创建时间
    updated_at: Optional[datetime] = None  # 更新时间
    enabled: bool = True  # 是否启用


class ScoreDetail(BaseModel):
    """
    评分详情
    """
    score_rule_name: str
    score: float
    description: str


class ScoreRecord(ElasticSearchModel):
    """
    评分记录
    """
    ip: str  # IP
    score_fixed: float = 0  # 固定评分
    score_dynamic: float = 0  # 动态评分
    score_feature: float = 0  # 特征评分
    score_details: List[ScoreDetail] = Field(default_factory=list)  # 评分详情
    batch_id: str = Field(default="")  # 批次ID


class ScoreAggregate(ElasticSearchModel):
    """
    评分聚合
    """
    ip: str  # IP
    score_fixed: float = 0  # 固定评分
    score_dynamic: float = 0  # 动态评分
    score_feature: float = 0  # 特征评分
    score_total: float = 0  # 总评分
    last_update: datetime = Field(default=datetime.now())

    @model_validator(mode="after")
    def auto_fix(self) -> Self:
        self.score_total = self.score_fixed + self.score_dynamic + self.score_feature


UA_KEYWORDS = {
    # 典型爬虫 / bot
    "bot": [
        "bot", "spider", "crawler", "crawl",
        "slurp", "bingbot", "googlebot", "baiduspider",
        "yandex", "duckduckbot", "sogou", "exabot"
    ],

    # 自动化 / 无头浏览器
    "headless": [
        "headless", "puppeteer", "playwright",
        "selenium", "phantomjs", "nightmare"
    ],

    # 程序 HTTP 客户端
    "http_client": [
        "curl", "wget", "httpclient", "okhttp",
        "python-requests", "aiohttp", "urllib",
        "libwww-perl", "restsharp", "postman"
    ],

    # 扫描器 / 安全工具
    "scanner": [
        "nmap", "masscan", "zmap", "nikto",
        "sqlmap", "acunetix", "nessus",
        "burpsuite", "wpscan"
    ],

    # 云 / 代理 / 中转
    "proxy": [
        "proxy", "vpn", "tor", "shadow",
        "v2ray", "trojan", "clash"
    ],

    # 非浏览器 / 异常 UA
    "abnormal": [
        "java/", "go-http-client", "node-fetch",
        "axios", "grpc", "okhttp"
    ],
}


class AccessIpScoreFeatures(BaseModel):
    """
    AccessIpAggregation 的扁平化评分特征
    """
    ip: str
    batch_id: str

    features: Dict[str, Any] = Field(default_factory=dict)
    behavior_vector: List[float] = Field(default_factory=list)

    @classmethod
    def from_aggregation(cls, agg: AccessIpAggregation) -> "AccessIpScoreFeatures":
        features: Dict[str, Any] = {
            "count": float(agg.count),
            "path_size": float(len(agg.path)),
            "ip_enrich_allowed": agg.ip_enrich.allowed,
            "ip_enrich_org_name": agg.ip_enrich.org_name,
            "ip_enrich_city_name": agg.ip_enrich.city_name,
            "ip_enrich_country_name": agg.ip_enrich.country_name,
            "ip_enrich_continent_name": agg.ip_enrich.continent_name,
            "ip_enrich_country_code": agg.ip_enrich.country_code,
            "ip_enrich_continent_code": agg.ip_enrich.continent_code,
        }
        # path_categories
        PATH_CATEGORIES_KEYS = ["STATIC", "NORMAL", "PAGE"]
        for k in PATH_CATEGORIES_KEYS:
            features[f"path_categories_{k}"] = 0.0
        for item in agg.path_categories:
            features[f"path_categories_{item.key}"] = float(item.value)
        # referer_categories
        REFERER_CATEGORIES_KEYS = ["empty_referer", "non_empty_referer"]
        for k in REFERER_CATEGORIES_KEYS:
            features[f"referer_categories_{k}"] = 0.0
        for item in agg.referer_categories:
            features[f"referer_categories_{item.key}"] = float(item.value)
        # status
        STATUS_KEYS = {200, 403, 404, 429, 500}
        for k in STATUS_KEYS:
            features[f"status_{k}"] = 0.0

        features["status_2xx"] = 0.0
        features["status_3xx"] = 0.0
        features["status_4xx"] = 0.0
        features["status_5xx"] = 0.0
        features["status_other"] = 0.0

        for item in agg.status:
            code = int(item.key)
            count = float(item.value)
            if code in STATUS_KEYS:
                features[f"status_{code}"] += count
            if 200 <= code < 300:
                features["status_2xx"] += count
            elif 300 <= code < 400:
                features["status_3xx"] += count
            elif 400 <= code < 500:
                features["status_4xx"] += count
            elif 500 <= code < 600:
                features["status_5xx"] += count
            else:
                features["status_other"] += count

        # stats
        def flatten_stats(prefix: str, stats: ExtendedStats):
            features[f"{prefix}_count"] = float(stats.count)
            features[f"{prefix}_min"] = float(stats.min)
            features[f"{prefix}_max"] = float(stats.max)
            features[f"{prefix}_avg"] = float(stats.avg)
            features[f"{prefix}_sum"] = float(stats.sum)
            features[f"{prefix}_variance"] = float(stats.variance)
            features[f"{prefix}_std"] = float(stats.std_deviation)

        flatten_stats("request_length", agg.request_length)
        flatten_stats("body_bytes_sent", agg.body_bytes_sent)
        flatten_stats("request_time", agg.request_time)
        # http_user_agent
        ua_list = agg.http_user_agent
        features["http_user_agent_size"] = float(len(ua_list))
        for group in UA_KEYWORDS:
            features[f"http_user_agent_{group}"] = 0.0
        for ua in ua_list:
            ua_lower = ua.key.lower()
            for group, keywords in UA_KEYWORDS.items():
                if any(k in ua_lower for k in keywords):
                    features[f"http_user_agent_{group}"] = 1.0

        return cls(
            ip=agg.ip,
            batch_id=agg.batch_id,
            features=features,
            behavior_vector=agg.behavior_vector,
        )
