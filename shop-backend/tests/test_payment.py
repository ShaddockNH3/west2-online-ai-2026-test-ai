"""mock 支付：失败重试、重复支付、已取消订单、跨用户隔离。"""

from __future__ import annotations

from tests.helpers import Api


async def _order(user: Api, request_id: str) -> dict:
    await user.add_to_cart(1, 1)
    return await user.checkout(request_id)


async def test_failed_payment_keeps_order_pending(user: Api):
    order = await _order(user, "pay-fail-000001")
    payment = await user.pay(order["orderNo"], "FAILURE")
    assert payment["status"] == "FAILED"
    assert payment["failureReason"]
    assert payment["amount"] == "34.00"
    detail = await user.order_detail(order["orderNo"])
    assert detail["status"] == "PENDING_PAYMENT"
    assert detail["paidAt"] is None

    again = await user.pay(order["orderNo"], "SUCCESS")
    assert again["status"] == "SUCCESS"
    assert (await user.order_detail(order["orderNo"]))["status"] == "PAID"


async def test_success_payment_uses_server_amount(user: Api):
    order = await _order(user, "pay-amount-0001")
    payment = await user.pay(order["orderNo"])
    assert payment["amount"] == "34.00"
    assert payment["transactionNo"]
    assert payment["channel"] == "MOCK"


async def test_duplicate_success_payment_rejected(user: Api):
    order = await _order(user, "pay-duplicate-01")
    await user.pay(order["orderNo"])
    await user.error(
        "post", f"/orders/{order['orderNo']}/payments", {"result": "SUCCESS"}, status=409
    )
    payments = (await user.get(f"/orders/{order['orderNo']}/payments"))["items"]
    assert [item["status"] for item in payments] == ["SUCCESS"]


async def test_cancelled_order_cannot_be_paid(user: Api):
    order = await _order(user, "pay-cancelled-01")
    await user.post(f"/orders/{order['orderNo']}/cancel")
    await user.error(
        "post", f"/orders/{order['orderNo']}/payments", {"result": "SUCCESS"}, status=409
    )


async def test_paid_order_cannot_be_cancelled(user: Api):
    order = await _order(user, "pay-paid-000001")
    await user.pay(order["orderNo"])
    await user.error("post", f"/orders/{order['orderNo']}/cancel", status=409)


async def test_payment_list_keeps_failures(user: Api):
    order = await _order(user, "pay-history-0001")
    await user.pay(order["orderNo"], "FAILURE")
    await user.pay(order["orderNo"], "FAILURE")
    await user.pay(order["orderNo"], "SUCCESS")
    rows = (await user.get(f"/orders/{order['orderNo']}/payments"))["items"]
    assert len(rows) == 3
    assert sum(1 for row in rows if row["status"] == "SUCCESS") == 1


async def test_invalid_payment_result(user: Api):
    order = await _order(user, "pay-invalid-0001")
    await user.error(
        "post", f"/orders/{order['orderNo']}/payments", {"result": "MAYBE"}, status=400
    )


async def test_cannot_pay_other_users_order(shop: Api):
    demo = await shop.login()
    order = await _order(demo, "pay-privacy-0001")
    await shop.post(
        "/auth/register", {"username": "pay_intruder", "password": "abc12345"}, expected=201
    )
    other = await shop.login("pay_intruder", "abc12345")
    await other.error(
        "post", f"/orders/{order['orderNo']}/payments", {"result": "SUCCESS"}, status=404
    )
    await other.error("get", f"/orders/{order['orderNo']}/payments", status=404)
