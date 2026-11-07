"""注册、登录、双 Token 刷新与个人信息。

依赖 UserRepository / SessionRepository 两个端口，不碰 SQL。
"""

from __future__ import annotations

import secrets
from datetime import timedelta

from app.application.ports.services import Clock
from app.application.ports.uow import UowFactory
from app.core.config import get_settings
from app.core.security import (
    REFRESH,
    decode_token,
    encode_token,
    hash_password,
    validate_password_strength,
    verify_password,
)
from app.domain.constants import Role, UserStatus
from app.domain.entities import User
from app.domain.errors import (
    AuthError,
    ConflictError,
    NotFoundError,
    PermissionDenied,
    ValidationError,
)


class AuthService:
    def __init__(self, uow_factory: UowFactory, clock: Clock) -> None:
        self._uow = uow_factory
        self._clock = clock

    def _issue_tokens(self, user: User, session_id: str) -> dict:
        settings = get_settings()
        access_token, _, access_ttl = encode_token(
            user_id=user.id,
            role=user.role,
            session_id=session_id,
            token_type="access",
            ttl=settings.access_ttl,
            secret=settings.jwt_secret,
        )
        refresh_token, refresh_jti, refresh_ttl = encode_token(
            user_id=user.id,
            role=user.role,
            session_id=session_id,
            token_type=REFRESH,
            ttl=settings.refresh_ttl,
            secret=settings.jwt_secret,
        )
        return {
            "accessToken": access_token,
            "refreshToken": refresh_token,
            "tokenType": "Bearer",
            "expiresIn": access_ttl,
            "refreshExpiresIn": refresh_ttl,
            "refreshJti": refresh_jti,
        }

    async def register(self, *, username: str, password: str, nickname: str | None) -> User:
        validate_password_strength(password)
        async with self._uow() as uow:
            if await uow.users.username_exists(username):
                raise ConflictError("用户名已被注册")
            user = await uow.users.create(
                username=username,
                password_hash=hash_password(password),
                nickname=nickname or username,
                role=Role.USER,
            )
            await uow.commit()
            return user

    async def login(self, *, username: str, password: str, user_agent: str = "") -> dict:
        async with self._uow() as uow:
            user = await uow.users.get_by_username(username)
            if user is None or not verify_password(user.password_hash, password):
                raise AuthError("用户名或密码错误")
            if user.status != UserStatus.ACTIVE:
                raise PermissionDenied("账号已被禁用")

            session_id = secrets.token_urlsafe(24)
            tokens = self._issue_tokens(user, session_id)
            settings = get_settings()
            await uow.sessions.create(
                session_id=session_id,
                user_id=user.id,
                refresh_jti=tokens.pop("refreshJti"),
                expires_at=self._clock.now() + timedelta(seconds=settings.refresh_ttl),
                user_agent=user_agent,
            )
            await uow.commit()
            tokens["user"] = user
            return tokens

    async def refresh(self, *, refresh_token: str, user_agent: str = "") -> dict:
        settings = get_settings()
        claims = decode_token(refresh_token, expected_type=REFRESH, secret=settings.jwt_secret)
        async with self._uow() as uow:
            auth_session = await uow.sessions.get(str(claims.get("sid")))
            if auth_session is None or auth_session.revoked_at is not None:
                raise AuthError("刷新凭证已失效，请重新登录")
            if auth_session.expires_at <= self._clock.now():
                raise AuthError("刷新凭证已过期，请重新登录")
            if auth_session.refresh_jti != claims.get("jti"):
                # 旧 refresh token 被再次使用：作废整个会话，避免被重放
                await uow.sessions.revoke(auth_session.id, now=self._clock.now())
                await uow.commit()
                raise AuthError("刷新凭证已失效，请重新登录")

            user = await uow.users.get(auth_session.user_id)
            if user is None or user.status != UserStatus.ACTIVE:
                raise AuthError("账号不可用，请联系管理员")

            tokens = self._issue_tokens(user, auth_session.id)
            await uow.sessions.rotate(
                auth_session.id,
                refresh_jti=tokens.pop("refreshJti"),
                expires_at=self._clock.now() + timedelta(seconds=settings.refresh_ttl),
                last_used_at=self._clock.now(),
                user_agent=user_agent,
            )
            await uow.commit()
            tokens["user"] = user
            return tokens

    async def logout(self, session_id: str) -> None:
        async with self._uow() as uow:
            await uow.sessions.revoke(session_id, now=self._clock.now())
            await uow.commit()

    async def profile(self, user_id: int) -> User:
        async with self._uow() as uow:
            user = await uow.users.get(user_id)
            if user is None:
                raise NotFoundError("用户不存在")
            return user

    async def update_profile(
        self, user_id: int, *, nickname: str | None, email: str | None, phone: str | None
    ) -> User:
        async with self._uow() as uow:
            user = await uow.users.update_profile(
                user_id, nickname=nickname, email=email, phone=phone
            )
            await uow.commit()
            return user

    async def change_password(self, user_id: int, *, old_password: str, new_password: str) -> None:
        if old_password == new_password:
            raise ValidationError("新密码不能与原密码相同")
        validate_password_strength(new_password)
        async with self._uow() as uow:
            user = await uow.users.get(user_id)
            if user is None:
                raise NotFoundError("用户不存在")
            if not verify_password(user.password_hash, old_password):
                raise ValidationError("原密码不正确")
            await uow.users.update_password(user_id, hash_password(new_password))
            # 改密后所有登录态失效
            await uow.users.revoke_sessions(user_id, now=self._clock.now())
            await uow.commit()


class PrincipalService:
    """鉴权用：校验会话状态，返回当前用户。"""

    def __init__(self, uow_factory: UowFactory, clock: Clock) -> None:
        self._uow = uow_factory
        self._clock = clock

    async def load(self, *, session_id: str, user_id: int) -> User:
        async with self._uow() as uow:
            pair = await uow.sessions.get_with_user(session_id)
            if pair is None:
                raise AuthError("登录已失效，请重新登录")
            auth_session, user = pair
            if auth_session.revoked_at is not None:
                raise AuthError("登录已失效，请重新登录")
            if auth_session.expires_at <= self._clock.now():
                raise AuthError("登录已过期，请重新登录")
            if auth_session.user_id != user_id:
                raise AuthError("登录凭证无效")
            if user.status != UserStatus.ACTIVE:
                raise AuthError("账号不可用，请联系管理员")
            return user
