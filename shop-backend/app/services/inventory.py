"""库存：占用、释放、扣减都走带条件的原子 UPDATE，先扣成功再记账。"""

from __future__ import annotations

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.cache import cache
from app.constants import DEFAULT_WAREHOUSE_ID, InventoryChange
from app.errors import NotFoundError
from app.models import Inventory, InventoryLog, Product, Sku
from app.utils import iso, utcnow


async def get_inventory(session: AsyncSession, sku_id: int) -> Inventory | None:
    return await session.scalar(
        select(Inventory).where(
            Inventory.sku_id == sku_id, Inventory.warehouse_id == DEFAULT_WAREHOUSE_ID
        )
    )


async def ensure_inventory(session: AsyncSession, sku_id: int, initial: int = 0) -> Inventory:
    inventory = await get_inventory(session, sku_id)
    if inventory is not None:
        return inventory
    inventory = Inventory(
        warehouse_id=DEFAULT_WAREHOUSE_ID,
        sku_id=sku_id,
        available=initial,
        reserved=0,
        sold=0,
    )
    session.add(inventory)
    await session.flush()
    if initial:
        await _log(
            session,
            inventory,
            change_type=InventoryChange.INBOUND,
            quantity=initial,
            before=0,
            after=initial,
            reason="初始化库存",
        )
    return inventory


async def available_map(session: AsyncSession, sku_ids: list[int]) -> dict[int, int]:
    if not sku_ids:
        return {}
    rows = await session.execute(
        select(Inventory.sku_id, func.coalesce(func.sum(Inventory.available), 0))
        .where(Inventory.sku_id.in_(sku_ids))
        .group_by(Inventory.sku_id)
    )
    return {int(sku_id): int(available) for sku_id, available in rows.all()}


async def available_of(session: AsyncSession, sku_id: int) -> int:
    total = await session.scalar(
        select(func.coalesce(func.sum(Inventory.available), 0)).where(Inventory.sku_id == sku_id)
    )
    return int(total or 0)


def _supports_returning(session: AsyncSession) -> bool:
    """SQLite 3.35+ 支持 UPDATE ... RETURNING，可以少一次 SELECT；MySQL 走回退分支。"""
    bind = session.get_bind()
    return bind is not None and bind.dialect.name == "sqlite"


async def reserve(
    session: AsyncSession, sku_id: int, quantity: int, *, order_no: str | None, reason: str
) -> bool:
    inventory = await get_inventory(session, sku_id)
    if inventory is None:
        return False
    before = inventory.available
    statement = (
        update(Inventory)
        .where(
            Inventory.id == inventory.id,
            Inventory.available >= quantity,
        )
        .values(
            available=Inventory.available - quantity,
            reserved=Inventory.reserved + quantity,
            updated_at=utcnow(),
        )
    )
    if _supports_returning(session):
        row = (await session.execute(statement.returning(Inventory.available))).first()
        if row is None:
            return False
        after = int(row[0])
        before = after + quantity
    else:
        result = await session.execute(statement)
        if result.rowcount != 1:
            return False
        after = before - quantity
    await _log(
        session,
        inventory,
        change_type=InventoryChange.RESERVE,
        quantity=-quantity,
        before=before,
        after=after,
        order_no=order_no,
        reason=reason,
    )
    return True


async def release(
    session: AsyncSession, sku_id: int, quantity: int, *, order_no: str | None, reason: str
) -> bool:
    inventory = await get_inventory(session, sku_id)
    if inventory is None:
        return False
    before = inventory.available
    statement = (
        update(Inventory)
        .where(Inventory.id == inventory.id, Inventory.reserved >= quantity)
        .values(
            available=Inventory.available + quantity,
            reserved=Inventory.reserved - quantity,
            updated_at=utcnow(),
        )
    )
    if _supports_returning(session):
        row = (await session.execute(statement.returning(Inventory.available))).first()
        if row is None:
            return False
        after = int(row[0])
        before = after - quantity
    else:
        result = await session.execute(statement)
        if result.rowcount != 1:
            return False
        after = before + quantity
    await _log(
        session,
        inventory,
        change_type=InventoryChange.RELEASE,
        quantity=quantity,
        before=before,
        after=after,
        order_no=order_no,
        reason=reason,
    )
    return True


async def deduct(
    session: AsyncSession, sku_id: int, quantity: int, *, order_no: str | None, reason: str
) -> bool:
    inventory = await get_inventory(session, sku_id)
    if inventory is None:
        return False
    before = inventory.available
    statement = (
        update(Inventory)
        .where(Inventory.id == inventory.id, Inventory.reserved >= quantity)
        .values(
            reserved=Inventory.reserved - quantity,
            sold=Inventory.sold + quantity,
            updated_at=utcnow(),
        )
    )
    if _supports_returning(session):
        row = (await session.execute(statement.returning(Inventory.available))).first()
        if row is None:
            return False
        after = int(row[0])
        before = after
    else:
        result = await session.execute(statement)
        if result.rowcount != 1:
            return False
        after = before
    await _log(
        session,
        inventory,
        change_type=InventoryChange.DEDUCT,
        quantity=-quantity,
        before=before,
        after=after,
        order_no=order_no,
        reason=reason,
    )
    return True


