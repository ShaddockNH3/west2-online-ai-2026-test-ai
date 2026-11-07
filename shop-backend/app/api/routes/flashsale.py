"""限量发售接口。提交后立即返回 ticket，建单由后台任务完成。"""

from __future__ import annotations

from blacksheep import Request
from blacksheep.server.routing import Router

from app.core.db import db
from app.core.params import read_body
from app.core.responses import ok
from app.deps import require_principal
from app.schemas import FlashSaleIn
from app.services import flashsale as flashsale_service


def register(router: Router) -> None:
    @router.post("/activities/{activity_id}/flash-sale")
    async def join_flash_sale(request: Request, activity_id: int):
        principal = await require_principal(request)
        data = await read_body(request, FlashSaleIn)
        async with db.session() as session:
            record, created = await flashsale_service.join(
                session, principal.user_id, activity_id, data
            )
            return ok(
                flashsale_service.public_request(record),
                status=202 if created else 200,
            )

    @router.get("/flash-sale/requests")
    async def list_my_requests(request: Request):
        principal = await require_principal(request)
        async with db.session() as session:
            return ok({"items": await flashsale_service.list_mine(session, principal.user_id)})

    @router.get("/flash-sale/requests/{request_id}")
    async def get_request(request: Request, request_id: str):
        principal = await require_principal(request)
        async with db.session() as session:
            return ok(await flashsale_service.get_result(session, principal.user_id, request_id))
