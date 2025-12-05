from typing import List

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
            access_ip_agg = self.parse_bucket_to_model(bucket, batch_id)
            ip = access_ip_agg.ip
            # 获取 allowed
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
    def safe_float(value, default=0.0):
        """安全转换浮点数，处理 NaN 和 None 情况"""
        if not isinstance(value, float):
            return default
        return float(value)

    def parse_extended_stats(self, stats):
        """解析 extended_stats 聚合成 ExtendedStats 模型"""
        if not stats:
            return None
        bounds = stats.get("std_deviation_bounds", {})
        return ExtendedStats(
            count=stats.get("count", 0),
            min=self.safe_float(stats.get("min", 0.0)),
            max=self.safe_float(stats.get("max", 0.0)),
            avg=self.safe_float(stats.get("avg", 0.0)),
            sum=self.safe_float(stats.get("sum", 0.0)),
            sum_of_squares=self.safe_float(stats.get("sum_of_squares", 0.0)),
            variance=self.safe_float(stats.get("variance", 0.0)),
            variance_population=self.safe_float(stats.get("variance_population", 0.0)),
            variance_sampling=self.safe_float(stats.get("variance_sampling", 0.0)),
            std_deviation=self.safe_float(stats.get("std_deviation", 0.0)),
            std_deviation_population=self.safe_float(stats.get("std_deviation_population", 0.0)),
            std_deviation_sampling=self.safe_float(stats.get("std_deviation_sampling", 0.0)),
            std_deviation_bounds=StdDeviationBound(
                upper=self.safe_float(bounds.get("upper", 0.0)),
                lower=self.safe_float(bounds.get("lower", 0.0)),
                upper_population=self.safe_float(bounds.get("upper_population", 0.0)),
                lower_population=self.safe_float(bounds.get("lower_population", 0.0)),
                upper_sampling=self.safe_float(bounds.get("upper_sampling", 0.0)),
                lower_sampling=self.safe_float(bounds.get("lower_sampling", 0.0)),
            )
        )

    def parse_bucket_to_model(self, bucket, batch_id: str) -> AccessIpAggregation:
        # referer_categories 是 filters 聚合
        referer_list = [
            KeyValue(key=key, value=value.get("doc_count", 0))
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
            batch_id=batch_id
        )
