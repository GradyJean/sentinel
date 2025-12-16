from typing import List

from elasticsearch import helpers
from loguru import logger

from core.scheduler.task_runner import TaskRunner
from manager.ip_score_manager import IpSummaryManager, ScoreRecordManager
from manager.log_metadata_manager import LogMetaDataBatchManager
from models.log import BatchStatus
from models.score import IpSummary


class ScoreAggregatorTask(TaskRunner):
    """
    评分定时任务
    """
    task_id = "score_aggregator_task"
    ip_summary_manager = IpSummaryManager()
    log_metadata_batch_manager = LogMetaDataBatchManager()
    score_record_manager = ScoreRecordManager()

    def run(self):
        # 获取索引名称
        ip_summary_index = self.ip_summary_manager.index
        # 获取ES客户端
        es_client = self.ip_summary_manager.get_client()
        # 获取所有批次
        batches = self.log_metadata_batch_manager.get_all_by_status(BatchStatus.SCORED)
        for batch in batches:
            batch.status = BatchStatus.AGGREGATING
            self.log_metadata_batch_manager.merge( batch)
            actions = []
            # 获取所有评分记录
            score_records = self.score_record_manager.get_all_by_batch_id(batch.batch_id)
            for score_record in score_records:
                ip_summary = IpSummary(
                    ip=score_record.ip,
                    score_fixed=score_record.score_fixed,
                    score_dynamic=score_record.score_dynamic,
                    score_feature=score_record.score_feature,
                    ip_enrich=score_record.ip_enrich,
                )
                actions.append({
                    "_op_type": "update",
                    "_index": ip_summary_index,
                    "_id": score_record.ip,
                    "scripted_upsert": True,
                    "script": self.build_script(ip_summary),
                    "upsert": ip_summary.model_dump(exclude_none=True)
                })

            success_count, error = helpers.bulk(
                es_client,
                actions,
                chunk_size=1000,
                request_timeout=60,
                raise_on_error=True,
                raise_on_exception=True,
                error_trace=True
            )
            if error:
                logger.error(error)

    @staticmethod
    def build_script(record: IpSummary) -> dict:
        script = {
            "lang": "painless",
            "source": """
                    // 累加型字段
                    if (ctx._source.score_fixed == null) {
                        ctx._source.score_fixed = params.score_fixed;
                    } else {
                        ctx._source.score_fixed += params.score_fixed;
                    }

                    if (ctx._source.score_dynamic == null) {
                        ctx._source.score_dynamic = params.score_dynamic;
                    } else {
                        ctx._source.score_dynamic += params.score_dynamic;
                    }

                    if (ctx._source.score_feature == null) {
                        ctx._source.score_feature = params.score_feature;
                    } else {
                        ctx._source.score_feature += params.score_feature;
                    }

                    // 覆盖型字段
                    ctx._source.feature_tags = params.feature_tags;
                    ctx._source.ip_enrich = params.ip_enrich;
                    ctx._source.last_update = params.last_update;
                    """,
            "params": {
                "score_fixed": record.score_fixed,
                "score_dynamic": record.score_dynamic,
                "score_feature": record.score_feature,
                "feature_tags": record.feature_tags,
                "ip_enrich": record.ip_enrich.model_dump(exclude_none=True),
                "last_update": record.last_update
            }
        }
        return script


if __name__ == '__main__':
    task = ScoreAggregatorTask()
    task.run()
