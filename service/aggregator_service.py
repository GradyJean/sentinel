import ipaddress
import math
from typing import List, Union

from loguru import logger

from models.aggregator import AccessIpAggregation, KeyValue, ExtendedStats, StdDeviationBound, IpEnrich
from service.ip_service import AllowedIpSegmentService, GeoIpService
from storage.document import ElasticSearchRepository


class AccessIpAggregationService(ElasticSearchRepository[AccessIpAggregation]):
    """
    访问IP聚合服务
    """
    allowed_ip_segment_service = AllowedIpSegmentService()
    geoip_service = GeoIpService()
    LOG_META_DATA_PREFIX = "log_metadata_"
    PREFIX = "access_ip_aggregation_"
    TEMPLATE_NAME = "access_ip_aggregation"

    def __init__(self):
        super().__init__("access_ip_aggregation", AccessIpAggregation)

    def create_daily_index(self, index_stuff: str):
        index_name = f"{self.PREFIX}{index_stuff}"
        template = self.get_index_template(index_name=self.TEMPLATE_NAME)
        self.create_index(index_name, template)

    def query_access_ip_aggregation(self, batch_id: str) -> List[AccessIpAggregation]:
        index_name = f"{self.LOG_META_DATA_PREFIX}{batch_id[:10]}"
        query = {
            "from": 0,
            "size": 0,
            "query": {"term": {"batch_id": batch_id}},
            "aggregations": {
                "ip": {
                    "composite": {
                        "size": 1000,
                        "sources": [
                            {"remote_addr": {"terms": {"field": "remote_addr"}}}
                        ]
                    },
                    "aggregations": {
                        "status": {"terms": {"field": "status"}},
                        "path": {"terms": {"field": "path"}},
                        "path_categories": {"terms": {"field": "path_type"}},
                        "request_length": {"extended_stats": {"field": "request_length"}},
                        "body_bytes_sent": {"extended_stats": {"field": "body_bytes_sent"}},
                        "request_time": {"extended_stats": {"field": "request_time"}},
                        "referer_categories": {
                            "filters": {
                                "filters": {
                                    "empty_referer": {"term": {"http_referer.keyword": "-"}},
                                    "non_empty_referer": {
                                        "bool": {"must_not": {"term": {"http_referer.keyword": "-"}}}
                                    }
                                }
                            }
                        },
                        "http_user_agent": {"terms": {"field": "http_user_agent.keyword"}}
                    }
                }
            }
        }
        buckets = []
        after_key = None
        while True:
            if after_key:
                query["aggregations"]["ip"]["composite"]["after"] = after_key

            res = self.get_client().search(index=index_name, body=query)
            page_buckets = res["aggregations"]["ip"]["buckets"]
            buckets.extend(page_buckets)

            after_key = res["aggregations"]["ip"].get("after_key")
            if not after_key:
                break
        ips = [bucket["key"]["remote_addr"] for bucket in buckets]
        allowed_ip_segments = self.allowed_ip_segment_service.query_ips(ips)
        geoip_cities = self.geoip_service.query_cities(ips)
        result: List[AccessIpAggregation] = []
        for bucket in buckets:
            allowed: bool = False
            org_name: str = ""
            city_name: str = ""
            country_name: str = ""
            country_code: str = ""
            continent_name: str = ""
            continent_code: str = ""
            # 解析基础字段
            access_ip_agg = self.parse_bucket_to_model(bucket, batch_id)
            ip = access_ip_agg.ip
            # enrich 字段
            allowed_ips = allowed_ip_segments.get(ip)
            if allowed_ips:
                org_name = allowed_ips[0].org_name
                allowed = allowed_ips[0].is_internal

            ego_city = geoip_cities.get(ip)
            if ego_city:
                city_name = ego_city.city.names.get("zh-CN", "") if ego_city.city.names else ""
                country_name = ego_city.country.names.get("zh-CN", "") if ego_city.country.names else ""
                country_code = getattr(ego_city.country, 'iso_code', "")
                continent_name = ego_city.continent.names.get("zh-CN", "") if ego_city.continent.names else ""
                continent_code = getattr(ego_city.continent, 'code', "")

            access_ip_agg.ip_enrich = IpEnrich(
                allowed=allowed,
                org_name=org_name,
                city_name=city_name,
                country_name=country_name,
                country_code=country_code,
                continent_name=continent_name,
                continent_code=continent_code
            )

            # 生成行为向量
            try:
                access_ip_agg.behavior_vector = self.build_behavior_vector(access_ip_agg)
            except Exception as e:
                logger.error(e)
                access_ip_agg.behavior_vector = []
            # 写入结果
            result.append(access_ip_agg)
        return result

    @staticmethod
    def parse_terms_buckets(buckets):
        """解析 terms 聚合成 List[KeyValue]"""
        return [
            KeyValue(key=str(bucket["key"]), value=bucket["doc_count"])
            for bucket in buckets
        ]

    @staticmethod
    def get_number(stats: dict, key: str, default: Union[int, float] = 0):
        value = stats.get(key, default)
        # 只允许 int 和 float
        if isinstance(value, (int, float)):
            return value

        return default

    def parse_extended_stats(self, stats):
        """解析 extended_stats 聚合成 ExtendedStats 模型"""
        if not stats:
            return None
        bounds = stats.get("std_deviation_bounds", {})
        return ExtendedStats(
            count=self.get_number(stats, "count", 0),
            min=self.get_number(stats, "min", 0.0),
            max=self.get_number(stats, "max", 0.0),
            avg=self.get_number(stats, "avg", 0.0),
            sum=self.get_number(stats, "sum", 0.0),
            sum_of_squares=self.get_number(stats, "sum_of_squares", 0.0),
            variance=self.get_number(stats, "variance", 0.0),
            variance_population=self.get_number(stats, "variance_population", 0.0),
            variance_sampling=self.get_number(stats, "variance_sampling", 0.0),
            std_deviation=self.get_number(stats, "std_deviation", 0.0),
            std_deviation_population=self.get_number(stats, "std_deviation_population", 0.0),
            std_deviation_sampling=self.get_number(stats, "std_deviation_sampling", 0.0),
            std_deviation_bounds=StdDeviationBound(
                upper=self.get_number(bounds, "upper", 0.0),
                lower=self.get_number(bounds, "lower", 0.0),
                upper_population=self.get_number(bounds, "upper_population", 0.0),
                lower_population=self.get_number(bounds, "lower_population", 0.0),
                upper_sampling=self.get_number(bounds, "upper_sampling", 0.0),
                lower_sampling=self.get_number(bounds, "lower_sampling", 0.0),
            )
        )

    def parse_bucket_to_model(self, bucket, batch_id: str) -> AccessIpAggregation:
        # referer_categories 是 filters 聚合
        referer_list = [
            KeyValue(key=key, value=self.get_number(value, "doc_count", 0))
            for key, value in bucket.get("referer_categories", {}).get("buckets", {}).items()
        ]
        return AccessIpAggregation(
            ip=bucket["key"]["remote_addr"],
            ip_enrich=None,
            count=bucket["doc_count"],
            status=self.parse_terms_buckets(bucket["status"]["buckets"]),
            path=self.parse_terms_buckets(bucket["path"]["buckets"]),
            path_categories=self.parse_terms_buckets(bucket["path_categories"]["buckets"]),
            request_length=self.parse_extended_stats(bucket["request_length"]),
            body_bytes_sent=self.parse_extended_stats(bucket["body_bytes_sent"]),
            request_time=self.parse_extended_stats(bucket["request_time"]),
            http_user_agent=self.parse_terms_buckets(bucket["http_user_agent"]["buckets"]),
            referer_categories=referer_list,
            batch_id=batch_id,
            behavior_vector=None
        )

    @staticmethod
    def build_behavior_vector(access_ip_agg: AccessIpAggregation) -> List[float]:
        # IP 数值特征
        ip_int = int(ipaddress.ip_address(access_ip_agg.ip))
        ip_norm = ip_int / (2 ** 32 - 1)
        a, b, *_ = access_ip_agg.ip.split(".")
        prefix16 = (int(a) * 256 + int(b)) / (256 * 256 - 1)
        # 基础请求量
        count = float(access_ip_agg.count or 0)
        # path 特征
        paths = access_ip_agg.path  # List[KeyValue]
        total_paths = sum(kv.value for kv in paths) or 1
        distinct_paths = len(paths)
        # 最常访问 URL 占比（弱噪声但稳定）
        top_path_ratio = max((kv.value for kv in paths), default=0) / total_paths

        # 路径熵，越高越像扫描器
        path_entropy = 0.0
        for kv in paths:
            p = kv.value / total_paths
            path_entropy -= p * math.log2(p)

        # path category
        def ratio(arr, key):
            total = sum(kv.value for kv in arr) or 1
            for kv in arr:
                if kv.key == key:
                    return kv.value / total
            return 0.0

        page_ratio = ratio(access_ip_agg.path_categories, "PAGE")
        normal_ratio = ratio(access_ip_agg.path_categories, "NORMAL")
        static_ratio = ratio(access_ip_agg.path_categories, "STATIC")
        # 状态码特征
        ratio_200 = ratio(access_ip_agg.status, "200")
        ratio_403 = ratio(access_ip_agg.status, "403")
        ratio_404 = ratio(access_ip_agg.status, "404")
        ratio_429 = ratio(access_ip_agg.status, "429")
        ratio_499 = ratio(access_ip_agg.status, "499")

        # redirect 合并
        ratio_redirect = (
                ratio(access_ip_agg.status, "301")
                + ratio(access_ip_agg.status, "302")
        )

        # 5xx 合并
        ratio_5xx = (
                ratio(access_ip_agg.status, "500")
                + ratio(access_ip_agg.status, "502")
                + ratio(access_ip_agg.status, "503")
                + ratio(access_ip_agg.status, "504")
        )

        # other
        ratio_other = max(
            0.0,
            1 - (
                    ratio_200
                    + ratio_403
                    + ratio_404
                    + ratio_429
                    + ratio_499
                    + ratio_redirect
                    + ratio_5xx
            )
        )
        # referer
        ref_empty = ratio(access_ip_agg.referer_categories, "empty_referer")
        ref_non_empty = 1 - ref_empty
        # Stats 数值字段
        rl_avg = float(access_ip_agg.request_length.avg or 0)
        rl_std = float(access_ip_agg.request_length.std_deviation or 0)

        bb_avg = float(access_ip_agg.body_bytes_sent.avg or 0)
        bb_std = float(access_ip_agg.body_bytes_sent.std_deviation or 0)

        rt_avg = float(access_ip_agg.request_time.avg or 0)
        rt_std = float(access_ip_agg.request_time.std_deviation or 0)

        # UA 特征
        def parse_ua_features(ua_list):
            total = sum(kv.value for kv in ua_list) or 1
            distinct = len(ua_list)

            entropy = 0.0
            for kv in ua_list:
                p = kv.value / total
                entropy -= p * math.log(p)
            suspicious_keywords = [
                "HeadlessChrome", "PhantomJS", "Python", "curl",
                "Java/", "Go-http-client", "Dalvik", "okhttp"
            ]
            suspicious = 0
            for kv in ua_list:
                if any(k in kv.key for k in suspicious_keywords):
                    suspicious = 1
                    break
            max_ratio = max(kv.value for kv in ua_list) / total if ua_list else 0.0

            def detect_category(s):
                s = s.lower()
                if "headless" in s:
                    return [1, 0, 0, 0, 0, 0]
                if "android" in s and ("wv" in s or "uni-app" in s):
                    return [0, 0, 0, 1, 0, 0]
                if "android" in s or "iphone" in s or "mobile" in s:
                    return [0, 1, 0, 0, 0, 0]
                if "spider" in s or "bot" in s:
                    return [0, 0, 0, 0, 1, 0]
                if "windows" in s or "macintosh" in s or "x11" in s:
                    return [1, 0, 0, 0, 0, 0]
                return [0, 0, 0, 0, 0, 1]

            main_ua = max(ua_list, key=lambda x: x.value).key if ua_list else ""
            cat_vec = detect_category(main_ua)
            return [
                float(distinct),
                float(entropy),
                float(suspicious),
                float(max_ratio),
                *cat_vec
            ]

        ua_vec = parse_ua_features(access_ip_agg.http_user_agent)
        # 拼向量
        return [
            ip_norm,
            prefix16,
            count,
            # path categories
            page_ratio,
            # path 行为特征
            distinct_paths,
            top_path_ratio,
            path_entropy,
            normal_ratio,
            static_ratio,
            # http status
            ratio_200,
            ratio_403,
            ratio_404,
            ratio_429,
            ratio_499,
            ratio_redirect,
            ratio_5xx,
            ratio_other,
            # referer
            ref_empty,
            ref_non_empty,
            # numeric stats
            rl_avg,
            rl_std,
            bb_avg,
            bb_std,
            rt_avg,
            rt_std,
            # UA 特征
            *ua_vec
        ]
