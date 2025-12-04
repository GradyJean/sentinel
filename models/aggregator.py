from typing import List

from pydantic import BaseModel

from models.storage.document import ElasticSearchModel


class StdDeviationBound(BaseModel):
    upper: float
    lower: float
    upper_population: float
    lower_population: float
    upper_sampling: float
    lower_sampling: float


class ExtendedStats(BaseModel):
    count: int
    min: float
    max: float
    avg: float
    sum: float
    sum_of_squares: float
    variance: float
    variance_population: float
    variance_sampling: float
    std_deviation: float
    std_deviation_population: float
    std_deviation_sampling: float
    std_deviation_bounds: StdDeviationBound


class KeyValue(BaseModel):
    key: str
    value: int


class AccessIpAggregation(ElasticSearchModel):
    ip: str
    count: int
    path_categories: List[KeyValue]
    path: List[KeyValue]
    request_length: ExtendedStats
    body_bytes_sent: ExtendedStats
    request_time: ExtendedStats
    http_user_agent: List[KeyValue]
    referer_categories: List[KeyValue]
    status: List[KeyValue]
    batch_id: str
