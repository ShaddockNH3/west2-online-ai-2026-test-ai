"""订单与 mock 支付接口。"""

from __future__ import annotations

from blacksheep import Request
from blacksheep.server.routing import Router

from app.api import presenters
from app.application.services.auth import PrincipalService
from app.application.services.fulfillment import FulfillmentService
from app.application.services.orders import OrderService
from app.application.services.payments import PaymentService
from app.core.params import pagination, query_str, read_body
from app.core.responses import ok, paged
from app.deps import require_principal
from app.domain.money import yuan
from app.schemas import CartItemIdsIn, CreateOrderIn, PaymentIn


def register(router: Router) -> None:
    @router.post("/orders/preview")
    async def preview_order(request: Request, orders: OrderService, principals: PrincipalService):
        principal = await require_principal(request, principals)
        data = await read_body(request, CartItemIdsIn)
        preview = await orders.preview(
            principal.user_id,
            cart_item_ids=data.cartItemIds,
            address_id=data.addressId,
        )
        return ok(presenters.order_preview(preview))

    @router.post("/orders")
    async def create_order(request: Request, orders: OrderService, principals: PrincipalService):
        principal = await require_principal(request, principals)
        data = await read_body(request, CreateOrderIn)
        order, created = await orders.create(
            principal.user_id,
            cart_item_ids=data.cartItemIds,
            address_id=data.addressId,
            request_id=data.requestId,
            remark=data.remark,
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
    async def list_orders(request: Request, orders: OrderService, principals: PrincipalService):
        principal = await require_principal(request, principals)
        page, page_size = pagination(request)
        status = query_str(request, "status")
        rows, total = await orders.list_for_user(
            principal.user_id, page=page, page_size=page_size, status=status
        )
        items = [presenters.order_summary(order, count) for order, count in rows]
        return paged(items, total, page, page_size)

    @router.get("/orders/{order_no}")
    async def get_order(
        request: Request, order_no: str, orders: OrderService, principals: PrincipalService
    ):
        principal = await require_principal(request, principals)
        detail = await orders.detail(order_no, user_id=principal.user_id)
        return ok(presenters.order_detail(detail))

    @router.post("/orders/{order_no}/cancel")
    async def cancel_order(
        request: Request, order_no: str, orders: OrderService, principals: PrincipalService
    ):
        principal = await require_principal(request, principals)
        order = await orders.cancel(principal.user_id, order_no)
        return ok({"orderNo": order.order_no, "status": order.status, "message": "订单已取消"})

    @router.post("/orders/{order_no}/confirm")
    async def confirm_order(
        request: Request,
        order_no: str,
        fulfillments: FulfillmentService,
        principals: PrincipalService,
    ):
        principal = await require_principal(request, principals)
        order = await fulfillments.confirm_receipt(principal.user_id, order_no)
        return ok({"orderNo": order.order_no, "status": order.status})

    @router.get("/fulfillments/{order_no}")
    async def fulfillment_progress(
        request: Request,
        order_no: str,
        fulfillments: FulfillmentService,
        principals: PrincipalService,
    ):
        principal = await require_principal(request, principals)
        record = await fulfillments.get_for_user(principal.user_id, order_no)
        return ok(presenters.fulfillment(record))

    @router.post("/orders/{order_no}/payments")
    async def pay_order(
        request: Request, order_no: str, payments: PaymentService, principals: PrincipalService
    ):
        principal = await require_principal(request, principals)
        data = await read_body(request, PaymentIn)
        payment = await payments.pay(principal.user_id, order_no, result=data.result)
        return ok(presenters.payment_with_order(payment), status=201)

    @router.get("/orders/{order_no}/payments")
    async def list_payments(
        request: Request, order_no: str, payments: PaymentService, principals: PrincipalService
    ):
        principal = await require_principal(request, principals)
        items = await payments.list_for_order(principal.user_id, order_no)
        return ok({"items": [presenters.payment(item) for item in items]})
