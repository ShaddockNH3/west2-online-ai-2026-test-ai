"""限量发售接口。提交后立即返回 ticket，建单由后台任务完成。"""

from __future__ import annotations

from blacksheep import Request
from blacksheep.server.routing import Router

from app.api import presenters
from app.application.services.auth import PrincipalService
from app.application.services.flashsale import FlashSaleService
from app.core.params import read_body
from app.core.responses import ok
from app.deps import require_principal
from app.schemas import FlashSaleIn


def register(router: Router) -> None:
    @router.post("/activities/{activity_id}/flash-sale")
    async def join_flash_sale(
        request: Request, activity_id: int, flash: FlashSaleService, principals: PrincipalService
    ):
        principal = await require_principal(request, principals)
        data = await read_body(request, FlashSaleIn)
        record, created = await flash.join(
            principal.user_id,
            activity_id,
            sku_id=data.skuId,
            quantity=data.quantity,
            address_id=data.addressId,
            request_id=data.requestId,
        )
        return ok(presenters.flash_request(record), status=202 if created else 200)

    @router.get("/flash-sale/requests")
    async def list_my_requests(
        request: Request, flash: FlashSaleService, principals: PrincipalService
    ):
        principal = await require_principal(request, principals)
        rows = await flash.list_mine(principal.user_id)
        return ok({"items": [presenters.flash_request(row) for row in rows]})

    @router.get("/flash-sale/requests/{request_id}")
    async def get_request(
        request: Request, request_id: str, flash: FlashSaleService, principals: PrincipalService
    ):
        principal = await require_principal(request, principals)
        record = await flash.result(principal.user_id, request_id)
        return ok(presenters.flash_request(record))