async def inbound(
    session: AsyncSession, sku_id: int, quantity: int, *, reason: str = "采购入库"
) -> Inventory:
    inventory = await ensure_inventory(session, sku_id)
    before = inventory.available
    inventory.available = before + quantity
    inventory.updated_at = utcnow()
    await session.flush()
    await _log(
        session,
        inventory,
        change_type=InventoryChange.INBOUND,
        quantity=quantity,
        before=before,
        after=before + quantity,
        reason=reason,
    )
    await session.commit()
    await cache.bump("catalog")
    await session.refresh(inventory)
    return inventory


async def adjust_to(
    session: AsyncSession, sku_id: int, target: int, *, reason: str = "盘点调整"
) -> Inventory:
    if target < 0:
        raise NotFoundError("库存不能为负数")
    inventory = await ensure_inventory(session, sku_id)
    before = inventory.available
    delta = target - before
    if delta == 0:
        return inventory
    inventory.available = target
    inventory.updated_at = utcnow()
    await session.flush()
    await _log(
        session,
        inventory,
        change_type=InventoryChange.ADJUST,
        quantity=delta,
        before=before,
        after=target,
        reason=reason,
    )
    await session.commit()
    await cache.bump("catalog")
    await session.refresh(inventory)
    return inventory


async def logs(
    session: AsyncSession, *, sku_id: int | None, page: int, page_size: int
) -> tuple[list[InventoryLog], int]:
    conditions = []
    if sku_id is not None:
        conditions.append(InventoryLog.sku_id == sku_id)
    total = await session.scalar(select(func.count(InventoryLog.id)).where(*conditions)) or 0
    rows = await session.scalars(
        select(InventoryLog)
        .where(*conditions)
        .order_by(InventoryLog.id.desc())
        .limit(page_size)
        .offset((page - 1) * page_size)
    )
    return list(rows), int(total)


async def list_inventory(
    session: AsyncSession,
    *,
    page: int,
    page_size: int,
    keyword: str | None = None,
    low_stock: int | None = None,
) -> tuple[list[dict], int]:
    conditions = []
    if keyword:
        like = f"%{keyword.strip()}%"
        conditions.append((Sku.sku_code.like(like)) | (Product.name.like(like)))
    if low_stock is not None:
        conditions.append(Inventory.available <= low_stock)
    base = (
        select(Inventory, Sku, Product)
        .join(Sku, Sku.id == Inventory.sku_id)
        .join(Product, Product.id == Sku.product_id)
        .where(*conditions)
    )
    total = await session.scalar(
        select(func.count())
        .select_from(Inventory)
        .join(Sku, Sku.id == Inventory.sku_id)
        .join(Product, Product.id == Sku.product_id)
        .where(*conditions)
    )
    rows = (
        await session.execute(
            base.order_by(Inventory.available.asc(), Inventory.id.asc())
            .limit(page_size)
            .offset((page - 1) * page_size)
        )
    ).all()
    items = [
        {
            **public_inventory(inventory, sku.sku_code),
            "productId": product.id,
            "productName": product.name,
            "specs": sku.specs,
            "skuStatus": sku.status,
            "productStatus": product.status,
        }
        for inventory, sku, product in rows
    ]
    return items, int(total or 0)


def public_inventory(inventory: Inventory, sku_code: str | None = None) -> dict:
    return {
        "skuId": inventory.sku_id,
        "skuCode": sku_code,
        "warehouseId": inventory.warehouse_id,
        "available": inventory.available,
        "reserved": inventory.reserved,
        "sold": inventory.sold,
        "updatedAt": iso(inventory.updated_at),
    }


def public_log(log: InventoryLog) -> dict:
    return {
        "id": log.id,
        "skuId": log.sku_id,
        "orderNo": log.order_no,
        "changeType": log.change_type,
        "quantity": log.quantity,
        "availableBefore": log.available_before,
        "availableAfter": log.available_after,
        "reason": log.reason,
        "createdAt": iso(log.created_at),
    }


async def _log(
    session: AsyncSession,
    inventory: Inventory,
    *,
    change_type: str,
    quantity: int,
    before: int,
    after: int,
    order_no: str | None = None,
    reason: str = "",
) -> None:
    session.add(
        InventoryLog(
            inventory_id=inventory.id,
            sku_id=inventory.sku_id,
            order_no=order_no,
            change_type=change_type,
            quantity=quantity,
            available_before=before,
            available_after=after,
            reason=reason,
        )
    )
