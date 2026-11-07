"""SQLAlchemy 工作单元：一个 UnitOfWork 一个会话，提交与回滚都在这里。"""

from __future__ import annotations

from types import TracebackType
from typing import Self

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.application.ports.uow import UowFactory
from app.infrastructure.persistence.repositories.activities import (
    SqlActivityRepository,
    SqlFlashSaleRepository,
)
from app.infrastructure.persistence.repositories.addresses import SqlAddressRepository
from app.infrastructure.persistence.repositories.cart import SqlCartRepository
from app.infrastructure.persistence.repositories.catalog import SqlCatalogRepository
from app.infrastructure.persistence.repositories.fulfillments import (
    SqlFulfillmentRepository,
    SqlJobRepository,
)
from app.infrastructure.persistence.repositories.inventory import SqlInventoryRepository
from app.infrastructure.persistence.repositories.orders import SqlOrderRepository
from app.infrastructure.persistence.repositories.users import (
    SqlSessionRepository,
    SqlUserRepository,
)


class SqlAlchemyUnitOfWork:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory
        self._session: AsyncSession | None = None

    async def __aenter__(self) -> Self:
        self._session = self._session_factory()
        self.users = SqlUserRepository(self._session)
        self.sessions = SqlSessionRepository(self._session)
        self.addresses = SqlAddressRepository(self._session)
        self.catalog = SqlCatalogRepository(self._session)
        self.cart = SqlCartRepository(self._session)
        self.orders = SqlOrderRepository(self._session)
        self.inventory = SqlInventoryRepository(self._session)
        self.activities = SqlActivityRepository(self._session)
        self.flash_sales = SqlFlashSaleRepository(self._session)
        self.fulfillments = SqlFulfillmentRepository(self._session)
        self.jobs = SqlJobRepository(self._session)
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        assert self._session is not None
        await self._session.close()
        self._session = None

    @property
    def session(self) -> AsyncSession:
        assert self._session is not None, "工作单元还没进入上下文"
        return self._session

    async def commit(self) -> None:
        await self.session.commit()

    async def rollback(self) -> None:
        await self.session.rollback()

    async def flush(self) -> None:
        await self.session.flush()


def make_uow_factory(
    session_factory: async_sessionmaker[AsyncSession],
) -> UowFactory:
    def factory() -> SqlAlchemyUnitOfWork:
        return SqlAlchemyUnitOfWork(session_factory)

    return factory
