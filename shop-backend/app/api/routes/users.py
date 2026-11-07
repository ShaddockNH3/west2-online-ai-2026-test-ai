"""个人信息接口。"""

from __future__ import annotations

from blacksheep import Request
from blacksheep.server.routing import Router

from app.core.db import db
from app.core.params import read_body
from app.core.responses import ok
from app.deps import require_principal
from app.schemas import ChangePasswordIn, UpdateMeIn
from app.services import auth as auth_service


def register(router: Router) -> None:
    @router.get("/users/me")
    async def me(request: Request):
        principal = await require_principal(request)
        async with db.session() as session:
            user = await auth_service.get_user(session, principal.user_id)
            return ok(auth_service.public_user(user))

    @router.patch("/users/me")
    async def update_me(request: Request):
        principal = await require_principal(request)
        data = await read_body(request, UpdateMeIn)
        async with db.session() as session:
            user = await auth_service.update_me(session, principal.user_id, data)
            return ok(auth_service.public_user(user))

    @router.patch("/users/me/password")
    async def change_password(request: Request):
        principal = await require_principal(request)
        data = await read_body(request, ChangePasswordIn)
        async with db.session() as session:
            await auth_service.change_password(session, principal.user_id, data)
        return ok({"message": "密码已修改，请重新登录"})
