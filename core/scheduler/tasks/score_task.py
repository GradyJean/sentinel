from core.scheduler.task_runner import TaskRunner


class ScoreTask(TaskRunner):
    """
    评分定时任务
    """
    task_id = "score_task"

    def run(self):
        pass
