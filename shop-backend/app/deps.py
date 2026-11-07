"""鉴权依赖：解析 Bearer Token，同时校验会话状态和角色。"""

from __future__ import annotations

from dataclasses import dataclass

from blacksheep import Request
from sqlalchemy import select

from app.config import get_settings
from app.constants import Role, UserStatus
from app.db import db
from app.errors import AuthError, PermissionDenied
from app.models import AuthSession, User
from app.security import ACCESS, decode_token
from app.utils import utcnow


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


async def require_principal(request: Request) -> Principal:
    settings = get_settings()
    claims = decode_token(bearer_token(request), expected_type=ACCESS, secret=settings.jwt_secret)
    session_id = str(claims.get("sid") or "")
    try:
        user_id = int(claims["sub"])
    except (KeyError, TypeError, ValueError) as exc:
        raise AuthError("登录凭证无效") from exc

    async with db.session() as session:
        # 会话与用户一次 join 查完，少一次往返；写路径上的每次查询都会拉长持锁时间
        row = (
            await session.execute(
                select(AuthSession, User)
                .join(User, User.id == AuthSession.user_id)
                .where(AuthSession.id == session_id)
            )
        ).first()
        if row is None:
            raise AuthError("登录已失效，请重新登录")
        auth_session, user = row
        if auth_session.revoked_at is not None:
            raise AuthError("登录已失效，请重新登录")
        if auth_session.expires_at <= utcnow():
            raise AuthError("登录已过期，请重新登录")
        if auth_session.user_id != user_id:
            raise AuthError("登录凭证无效")
        if user.status != UserStatus.ACTIVE:
            raise AuthError("账号不可用，请联系管理员")
        role = user.role
        username = user.username

    return Principal(user_id=user_id, username=username, role=role, session_id=session_id)


async def require_admin(request: Request) -> Principal:
    principal = await require_principal(request)
    if not principal.is_admin:
        raise PermissionDenied("需要管理员权限")
    return principal
