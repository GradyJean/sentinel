from models.scheduler import TaskScheduler
from storage.document import ElasticSearchRepository


class TaskSchedulerManager(ElasticSearchRepository[TaskScheduler]):
    """
    任务调度服务
    """

    def __init__(self):
        super().__init__("task_scheduler", TaskScheduler)
