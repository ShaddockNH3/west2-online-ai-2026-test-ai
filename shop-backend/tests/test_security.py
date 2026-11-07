"""安全边界：越权、伪造字段、过期令牌与信息泄露。"""

from __future__ import annotations

import pytest

from app.config import get_settings
from app.security import encode_token
from tests.helpers import Api


async def test_request_body_cannot_forge_money_or_owner(user: Api):
    await user.add_to_cart(1, 1)
    ids = [item["id"] for item in (await user.cart())["items"]]
    address = await user.first_address()
    base = {"cartItemIds": ids, "addressId": address["id"], "requestId": "forge-test-001"}

    for extra in (
        {"totalAmount": "0.01"},
        {"userId": 1},
        {"status": "PAID"},
        {"unitPrice": "0.01"},
    ):
        await user.error("post", "/orders", {**base, **extra}, status=400)
    assert (await user.get("/orders"))["items"] == []


async def test_cart_cannot_override_price(user: Api):
    await user.error(
        "post", "/cart/items", {"skuId": 1, "quantity": 1, "price": "0.01"}, status=400
    )


async def test_expired_access_token_rejected(shop: Api):
    settings = get_settings()
    token, _, _ = encode_token(
        user_id=2,
        role="USER",
        session_id="whatever",
        token_type="access",
        ttl=-10,
        secret=settings.jwt_secret,
    )
    body = await shop.error("get", "/users/me", token=token, status=401)
    assert body["code"] == "TOKEN_EXPIRED"


async def test_refresh_token_cannot_be_used_as_access(shop: Api):
    tokens = await shop.post("/auth/login", {"username": "demo", "password": "demo123456"})
    body = await shop.error("get", "/users/me", token=tokens["refreshToken"], status=401)
    assert body["code"] == "TOKEN_EXPIRED"


async def test_malformed_authorization_header(shop: Api):
    await shop.error("get", "/users/me", token="", status=401)


async def test_admin_can_read_all_orders(shop: Api, admin: Api):
    demo = await shop.login()
    await demo.add_to_cart(3, 1)
    order = await demo.checkout("admin-view-0001")
    rows = (await admin.get("/admin/orders"))["items"]
    target = next(row for row in rows if row["orderNo"] == order["orderNo"])
    assert target["username"] == "demo"
    detail = await admin.get(f"/admin/orders/{order['orderNo']}")
    assert detail["totalAmount"] == "29.00"


async def test_password_hash_never_exposed(shop: Api, admin: Api):
    me = await shop.login()
    data = await me.me()
    assert "password" not in data and "passwordHash" not in data
    orders = await admin.get("/admin/orders")
    assert "password" not in str(orders)


async def test_error_response_has_no_internal_detail(shop: Api):
    body = await shop.error(
        "post", "/auth/login", {"username": "nobody", "password": "abc12345"}, status=401
    )
    assert "Traceback" not in str(body)
    assert "argon2" not in str(body)


async def test_user_cannot_use_admin_order_endpoint(user: Api):
    await user.add_to_cart(3, 1)
    order = await user.checkout("admin-deny-0001")
    await user.error("get", "/admin/orders", status=403)
    await user.error("get", f"/admin/orders/{order['orderNo']}", status=403)


@pytest.mark.parametrize(
    "method,path",
    [
        ("get", "/admin/overview"),
        ("get", "/admin/fulfillments"),
        ("post", "/admin/jobs/run-once"),
        ("get", "/admin/activities"),
    ],
)
async def test_admin_endpoints_deny_normal_user(user: Api, method: str, path: str):
    await user.error(method, path, status=403)
