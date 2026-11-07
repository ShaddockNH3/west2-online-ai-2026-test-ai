"""第三轮验收：结算预览、创建订单、快照、取消与库存占用。"""

from __future__ import annotations

from tests.helpers import Api


async def _prepare_cart(user: Api) -> list[int]:
    await user.add_to_cart(1, 2)  # 文化衫 34 元 x2
    await user.add_to_cart(3, 1)  # 帆布袋 29 元 x1
    return [item["id"] for item in (await user.cart())["items"]]


async def test_preview_computes_amount_on_server(user: Api):
    ids = await _prepare_cart(user)
    address = await user.first_address()
    preview = await user.post("/orders/preview", {"cartItemIds": ids, "addressId": address["id"]})
    assert preview["originalAmount"] == "107.00"
    assert preview["discountAmount"] == "10.00"
    assert preview["totalAmount"] == "97.00"
    assert preview["issues"] == []
    assert preview["address"]["receiver"] == address["receiver"]
    assert {item["productName"] for item in preview["items"]} == {"工作室文化衫", "帆布袋"}


async def test_create_order_returns_no_and_clears_cart(user: Api, admin: Api):
    ids = await _prepare_cart(user)
    created = await user.checkout("order-test-000001")
    assert created["status"] == "PENDING_PAYMENT"
    assert created["totalAmount"] == "97.00"
    order_no = created["orderNo"]
    assert order_no.isdigit() and len(order_no) >= 14

    detail = await user.order_detail(order_no)
    assert detail["status"] == "PENDING_PAYMENT"
    assert detail["receiver"]
    assert len(detail["items"]) == 2
    tee = next(item for item in detail["items"] if item["productName"] == "工作室文化衫")
    assert tee["unitPrice"] == "34.00"
    assert tee["originalUnitPrice"] == "39.00"
    assert tee["quantity"] == 2
    assert tee["subtotal"] == "68.00"
    assert detail["totalAmount"] == "97.00"

    # 已下单的购物车项要移出待购列表
    assert (await user.cart())["items"] == []

    # 下单即占用库存
    rows = (await admin.get("/admin/inventory?keyword=TEE-BLK"))["items"]
    assert rows[0]["reserved"] == 2
    _ = ids


async def test_same_request_id_returns_same_order(user: Api):
    ids = await _prepare_cart(user)
    address = await user.first_address()
    first = await user.checkout("idempotent-00001", address_id=address["id"], cart_item_ids=ids)
    # 客户端原样重放同一请求（购物车项已被删除，仍应返回原订单）
    second = await user.checkout("idempotent-00001", address_id=address["id"], cart_item_ids=ids)
    assert first["orderNo"] == second["orderNo"]
    assert second["replayed"] is True
    assert len((await user.get("/orders"))["items"]) == 1


async def test_same_request_id_different_payload_rejected(user: Api):
    ids = await _prepare_cart(user)
    address = await user.first_address()
    payload = {"cartItemIds": ids, "addressId": address["id"], "requestId": "conflict-000001"}
    await user.post("/orders", payload, expected=201)
    await user.error("post", "/orders", {**payload, "cartItemIds": ids[:1]}, status=409)


async def test_order_snapshot_survives_price_and_name_change(user: Api, admin: Api):
    await user.add_to_cart(3, 1)
    order = await user.checkout("snapshot-000001")
    await admin.patch("/admin/products/2", {"name": "帆布袋（新款）"})
    await admin.patch("/admin/skus/3", {"price": "49.00"})
    detail = await user.order_detail(order["orderNo"])
    assert detail["items"][0]["productName"] == "帆布袋"
    assert detail["items"][0]["unitPrice"] == "29.00"
    assert detail["totalAmount"] == "29.00"


async def test_cancel_order_releases_stock(user: Api, admin: Api):
    await user.add_to_cart(1, 2)
    order = await user.checkout("cancel-test-0001")
    before = (await admin.get("/admin/inventory?keyword=TEE-BLK"))["items"][0]
    assert before["reserved"] == 2 and before["available"] == 48

    cancelled = await user.post(f"/orders/{order['orderNo']}/cancel")
    assert cancelled["status"] == "CANCELLED"
    after = (await admin.get("/admin/inventory?keyword=TEE-BLK"))["items"][0]
    assert after["reserved"] == 0 and after["available"] == 50

    detail = await user.order_detail(order["orderNo"])
    assert detail["status"] == "CANCELLED"
    assert detail["cancelledAt"]


async def test_cancel_twice_conflicts(user: Api):
    await user.add_to_cart(2, 1)
    order = await user.checkout("cancel-twice-001")
    await user.post(f"/orders/{order['orderNo']}/cancel")
    await user.error("post", f"/orders/{order['orderNo']}/cancel", status=409)


async def test_out_of_stock_rolls_back_everything(user: Api, admin: Api):
    await user.add_to_cart(3, 2)
    await admin.put("/admin/skus/3/inventory", {"available": 1})
    await user.error(
        "post",
        "/orders",
        {
            "cartItemIds": [(await user.cart())["items"][0]["id"]],
            "addressId": (await user.first_address())["id"],
            "requestId": "stock-fail-00001",
        },
        status=409,
    )
    # 下单失败：不能留下订单，购物车也不能被清空
    assert (await user.get("/orders"))["items"] == []
    assert len((await user.cart())["items"]) == 1


async def test_preview_does_not_lock_price(user: Api, admin: Api):
    await user.add_to_cart(3, 1)
    ids = [item["id"] for item in (await user.cart())["items"]]
    address = await user.first_address()
    preview = await user.post("/orders/preview", {"cartItemIds": ids, "addressId": address["id"]})
    assert preview["totalAmount"] == "29.00"
    await admin.patch("/admin/skus/3", {"price": "39.00"})
    order = await user.checkout("price-change-001")
    assert order["totalAmount"] == "39.00"
    await admin.patch("/admin/skus/3", {"price": "29.00"})


async def test_cannot_read_other_users_order(shop: Api):
    demo = await shop.login()
    await demo.add_to_cart(2, 1)
    order = await demo.checkout("privacy-test-001")
    await shop.post(
        "/auth/register", {"username": "order_intruder", "password": "abc12345"}, expected=201
    )
    other = await shop.login("order_intruder", "abc12345")
    await other.error("get", f"/orders/{order['orderNo']}", status=404)
    await other.error("post", f"/orders/{order['orderNo']}/cancel", status=404)


async def test_order_list_filters_by_status(user: Api):
    await user.add_to_cart(2, 1)
    order = await user.checkout("list-filter-0001")
    await user.post(f"/orders/{order['orderNo']}/cancel")
    cancelled = await user.get("/orders?status=CANCELLED")
    assert [item["orderNo"] for item in cancelled["items"]] == [order["orderNo"]]
    pending = await user.get("/orders?status=PENDING_PAYMENT")
    assert pending["items"] == []
    await user.error("get", "/orders?status=UNKNOWN", status=400)


async def test_preview_requires_owned_cart_items(user: Api):
    other_address = await user.first_address()
    await user.error(
        "post",
        "/orders/preview",
        {"cartItemIds": [9999], "addressId": other_address["id"]},
        status=400,
    )
