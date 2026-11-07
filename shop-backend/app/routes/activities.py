"""活动域接口：公开查询与管理端配置。"""

from __future__ import annotations

from blacksheep import Request
from blacksheep.server.routing import Router

from app.db import db
from app.deps import require_admin
from app.params import read_body
from app.responses import ok
from app.schemas import ActivityIn, ActivityPatch
from app.services import activities as activity_service


def register(router: Router) -> None:
    @router.get("/activities")
    async def list_activities(request: Request):
        async with db.session() as session:
            rows = await activity_service.list_activities(session, active_only=True)
            items = [await activity_service.detail(session, row) for row in rows]
            return ok({"items": items})

    @router.get("/activities/{activity_id}")
    async def get_activity(request: Request, activity_id: int):
        async with db.session() as session:
            activity = await activity_service.get_activity(session, activity_id)
            return ok(await activity_service.detail(session, activity))

    @router.get("/admin/activities")
    async def admin_list_activities(request: Request):
        await require_admin(request)
        async with db.session() as session:
            rows = await activity_service.list_activities(session, include_disabled=True)
            items = [await activity_service.detail(session, row) for row in rows]
            return ok({"items": items})

    @router.post("/admin/activities")
    async def create_activity(request: Request):
        await require_admin(request)
        data = await read_body(request, ActivityIn)
        async with db.session() as session:
            activity = await activity_service.create_activity(session, data)
            return ok(await activity_service.detail(session, activity), status=201)

    @router.patch("/admin/activities/{activity_id}")
    async def update_activity(request: Request, activity_id: int):
        await require_admin(request)
        data = await read_body(request, ActivityPatch)
        async with db.session() as session:
            activity = await activity_service.update_activity(session, activity_id, data)
            return ok(await activity_service.detail(session, activity))
