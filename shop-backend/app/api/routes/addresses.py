"""收货地址接口。"""

from __future__ import annotations

from blacksheep import Request
from blacksheep.server.routing import Router

from app.api import presenters
from app.application.services.addresses import AddressService
from app.application.services.auth import PrincipalService
from app.core.params import read_body
from app.core.responses import ok
from app.deps import require_principal
from app.schemas import AddressIn, AddressPatch


def register(router: Router) -> None:
    @router.get("/addresses")
    async def list_addresses(
        request: Request, addresses: AddressService, principals: PrincipalService
    ):
        principal = await require_principal(request, principals)
        rows = await addresses.list(principal.user_id)
        return ok({"items": [presenters.address(row) for row in rows]})

    @router.post("/addresses")
    async def create_address(
        request: Request, addresses: AddressService, principals: PrincipalService
    ):
        principal = await require_principal(request, principals)
        data = await read_body(request, AddressIn)
        address = await addresses.create(
            principal.user_id,
            receiver=data.receiver,
            phone=data.phone,
            detail=data.detail,
            is_default=data.isDefault,
        )
        return ok(presenters.address(address), status=201)

    @router.patch("/addresses/{address_id}")
    async def update_address(
        request: Request, address_id: int, addresses: AddressService, principals: PrincipalService
    ):
        principal = await require_principal(request, principals)
        data = await read_body(request, AddressPatch)
        address = await addresses.update(
            principal.user_id,
            address_id,
            receiver=data.receiver,
            phone=data.phone,
            detail=data.detail,
            is_default=data.isDefault,
        )
        return ok(presenters.address(address))

    @router.delete("/addresses/{address_id}")
    async def delete_address(
        request: Request, address_id: int, addresses: AddressService, principals: PrincipalService
    ):
        principal = await require_principal(request, principals)
        await addresses.delete(principal.user_id, address_id)
        return ok({"message": "地址已删除"})

    @router.put("/addresses/{address_id}/default")
    async def set_default(
        request: Request, address_id: int, addresses: AddressService, principals: PrincipalService
    ):
        principal = await require_principal(request, principals)
        address = await addresses.set_default(principal.user_id, address_id)
        return ok(presenters.address(address))
