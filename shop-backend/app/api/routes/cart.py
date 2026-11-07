"""购物车接口。"""

from __future__ import annotations

from blacksheep import Request
from blacksheep.server.routing import Router

from app.api import presenters
from app.application.services.auth import PrincipalService
from app.application.services.cart import CartService
from app.core.params import read_body
from app.core.responses import ok
from app.deps import require_principal
from app.schemas import CartAddIn, CartPatch


def register(router: Router) -> None:
    @router.get("/cart/items")
    async def list_cart(request: Request, cart: CartService, principals: PrincipalService):
        principal = await require_principal(request, principals)
        return ok(presenters.cart_view(await cart.view(principal.user_id)))

    @router.post("/cart/items")
    async def add_item(request: Request, cart: CartService, principals: PrincipalService):
        principal = await require_principal(request, principals)
        data = await read_body(request, CartAddIn)
        item = await cart.add(principal.user_id, sku_id=data.skuId, quantity=data.quantity)
        return ok(
            {"id": item.id, "skuId": item.sku_id, "quantity": item.quantity},
            status=201,
        )

    @router.patch("/cart/items/{item_id}")
    async def update_item(
        request: Request, item_id: int, cart: CartService, principals: PrincipalService
    ):
        principal = await require_principal(request, principals)
        data = await read_body(request, CartPatch)
        item = await cart.update(principal.user_id, item_id, quantity=data.quantity)
        return ok({"id": item.id, "skuId": item.sku_id, "quantity": item.quantity})

    @router.delete("/cart/items/{item_id}")
    async def remove_item(
        request: Request, item_id: int, cart: CartService, principals: PrincipalService
    ):
        principal = await require_principal(request, principals)
        await cart.remove(principal.user_id, item_id)
        return ok({"message": "已从购物车移除"})
