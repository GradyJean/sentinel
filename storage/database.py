import logging

from sqlmodel import SQLModel, create_engine, Session

from config import settings


class Database:
    """
    系统数据库管理类
    """

    def __init__(self, db_url: str):
        """
        初始化数据库连接
        """
        try:
            self.engine = create_engine(db_url, echo=False)
        except Exception as e:
            logging.error(f"Database initialization error: {e}")
            raise

    def get_session(self):
        with Session(self.engine) as session:
            yield session

    def init_db(self):
        """
        初始化数据库表结构
        """
        try:
            SQLModel.metadata.create_all(self.engine)
        except Exception as e:
            logging.error(f"Error initializing DB schema: {e}")
