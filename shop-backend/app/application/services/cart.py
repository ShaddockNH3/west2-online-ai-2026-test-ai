"""购物车用例：同 SKU 合并数量，只允许操作自己的购物车项。"""

from __future__ import annotations

from app.application.ports.services import Clock
from app.application.ports.uow import UowFactory
from app.application.read_models import CartLine, CartView
from app.domain.constants import ProductStatus
from app.domain.entities import CartItem
from app.domain.errors import ConflictError, NotFoundError
from app.domain.pricing import quote


class CartService:
    def __init__(self, uow_factory: UowFactory, clock: Clock) -> None:
        self._uow = uow_factory
        self._clock = clock

    async def view(self, user_id: int) -> CartView:
        async with self._uow() as uow:
            items = await uow.cart.list_for_user(user_id)
            if not items:
                return CartView()

            sku_ids = [item.sku_id for item in items]
            pairs = await uow.catalog.get_skus_with_products(sku_ids)
            mapping = {sku.id: (sku, product) for sku, product in pairs}
            rules = await uow.activities.active_rules(sku_ids, now=self._clock.now())
            stock = await uow.inventory.available_map(sku_ids)

            lines: list[CartLine] = []
            total_amount = 0
            total_quantity = 0
            for item in items:
                sku, product = mapping.get(item.sku_id, (None, None))
                if sku is None or product is None:
                    continue
                priced = quote(sku.price_cents, rules.get(sku.id))
                available = stock.get(sku.id, 0)
                reason = ""
                if product.status != ProductStatus.ON_SALE:
                    reason = "商品已下架"
                elif sku.status != ProductStatus.ON_SALE:
                    reason = "规格已下架"
                elif available < item.quantity:
                    reason = "库存不足"
                purchasable = not reason
                subtotal = priced.unit_cents * item.quantity
                if purchasable:
                    total_amount += subtotal
                    total_quantity += item.quantity
                lines.append(
                    CartLine(
                        id=item.id,
                        sku_id=sku.id,
                        product_id=product.id,
                        product_name=product.name,
                        specs=dict(sku.specs or {}),
                        price_cents=priced.unit_cents,
                        original_cents=priced.original_cents,
                        activity_name=priced.activity_name,
                        quantity=item.quantity,
                        subtotal_cents=subtotal,
                        available_stock=available,
                        purchasable=purchasable,
                        reason=reason,
                    )
                )
            return CartView(
                items=lines, total_quantity=total_quantity, total_amount_cents=total_amount
            )

    async def add(self, user_id: int, *, sku_id: int, quantity: int) -> CartItem:
        async with self._uow() as uow:
            sku = await uow.catalog.get_sku(sku_id)
            pairs = await uow.catalog.get_skus_with_products([sku_id])
            if sku is None or not pairs:
                raise NotFoundError("SKU 不存在")
            product = pairs[0][1]
            if product.status != ProductStatus.ON_SALE:
                raise ConflictError("商品已下架")
            if sku.status != ProductStatus.ON_SALE:
                raise ConflictError("该规格已下架")

            available = await uow.inventory.available_of(sku_id)
            existing = await uow.cart.find_by_sku(user_id, sku_id)
            target = quantity + (existing.quantity if existing else 0)
            if target > available:
                raise ConflictError(f"库存不足，当前最多可购买 {available} 件")

            if existing is not None:
                item = await uow.cart.update_quantity(existing.id, target)
            else:
                item = await uow.cart.add(user_id=user_id, sku_id=sku_id, quantity=quantity)
            await uow.commit()
            return item

    async def update(self, user_id: int, item_id: int, *, quantity: int) -> CartItem:
        async with self._uow() as uow:
            item = await uow.cart.get_owned(item_id, user_id)
            if item is None:
                raise NotFoundError("购物车项不存在")
            available = await uow.inventory.available_of(item.sku_id)
            if quantity > available:
                raise ConflictError(f"库存不足，当前最多可购买 {available} 件")
            updated = await uow.cart.update_quantity(item_id, quantity)
            await uow.commit()
            return updated

    async def remove(self, user_id: int, item_id: int) -> None:
        async with self._uow() as uow:
            item = await uow.cart.get_owned(item_id, user_id)
            if item is None:
                raise NotFoundError("购物车项不存在")
            await uow.cart.delete(item_id)
            await uow.commit()
