import logging
from typing import TypeVar, Any, List, Optional, Type

from sqlalchemy.sql.functions import func
from sqlmodel import SQLModel, create_engine, Session, select, delete

from config import settings
from storage.repository import IRepository
from models import *

engine = create_engine(settings.database.url, echo=False)

E = TypeVar("E", bound=DatabaseModel)


class DatabaseRepository(IRepository[E]):
    def __init__(self, model: Type[E]):
        super().__init__(model)

    def get_all(self) -> List[E]:
        with Session(engine) as session:
            return session.exec(select(self.model)).all()

    def query_list(self, query: Any) -> List[E]:
        with Session(engine) as session:
            return session.exec(query).all()

    def get_by_id(self, id: str) -> Optional[E]:
        with Session(engine) as session:
            return session.get(self.model, id)

    def delete_by_id(self, id: str) -> bool:
        with Session(engine) as session:
            try:
                statement = delete(self.model).where(self.model.id == id)
                result = session.exec(statement)
                session.commit()
                return result.rowcount > 0
            except Exception as e:
                session.rollback()
                logging.error(f"Error deleting record: {e}")
                return False

    def merge(self, record: E) -> bool:
        with Session(engine) as session:
            try:
                session.merge(record)
                session.commit()
                return True
            except Exception as e:
                session.rollback()
                logging.error(f"Error saving record: {e}")
                return False

    def batch_save(self, records: List[E]) -> bool:
        with Session(engine) as session:
            try:
                session.add_all(records)
                session.commit()
                return True
            except Exception as e:
                session.rollback()
                logging.error(f"Error saving records: {e}")
                return False

    def count(self, query: Any = None) -> int:
        with Session(engine) as session:
            return session.exec(
                select(func.count()).select_from(self.model)
            ).one()

    @staticmethod
    def get_client():
        """
        获取数据库会话 不需要手动 close
        Session 里面已经实现了 __exit__ 方法会自己close
        commit 和 rollback 没有实现得自己写
        """
        return Session(engine)


def init_database():
    """
    初始化数据库表结构
    """

    try:
        SQLModel.metadata.create_all(engine)
    except Exception as e:
        logging.error(f"Error initializing DB schema: {e}")
