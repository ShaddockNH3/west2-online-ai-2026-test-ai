"""鉴权：解析 Bearer Token，校验会话，再交给应用层的 PrincipalService。"""

from __future__ import annotations

from dataclasses import dataclass

from blacksheep import Request

from app.application.services.auth import PrincipalService
from app.core.config import get_settings
from app.core.security import ACCESS, decode_token
from app.domain.constants import Role
from app.domain.errors import AuthError, PermissionDenied


@dataclass(frozen=True, slots=True)
class Principal:
    user_id: int
    username: str
    role: str
    session_id: str

    @property
    def is_admin(self) -> bool:
        return self.role == Role.ADMIN


def bearer_token(request: Request) -> str:
    raw = request.get_first_header(b"authorization")
    if not raw:
        raise AuthError("请先登录")
    text = raw.decode("latin1").strip() if isinstance(raw, bytes) else str(raw).strip()
    scheme, _, token = text.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        raise AuthError("Authorization 需使用 Bearer Token")
    return token.strip()


async def require_principal(request: Request, principals: PrincipalService) -> Principal:
    claims = decode_token(
        bearer_token(request), expected_type=ACCESS, secret=get_settings().jwt_secret
    )
    session_id = str(claims.get("sid") or "")
    try:
        user_id = int(claims["sub"])
    except (KeyError, TypeError, ValueError) as exc:
        raise AuthError("登录凭证无效") from exc

    user = await principals.load(session_id=session_id, user_id=user_id)
    return Principal(user_id=user.id, username=user.username, role=user.role, session_id=session_id)


async def require_admin(request: Request, principals: PrincipalService) -> Principal:
    principal = await require_principal(request, principals)
    if not principal.is_admin:
        raise PermissionDenied("需要管理员权限")
    return principal
