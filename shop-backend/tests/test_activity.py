"""活动选价：生效时间窗、停用恢复原价、活动价不得高于原价。"""

from __future__ import annotations

from datetime import timedelta

from app.utils import iso, utcnow
from tests.helpers import Api


async def test_activity_price_applied(shop: Api):
    detail = await shop.get("/products/1")
    black = next(sku for sku in detail["skus"] if sku["code"] == "TEE-BLK-M")
    assert black["price"] == "34.00"
    assert black["originalPrice"] == "39.00"
    assert black["activityName"] == "开学季周边特惠"


async def test_disabled_activity_restores_price(shop: Api, admin: Api):
    await admin.patch("/admin/activities/1", {"status": "DISABLED"})
    detail = await shop.get("/products/1")
    black = next(sku for sku in detail["skus"] if sku["code"] == "TEE-BLK-M")
    assert black["price"] == "39.00"
    assert black["activityName"] is None
    await admin.patch("/admin/activities/1", {"status": "ACTIVE"})


async def test_future_activity_not_applied(shop: Api, admin: Api):
    now = utcnow()
    await admin.post(
        "/admin/activities",
        {
            "name": "双十二预热",
            "type": "FIXED_PRICE",
            "startsAt": iso(now + timedelta(days=3)),
            "endsAt": iso(now + timedelta(days=10)),
            "status": "ACTIVE",
            "skus": [{"skuId": 2, "activityPrice": "30.00"}],
        },
        expected=201,
    )
    detail = await shop.get("/products/1")
    white = next(sku for sku in detail["skus"] if sku["code"] == "TEE-WHT-L")
    assert white["price"] == "39.00"


async def test_activity_price_above_original_rejected(admin: Api):
    now = utcnow()
    await admin.error(
        "post",
        "/admin/activities",
        {
            "name": "假优惠",
            "type": "FIXED_PRICE",
            "startsAt": iso(now - timedelta(hours=1)),
            "endsAt": iso(now + timedelta(days=1)),
            "skus": [{"skuId": 2, "activityPrice": "99.00"}],
        },
        status=400,
    )


async def test_activity_time_window_validation(admin: Api):
    now = utcnow()
    await admin.error(
        "post",
        "/admin/activities",
        {
            "name": "时间反了",
            "type": "FIXED_PRICE",
            "startsAt": iso(now + timedelta(days=2)),
            "endsAt": iso(now),
        },
        status=400,
    )


async def test_lowest_price_wins_between_activities(shop: Api, admin: Api):
    now = utcnow()
    await admin.post(
        "/admin/activities",
        {
            "name": "更低的活动价",
            "type": "FIXED_PRICE",
            "startsAt": iso(now - timedelta(hours=1)),
            "endsAt": iso(now + timedelta(days=1)),
            "status": "ACTIVE",
            "skus": [{"skuId": 1, "activityPrice": "30.00"}],
        },
        expected=201,
    )
    detail = await shop.get("/products/1")
    black = next(sku for sku in detail["skus"] if sku["code"] == "TEE-BLK-M")
    assert black["price"] == "30.00"


async def test_order_uses_activity_price_and_shows_discount(user: Api):
    await user.add_to_cart(1, 2)
    order = await user.checkout("activity-price-1")
    detail = await user.order_detail(order["orderNo"])
    assert detail["originalAmount"] == "78.00"
    assert detail["discountAmount"] == "10.00"
    assert detail["totalAmount"] == "68.00"
    assert detail["items"][0]["activityName"] == "开学季周边特惠"


async def test_activity_list_shows_running_state(shop: Api):
    items = (await shop.get("/activities"))["items"]
    assert items
    assert all(item["running"] is True for item in items)
    assert all(item["status"] == "ACTIVE" for item in items)
