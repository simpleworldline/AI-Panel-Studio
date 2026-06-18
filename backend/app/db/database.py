"""数据库引擎与 Session 工厂 — 严格遵循 DATABASE_DESIGN.md §4"""

from sqlalchemy import event
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession


def _set_pragma(dbapi_connection, _connection_record):
    """每次连接时设置 SQLite PRAGMA"""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def create_engine(database_url: str, echo: bool = False):
    """创建异步 SQLAlchemy 引擎，自动配置 WAL + FK"""
    engine = create_async_engine(
        database_url,
        echo=echo,
        connect_args={"check_same_thread": False},
    )
    event.listen(engine.sync_engine, "connect", _set_pragma)
    return engine


def create_session_factory(engine):
    """创建异步 Session 工厂"""
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
