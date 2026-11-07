"""收货地址接口。"""

from __future__ import annotations

from blacksheep import Request
from blacksheep.server.routing import Router

from app.db import db
from app.deps import require_principal
from app.params import read_body
from app.responses import ok
from app.schemas import AddressIn, AddressPatch
from app.services import addresses as address_service


def register(router: Router) -> None:
    @router.get("/addresses")
    async def list_addresses(request: Request):
        principal = await require_principal(request)
        async with db.session() as session:
            rows = await address_service.list_addresses(session, principal.user_id)
            return ok({"items": [address_service.public_address(row) for row in rows]})

    @router.post("/addresses")
    async def create_address(request: Request):
        principal = await require_principal(request)
        data = await read_body(request, AddressIn)
        async with db.session() as session:
            address = await address_service.create_address(session, principal.user_id, data)
            return ok(address_service.public_address(address), status=201)

    @router.patch("/addresses/{address_id}")
    async def update_address(request: Request, address_id: int):
        principal = await require_principal(request)
        data = await read_body(request, AddressPatch)
        async with db.session() as session:
            address = await address_service.update_address(
                session, address_id, principal.user_id, data
            )
            return ok(address_service.public_address(address))

    @router.delete("/addresses/{address_id}")
    async def delete_address(request: Request, address_id: int):
        principal = await require_principal(request)
        async with db.session() as session:
            await address_service.delete_address(session, address_id, principal.user_id)
        return ok({"message": "地址已删除"})

    @router.put("/addresses/{address_id}/default")
    async def set_default(request: Request, address_id: int):
        principal = await require_principal(request)
        async with db.session() as session:
            address = await address_service.set_default(session, address_id, principal.user_id)
            return ok(address_service.public_address(address))
