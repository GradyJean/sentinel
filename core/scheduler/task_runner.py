from abc import ABC, abstractmethod


class TaskRunner(ABC):
    """
    任务抽象类
    """
    task_id: str

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if not hasattr(cls, "task_id") or cls.task_id is None:
            raise TypeError(f"{cls.__name__} task_id")

    @abstractmethod
    async def run(self):
        pass
