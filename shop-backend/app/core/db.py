"""数据库引擎与会话工厂。用例只有一个进程，进程内单例即可。"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy import event
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import Settings
from app.models import Base


class Database:
    def __init__(self) -> None:
        self.engine: AsyncEngine | None = None
        self.session_factory: async_sessionmaker[AsyncSession] | None = None
        self.url: str | None = None
        self.is_sqlite = False

    def configure(self, settings: Settings) -> None:
        if self.engine is not None and self.url == settings.database_url:
            return
        self.url = settings.database_url
        self.is_sqlite = settings.is_sqlite
        kwargs: dict = {"echo": False}
        if settings.is_sqlite:
            kwargs["connect_args"] = {"timeout": 30}
        else:
            kwargs.update({"pool_pre_ping": True, "pool_recycle": 1800, "pool_size": 10})
        self.engine = create_async_engine(settings.database_url, **kwargs)
        if settings.is_sqlite:
            event.listen(self.engine.sync_engine, "connect", _sqlite_pragmas)
        self.session_factory = async_sessionmaker(
            self.engine, expire_on_commit=False, autoflush=False
        )

    @asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        if self.session_factory is None:
            raise RuntimeError("数据库尚未初始化")
        async with self.session_factory() as session:
            yield session

    async def create_all(self) -> None:
        assert self.engine is not None
        async with self.engine.begin() as conn:
            # WAL 只对 SQLite 有意义；MySQL 上执行 PRAGMA 会直接语法错误
            if self.is_sqlite:
                await conn.exec_driver_sql("PRAGMA journal_mode=WAL")
            await conn.run_sync(Base.metadata.create_all)

    async def drop_all(self) -> None:
        assert self.engine is not None
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    async def dispose(self) -> None:
        if self.engine is not None:
            await self.engine.dispose()
        self.engine = None
        self.session_factory = None
        self.url = None


def _sqlite_pragmas(dbapi_connection, _record) -> None:  # type: ignore[no-untyped-def]
    """每次新建连接只设会话级参数。

    journal_mode 是写进数据库文件的持久设置，放在 create_all 里设一次即可；
    每条连接都执行一次反而会多一次加锁检查。
    """
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA busy_timeout=5000")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.close()


db = Database()
