"""工作单元端口：一次业务操作一个事务，仓储从它身上拿。"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from types import TracebackType
from typing import Protocol, Self

from app.application.ports.repositories import (
    ActivityRepository,
    AddressRepository,
    CartRepository,
    CatalogRepository,
    FlashSaleRepository,
    FulfillmentRepository,
    InventoryRepository,
    JobRepository,
    OrderRepository,
    SessionRepository,
    UserRepository,
)


class UnitOfWork(Protocol):
    """进入上下文开一个会话，退出时未提交的事务自动回滚。"""

    users: UserRepository
    sessions: SessionRepository
    addresses: AddressRepository
    catalog: CatalogRepository
    cart: CartRepository
    orders: OrderRepository
    inventory: InventoryRepository
    activities: ActivityRepository
    flash_sales: FlashSaleRepository
    fulfillments: FulfillmentRepository
    jobs: JobRepository

    async def __aenter__(self) -> Self: ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None: ...

    async def commit(self) -> None: ...

    async def rollback(self) -> None: ...

    async def flush(self) -> None: ...


# 应用服务拿到的是「怎么开一个工作单元」，而不是具体实现
UowFactory = Callable[[], UnitOfWork]
# 事务边界之外的钩子（提交后让缓存失效之类）
AfterCommit = Callable[[], Awaitable[None]]
