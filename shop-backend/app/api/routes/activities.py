"""活动域接口：公开查询与管理端配置。"""

from __future__ import annotations

from blacksheep import Request
from blacksheep.server.routing import Router

from app.api import presenters
from app.application.services.activities import ActivityService
from app.application.services.auth import PrincipalService
from app.core.params import read_body
from app.core.responses import ok
from app.deps import require_admin
from app.schemas import ActivityIn, ActivityPatch


def register(router: Router) -> None:
    @router.get("/activities")
    async def list_activities(activities: ActivityService):
        rows = await activities.list(active_only=True)
        items = [presenters.activity_detail(await activities.detail(row)) for row in rows]
        return ok({"items": items})

    @router.get("/activities/{activity_id}")
    async def get_activity(activity_id: int, activities: ActivityService):
        return ok(presenters.activity_detail(await activities.detail_of(activity_id)))

    @router.get("/admin/activities")
    async def admin_list_activities(
        request: Request, activities: ActivityService, principals: PrincipalService
    ):
        await require_admin(request, principals)
        rows = await activities.list(include_disabled=True)
        items = [presenters.activity_detail(await activities.detail(row)) for row in rows]
        return ok({"items": items})

    @router.post("/admin/activities")
    async def create_activity(
        request: Request, activities: ActivityService, principals: PrincipalService
    ):
        await require_admin(request, principals)
        data = await read_body(request, ActivityIn)
        activity = await activities.create(
            name=data.name,
            type=data.type,
            status=data.status,
            description=data.description,
            starts_at=data.startsAt,
            ends_at=data.endsAt,
            skus=[item.model_dump() for item in data.skus],
        )
        return ok(presenters.activity_detail(await activities.detail(activity)), status=201)

    @router.patch("/admin/activities/{activity_id}")
    async def update_activity(
        request: Request,
        activity_id: int,
        activities: ActivityService,
        principals: PrincipalService,
    ):
        await require_admin(request, principals)
        data = await read_body(request, ActivityPatch)
        activity = await activities.update(
            activity_id,
            name=data.name,
            description=data.description,
            starts_at=data.startsAt,
            ends_at=data.endsAt,
            status=data.status,
        )
        return ok(presenters.activity_detail(await activities.detail(activity)))
