"""AI Panel Studio — SQLAlchemy 异步引擎 + 会话工厂"""

from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


class Base(DeclarativeBase):
    pass


def init_models():
    """Import all models to register them with Base.metadata. Call before create_all."""
    import app.models.discussion  # noqa: F401
    import app.models.panel_member  # noqa: F401
    import app.models.utterance  # noqa: F401
    import app.models.consensus  # noqa: F401
    import app.models.expert_status_log  # noqa: F401


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
