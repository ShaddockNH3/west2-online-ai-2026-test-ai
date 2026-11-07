"""认证接口：注册、登录、刷新、退出。"""

from __future__ import annotations

from blacksheep import Request
from blacksheep.server.routing import Router

from app.db import db
from app.deps import require_principal
from app.params import read_body
from app.responses import ok
from app.schemas import LoginIn, RefreshIn, RegisterIn
from app.services import auth as auth_service


def _user_agent(request: Request) -> str:
    raw = request.get_first_header(b"user-agent")
    if not raw:
        return ""
    return raw.decode("latin1", errors="ignore") if isinstance(raw, bytes) else str(raw)


def register(router: Router) -> None:
    @router.post("/auth/register")
    async def register_user(request: Request):
        data = await read_body(request, RegisterIn)
        async with db.session() as session:
            user = await auth_service.register(session, data)
        return ok(auth_service.public_user(user), status=201)

    @router.post("/auth/login")
    async def login_user(request: Request):
        data = await read_body(request, LoginIn)
        async with db.session() as session:
            tokens = await auth_service.login(session, data, _user_agent(request))
        return ok(tokens)

    @router.post("/auth/refresh")
    async def refresh(request: Request):
        data = await read_body(request, RefreshIn)
        async with db.session() as session:
            tokens = await auth_service.refresh_tokens(session, data, _user_agent(request))
        return ok(tokens)

    @router.post("/auth/logout")
    async def logout(request: Request):
        principal = await require_principal(request)
        async with db.session() as session:
            await auth_service.logout(session, principal.session_id)
        return ok({"message": "已退出登录"})
