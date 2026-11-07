"""认证接口：注册、登录、刷新、退出。"""

from __future__ import annotations

from blacksheep import Request
from blacksheep.server.routing import Router

from app.api import presenters
from app.application.services.auth import AuthService, PrincipalService
from app.core.params import read_body
from app.core.responses import ok
from app.deps import require_principal
from app.schemas import LoginIn, RefreshIn, RegisterIn


def _user_agent(request: Request) -> str:
    raw = request.get_first_header(b"user-agent")
    if not raw:
        return ""
    return raw.decode("latin1", errors="ignore") if isinstance(raw, bytes) else str(raw)


def register(router: Router) -> None:
    @router.post("/auth/register")
    async def register_user(request: Request, auth: AuthService):
        data = await read_body(request, RegisterIn)
        user = await auth.register(
            username=data.username, password=data.password, nickname=data.nickname
        )
        return ok(presenters.user(user), status=201)

    @router.post("/auth/login")
    async def login_user(request: Request, auth: AuthService):
        data = await read_body(request, LoginIn)
        tokens = await auth.login(
            username=data.username, password=data.password, user_agent=_user_agent(request)
        )
        return ok({**tokens, "user": presenters.user(tokens["user"])})

    @router.post("/auth/refresh")
    async def refresh(request: Request, auth: AuthService):
        data = await read_body(request, RefreshIn)
        tokens = await auth.refresh(
            refresh_token=data.refreshToken, user_agent=_user_agent(request)
        )
        return ok({**tokens, "user": presenters.user(tokens["user"])})

    @router.post("/auth/logout")
    async def logout(request: Request, auth: AuthService, principals: PrincipalService):
        principal = await require_principal(request, principals)
        await auth.logout(principal.session_id)
        return ok({"message": "已退出登录"})
