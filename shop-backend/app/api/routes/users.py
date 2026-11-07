"""个人信息接口。"""

from __future__ import annotations

from blacksheep import Request
from blacksheep.server.routing import Router

from app.api import presenters
from app.application.services.auth import AuthService, PrincipalService
from app.core.params import read_body
from app.core.responses import ok
from app.deps import require_principal
from app.schemas import ChangePasswordIn, UpdateMeIn


def register(router: Router) -> None:
    @router.get("/users/me")
    async def me(request: Request, auth: AuthService, principals: PrincipalService):
        principal = await require_principal(request, principals)
        return ok(presenters.user(await auth.profile(principal.user_id)))

    @router.patch("/users/me")
    async def update_me(request: Request, auth: AuthService, principals: PrincipalService):
        principal = await require_principal(request, principals)
        data = await read_body(request, UpdateMeIn)
        user = await auth.update_profile(
            principal.user_id,
            nickname=data.nickname,
            email=data.email,
            phone=data.phone,
        )
        return ok(presenters.user(user))

    @router.patch("/users/me/password")
    async def change_password(request: Request, auth: AuthService, principals: PrincipalService):
        principal = await require_principal(request, principals)
        data = await read_body(request, ChangePasswordIn)
        await auth.change_password(
            principal.user_id,
            old_password=data.oldPassword,
            new_password=data.newPassword,
        )
        return ok({"message": "密码已修改，请重新登录"})
