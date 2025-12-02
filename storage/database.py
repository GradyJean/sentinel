import datetime
import logging
from typing import TypeVar, Any, List, Optional, Type

from sqlalchemy.sql.functions import func
from sqlmodel import SQLModel, create_engine, Session, select, delete

from config import settings
from models.storage.database import DatabaseModel
from models import *
from storage.repository import IRepository

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

    def batch_insert(self, records: List[E]) -> bool:
        with Session(engine) as session:
            try:
                session.add_all(records)
                session.commit()
                return True
            except Exception as e:
                session.rollback()
                logging.error(f"Error saving records: {e}")
                return False

    def batch_merge(self, records: List[E]) -> bool:
        with Session(engine) as session:
            try:
                for record in records:
                    session.merge(record)
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
        init_offset_config()
    except Exception as e:
        logging.error(f"Error initializing DB schema: {e}")


def init_offset_config():
    """
    初始化文件偏移量配置
    """
    with Session(engine) as session:
        record_count = session.exec(select(func.count()).select_from(OffsetConfig)).one()
        if record_count == 0:
            session.add(OffsetConfig(
                id="log_collect",
                offset=0,
            ))
            session.commit()
