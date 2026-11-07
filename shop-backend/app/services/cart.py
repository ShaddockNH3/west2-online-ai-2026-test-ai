"""购物车：同 SKU 合并数量，只允许操作自己的购物车项。"""

from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants import ProductStatus
from app.errors import ConflictError, NotFoundError
from app.models import CartItem, Product, Sku
from app.services import inventory as inventory_service
from app.services.pricing import active_rules, resolve_price
from app.utils import yuan


async def list_items(session: AsyncSession, user_id: int) -> dict:
    items = list(
        await session.scalars(
            select(CartItem).where(CartItem.user_id == user_id).order_by(CartItem.id.desc())
        )
    )
    if not items:
        return {"items": [], "totalQuantity": 0, "totalAmount": "0.00"}
    sku_ids = [item.sku_id for item in items]
    rows = await session.execute(
        select(Sku, Product).join(Product, Product.id == Sku.product_id).where(Sku.id.in_(sku_ids))
    )
    mapping = {sku.id: (sku, product) for sku, product in rows.all()}
    rules = await active_rules(session, sku_ids)
    stock = await inventory_service.available_map(session, sku_ids)

    views = []
    total_amount = 0
    total_quantity = 0
    for item in items:
        sku, product = mapping.get(item.sku_id, (None, None))
        if sku is None or product is None:
            continue
        price, original, activity_name = resolve_price(sku, rules.get(sku.id))
        available = stock.get(sku.id, 0)
        reason = ""
        if product.status != ProductStatus.ON_SALE:
            reason = "商品已下架"
        elif sku.status != "ON_SALE":
            reason = "规格已下架"
        elif available < item.quantity:
            reason = "库存不足"
        purchasable = not reason
        subtotal = price * item.quantity
        if purchasable:
            total_amount += subtotal
            total_quantity += item.quantity
        views.append(
            {
                "id": item.id,
                "skuId": sku.id,
                "productId": product.id,
                "productName": product.name,
                "specs": sku.specs,
                "price": yuan(price),
                "originalPrice": yuan(original),
                "activityName": activity_name or None,
                "quantity": item.quantity,
                "subtotal": yuan(subtotal),
                "availableStock": available,
                "purchasable": purchasable,
                "reason": reason or None,
            }
        )
    return {
        "items": views,
        "totalQuantity": total_quantity,
        "totalAmount": yuan(total_amount),
    }


async def add_item(session: AsyncSession, user_id: int, sku_id: int, quantity: int) -> CartItem:
    sku, product = await _sellable_sku(session, sku_id)
    available = await inventory_service.available_of(session, sku_id)
    existing = await session.scalar(
        select(CartItem).where(CartItem.user_id == user_id, CartItem.sku_id == sku_id)
    )
    target_quantity = quantity + (existing.quantity if existing else 0)
    if target_quantity > available:
        raise ConflictError(f"库存不足，当前最多可购买 {available} 件")
    if existing is not None:
        existing.quantity = target_quantity
        await session.commit()
        await session.refresh(existing)
        return existing
    item = CartItem(user_id=user_id, sku_id=sku_id, quantity=quantity)
    session.add(item)
    await session.commit()
    await session.refresh(item)
    return item


async def update_item(session: AsyncSession, user_id: int, item_id: int, quantity: int) -> CartItem:
    item = await _owned_item(session, user_id, item_id)
    available = await inventory_service.available_of(session, item.sku_id)
    if quantity > available:
        raise ConflictError(f"库存不足，当前最多可购买 {available} 件")
    item.quantity = quantity
    await session.commit()
    await session.refresh(item)
    return item


async def remove_item(session: AsyncSession, user_id: int, item_id: int) -> None:
    item = await _owned_item(session, user_id, item_id)
    await session.execute(delete(CartItem).where(CartItem.id == item.id))
    await session.commit()


async def _owned_item(session: AsyncSession, user_id: int, item_id: int) -> CartItem:
    item = await session.scalar(
        select(CartItem).where(CartItem.id == item_id, CartItem.user_id == user_id)
    )
    if item is None:
        raise NotFoundError("购物车项不存在")
    return item


async def _sellable_sku(session: AsyncSession, sku_id: int) -> tuple[Sku, Product]:
    row = (
        await session.execute(
            select(Sku, Product).join(Product, Product.id == Sku.product_id).where(Sku.id == sku_id)
        )
    ).first()
    if row is None:
        raise NotFoundError("SKU 不存在")
    sku, product = row
    if product.status != ProductStatus.ON_SALE:
        raise ConflictError("商品已下架")
    if sku.status != "ON_SALE":
        raise ConflictError("该规格已下架")
    return sku, product
