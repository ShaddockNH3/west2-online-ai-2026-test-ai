"""第二轮验收：注册、登录、刷新、退出、个人信息与密码。"""

from __future__ import annotations

import pytest

from tests.helpers import Api


async def test_register_creates_normal_user(shop: Api):
    data = await shop.post(
        "/auth/register",
        {"username": "new_student", "password": "abc12345", "nickname": "新同学"},
        expected=201,
    )
    assert data["username"] == "new_student"
    assert data["role"] == "USER"
    assert data["nickname"] == "新同学"
    assert "password" not in data


async def test_register_cannot_escalate_role(shop: Api):
    await shop.error(
        "post",
        "/auth/register",
        {"username": "hacker", "password": "abc12345", "role": "ADMIN"},
        status=400,
    )
    token = (await shop.login()).token
    users = await shop.get("/users/me", token=token)
    assert users["role"] == "USER"


@pytest.mark.parametrize(
    "payload",
    [
        {"username": "ab", "password": "abc12345"},
        {"username": "bad name", "password": "abc12345"},
        {"username": "weakpwd", "password": "12345678"},
        {"username": "short", "password": "a1"},
    ],
)
async def test_register_rejects_invalid_input(shop: Api, payload: dict):
    await shop.error("post", "/auth/register", payload, status=400)


async def test_register_duplicate_username(shop: Api):
    await shop.post(
        "/auth/register", {"username": "dup_user", "password": "abc12345"}, expected=201
    )
    body = await shop.error(
        "post", "/auth/register", {"username": "dup_user", "password": "abc12345"}, status=409
    )
    assert body["code"] == "CONFLICT"


async def test_login_and_me(shop: Api):
    user = await shop.login()
    me = await user.me()
    assert me["username"] == "demo"
    assert me["role"] == "USER"


async def test_wrong_password(shop: Api):
    body = await shop.error(
        "post", "/auth/login", {"username": "demo", "password": "wrong-pass-1"}, status=401
    )
    assert body["code"] == "AUTH_REQUIRED"


async def test_protected_endpoint_requires_token(shop: Api):
    await shop.error("get", "/users/me", status=401)
    await shop.error("get", "/orders", status=401)
    token = (await shop.login()).token
    await shop.error("get", "/users/me", token=token + "x", status=401)


async def test_refresh_rotates_tokens(shop: Api):
    tokens = await shop.post("/auth/login", {"username": "demo", "password": "demo123456"})
    refreshed = await shop.post("/auth/refresh", {"refreshToken": tokens["refreshToken"]})
    assert refreshed["accessToken"] != tokens["accessToken"]
    assert refreshed["refreshToken"] != tokens["refreshToken"]
    me = await shop.get("/users/me", token=refreshed["accessToken"])
    assert me["username"] == "demo"

    # 旧 refresh token 再用一次应被拒绝，且会话作废
    await shop.error("post", "/auth/refresh", {"refreshToken": tokens["refreshToken"]}, status=401)
    await shop.error("get", "/users/me", token=refreshed["accessToken"], status=401)


async def test_logout_invalidates_tokens(shop: Api):
    tokens = await shop.post("/auth/login", {"username": "demo", "password": "demo123456"})
    user = shop.with_token(tokens["accessToken"])
    await user.post("/auth/logout")
    await shop.error("get", "/users/me", token=tokens["accessToken"], status=401)
    await shop.error("post", "/auth/refresh", {"refreshToken": tokens["refreshToken"]}, status=401)


async def test_change_password_requires_relogin(shop: Api):
    user = await shop.login()
    await user.patch(
        "/users/me/password",
        {"oldPassword": "demo123456", "newPassword": "newpass123"},
    )
    await shop.error("get", "/users/me", token=user.token, status=401)
    await shop.error(
        "post", "/auth/login", {"username": "demo", "password": "demo123456"}, status=401
    )
    fresh = await shop.login(password="newpass123")
    assert (await fresh.me())["username"] == "demo"


async def test_change_password_rejects_wrong_old_password(shop: Api):
    user = await shop.login()
    await user.error(
        "patch",
        "/users/me/password",
        {"oldPassword": "not-my-password", "newPassword": "newpass123"},
        status=400,
    )


async def test_update_profile(shop: Api):
    user = await shop.login()
    updated = await user.patch("/users/me", {"nickname": "改过的昵称", "email": "me@example.com"})
    assert updated["nickname"] == "改过的昵称"
    assert updated["email"] == "me@example.com"
    assert (await user.me())["nickname"] == "改过的昵称"


async def test_update_profile_rejects_bad_email(shop: Api):
    user = await shop.login()
    await user.error("patch", "/users/me", {"email": "not-an-email"}, status=400)
