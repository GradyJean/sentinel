from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Optional, List, Any, Type

E = TypeVar("E")


class IRepository(ABC, Generic[E]):
    """
    抽象仓库类
    """

    def __init__(self, model: Type[E]):
        if model is None:
            raise ValueError("Repository must specify a model")
        self.model = model

    @abstractmethod
    def get_all(self) -> List[E]:
        """
        获取所有记录
        """
        pass

    @abstractmethod
    def query_list(self, query: Any) -> List[E]:
        """
        列表查询
        """
        pass

    @abstractmethod
    def get_by_id(self, id: str) -> Optional[E]:
        """
        根据id获取记录
        """
        pass

    @abstractmethod
    def delete_by_id(self, id: str) -> bool:
        """
        根据id删除记录
        """
        pass

    @abstractmethod
    def merge(self, record: E) -> bool:
        """
        插入/update/记录
        """
        pass

    @abstractmethod
    def batch_save(self, records: List[E]) -> bool:
        """
        批量保存记录
        只批量插入
        不更新
        """
        pass

    @abstractmethod
    def count(self, query: Any = None) -> int:
        """
        统计记录
        """
        pass

    @staticmethod
    @abstractmethod
    def get_client():
        """
        获取客户端
        """
        pass
