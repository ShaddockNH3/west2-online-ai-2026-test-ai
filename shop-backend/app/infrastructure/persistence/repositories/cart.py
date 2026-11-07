"""购物车的 SQLAlchemy 实现。"""

from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities import CartItem
from app.infrastructure.persistence.mappers import to_cart_item
from app.infrastructure.persistence.models import CartItem as CartItemRow


class SqlCartRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_for_user(self, user_id: int) -> list[CartItem]:
        rows = await self._session.scalars(
            select(CartItemRow)
            .where(CartItemRow.user_id == user_id)
            .order_by(CartItemRow.id.desc())
        )
        return [to_cart_item(row) for row in rows]

    async def get_by_ids(self, user_id: int, item_ids: list[int]) -> list[CartItem]:
        if not item_ids:
            return []
        rows = await self._session.scalars(
            select(CartItemRow).where(CartItemRow.user_id == user_id, CartItemRow.id.in_(item_ids))
        )
        return [to_cart_item(row) for row in rows]

    async def get_owned(self, item_id: int, user_id: int) -> CartItem | None:
        row = await self._session.scalar(
            select(CartItemRow).where(CartItemRow.id == item_id, CartItemRow.user_id == user_id)
        )
        return to_cart_item(row) if row else None

    async def find_by_sku(self, user_id: int, sku_id: int) -> CartItem | None:
        row = await self._session.scalar(
            select(CartItemRow).where(CartItemRow.user_id == user_id, CartItemRow.sku_id == sku_id)
        )
        return to_cart_item(row) if row else None

    async def add(self, *, user_id: int, sku_id: int, quantity: int) -> CartItem:
        row = CartItemRow(user_id=user_id, sku_id=sku_id, quantity=quantity)
        self._session.add(row)
        await self._session.flush()
        return to_cart_item(row)

    async def update_quantity(self, item_id: int, quantity: int) -> CartItem:
        row = await self._session.get(CartItemRow, item_id)
        if row is None:
            raise LookupError("购物车项不存在")
        row.quantity = quantity
        await self._session.flush()
        return to_cart_item(row)

    async def delete(self, item_id: int) -> None:
        await self._session.execute(delete(CartItemRow).where(CartItemRow.id == item_id))

    async def delete_many(self, item_ids: list[int]) -> None:
        if not item_ids:
            return
        await self._session.execute(delete(CartItemRow).where(CartItemRow.id.in_(item_ids)))
