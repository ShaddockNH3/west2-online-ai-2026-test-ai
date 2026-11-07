"""限量发售专项：受理、异步建单、限购、售罄与并发不超卖。"""

from __future__ import annotations

import asyncio
from datetime import timedelta

from app.utils import utcnow
from app.worker import WorkerPool
from tests.helpers import Api


async def make_user(shop: Api, index: int) -> Api:
    username = f"flash_{index}"
    await shop.post("/auth/register", {"username": username, "password": "abc12345"}, expected=201)
    user = await shop.login(username, "abc12345")
    await user.post(
        "/addresses",
        {
            "receiver": f"抢购同学{index}",
            "phone": "13900000000",
            "detail": f"福大 9 号楼 {index}01",
            "isDefault": True,
        },
        expected=201,
    )
    return user


async def create_flash_activity(
    admin: Api, *, quota: int, per_user: int, price: str = "8.00"
) -> int:
    now = utcnow()
    data = await admin.post(
        "/admin/activities",
        {
            "name": f"限量抢购-{quota}",
            "type": "FLASH_SALE",
            "status": "ACTIVE",
            "startsAt": (now - timedelta(hours=1)).isoformat() + "Z",
            "endsAt": (now + timedelta(days=1)).isoformat() + "Z",
            "skus": [
                {
                    "skuId": 4,
                    "activityPrice": price,
                    "saleQuota": quota,
                    "perUserLimit": per_user,
                }
            ],
        },
        expected=201,
    )
    return data["id"]


async def test_flash_sale_accepts_then_creates_order(shop: Api, admin: Api):
    user = await make_user(shop, 1)
    address = await user.first_address()
    activity_id = await create_flash_activity(admin, quota=5, per_user=2)

    accepted = await user.post(
        f"/activities/{activity_id}/flash-sale",
        {
            "skuId": 4,
            "quantity": 2,
            "addressId": address["id"],
            "requestId": "flash-accept-01",
        },
        expected=202,
    )
    assert accepted["status"] == "QUEUED"
    assert accepted["unitPrice"] == "8.00"
    assert accepted["orderNo"] is None

    queued = await user.get("/flash-sale/requests/flash-accept-01")
    assert queued["status"] == "QUEUED"

    await WorkerPool(1).run_once(limit=20)
    done = await user.get("/flash-sale/requests/flash-accept-01")
    assert done["status"] == "SUCCEEDED"
    assert done["orderNo"]

    detail = await user.order_detail(done["orderNo"])
    assert detail["status"] == "PENDING_PAYMENT"
    assert detail["totalAmount"] == "16.00"
    assert detail["items"][0]["unitPrice"] == "8.00"
    assert detail["items"][0]["activityName"] == "限量抢购-5"


async def test_flash_sale_per_user_limit(shop: Api, admin: Api):
    user = await make_user(shop, 2)
    address = await user.first_address()
    activity_id = await create_flash_activity(admin, quota=10, per_user=2)
    await user.post(
        f"/activities/{activity_id}/flash-sale",
        {"skuId": 4, "quantity": 1, "addressId": address["id"], "requestId": "limit-one-01"},
        expected=202,
    )
    await user.error(
        "post",
        f"/activities/{activity_id}/flash-sale",
        {"skuId": 4, "quantity": 2, "addressId": address["id"], "requestId": "limit-two-01"},
        status=409,
    )


async def test_flash_sale_sold_out(shop: Api, admin: Api):
    user = await make_user(shop, 3)
    address = await user.first_address()
    activity_id = await create_flash_activity(admin, quota=1, per_user=1)
    await user.post(
        f"/activities/{activity_id}/flash-sale",
        {"skuId": 4, "quantity": 1, "addressId": address["id"], "requestId": "sold-out-001"},
        expected=202,
    )
    other = await make_user(shop, 4)
    other_address = await other.first_address()
    body = await other.error(
        "post",
        f"/activities/{activity_id}/flash-sale",
        {
            "skuId": 4,
            "quantity": 1,
            "addressId": other_address["id"],
            "requestId": "sold-out-002",
        },
        status=409,
    )
    assert "售罄" in body["message"]


async def test_flash_sale_idempotent_request(shop: Api, admin: Api):
    user = await make_user(shop, 5)
    address = await user.first_address()
    activity_id = await create_flash_activity(admin, quota=5, per_user=2)
    payload = {
        "skuId": 4,
        "quantity": 1,
        "addressId": address["id"],
        "requestId": "flash-idem-001",
    }
    first = await user.post(f"/activities/{activity_id}/flash-sale", payload, expected=202)
    second = await user.post(f"/activities/{activity_id}/flash-sale", payload, expected=200)
    assert first["requestId"] == second["requestId"]
    await WorkerPool(1).run_once(limit=20)
    orders = (await user.get("/orders"))["items"]
    assert len(orders) == 1


async def test_flash_sale_rejects_normal_activity(shop: Api):
    user = await shop.login()
    address = await user.first_address()
    await user.error(
        "post",
        "/activities/1/flash-sale",
        {"skuId": 1, "quantity": 1, "addressId": address["id"], "requestId": "not-flash-001"},
        status=409,
    )


async def test_flash_sale_requires_stock(shop: Api, admin: Api):
    user = await make_user(shop, 6)
    address = await user.first_address()
    activity_id = await create_flash_activity(admin, quota=5, per_user=1)
    await admin.put("/admin/skus/4/inventory", {"available": 0})
    await user.error(
        "post",
        f"/activities/{activity_id}/flash-sale",
        {"skuId": 4, "quantity": 1, "addressId": address["id"], "requestId": "no-stock-001"},
        status=409,
    )


async def test_flash_sale_concurrency_never_oversells(shop: Api, admin: Api):
    activity_id = await create_flash_activity(admin, quota=3, per_user=1)
    users = [await make_user(shop, 10 + index) for index in range(8)]

    async def grab(user: Api, index: int) -> bool:
        address = await user.first_address()
        data = await user.post(
            f"/activities/{activity_id}/flash-sale",
            {
                "skuId": 4,
                "quantity": 1,
                "addressId": address["id"],
                "requestId": f"race-{index:04d}-001",
            },
            expected=(200, 202, 409),
        )
        return data.get("status") == "QUEUED"

    results = await asyncio.gather(
        *(grab(user, index) for index, user in enumerate(users)), return_exceptions=True
    )
    errors = [item for item in results if isinstance(item, Exception)]
    assert not errors, errors
    assert sum(1 for item in results if item is True) == 3

    await WorkerPool(1).run_once(limit=30)
    created = [await user.get("/flash-sale/requests") for user in users]
    succeeded = [
        item for rows in created for item in rows["items"] if item["status"] == "SUCCEEDED"
    ]
    assert len(succeeded) == 3
    orders = (await admin.get("/admin/orders?status=PENDING_PAYMENT"))["items"]
    assert len(orders) == 3
