"""库存用例：入库、盘点、查询与流水。占/放/扣由下单、支付、取消流程触发。"""

from __future__ import annotations

from app.application.cache_keys import CATALOG_NAMESPACE
from app.application.ports.services import CachePort
from app.application.ports.uow import UowFactory
from app.domain.entities import InventoryLogEntry, InventoryRecord, InventoryRow


class InventoryService:
    def __init__(self, uow_factory: UowFactory, cache: CachePort) -> None:
        self._uow = uow_factory
        self._cache = cache

    async def list(
        self,
        *,
        page: int,
        page_size: int,
        keyword: str | None = None,
        low_stock: int | None = None,
    ) -> tuple[list[InventoryRow], int]:
        async with self._uow() as uow:
            return await uow.inventory.list_rows(
                page=page, page_size=page_size, keyword=keyword, low_stock=low_stock
            )

    async def logs(
        self, *, sku_id: int | None, page: int, page_size: int
    ) -> tuple[list[InventoryLogEntry], int]:
        async with self._uow() as uow:
            return await uow.inventory.logs(sku_id=sku_id, page=page, page_size=page_size)

    async def inbound(self, sku_id: int, quantity: int, *, reason: str) -> InventoryRecord:
        async with self._uow() as uow:
            record = await uow.inventory.inbound(sku_id, quantity, reason=reason)
            await uow.commit()
        await self._cache.bump(CATALOG_NAMESPACE)
        return record

    async def adjust_to(self, sku_id: int, target: int, *, reason: str) -> InventoryRecord:
        async with self._uow() as uow:
            record = await uow.inventory.adjust_to(sku_id, target, reason=reason)
            await uow.commit()
        await self._cache.bump(CATALOG_NAMESPACE)
        return record
