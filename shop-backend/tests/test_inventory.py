"""仓储域：入库、盘点、占用、释放、扣减与流水。"""

from __future__ import annotations

import asyncio

from tests.helpers import Api


async def test_inbound_and_adjust(admin: Api):
    inventory = await admin.post("/admin/skus/2/inventory", {"quantity": 10, "reason": "采购补货"})
    assert inventory["available"] == 40
    logs = (await admin.get("/admin/inventory/logs?skuId=2"))["items"]
    assert logs[0]["changeType"] == "INBOUND"
    assert logs[0]["quantity"] == 10
    assert logs[0]["availableAfter"] == 40

    adjusted = await admin.put("/admin/skus/2/inventory", {"available": 8, "reason": "盘点差异"})
    assert adjusted["available"] == 8
    logs = (await admin.get("/admin/inventory/logs?skuId=2"))["items"]
    assert logs[0]["changeType"] == "ADJUST"
    assert logs[0]["quantity"] == -32


async def test_reserve_release_and_deduct(user: Api, admin: Api):
    await user.add_to_cart(1, 2)
    order = await user.checkout("stock-flow-0001")
    rows = (await admin.get("/admin/inventory?keyword=TEE-BLK"))["items"]
    assert rows[0]["available"] == 48
    assert rows[0]["reserved"] == 2
    assert rows[0]["sold"] == 0

    await user.pay(order["orderNo"])
    rows = (await admin.get("/admin/inventory?keyword=TEE-BLK"))["items"]
    assert rows[0]["available"] == 48
    assert rows[0]["reserved"] == 0
    assert rows[0]["sold"] == 2

    logs = (await admin.get("/admin/inventory/logs?skuId=1"))["items"]
    types = [log["changeType"] for log in logs]
    assert "RESERVE" in types and "DEDUCT" in types
    assert any(log["orderNo"] == order["orderNo"] for log in logs)


async def test_cancel_releases_and_logs(user: Api, admin: Api):
    await user.add_to_cart(3, 2)
    order = await user.checkout("stock-release-01")
    await user.post(f"/orders/{order['orderNo']}/cancel")
    rows = (await admin.get("/admin/inventory?keyword=BAG-NAT"))["items"]
    assert rows[0]["available"] == 20
    assert rows[0]["reserved"] == 0
    logs = (await admin.get("/admin/inventory/logs?skuId=3"))["items"]
    assert any(log["changeType"] == "RELEASE" for log in logs)


async def test_concurrent_orders_never_oversell(shop: Api, admin: Api):
    await admin.put("/admin/skus/3/inventory", {"available": 3})
    users: list[Api] = []
    for index in range(5):
        username = f"crowd_{index}"
        await shop.post(
            "/auth/register", {"username": username, "password": "abc12345"}, expected=201
        )
        user = await shop.login(username, "abc12345")
        await user.post(
            "/addresses",
            {
                "receiver": "并发同学",
                "phone": "13900000000",
                "detail": f"福大 {index} 号楼 101",
                "isDefault": True,
            },
            expected=201,
        )
        await user.add_to_cart(3, 1)
        users.append(user)

    async def place(user: Api) -> bool:
        address = await user.first_address()
        cart = await user.cart()
        data = await user.post(
            "/orders",
            {
                "cartItemIds": [cart["items"][0]["id"]],
                "addressId": address["id"],
                "requestId": f"concurrent-{user.token[:6]}-001",
            },
            expected=(201, 409),
        )
        return "orderNo" in data

    results = await asyncio.gather(*(place(user) for user in users), return_exceptions=True)
    failures = [item for item in results if isinstance(item, Exception)]
    assert not failures, failures
    assert sum(1 for item in results if item is True) == 3

    rows = (await admin.get("/admin/inventory?keyword=BAG-NAT"))["items"]
    assert rows[0]["available"] == 0
    assert rows[0]["reserved"] == 3
    assert len((await admin.get("/admin/orders?status=PENDING_PAYMENT"))["items"]) == 3


async def test_low_stock_filter(admin: Api):
    await admin.put("/admin/skus/3/inventory", {"available": 2})
    rows = (await admin.get("/admin/inventory?lowStock=5"))["items"]
    assert any(row["skuId"] == 3 for row in rows)
    assert all(row["available"] <= 5 for row in rows)


async def test_inventory_summary_in_product(shop: Api):
    detail = await shop.get("/products/1")
    black = next(sku for sku in detail["skus"] if sku["code"] == "TEE-BLK-M")
    assert black["availableStock"] == 50
    assert black["purchasable"] is True
