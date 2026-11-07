"""库存的 SQLAlchemy 实现。

占用、释放、扣减都是一个带条件的原子 UPDATE：
`WHERE available >= ?` 命中不到行就说明库存不够，返回 False 由上层回滚整个事务。
"""

from __future__ import annotations

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.constants import DEFAULT_WAREHOUSE_ID, InventoryChange
from app.domain.entities import InventoryLogEntry, InventoryRecord, InventoryRow
from app.domain.errors import ConflictError
from app.domain.money import utcnow
from app.infrastructure.persistence.mappers import to_inventory, to_inventory_log
from app.infrastructure.persistence.models import Inventory as InventoryRowModel
from app.infrastructure.persistence.models import InventoryLog as InventoryLogRow
from app.infrastructure.persistence.models import Product as ProductRow
from app.infrastructure.persistence.models import Sku as SkuRow


class SqlInventoryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def _row(self, sku_id: int) -> InventoryRowModel | None:
        return await self._session.scalar(
            select(InventoryRowModel).where(
                InventoryRowModel.sku_id == sku_id,
                InventoryRowModel.warehouse_id == DEFAULT_WAREHOUSE_ID,
            )
        )

    async def get(self, sku_id: int) -> InventoryRecord | None:
        row = await self._row(sku_id)
        return to_inventory(row) if row else None

    async def ensure(self, sku_id: int, initial: int = 0) -> InventoryRecord:
        row = await self._row(sku_id)
        if row is not None:
            return to_inventory(row)
        row = InventoryRowModel(
            warehouse_id=DEFAULT_WAREHOUSE_ID,
            sku_id=sku_id,
            available=initial,
            reserved=0,
            sold=0,
        )
        self._session.add(row)
        await self._session.flush()
        if initial:
            self._session.add(
                InventoryLogRow(
                    inventory_id=row.id,
                    sku_id=sku_id,
                    change_type=InventoryChange.INBOUND,
                    quantity=initial,
                    available_before=0,
                    available_after=initial,
                    reason="初始化库存",
                )
            )
            await self._session.flush()
        return to_inventory(row)

    async def available_map(self, sku_ids: list[int]) -> dict[int, int]:
        if not sku_ids:
            return {}
        rows = await self._session.execute(
            select(
                InventoryRowModel.sku_id, func.coalesce(func.sum(InventoryRowModel.available), 0)
            )
            .where(InventoryRowModel.sku_id.in_(sku_ids))
            .group_by(InventoryRowModel.sku_id)
        )
        return {int(sku_id): int(available) for sku_id, available in rows.all()}

    async def available_of(self, sku_id: int) -> int:
        total = await self._session.scalar(
            select(func.coalesce(func.sum(InventoryRowModel.available), 0)).where(
                InventoryRowModel.sku_id == sku_id
            )
        )
        return int(total or 0)

    def _supports_returning(self) -> bool:
        bind = self._session.get_bind()
        return bind is not None and bind.dialect.name == "sqlite"

    async def move(
        self,
        sku_id: int,
        quantity: int,
        *,
        action: str,
        order_no: str | None,
        reason: str,
    ) -> bool:
        row = await self._row(sku_id)
        if row is None:
            return False
        before = row.available

        if action == InventoryChange.RESERVE:
            statement = (
                update(InventoryRowModel)
                .where(
                    InventoryRowModel.id == row.id,
                    InventoryRowModel.available >= quantity,
                )
                .values(
                    available=InventoryRowModel.available - quantity,
                    reserved=InventoryRowModel.reserved + quantity,
                    updated_at=utcnow(),
                )
            )
        elif action == InventoryChange.RELEASE:
            statement = (
                update(InventoryRowModel)
                .where(
                    InventoryRowModel.id == row.id,
                    InventoryRowModel.reserved >= quantity,
                )
                .values(
                    available=InventoryRowModel.available + quantity,
                    reserved=InventoryRowModel.reserved - quantity,
                    updated_at=utcnow(),
                )
            )
        elif action == InventoryChange.DEDUCT:
            statement = (
                update(InventoryRowModel)
                .where(
                    InventoryRowModel.id == row.id,
                    InventoryRowModel.reserved >= quantity,
                )
                .values(
                    reserved=InventoryRowModel.reserved - quantity,
                    sold=InventoryRowModel.sold + quantity,
                    updated_at=utcnow(),
                )
            )
        else:
            raise ValueError(f"未知库存动作：{action}")

        if self._supports_returning():
            returned = (
                await self._session.execute(statement.returning(InventoryRowModel.available))
            ).first()
            if returned is None:
                return False
            after = int(returned[0])
        else:
            result = await self._session.execute(statement)
            if result.rowcount != 1:
                return False
            if action == InventoryChange.RESERVE:
                after = before - quantity
            elif action == InventoryChange.RELEASE:
                after = before + quantity
            else:
                after = before

        signed = quantity if action == InventoryChange.RELEASE else -quantity
        if action == InventoryChange.DEDUCT:
            signed = -quantity
        self._session.add(
            InventoryLogRow(
                inventory_id=row.id,
                sku_id=row.sku_id,
                order_no=order_no,
                change_type=action,
                quantity=signed,
                available_before=before,
                available_after=after,
                reason=reason,
            )
        )
        await self._session.flush()
        return True

    async def inbound(self, sku_id: int, quantity: int, *, reason: str) -> InventoryRecord:
        record = await self.ensure(sku_id)
        row = await self._session.get(InventoryRowModel, record.id)
        assert row is not None
        before = row.available
        row.available = before + quantity
        self._session.add(
            InventoryLogRow(
                inventory_id=row.id,
                sku_id=sku_id,
                change_type=InventoryChange.INBOUND,
                quantity=quantity,
                available_before=before,
                available_after=before + quantity,
                reason=reason,
            )
        )
        await self._session.flush()
        return to_inventory(row)

    async def adjust_to(self, sku_id: int, target: int, *, reason: str) -> InventoryRecord:
        if target < 0:
            raise ConflictError("库存不能为负数")
        record = await self.ensure(sku_id)
        row = await self._session.get(InventoryRowModel, record.id)
        assert row is not None
        before = row.available
        if target == before:
            return to_inventory(row)
        row.available = target
        self._session.add(
            InventoryLogRow(
                inventory_id=row.id,
                sku_id=sku_id,
                change_type=InventoryChange.ADJUST,
                quantity=target - before,
                available_before=before,
                available_after=target,
                reason=reason,
            )
        )
        await self._session.flush()
        return to_inventory(row)

    async def list_rows(
        self,
        *,
        page: int,
        page_size: int,
        keyword: str | None,
        low_stock: int | None,
    ) -> tuple[list[InventoryRow], int]:
        conditions = []
        if keyword:
            like = f"%{keyword.strip()}%"
            conditions.append((SkuRow.sku_code.like(like)) | (ProductRow.name.like(like)))
        if low_stock is not None:
            conditions.append(InventoryRowModel.available <= low_stock)

        total = await self._session.scalar(
            select(func.count())
            .select_from(InventoryRowModel)
            .join(SkuRow, SkuRow.id == InventoryRowModel.sku_id)
            .join(ProductRow, ProductRow.id == SkuRow.product_id)
            .where(*conditions)
        )
        rows = (
            await self._session.execute(
                select(InventoryRowModel, SkuRow, ProductRow)
                .join(SkuRow, SkuRow.id == InventoryRowModel.sku_id)
                .join(ProductRow, ProductRow.id == SkuRow.product_id)
                .where(*conditions)
                .order_by(InventoryRowModel.available.asc(), InventoryRowModel.id.asc())
                .limit(page_size)
                .offset((page - 1) * page_size)
            )
        ).all()
        items = [
            InventoryRow(
                inventory=to_inventory(inventory),
                sku_code=sku.sku_code,
                sku_specs=dict(sku.specs or {}),
                sku_status=sku.status,
                product_id=product.id,
                product_name=product.name,
                product_status=product.status,
            )
            for inventory, sku, product in rows
        ]
        return items, int(total or 0)

    async def logs(
        self, *, sku_id: int | None, page: int, page_size: int
    ) -> tuple[list[InventoryLogEntry], int]:
        conditions = []
        if sku_id is not None:
            conditions.append(InventoryLogRow.sku_id == sku_id)
        total = await self._session.scalar(
            select(func.count(InventoryLogRow.id)).where(*conditions)
        )
        rows = await self._session.scalars(
            select(InventoryLogRow)
            .where(*conditions)
            .order_by(InventoryLogRow.id.desc())
            .limit(page_size)
            .offset((page - 1) * page_size)
        )
        return [to_inventory_log(row) for row in rows], int(total or 0)
