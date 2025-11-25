from typing import List

from models.scheduler import TaskScheduler
from storage import es_client


class TaskSchedulerService:
    """
    任务调度服务
    """

    def __init__(self):
        self.es_client = es_client
        self.task_scheduler_index = "task_scheduler"

    def load_task_scheduler(self) -> List[TaskScheduler]:
        """
        加载任务调度配置
        :return: 任务调度配置列表
        """
        task_schedulers: List[TaskScheduler] = []
        res = self.es_client.search(index=self.task_scheduler_index, body={"query": {"match_all": {}}})
        for hit in res["hits"]["hits"]:
            task_scheduler = TaskScheduler(**hit["_source"])
            task_scheduler.id = hit["_id"]
            task_schedulers.append(task_scheduler)
        return task_schedulers

    def save_task_scheduler(self, task_scheduler: TaskScheduler):
        """
        保存任务调度配置
        :param task_scheduler: 任务调度配置
        """
        doc_id = task_scheduler.id if task_scheduler.id else None
        self.es_client.index(index=self.task_scheduler_index, id=doc_id, body=task_scheduler.model_dump())
