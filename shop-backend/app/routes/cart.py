"""购物车接口。"""

from __future__ import annotations

from blacksheep import Request
from blacksheep.server.routing import Router

from app.db import db
from app.deps import require_principal
from app.params import read_body
from app.responses import ok
from app.schemas import CartAddIn, CartPatch
from app.services import cart as cart_service


def register(router: Router) -> None:
    @router.get("/cart/items")
    async def list_cart(request: Request):
        principal = await require_principal(request)
        async with db.session() as session:
            return ok(await cart_service.list_items(session, principal.user_id))

    @router.post("/cart/items")
    async def add_item(request: Request):
        principal = await require_principal(request)
        data = await read_body(request, CartAddIn)
        async with db.session() as session:
            item = await cart_service.add_item(
                session, principal.user_id, data.skuId, data.quantity
            )
            return ok(
                {"id": item.id, "skuId": item.sku_id, "quantity": item.quantity},
                status=201,
            )

    @router.patch("/cart/items/{item_id}")
    async def update_item(request: Request, item_id: int):
        principal = await require_principal(request)
        data = await read_body(request, CartPatch)
        async with db.session() as session:
            item = await cart_service.update_item(
                session, principal.user_id, item_id, data.quantity
            )
            return ok({"id": item.id, "skuId": item.sku_id, "quantity": item.quantity})

    @router.delete("/cart/items/{item_id}")
    async def remove_item(request: Request, item_id: int):
        principal = await require_principal(request)
        async with db.session() as session:
            await cart_service.remove_item(session, principal.user_id, item_id)
        return ok({"message": "已从购物车移除"})
