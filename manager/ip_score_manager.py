from models.score import ScoreRule, ScoreRecord, ScoreAggregate
from storage.document import ElasticSearchRepository


class ScoreRuleManager(ElasticSearchRepository[ScoreRule]):
    """
    分数规则服务
    """

    def __init__(self):
        super().__init__("score_rule", ScoreRule)


class ScoreRecordManager(ElasticSearchRepository[ScoreRecord]):
    """
    分数记录服务
    """

    def __init__(self):
        super().__init__("score_record", ScoreRecord)


class ScoreAggregateManager(ElasticSearchRepository[ScoreAggregate]):
    """
    分数聚合服务
    """

    def __init__(self):
        super().__init__("score_aggregate", ScoreAggregate)
