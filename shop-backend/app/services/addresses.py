"""收货地址：归属校验和默认地址维护。"""

from __future__ import annotations

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError
from app.models import Address
from app.schemas import AddressIn, AddressPatch
from app.utils import iso


def public_address(address: Address) -> dict:
    return {
        "id": address.id,
        "receiver": address.receiver,
        "phone": address.phone,
        "detail": address.detail,
        "isDefault": address.is_default,
        "createdAt": iso(address.created_at),
        "updatedAt": iso(address.updated_at),
    }


async def list_addresses(session: AsyncSession, user_id: int) -> list[Address]:
    result = await session.scalars(
        select(Address)
        .where(Address.user_id == user_id)
        .order_by(Address.is_default.desc(), Address.id.desc())
    )
    return list(result)


async def get_owned(session: AsyncSession, address_id: int, user_id: int) -> Address:
    address = await session.scalar(
        select(Address).where(Address.id == address_id, Address.user_id == user_id)
    )
    if address is None:
        # 不区分"不存在"和"别人的"，避免暴露他人数据
        raise NotFoundError("收货地址不存在")
    return address


async def create_address(session: AsyncSession, user_id: int, data: AddressIn) -> Address:
    has_any = await session.scalar(select(Address.id).where(Address.user_id == user_id).limit(1))
    address = Address(
        user_id=user_id,
        receiver=data.receiver,
        phone=data.phone,
        detail=data.detail,
        is_default=data.isDefault or has_any is None,
    )
    session.add(address)
    await session.flush()
    if address.is_default:
        await _clear_other_defaults(session, user_id, address.id)
    await session.commit()
    await session.refresh(address)
    return address


async def update_address(
    session: AsyncSession, address_id: int, user_id: int, data: AddressPatch
) -> Address:
    address = await get_owned(session, address_id, user_id)
    if data.receiver is not None:
        address.receiver = data.receiver
    if data.phone is not None:
        address.phone = data.phone
    if data.detail is not None:
        address.detail = data.detail
    if data.isDefault is not None:
        address.is_default = data.isDefault
        if data.isDefault:
            await _clear_other_defaults(session, user_id, address.id)
    await session.commit()
    await session.refresh(address)
    return address


async def delete_address(session: AsyncSession, address_id: int, user_id: int) -> None:
    address = await get_owned(session, address_id, user_id)
    await session.delete(address)
    await session.commit()
    # 删掉默认地址后，把最近更新的一条设为默认，避免结算时没有默认项
    if address.is_default:
        candidate = await session.scalar(
            select(Address).where(Address.user_id == user_id).order_by(Address.id.desc()).limit(1)
        )
        if candidate is not None:
            candidate.is_default = True
            await session.commit()


async def set_default(session: AsyncSession, address_id: int, user_id: int) -> Address:
    address = await get_owned(session, address_id, user_id)
    address.is_default = True
    await _clear_other_defaults(session, user_id, address.id)
    await session.commit()
    await session.refresh(address)
    return address


async def _clear_other_defaults(session: AsyncSession, user_id: int, keep_id: int) -> None:
    await session.execute(
        update(Address)
        .where(Address.user_id == user_id, Address.id != keep_id)
        .values(is_default=False)
    )
