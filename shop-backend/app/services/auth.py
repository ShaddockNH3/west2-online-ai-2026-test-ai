"""注册、登录、双 Token 刷新与个人信息。"""

from __future__ import annotations

import secrets
from datetime import timedelta

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.constants import Role, UserStatus
from app.errors import AuthError, ConflictError, NotFoundError, PermissionDenied, ValidationError
from app.models import AuthSession, User
from app.schemas import ChangePasswordIn, LoginIn, RefreshIn, RegisterIn, UpdateMeIn
from app.security import (
    REFRESH,
    encode_token,
    hash_password,
    validate_password_strength,
    verify_password,
)
from app.utils import iso, utcnow


def public_user(user: User) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "nickname": user.nickname,
        "email": user.email,
        "phone": user.phone,
        "role": user.role,
        "createdAt": iso(user.created_at),
        "updatedAt": iso(user.updated_at),
    }


def _issue_tokens(user: User, session_id: str) -> dict:
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


async def register(session: AsyncSession, data: RegisterIn) -> User:
    validate_password_strength(data.password)
    existing = await session.scalar(select(User.id).where(User.username == data.username))
    if existing is not None:
        raise ConflictError("用户名已被注册")
    user = User(
        username=data.username,
        password_hash=hash_password(data.password),
        nickname=data.nickname or data.username,
        role=Role.USER,
    )
    session.add(user)
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise ConflictError("用户名已被注册") from exc
    await session.refresh(user)
    return user


async def login(session: AsyncSession, data: LoginIn, user_agent: str = "") -> dict:
    user = await session.scalar(select(User).where(User.username == data.username))
    if user is None or not verify_password(user.password_hash, data.password):
        raise AuthError("用户名或密码错误")
    if user.status != UserStatus.ACTIVE:
        raise PermissionDenied("账号已被禁用")

    session_id = secrets.token_urlsafe(24)
    tokens = _issue_tokens(user, session_id)
    settings = get_settings()
    session.add(
        AuthSession(
            id=session_id,
            user_id=user.id,
            refresh_jti=tokens.pop("refreshJti"),
            expires_at=utcnow() + timedelta(seconds=settings.refresh_ttl),
            user_agent=user_agent[:255],
        )
    )
    await session.commit()
    tokens["user"] = public_user(user)
    return tokens


async def refresh_tokens(session: AsyncSession, data: RefreshIn, user_agent: str = "") -> dict:
    from app.security import decode_token

    settings = get_settings()
    claims = decode_token(data.refreshToken, expected_type=REFRESH, secret=settings.jwt_secret)
    auth_session = await session.get(AuthSession, str(claims.get("sid")))
    if auth_session is None or auth_session.revoked_at is not None:
        raise AuthError("刷新凭证已失效，请重新登录")
    if auth_session.expires_at <= utcnow():
        raise AuthError("刷新凭证已过期，请重新登录")
    if auth_session.refresh_jti != claims.get("jti"):
        # 旧 refresh token 被再次使用：直接作废该会话，避免被重放
        auth_session.revoked_at = utcnow()
        await session.commit()
        raise AuthError("刷新凭证已失效，请重新登录")

    user = await session.get(User, auth_session.user_id)
    if user is None or user.status != UserStatus.ACTIVE:
        raise AuthError("账号不可用，请联系管理员")

    tokens = _issue_tokens(user, auth_session.id)
    auth_session.refresh_jti = tokens.pop("refreshJti")
    auth_session.expires_at = utcnow() + timedelta(seconds=settings.refresh_ttl)
    auth_session.last_used_at = utcnow()
    auth_session.user_agent = user_agent[:255] or auth_session.user_agent
    await session.commit()
    tokens["user"] = public_user(user)
    return tokens


async def logout(session: AsyncSession, session_id: str) -> None:
    auth_session = await session.get(AuthSession, session_id)
    if auth_session is not None and auth_session.revoked_at is None:
        auth_session.revoked_at = utcnow()
        await session.commit()


async def get_user(session: AsyncSession, user_id: int) -> User:
    user = await session.get(User, user_id)
    if user is None:
        raise NotFoundError("用户不存在")
    return user


async def update_me(session: AsyncSession, user_id: int, data: UpdateMeIn) -> User:
    user = await get_user(session, user_id)
    if data.nickname is not None:
        user.nickname = data.nickname
    if data.email is not None:
        user.email = data.email or None
    if data.phone is not None:
        user.phone = data.phone or None
    await session.commit()
    await session.refresh(user)
    return user


async def change_password(session: AsyncSession, user_id: int, data: ChangePasswordIn) -> None:
    user = await get_user(session, user_id)
    if not verify_password(user.password_hash, data.oldPassword):
        raise ValidationError("原密码不正确")
    if data.oldPassword == data.newPassword:
        raise ValidationError("新密码不能与原密码相同")
    validate_password_strength(data.newPassword)
    user.password_hash = hash_password(data.newPassword)
    # 改密后所有登录态失效，必须重新登录
    await session.execute(
        update(AuthSession)
        .where(AuthSession.user_id == user_id, AuthSession.revoked_at.is_(None))
        .values(revoked_at=utcnow())
    )
    await session.commit()
