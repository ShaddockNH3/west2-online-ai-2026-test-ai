"""收货地址的 SQLAlchemy 实现。"""

from __future__ import annotations

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities import Address
from app.domain.errors import NotFoundError
from app.infrastructure.persistence.mappers import to_address
from app.infrastructure.persistence.models import Address as AddressRow


class SqlAddressRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_for_user(self, user_id: int) -> list[Address]:
        rows = await self._session.scalars(
            select(AddressRow)
            .where(AddressRow.user_id == user_id)
            .order_by(AddressRow.is_default.desc(), AddressRow.id.desc())
        )
        return [to_address(row) for row in rows]

    async def get_owned(self, address_id: int, user_id: int) -> Address | None:
        row = await self._session.scalar(
            select(AddressRow).where(AddressRow.id == address_id, AddressRow.user_id == user_id)
        )
        return to_address(row) if row else None

    async def has_any(self, user_id: int) -> bool:
        found = await self._session.scalar(
            select(AddressRow.id).where(AddressRow.user_id == user_id).limit(1)
        )
        return found is not None

    async def create(
        self, *, user_id: int, receiver: str, phone: str, detail: str, is_default: bool
    ) -> Address:
        row = AddressRow(
            user_id=user_id,
            receiver=receiver,
            phone=phone,
            detail=detail,
            is_default=is_default,
        )
        self._session.add(row)
        await self._session.flush()
        return to_address(row)

    async def update(
        self,
        address_id: int,
        *,
        receiver: str | None,
        phone: str | None,
        detail: str | None,
        is_default: bool | None,
    ) -> Address:
        row = await self._session.get(AddressRow, address_id)
        if row is None:
            raise NotFoundError("收货地址不存在")
        if receiver is not None:
            row.receiver = receiver
        if phone is not None:
            row.phone = phone
        if detail is not None:
            row.detail = detail
        if is_default is not None:
            row.is_default = is_default
        await self._session.flush()
        return to_address(row)

    async def delete(self, address_id: int) -> None:
        row = await self._session.get(AddressRow, address_id)
        if row is not None:
            await self._session.delete(row)
            await self._session.flush()

    async def clear_other_defaults(self, user_id: int, keep_id: int) -> None:
        await self._session.execute(
            update(AddressRow)
            .where(AddressRow.user_id == user_id, AddressRow.id != keep_id)
            .values(is_default=False)
        )

    async def latest_for_user(self, user_id: int) -> Address | None:
        row = await self._session.scalar(
            select(AddressRow)
            .where(AddressRow.user_id == user_id)
            .order_by(AddressRow.id.desc())
            .limit(1)
        )
        return to_address(row) if row else None
