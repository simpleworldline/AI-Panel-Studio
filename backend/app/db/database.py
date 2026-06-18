"""AI Panel Studio — SQLAlchemy 异步引擎 + 会话工厂"""

from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


class Base(DeclarativeBase):
    pass


# 导入所有模型，确保 Base.metadata 包含全部表
from app.models.discussion import Discussion  # noqa: E402, F401
from app.models.panel_member import PanelMember  # noqa: E402, F401
from app.models.utterance import Utterance  # noqa: E402, F401
from app.models.consensus import ConsensusDisagreement  # noqa: E402, F401
from app.models.expert_status_log import ExpertStatusLog  # noqa: E402, F401

engine = create_async_engine(
    settings.database_url,
    echo=False,
    connect_args={"check_same_thread": False},
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@event.listens_for(engine.sync_engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """连接时启用 WAL 模式 + 外键约束"""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL;")
    cursor.execute("PRAGMA foreign_keys=ON;")
    cursor.close()
