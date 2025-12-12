from typing import List, Dict

from geoip2 import database as geoip_database
from geoip2.errors import GeoIP2Error
from geoip2.models import City
from loguru import logger

from config import settings
from models.ip import AllowedIpSegment
from storage.document import ElasticSearchRepository


class AllowedIpSegmentManager(ElasticSearchRepository[AllowedIpSegment]):
    """
    允许的 IP 段服务
    """

    def __init__(self):
        super().__init__("allowed_ip_segment", AllowedIpSegment)

    def query_ip(self, ip: str) -> List[AllowedIpSegment]:
        query_body = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "range": {
                                "start_ip": {
                                    "lte": ip
                                }
                            }
                        },
                        {
                            "range": {
                                "end_ip": {
                                    "gte": ip
                                }
                            }
                        }
                    ]
                }
            }
        }
        return self.query_list(query_body)

    def query_ips(self, ips: List[str]) -> Dict[str, List[AllowedIpSegment]]:
        body = []
        for ip in ips:
            body.append({"index": self.index})
            body.append({
                "query": {
                    "bool": {
                        "must": [
                            {"range": {"start_ip": {"lte": ip}}},
                            {"range": {"end_ip": {"gte": ip}}}
                        ]
                    }
                }
            })

        results = self.get_client().msearch(body=body)
        # 解析返回值
        output: Dict[str, List[AllowedIpSegment]] = {}
        responses = results.get("responses", [])

        for i, res in enumerate(responses):
            ip = ips[i]
            hits = res.get("hits", {}).get("hits", [])
            segments = []
            for hit in hits:
                src = hit.get("_source", {})
                try:
                    segment = AllowedIpSegment(**src)
                except Exception as e:
                    logger.error(f"Failed to parse AllowedIpSegment for IP {ip}: {e}")
                    continue
                segments.append(segment)
            output[ip] = segments
        return output


class GeoIpManager:
    """
    GeoIP服务
    """

    def __init__(self):
        self.geoip_client = geoip_database.Reader(settings.geoip.data_path)

    def query_city(self, ip: str) -> City | None:
        """
        查询IP信息
        :param ip:
        :return:
        """
        try:
            res = self.geoip_client.city(ip)
        except GeoIP2Error as e:
            return None
        return res

    def query_cities(self, ips: List[str]) -> Dict[str, City | None]:
        """
        批量查询IP信息
        :param ips:
        :return:
        """
        results = {}
        for ip in ips:
            results[ip] = self.query_city(ip)
        return results
