"""履约域：支付后生成履约单、备货、模拟发货失败重试、确认收货。"""

from __future__ import annotations

from app.worker import WorkerPool
from tests.helpers import Api


async def paid_order(user: Api, request_id: str) -> str:
    await user.add_to_cart(1, 1)
    order = await user.checkout(request_id)
    await user.pay(order["orderNo"])
    return order["orderNo"]


async def fulfillment_of(admin: Api, order_no: str) -> dict:
    rows = (await admin.get("/admin/fulfillments"))["items"]
    for row in rows:
        if row["orderNo"] == order_no:
            return row
    raise AssertionError("没有生成履约单")


async def test_payment_schedules_fulfillment(user: Api, admin: Api):
    order_no = await paid_order(user, "fulfill-build-01")
    assert (await admin.get("/admin/fulfillments"))["items"] == []
    assert await WorkerPool(concurrency=1).run_once(limit=20) >= 1
    record = await fulfillment_of(admin, order_no)
    assert record["status"] == "PENDING"
    assert record["items"]
    assert record["receiver"]


async def test_prepare_and_ship_then_confirm(user: Api, admin: Api):
    order_no = await paid_order(user, "fulfill-flow-01")
    await WorkerPool(1).run_once(limit=20)
    record = await fulfillment_of(admin, order_no)

    prepared = await admin.post(f"/admin/fulfillments/{record['fulfillmentNo']}/prepare")
    assert prepared["status"] == "READY_TO_SHIP"

    # 未备货不能发货（另一张单）
    other_no = await paid_order(user, "fulfill-flow-02")
    await WorkerPool(1).run_once(limit=20)
    other = await fulfillment_of(admin, other_no)
    await admin.error("post", f"/admin/fulfillments/{other['fulfillmentNo']}/ship", status=409)

    shipped = await admin.post(
        f"/admin/fulfillments/{record['fulfillmentNo']}/ship", {"simulate": "SUCCESS"}
    )
    assert shipped["status"] == "SHIPPED"
    assert shipped["trackingNo"].startswith("SF")
    assert (await user.order_detail(order_no))["status"] == "SHIPPED"

    confirmed = await user.post(f"/orders/{order_no}/confirm")
    assert confirmed["status"] == "COMPLETED"
    detail = await user.order_detail(order_no)
    assert detail["fulfillment"]["status"] == "COMPLETED"
    assert detail["completedAt"]


async def test_ship_failure_can_retry(user: Api, admin: Api):
    order_no = await paid_order(user, "fulfill-retry-01")
    await WorkerPool(1).run_once(limit=20)
    record = await fulfillment_of(admin, order_no)
    no = record["fulfillmentNo"]
    await admin.post(f"/admin/fulfillments/{no}/prepare")

    failed = await admin.error(
        "post", f"/admin/fulfillments/{no}/ship", {"simulate": "FAIL"}, status=502
    )
    assert "重试" in failed["message"]
    after_fail = await fulfillment_of(admin, order_no)
    assert after_fail["attempts"] == 1
    assert after_fail["lastError"]
    assert after_fail["status"] == "READY_TO_SHIP"

    ok = await admin.post(f"/admin/fulfillments/{no}/ship", {"simulate": "SUCCESS"})
    assert ok["status"] == "SHIPPED"
    assert ok["attempts"] == 2
    assert ok["lastError"] is None


async def test_cannot_confirm_before_shipping(user: Api, admin: Api):
    order_no = await paid_order(user, "fulfill-early-01")
    await WorkerPool(1).run_once(limit=20)
    await user.error("post", f"/orders/{order_no}/confirm", status=409)


async def test_cannot_confirm_other_users_order(shop: Api, admin: Api):
    demo = await shop.login()
    order_no = await paid_order(demo, "fulfill-privacy-1")
    await WorkerPool(1).run_once(limit=20)
    record = await fulfillment_of(admin, order_no)
    await admin.post(f"/admin/fulfillments/{record['fulfillmentNo']}/prepare")
    await admin.post(f"/admin/fulfillments/{record['fulfillmentNo']}/ship", {"simulate": "SUCCESS"})

    await shop.post(
        "/auth/register", {"username": "ship_intruder", "password": "abc12345"}, expected=201
    )
    other = await shop.login("ship_intruder", "abc12345")
    await other.error("post", f"/orders/{order_no}/confirm", status=404)
    await other.error("get", f"/fulfillments/{order_no}", status=404)


async def test_user_can_query_fulfillment_progress(user: Api, admin: Api):
    order_no = await paid_order(user, "fulfill-progress-1")
    await WorkerPool(1).run_once(limit=20)
    record = await user.get(f"/fulfillments/{order_no}")
    assert record["status"] == "PENDING"
    assert record["orderNo"] == order_no
