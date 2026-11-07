"""商品域：类目、商品、SKU 的维护与公开浏览。"""

from __future__ import annotations

from tests.helpers import Api


async def test_admin_manages_category_and_product(admin: Api, shop: Api):
    category = await admin.post("/admin/categories", {"name": "帽子"}, expected=201)
    product = await admin.post(
        "/admin/products",
        {"name": "棒球帽", "description": "绣鲸鱼", "categoryId": category["id"]},
        expected=201,
    )
    assert product["status"] == "OFF_SALE"

    # 没有 SKU 不能上架
    await admin.error(
        "patch", f"/admin/products/{product['id']}/status", {"status": "ON_SALE"}, status=409
    )

    sku = await admin.post(
        f"/admin/products/{product['id']}/skus",
        {"specs": {"颜色": "深蓝"}, "price": "59.00", "stock": 12},
        expected=201,
    )
    listed = await admin.patch(f"/admin/products/{product['id']}/status", {"status": "ON_SALE"})
    assert listed["status"] == "ON_SALE"

    public = await shop.get(f"/products/{product['id']}")
    assert public["name"] == "棒球帽"
    assert public["skus"][0]["price"] == "59.00"
    assert public["skus"][0]["availableStock"] == 12
    assert public["skus"][0]["purchasable"] is True
    assert sku["stock"] == 12


async def test_offline_product_hidden_from_public(shop: Api, admin: Api):
    product_id = 1
    await admin.patch(f"/admin/products/{product_id}/status", {"status": "OFF_SALE"})
    await shop.error("get", f"/products/{product_id}", status=404)
    items = (await shop.get("/products"))["items"]
    assert all(item["id"] != product_id for item in items)
    # 管理员仍能看到
    detail = await admin.get(f"/admin/products/{product_id}")
    assert detail["status"] == "OFF_SALE"
    await admin.patch(f"/admin/products/{product_id}/status", {"status": "ON_SALE"})


async def test_product_list_pagination_and_filter(shop: Api):
    page = await shop.get("/products?page=1&pageSize=2")
    assert len(page["items"]) == 2
    assert page["total"] >= 3
    assert page["totalPages"] >= 2

    filtered = await shop.get("/products?categoryId=3")
    assert filtered["items"]
    assert all(item["categoryId"] == 3 for item in filtered["items"])

    found = await shop.get("/products?keyword=文化衫")
    assert any(item["name"] == "工作室文化衫" for item in found["items"])


async def test_product_list_shows_activity_price(shop: Api):
    items = (await shop.get("/products"))["items"]
    tee = next(item for item in items if item["name"] == "工作室文化衫")
    assert tee["minPrice"] == "34.00"
    assert tee["hasActivity"] is True


async def test_normal_user_cannot_use_admin_endpoints(user: Api):
    await user.error("post", "/admin/categories", {"name": "偷偷加的"}, status=403)
    await user.error("get", "/admin/products", status=403)
    await user.error("get", "/admin/orders", status=403)
    await user.error("get", "/admin/jobs", status=403)
    await user.error("get", "/admin/inventory", status=403)


async def test_invalid_price_rejected(admin: Api):
    await admin.error(
        "post",
        "/admin/products/1/skus",
        {"specs": {}, "price": "-1.00"},
        status=400,
    )
    await admin.error(
        "post",
        "/admin/products/1/skus",
        {"specs": {}, "price": "12.345"},
        status=400,
    )
    await admin.error(
        "post",
        "/admin/products/1/skus",
        {"specs": {}, "price": "0"},
        status=400,
    )


async def test_duplicate_category_name(admin: Api):
    await admin.post("/admin/categories", {"name": "重名类目"}, expected=201)
    await admin.error("post", "/admin/categories", {"name": "重名类目"}, status=409)


async def test_sku_update_price_and_status(admin: Api):
    updated = await admin.patch("/admin/skus/1", {"price": "45.00", "status": "ON_SALE"})
    assert updated["price"] == "45.00"
    await admin.patch("/admin/skus/1", {"price": "39.00"})
