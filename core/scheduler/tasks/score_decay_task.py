from core.scheduler.task_runner import TaskRunner
from manager.ip_score_manager import IpSummaryManager
from manager.system_config_manager import SystemConfigManager


class ScoreDecayTask(TaskRunner):
    """
    分数衰减定时任务
    """
    task_id = "score_decay_task"
    ip_summary_manager = IpSummaryManager()
    system_config_manager = SystemConfigManager()
    BASE_DECAY_SCORE = 10

    def run(self):
        system_config = self.system_config_manager.system_config
        factor_fixed = system_config["score_decay_factor_fixed"]
        actor_dynamic = system_config["score_decay_factor_dynamic"]
        factor_feature = system_config["score_decay_factor_feature"]
