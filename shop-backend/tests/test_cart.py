"""购物车：合并、改量、删除、可购买状态与越权。"""

from __future__ import annotations

from tests.helpers import Api


async def test_add_and_view_cart(user: Api):
    await user.add_to_cart(1, 2)
    cart = await user.cart()
    assert len(cart["items"]) == 1
    item = cart["items"][0]
    assert item["productName"] == "工作室文化衫"
    assert item["price"] == "34.00"
    assert item["originalPrice"] == "39.00"
    assert item["activityName"] == "开学季周边特惠"
    assert item["quantity"] == 2
    assert item["subtotal"] == "68.00"
    assert cart["totalAmount"] == "68.00"


async def test_same_sku_merges_quantity(user: Api):
    await user.add_to_cart(2, 1)
    await user.add_to_cart(2, 2)
    cart = await user.cart()
    assert len(cart["items"]) == 1
    assert cart["items"][0]["quantity"] == 3


async def test_update_quantity_and_remove(user: Api):
    item = await user.add_to_cart(2, 1)
    updated = await user.patch(f"/cart/items/{item['id']}", {"quantity": 4})
    assert updated["quantity"] == 4
    await user.delete(f"/cart/items/{item['id']}")
    assert (await user.cart())["items"] == []


async def test_quantity_must_be_positive(user: Api):
    await user.error("post", "/cart/items", {"skuId": 2, "quantity": 0}, status=400)
    await user.error("post", "/cart/items", {"skuId": 2, "quantity": -3}, status=400)
    item = await user.add_to_cart(2, 1)
    await user.error("patch", f"/cart/items/{item['id']}", {"quantity": 0}, status=400)


async def test_cannot_exceed_stock(user: Api, admin: Api):
    await admin.put("/admin/skus/2/inventory", {"available": 3})
    await user.error("post", "/cart/items", {"skuId": 2, "quantity": 4}, status=409)
    await user.add_to_cart(2, 2)
    # 合并后超库存也要拒绝
    await user.error("post", "/cart/items", {"skuId": 2, "quantity": 2}, status=409)


async def test_offline_sku_cannot_be_added(user: Api, admin: Api):
    await admin.patch("/admin/skus/2", {"status": "OFF_SALE"})
    await user.error("post", "/cart/items", {"skuId": 2, "quantity": 1}, status=409)
    await admin.patch("/admin/skus/2", {"status": "ON_SALE"})


async def test_existing_cart_item_marks_unpurchasable(user: Api, admin: Api):
    await user.add_to_cart(2, 1)
    await admin.patch("/admin/skus/2", {"status": "OFF_SALE"})
    cart = await user.cart()
    assert cart["items"][0]["purchasable"] is False
    assert cart["items"][0]["reason"]
    await admin.patch("/admin/skus/2", {"status": "ON_SALE"})


async def test_cannot_touch_others_cart(shop: Api):
    demo = await shop.login()
    item = await demo.add_to_cart(2, 1)
    await shop.post(
        "/auth/register", {"username": "cart_intruder", "password": "abc12345"}, expected=201
    )
    other = await shop.login("cart_intruder", "abc12345")
    await other.error("patch", f"/cart/items/{item['id']}", {"quantity": 9}, status=404)
    await other.error("delete", f"/cart/items/{item['id']}", status=404)
    assert len((await demo.cart())["items"]) == 1


async def test_cart_requires_login(shop: Api):
    await shop.error("get", "/cart/items", status=401)
    await shop.error("post", "/cart/items", {"skuId": 2, "quantity": 1}, status=401)
