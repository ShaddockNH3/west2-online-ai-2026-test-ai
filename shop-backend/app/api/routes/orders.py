"""订单与 mock 支付接口。"""

from __future__ import annotations

from blacksheep import Request
from blacksheep.server.routing import Router

from app.core.db import db
from app.core.params import pagination, query_str, read_body
from app.core.responses import ok, paged
from app.deps import require_principal
from app.schemas import CartItemIdsIn, CreateOrderIn, PaymentIn
from app.services import fulfillment as fulfillment_service
from app.services import orders as order_service
from app.services import payments as payment_service
from app.utils import yuan


def register(router: Router) -> None:
    @router.post("/orders/preview")
    async def preview_order(request: Request):
        principal = await require_principal(request)
        data = await read_body(request, CartItemIdsIn)
        async with db.session() as session:
            return ok(
                await order_service.preview(
                    session, principal.user_id, data.cartItemIds, data.addressId
                )
            )

    @router.post("/orders")
    async def create_order(request: Request):
        principal = await require_principal(request)
        data = await read_body(request, CreateOrderIn)
        async with db.session() as session:
            order, created = await order_service.create_order(
                session,
                principal.user_id,
                data.cartItemIds,
                data.addressId,
                data.requestId,
                data.remark,
            )
            return ok(
                {
                    "orderNo": order.order_no,
                    "status": order.status,
                    "totalAmount": yuan(order.total_amount_cents),
                    "replayed": not created,
                },
                status=201 if created else 200,
            )

    @router.get("/orders")
    async def list_orders(request: Request):
        principal = await require_principal(request)
        page, page_size = pagination(request)
        status = query_str(request, "status")
        async with db.session() as session:
            items, total = await order_service.list_orders(
                session, principal.user_id, page=page, page_size=page_size, status=status
            )
            return paged(items, total, page, page_size)

    @router.get("/orders/{order_no}")
    async def get_order(request: Request, order_no: str):
        principal = await require_principal(request)
        async with db.session() as session:
            order = await order_service.get_order(session, order_no, user_id=principal.user_id)
            return ok(await order_service.detail(session, order))

    @router.post("/orders/{order_no}/cancel")
    async def cancel_order(request: Request, order_no: str):
        principal = await require_principal(request)
        async with db.session() as session:
            order = await order_service.cancel_order(session, principal.user_id, order_no)
            return ok(
                {
                    "orderNo": order.order_no,
                    "status": order.status,
                    "message": "订单已取消",
                }
            )

    @router.post("/orders/{order_no}/confirm")
    async def confirm_order(request: Request, order_no: str):
        principal = await require_principal(request)
        async with db.session() as session:
            order = await fulfillment_service.confirm_receipt(session, principal.user_id, order_no)
            return ok({"orderNo": order.order_no, "status": order.status})

    @router.get("/fulfillments/{order_no}")
    async def fulfillment_progress(request: Request, order_no: str):
        principal = await require_principal(request)
        async with db.session() as session:
            record = await fulfillment_service.get_for_user(session, principal.user_id, order_no)
            return ok(fulfillment_service.public_fulfillment(record))

    @router.post("/orders/{order_no}/payments")
    async def pay_order(request: Request, order_no: str):
        principal = await require_principal(request)
        data = await read_body(request, PaymentIn)
        async with db.session() as session:
            payment = await payment_service.pay(session, principal.user_id, order_no, data.result)
            return ok(payment, status=201)

    @router.get("/orders/{order_no}/payments")
    async def list_payments(request: Request, order_no: str):
        principal = await require_principal(request)
        async with db.session() as session:
            items = await payment_service.list_payments(session, principal.user_id, order_no)
            return ok({"items": items})
