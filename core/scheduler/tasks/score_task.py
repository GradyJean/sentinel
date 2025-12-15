from typing import List

from core.detector.score_engine import ScoreEngine
from core.scheduler.task_runner import TaskRunner
from manager.ip_aggregator_manager import AccessIpAggregationManager
from manager.ip_score_manager import ScoreRuleManager, ScoreRecordManager
from manager.log_metadata_manager import LogMetaDataBatchManager
from models.aggregator import AccessIpAggregation
from models.log import BatchStatus
from models.score import AccessIpScoreFeatures, ScoreRule, ScoreRecord


class ScoreTask(TaskRunner):
    """
    评分定时任务
    """
    task_id = "score_task"
    log_metadata_batch_manager = LogMetaDataBatchManager()
    access_ip_aggregation_manager = AccessIpAggregationManager()
    score_rule_manager = ScoreRuleManager()
    score_record_manager = ScoreRecordManager()

    def __init__(self):
        self.score_engine = ScoreEngine(rules=self.get_rules())

    def run(self):
        query = {
            "query": {
                "term": {
                    "status": "AGGREGATED"
                }
            }, "sort": [
                {
                    "batch_id": {
                        "order": "asc"
                    }
                }]
        }
        # 获取批次数据
        batches = self.log_metadata_batch_manager.get_all(query=query)
        for batch in batches:
            batch_id = batch.batch_id
            # 批次状态更新
            batch.status = BatchStatus.SCORING
            self.log_metadata_batch_manager.merge(batch)
            # 获取批次聚合数据
            aggregation_ips = self.access_ip_aggregation_manager.get_all_by_batch_id(batch_id)
            # 计算分数
            score_records = self.calculate_scores(aggregation_ips)
            # 保存分数
            self.score_record_manager.batch_insert(score_records)
            # 批次状态更新
            batch.status = BatchStatus.SCORED
            self.log_metadata_batch_manager.merge(batch)

    def calculate_scores(self, aggregation_ips: List[AccessIpAggregation]) -> List[ScoreRecord]:
        """
        计算分数
        :param aggregation_ips:
        :return:
        """
        score_records: List[ScoreRecord] = []
        for aggregation_ip in aggregation_ips:
            features = AccessIpScoreFeatures.from_aggregation(aggregation_ip)
            score_record = self.score_engine.score(features)
            score_records.append(score_record)
        return score_records

    def get_rules(self) -> List[ScoreRule]:
        return self.score_rule_manager.get_all()


if __name__ == '__main__':
    task = ScoreTask()
    task.run()
