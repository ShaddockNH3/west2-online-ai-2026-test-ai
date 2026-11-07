"""用户与会话的 SQLAlchemy 实现。"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities import AuthSession, User
from app.domain.errors import NotFoundError
from app.infrastructure.persistence.mappers import to_session, to_user
from app.infrastructure.persistence.models import AuthSession as AuthSessionRow
from app.infrastructure.persistence.models import User as UserRow


class SqlUserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, user_id: int) -> User | None:
        row = await self._session.get(UserRow, user_id)
        return to_user(row) if row else None

    async def get_by_username(self, username: str) -> User | None:
        row = await self._session.scalar(select(UserRow).where(UserRow.username == username))
        return to_user(row) if row else None

    async def username_exists(self, username: str) -> bool:
        found = await self._session.scalar(select(UserRow.id).where(UserRow.username == username))
        return found is not None

    async def create(self, *, username: str, password_hash: str, nickname: str, role: str) -> User:
        row = UserRow(username=username, password_hash=password_hash, nickname=nickname, role=role)
        self._session.add(row)
        await self._session.flush()
        return to_user(row)

    async def update_profile(
        self, user_id: int, *, nickname: str | None, email: str | None, phone: str | None
    ) -> User:
        row = await self._session.get(UserRow, user_id)
        if row is None:
            raise NotFoundError("用户不存在")
        if nickname is not None:
            row.nickname = nickname
        if email is not None:
            row.email = email or None
        if phone is not None:
            row.phone = phone or None
        await self._session.flush()
        return to_user(row)

    async def update_password(self, user_id: int, password_hash: str) -> None:
        row = await self._session.get(UserRow, user_id)
        if row is None:
            raise NotFoundError("用户不存在")
        row.password_hash = password_hash
        await self._session.flush()

    async def revoke_sessions(self, user_id: int, *, now: datetime) -> None:
        await self._session.execute(
            update(AuthSessionRow)
            .where(AuthSessionRow.user_id == user_id, AuthSessionRow.revoked_at.is_(None))
            .values(revoked_at=now)
        )


class SqlSessionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        session_id: str,
        user_id: int,
        refresh_jti: str,
        expires_at: datetime,
        user_agent: str,
    ) -> None:
        self._session.add(
            AuthSessionRow(
                id=session_id,
                user_id=user_id,
                refresh_jti=refresh_jti,
                expires_at=expires_at,
                user_agent=user_agent[:255],
            )
        )
        await self._session.flush()

    async def get(self, session_id: str) -> AuthSession | None:
        row = await self._session.get(AuthSessionRow, session_id)
        return to_session(row) if row else None

    async def get_with_user(self, session_id: str) -> tuple[AuthSession, User] | None:
        # 一次 join 查完，少一次往返；鉴权在每个请求上都会跑
        row = (
            await self._session.execute(
                select(AuthSessionRow, UserRow)
                .join(UserRow, UserRow.id == AuthSessionRow.user_id)
                .where(AuthSessionRow.id == session_id)
            )
        ).first()
        if row is None:
            return None
        auth_session, user = row
        return to_session(auth_session), to_user(user)

    async def rotate(
        self,
        session_id: str,
        *,
        refresh_jti: str,
        expires_at: datetime,
        last_used_at: datetime,
        user_agent: str,
    ) -> None:
        row = await self._session.get(AuthSessionRow, session_id)
        if row is None:
            raise NotFoundError("会话不存在")
        row.refresh_jti = refresh_jti
        row.expires_at = expires_at
        row.last_used_at = last_used_at
        if user_agent:
            row.user_agent = user_agent[:255]
        await self._session.flush()

    async def revoke(self, session_id: str, *, now: datetime) -> None:
        row = await self._session.get(AuthSessionRow, session_id)
        if row is not None and row.revoked_at is None:
            row.revoked_at = now
            await self._session.flush()
