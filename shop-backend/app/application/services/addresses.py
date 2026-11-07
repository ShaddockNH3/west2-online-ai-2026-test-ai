"""收货地址用例：归属校验与默认地址维护。"""

from __future__ import annotations

from app.application.ports.uow import UowFactory
from app.domain.entities import Address
from app.domain.errors import NotFoundError


class AddressService:
    def __init__(self, uow_factory: UowFactory) -> None:
        self._uow = uow_factory

    async def list(self, user_id: int) -> list[Address]:
        async with self._uow() as uow:
            return await uow.addresses.list_for_user(user_id)

    async def create(
        self,
        user_id: int,
        *,
        receiver: str,
        phone: str,
        detail: str,
        is_default: bool,
    ) -> Address:
        async with self._uow() as uow:
            first = not await uow.addresses.has_any(user_id)
            address = await uow.addresses.create(
                user_id=user_id,
                receiver=receiver,
                phone=phone,
                detail=detail,
                is_default=is_default or first,
            )
            if address.is_default:
                await uow.addresses.clear_other_defaults(user_id, address.id)
            await uow.commit()
            return address

    async def update(
        self,
        user_id: int,
        address_id: int,
        *,
        receiver: str | None,
        phone: str | None,
        detail: str | None,
        is_default: bool | None,
    ) -> Address:
        async with self._uow() as uow:
            if await uow.addresses.get_owned(address_id, user_id) is None:
                raise NotFoundError("收货地址不存在")
            address = await uow.addresses.update(
                address_id,
                receiver=receiver,
                phone=phone,
                detail=detail,
                is_default=is_default,
            )
            if is_default:
                await uow.addresses.clear_other_defaults(user_id, address_id)
            await uow.commit()
            return address

    async def delete(self, user_id: int, address_id: int) -> None:
        async with self._uow() as uow:
            address = await uow.addresses.get_owned(address_id, user_id)
            if address is None:
                raise NotFoundError("收货地址不存在")
            was_default = address.is_default
            await uow.addresses.delete(address_id)
            if was_default:
                # 删掉默认地址后补一条，避免结算时没有默认项
                candidate = await uow.addresses.latest_for_user(user_id)
                if candidate is not None:
                    await uow.addresses.update(
                        candidate.id,
                        receiver=None,
                        phone=None,
                        detail=None,
                        is_default=True,
                    )
            await uow.commit()

    async def set_default(self, user_id: int, address_id: int) -> Address:
        async with self._uow() as uow:
            if await uow.addresses.get_owned(address_id, user_id) is None:
                raise NotFoundError("收货地址不存在")
            address = await uow.addresses.update(
                address_id, receiver=None, phone=None, detail=None, is_default=True
            )
            await uow.addresses.clear_other_defaults(user_id, address_id)
            await uow.commit()
            return address
