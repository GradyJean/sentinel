from typing import List

from core.detector.evaluator import SafeExpressionEvaluator
from models.score import ScoreRule, AccessIpScoreFeatures, ScoreRecord, ScoreDetail, ScoreType
from loguru import logger


class ScoreEngine:
    __rules: list[ScoreRule] = []

    def __init__(self, rules: list[ScoreRule]):
        self.load_rules(rules)

    def load_rules(self, rules: list[ScoreRule]):
        if not rules:
            raise ValueError("rules is empty")
        for rule in rules:
            if rule.enabled:
                self.__rules.append(rule)
                logger.info(f"load rule: {rule.rule_name}")

    def score(self, features: AccessIpScoreFeatures) -> ScoreRecord:
        evaluator = SafeExpressionEvaluator(features.features)
        score_details: List[ScoreDetail] = []
        score_fixed = 0
        score_dynamic = 0
        score_feature = 0
        for rule in self.__rules:
            condition_status = False
            score = 0
            try:
                condition_status = evaluator.eval(rule.condition)
            except Exception as e:
                logger.warning(f"eval rule {rule.rule_name}: {rule.condition} error: {e}")
            if not condition_status:
                continue
            try:
                score = evaluator.eval(rule.formula)
            except Exception as e:
                logger.warning(f"eval rule {rule.rule_name}: {rule.formula} error: {e}")
            score_fixed += score if rule.score_type == ScoreType.FIXED else 0
            score_dynamic += score if rule.score_type == ScoreType.DYNAMIC else 0
            score_feature += score if rule.score_type == ScoreType.FEATURE else 0
            score_details.append(ScoreDetail(
                score_rule_name=rule.rule_name,
                score=score,
                description=rule.description
            ))
        return ScoreRecord(
            ip=features.ip,
            score_fixed=score_fixed,
            score_dynamic=score_dynamic,
            score_feature=score_feature,
            score_details=score_details,
            batch_id=features.batch_id
        )
