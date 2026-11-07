"""收货地址：CRUD、默认地址唯一、跨用户隔离。"""

from __future__ import annotations

from tests.helpers import Api


async def register_and_login(shop: Api, username: str) -> Api:
    await shop.post("/auth/register", {"username": username, "password": "abc12345"}, expected=201)
    return await shop.login(username, "abc12345")


async def test_create_and_list_addresses(user: Api):
    first = await user.post(
        "/addresses",
        {"receiver": "张三", "phone": "13900000000", "detail": "福大 1 号楼 101"},
        expected=201,
    )
    assert first["isDefault"] is False or first["isDefault"] is True
    second = await user.post(
        "/addresses",
        {
            "receiver": "李四",
            "phone": "13900000001",
            "detail": "福大 2 号楼 202",
            "isDefault": True,
        },
        expected=201,
    )
    rows = (await user.get("/addresses"))["items"]
    # 演示账号自带 1 条地址，这里新增 2 条
    assert len(rows) == 3
    defaults = [row for row in rows if row["isDefault"]]
    assert len(defaults) == 1
    assert defaults[0]["id"] == second["id"]


async def test_only_one_default_address(user: Api):
    first = await user.post(
        "/addresses",
        {
            "receiver": "张三",
            "phone": "13900000000",
            "detail": "福大 1 号楼 101",
            "isDefault": True,
        },
        expected=201,
    )
    second = await user.post(
        "/addresses",
        {"receiver": "李四", "phone": "13900000001", "detail": "福大 2 号楼 202"},
        expected=201,
    )
    await user.put(f"/addresses/{second['id']}/default")
    rows = (await user.get("/addresses"))["items"]
    default_ids = [row["id"] for row in rows if row["isDefault"]]
    assert default_ids == [second["id"]]
    assert first["id"] not in default_ids


async def test_update_and_delete_address(user: Api):
    created = await user.post(
        "/addresses",
        {"receiver": "张三", "phone": "13900000000", "detail": "福大 1 号楼 101"},
        expected=201,
    )
    updated = await user.patch(f"/addresses/{created['id']}", {"detail": "福大 3 号楼 303"})
    assert updated["detail"] == "福大 3 号楼 303"
    await user.delete(f"/addresses/{created['id']}")
    rows = (await user.get("/addresses"))["items"]
    assert all(row["id"] != created["id"] for row in rows)


async def test_cannot_touch_other_users_address(shop: Api):
    demo = await shop.login()
    other = await register_and_login(shop, "other_user")
    address = await other.post(
        "/addresses",
        {"receiver": "王五", "phone": "13900000002", "detail": "别的地方 5 号"},
        expected=201,
    )
    await demo.error(
        "patch", f"/addresses/{address['id']}", {"detail": "篡改后的详细地址"}, status=404
    )
    await demo.error("delete", f"/addresses/{address['id']}", status=404)
    await demo.error("put", f"/addresses/{address['id']}/default", status=404)
    rows = (await other.get("/addresses"))["items"]
    assert rows[0]["detail"] == "别的地方 5 号"


async def test_invalid_address_payload(user: Api):
    await user.error(
        "post", "/addresses", {"receiver": "", "phone": "13900000000", "detail": "短"}, status=400
    )
    await user.error(
        "post",
        "/addresses",
        {"receiver": "张三", "phone": "abc", "detail": "福大 1 号楼"},
        status=400,
    )
