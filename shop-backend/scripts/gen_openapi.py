"""生成可导入 Apifox / Postman 的 OpenAPI 文档。

python -m scripts.gen_openapi
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

OUTPUT = Path(__file__).resolve().parent.parent / "docs" / "openapi.json"


def body(schema: str | dict[str, Any], *, required: bool = True) -> dict[str, Any]:
    ref = {"$ref": f"#/components/schemas/{schema}"} if isinstance(schema, str) else schema
    return {
        "required": required,
        "content": {"application/json": {"schema": ref}},
    }


def response(description: str, schema: str | dict[str, Any] | None = None) -> dict[str, Any]:
    if schema is None:
        return {"description": description}
    ref = {"$ref": f"#/components/schemas/{schema}"} if isinstance(schema, str) else schema
    return {
        "description": description,
        "content": {"application/json": {"schema": ref}},
    }


def operation(
    tag: str,
    summary: str,
    *,
    params: list[dict[str, Any]] | None = None,
    request: dict[str, Any] | None = None,
    ok: str = "成功",
    status: str = "200",
    schema: str | dict[str, Any] | None = None,
    admin: bool = False,
    public: bool = False,
) -> dict[str, Any]:
    op: dict[str, Any] = {
        "tags": [tag],
        "summary": summary,
        "responses": {
            status: response(ok, schema),
            "400": response("参数错误", "Error"),
            "401": response("未登录或令牌失效", "Error"),
        },
    }
    if params:
        op["parameters"] = params
    if request:
        op["requestBody"] = request
    if admin:
        op["responses"]["403"] = response("权限不足", "Error")
        op["security"] = [{"bearerAuth": []}]
    elif not public:
        op["security"] = [{"bearerAuth": []}]
    return op


def path_param(name: str, description: str) -> dict[str, Any]:
    return {
        "name": name,
        "in": "path",
        "required": True,
        "description": description,
        "schema": {"type": "string"},
    }


def query(name: str, description: str, type_: str = "string") -> dict[str, Any]:
    return {
        "name": name,
        "in": "query",
        "required": False,
        "description": description,
        "schema": {"type": type_},
    }


SCHEMAS: dict[str, Any] = {
    "Error": {
        "type": "object",
        "properties": {
            "code": {"type": "string", "example": "CONFLICT"},
            "message": {"type": "string", "example": "库存不足"},
            "details": {"nullable": True},
        },
    },
    "RegisterIn": {
        "type": "object",
        "additionalProperties": False,
        "required": ["username", "password"],
        "properties": {
            "username": {"type": "string", "pattern": "^[A-Za-z0-9_]{3,32}$"},
            "password": {"type": "string", "minLength": 8, "maxLength": 64},
            "nickname": {"type": "string", "maxLength": 32},
        },
    },
    "LoginIn": {
        "type": "object",
        "required": ["username", "password"],
        "properties": {
            "username": {"type": "string"},
            "password": {"type": "string"},
        },
    },
    "RefreshIn": {
        "type": "object",
        "required": ["refreshToken"],
        "properties": {"refreshToken": {"type": "string"}},
    },
    "TokenPair": {
        "type": "object",
        "properties": {
            "accessToken": {"type": "string"},
            "refreshToken": {"type": "string"},
            "tokenType": {"type": "string", "example": "Bearer"},
            "expiresIn": {"type": "integer", "example": 1800},
            "refreshExpiresIn": {"type": "integer", "example": 604800},
            "user": {"$ref": "#/components/schemas/User"},
        },
    },
    "User": {
        "type": "object",
        "properties": {
            "id": {"type": "integer"},
            "username": {"type": "string"},
            "nickname": {"type": "string"},
            "email": {"type": "string", "nullable": True},
            "phone": {"type": "string", "nullable": True},
            "role": {"type": "string", "enum": ["USER", "ADMIN"]},
        },
    },
    "UpdateMeIn": {
        "type": "object",
        "properties": {
            "nickname": {"type": "string"},
            "email": {"type": "string"},
            "phone": {"type": "string"},
        },
    },
    "ChangePasswordIn": {
        "type": "object",
        "required": ["oldPassword", "newPassword"],
        "properties": {
            "oldPassword": {"type": "string"},
            "newPassword": {"type": "string", "minLength": 8},
        },
    },
    "AddressIn": {
        "type": "object",
        "required": ["receiver", "phone", "detail"],
        "properties": {
            "receiver": {"type": "string", "example": "张三"},
            "phone": {"type": "string", "example": "13800000000"},
            "detail": {"type": "string", "example": "福建省福州市福州大学 1 号楼 101"},
            "isDefault": {"type": "boolean", "default": False},
        },
    },
    "Address": {
        "type": "object",
        "properties": {
            "id": {"type": "integer"},
            "receiver": {"type": "string"},
            "phone": {"type": "string"},
            "detail": {"type": "string"},
            "isDefault": {"type": "boolean"},
        },
    },
    "Sku": {
        "type": "object",
        "properties": {
            "id": {"type": "integer"},
            "code": {"type": "string"},
            "specs": {"type": "object", "additionalProperties": {"type": "string"}},
            "price": {"type": "string", "example": "34.00"},
            "originalPrice": {"type": "string", "example": "39.00"},
            "activityName": {"type": "string", "nullable": True},
            "availableStock": {"type": "integer"},
            "purchasable": {"type": "boolean"},
        },
    },
    "Product": {
        "type": "object",
        "properties": {
            "id": {"type": "integer"},
            "name": {"type": "string"},
            "description": {"type": "string"},
            "minPrice": {"type": "string"},
            "maxPrice": {"type": "string"},
            "hasActivity": {"type": "boolean"},
            "stockAvailable": {"type": "integer"},
            "skus": {"type": "array", "items": {"$ref": "#/components/schemas/Sku"}},
        },
    },
    "CartAddIn": {
        "type": "object",
        "required": ["skuId", "quantity"],
        "properties": {
            "skuId": {"type": "integer"},
            "quantity": {"type": "integer", "minimum": 1, "example": 2},
        },
    },
    "CartPatchIn": {
        "type": "object",
        "required": ["quantity"],
        "properties": {"quantity": {"type": "integer", "minimum": 1}},
    },
    "Cart": {
        "type": "object",
        "properties": {
            "items": {"type": "array", "items": {"type": "object"}},
            "totalQuantity": {"type": "integer"},
            "totalAmount": {"type": "string"},
        },
    },
    "PreviewIn": {
        "type": "object",
        "required": ["cartItemIds", "addressId"],
        "properties": {
            "cartItemIds": {"type": "array", "items": {"type": "integer"}},
            "addressId": {"type": "integer"},
        },
    },
    "CreateOrderIn": {
        "type": "object",
        "additionalProperties": False,
        "required": ["cartItemIds", "addressId", "requestId"],
        "properties": {
            "cartItemIds": {"type": "array", "items": {"type": "integer"}},
            "addressId": {"type": "integer"},
            "requestId": {
                "type": "string",
                "minLength": 8,
                "example": "checkout-20261102-001",
            },
            "remark": {"type": "string", "maxLength": 255},
        },
    },
    "OrderCreated": {
        "type": "object",
        "properties": {
            "orderNo": {"type": "string", "example": "202611020001"},
            "status": {"type": "string", "example": "PENDING_PAYMENT"},
            "totalAmount": {"type": "string", "example": "90.00"},
            "replayed": {"type": "boolean", "example": False},
        },
    },
    "OrderDetail": {
        "type": "object",
        "properties": {
            "orderNo": {"type": "string"},
            "status": {
                "type": "string",
                "enum": ["PENDING_PAYMENT", "PAID", "SHIPPED", "COMPLETED", "CANCELLED"],
            },
            "originalAmount": {"type": "string"},
            "discountAmount": {"type": "string"},
            "totalAmount": {"type": "string"},
            "receiver": {"type": "string"},
            "phone": {"type": "string"},
            "addressDetail": {"type": "string"},
            "items": {"type": "array", "items": {"type": "object"}},
            "payments": {"type": "array", "items": {"type": "object"}},
            "fulfillment": {"type": "object", "nullable": True},
        },
    },
    "PaymentIn": {
        "type": "object",
        "required": ["result"],
        "properties": {"result": {"type": "string", "enum": ["SUCCESS", "FAILURE"]}},
    },
    "Payment": {
        "type": "object",
        "properties": {
            "paymentNo": {"type": "string"},
            "orderNo": {"type": "string"},
            "amount": {"type": "string"},
            "status": {"type": "string", "enum": ["SUCCESS", "FAILED"]},
            "channel": {"type": "string", "example": "MOCK"},
            "transactionNo": {"type": "string", "nullable": True},
        },
    },
    "FlashSaleIn": {
        "type": "object",
        "required": ["skuId", "quantity", "addressId", "requestId"],
        "properties": {
            "skuId": {"type": "integer"},
            "quantity": {"type": "integer", "minimum": 1},
            "addressId": {"type": "integer"},
            "requestId": {"type": "string", "minLength": 8},
        },
    },
    "FlashSaleTicket": {
        "type": "object",
        "properties": {
            "requestId": {"type": "string"},
            "status": {"type": "string", "enum": ["QUEUED", "SUCCEEDED", "FAILED"]},
            "orderNo": {"type": "string", "nullable": True},
            "unitPrice": {"type": "string"},
            "message": {"type": "string", "nullable": True},
        },
    },
    "ShipIn": {
        "type": "object",
        "properties": {"simulate": {"type": "string", "enum": ["SUCCESS", "FAIL"]}},
    },
}

PATHS: dict[str, Any] = {
    "/health": {
        "get": operation("系统", "健康检查", public=True),
    },
    "/auth/register": {
        "post": operation(
            "认证",
            "注册普通用户",
            request=body("RegisterIn"),
            status="201",
            schema="User",
            public=True,
        ),
    },
    "/auth/login": {
        "post": operation(
            "认证", "登录，返回双 Token", request=body("LoginIn"), schema="TokenPair", public=True
        ),
    },
    "/auth/refresh": {
        "post": operation(
            "认证",
            "用 Refresh Token 换新的一对 Token",
            request=body("RefreshIn"),
            schema="TokenPair",
            public=True,
        ),
    },
    "/auth/logout": {
        "post": operation("认证", "退出当前登录，两种 Token 都失效"),
    },
    "/users/me": {
        "get": operation("用户", "查看个人信息", schema="User"),
        "patch": operation(
            "用户", "修改昵称、邮箱、电话", request=body("UpdateMeIn"), schema="User"
        ),
    },
    "/users/me/password": {
        "patch": operation("用户", "修改密码（所有登录态失效）", request=body("ChangePasswordIn")),
    },
    "/addresses": {
        "get": operation("地址", "列出自己的收货地址"),
        "post": operation(
            "地址", "新增收货地址", request=body("AddressIn"), status="201", schema="Address"
        ),
    },
    "/addresses/{id}": {
        "patch": operation(
            "地址",
            "修改地址",
            params=[path_param("id", "地址 ID")],
            request=body("AddressIn", required=False),
            schema="Address",
        ),
        "delete": operation("地址", "删除地址", params=[path_param("id", "地址 ID")]),
    },
    "/addresses/{id}/default": {
        "put": operation(
            "地址", "设为默认地址", params=[path_param("id", "地址 ID")], schema="Address"
        ),
    },
    "/categories": {"get": operation("商品", "查看启用中的类目", public=True)},
    "/products": {
        "get": operation(
            "商品",
            "分页浏览已上架商品",
            params=[
                query("page", "页码", "integer"),
                query("pageSize", "每页数量", "integer"),
                query("categoryId", "类目 ID", "integer"),
                query("keyword", "名称/介绍关键词"),
            ],
            public=True,
        )
    },
    "/products/{id}": {
        "get": operation(
            "商品",
            "商品详情与可售 SKU",
            params=[path_param("id", "商品 ID")],
            schema="Product",
            public=True,
        )
    },
    "/cart/items": {
        "get": operation("购物车", "查看购物车", schema="Cart"),
        "post": operation(
            "购物车", "加入购物车（同 SKU 合并）", request=body("CartAddIn"), status="201"
        ),
    },
    "/cart/items/{id}": {
        "patch": operation(
            "购物车",
            "修改数量",
            params=[path_param("id", "购物车项 ID")],
            request=body("CartPatchIn"),
        ),
        "delete": operation("购物车", "移出购物车", params=[path_param("id", "购物车项 ID")]),
    },
    "/orders/preview": {
        "post": operation("订单", "结算预览（不锁价、不建单）", request=body("PreviewIn")),
    },
    "/orders": {
        "post": operation(
            "订单",
            "创建订单（requestId 幂等）",
            request=body("CreateOrderIn"),
            status="201",
            schema="OrderCreated",
        ),
        "get": operation(
            "订单",
            "分页查看自己的订单",
            params=[query("status", "订单状态"), query("page", "页码", "integer")],
        ),
    },
    "/orders/{orderNo}": {
        "get": operation(
            "订单", "订单详情", params=[path_param("orderNo", "订单编号")], schema="OrderDetail"
        ),
    },
    "/orders/{orderNo}/cancel": {
        "post": operation("订单", "取消待支付订单", params=[path_param("orderNo", "订单编号")]),
    },
    "/orders/{orderNo}/confirm": {
        "post": operation("订单", "确认收货", params=[path_param("orderNo", "订单编号")]),
    },
    "/orders/{orderNo}/payments": {
        "post": operation(
            "支付",
            "发起 mock 支付",
            params=[path_param("orderNo", "订单编号")],
            request=body("PaymentIn"),
            status="201",
            schema="Payment",
        ),
        "get": operation(
            "支付", "查询该订单的支付记录", params=[path_param("orderNo", "订单编号")]
        ),
    },
    "/fulfillments/{orderNo}": {
        "get": operation("履约", "查看订单的履约进度", params=[path_param("orderNo", "订单编号")]),
    },
    "/activities": {"get": operation("活动", "进行中的活动", public=True)},
    "/activities/{id}": {
        "get": operation("活动", "活动详情", params=[path_param("id", "活动 ID")], public=True)
    },
    "/activities/{id}/flash-sale": {
        "post": operation(
            "秒杀",
            "抢购（异步建单，返回 ticket）",
            params=[path_param("id", "活动 ID")],
            request=body("FlashSaleIn"),
            status="202",
            schema="FlashSaleTicket",
        ),
    },
    "/flash-sale/requests": {"get": operation("秒杀", "我的抢购记录")},
    "/flash-sale/requests/{requestId}": {
        "get": operation(
            "秒杀",
            "查询抢购结果",
            params=[path_param("requestId", "抢购标识")],
            schema="FlashSaleTicket",
        )
    },
    "/admin/categories": {
        "get": operation("管理-类目", "全部类目", admin=True),
        "post": operation(
            "管理-类目", "新增类目", request=body("CategoryIn"), status="201", admin=True
        ),
    },
    "/admin/categories/{id}": {
        "patch": operation(
            "管理-类目",
            "修改或停用类目",
            params=[path_param("id", "类目 ID")],
            request=body("CategoryIn", required=False),
            admin=True,
        )
    },
    "/admin/products": {
        "get": operation("管理-商品", "商品列表（含下架）", admin=True),
        "post": operation(
            "管理-商品", "新增商品", request=body("ProductIn"), status="201", admin=True
        ),
    },
    "/admin/products/{id}": {
        "get": operation(
            "管理-商品", "商品详情（含下架 SKU）", params=[path_param("id", "商品 ID")], admin=True
        ),
        "patch": operation(
            "管理-商品",
            "修改商品信息",
            params=[path_param("id", "商品 ID")],
            request=body("ProductIn", required=False),
            admin=True,
        ),
    },
    "/admin/products/{id}/status": {
        "patch": operation(
            "管理-商品", "上架或下架", params=[path_param("id", "商品 ID")], admin=True
        )
    },
    "/admin/products/{id}/skus": {
        "get": operation(
            "管理-SKU", "查询 SKU 与库存", params=[path_param("id", "商品 ID")], admin=True
        ),
        "post": operation(
            "管理-SKU",
            "新增 SKU",
            params=[path_param("id", "商品 ID")],
            request=body("SkuIn"),
            status="201",
            admin=True,
        ),
    },
    "/admin/skus/{id}": {
        "patch": operation(
            "管理-SKU",
            "修改规格、价格或上下架",
            params=[path_param("id", "SKU ID")],
            request=body("SkuIn", required=False),
            admin=True,
        )
    },
    "/admin/skus/{id}/inventory": {
        "post": operation(
            "管理-库存",
            "入库",
            params=[path_param("id", "SKU ID")],
            request=body("InventoryIn"),
            admin=True,
        ),
        "put": operation(
            "管理-库存",
            "盘点调整到指定可售数量",
            params=[path_param("id", "SKU ID")],
            request=body("InventorySetIn"),
            admin=True,
        ),
    },
    "/admin/inventory": {"get": operation("管理-库存", "库存列表", admin=True)},
    "/admin/inventory/logs": {"get": operation("管理-库存", "库存变化流水", admin=True)},
    "/admin/orders": {"get": operation("管理-订单", "按状态或订单号查全部订单", admin=True)},
    "/admin/orders/{orderNo}": {
        "get": operation(
            "管理-订单",
            "订单详情",
            params=[path_param("orderNo", "订单编号")],
            schema="OrderDetail",
            admin=True,
        )
    },
    "/admin/fulfillments": {"get": operation("管理-履约", "履约单列表", admin=True)},
    "/admin/fulfillments/{fulfillmentNo}/prepare": {
        "post": operation(
            "管理-履约", "备货完成", params=[path_param("fulfillmentNo", "履约单号")], admin=True
        )
    },
    "/admin/fulfillments/{fulfillmentNo}/ship": {
        "post": operation(
            "管理-履约",
            "模拟发货，可指定失败",
            params=[path_param("fulfillmentNo", "履约单号")],
            request=body("ShipIn", required=False),
            admin=True,
        )
    },
    "/admin/jobs": {"get": operation("管理-任务", "后台任务列表", admin=True)},
    "/admin/jobs/{id}/retry": {
        "post": operation("管理-任务", "重新排队", params=[path_param("id", "任务 ID")], admin=True)
    },
    "/admin/jobs/run-once": {"post": operation("管理-任务", "立即执行待办任务", admin=True)},
    "/admin/overview": {"get": operation("管理-概览", "订单、履约、任务与低库存汇总", admin=True)},
    "/admin/activities": {
        "get": operation("管理-活动", "全部活动", admin=True),
        "post": operation(
            "管理-活动", "新建活动", request=body("ActivityIn"), status="201", admin=True
        ),
    },
    "/admin/activities/{id}": {
        "patch": operation(
            "管理-活动",
            "修改或停用活动",
            params=[path_param("id", "活动 ID")],
            request=body("ActivityIn", required=False),
            admin=True,
        )
    },
}

EXTRA_SCHEMAS = {
    "CategoryIn": {
        "type": "object",
        "required": ["name"],
        "properties": {"name": {"type": "string"}, "sortOrder": {"type": "integer"}},
    },
    "ProductIn": {
        "type": "object",
        "required": ["name", "categoryId"],
        "properties": {
            "name": {"type": "string"},
            "description": {"type": "string"},
            "categoryId": {"type": "integer"},
            "coverUrl": {"type": "string"},
        },
    },
    "SkuIn": {
        "type": "object",
        "required": ["price"],
        "properties": {
            "specs": {"type": "object", "additionalProperties": {"type": "string"}},
            "price": {"type": "string", "example": "39.00"},
            "skuCode": {"type": "string"},
            "stock": {"type": "integer", "minimum": 0},
            "status": {"type": "string", "enum": ["ON_SALE", "OFF_SALE"]},
        },
    },
    "InventoryIn": {
        "type": "object",
        "required": ["quantity"],
        "properties": {
            "quantity": {"type": "integer", "minimum": 1},
            "reason": {"type": "string"},
        },
    },
    "InventorySetIn": {
        "type": "object",
        "required": ["available"],
        "properties": {
            "available": {"type": "integer", "minimum": 0},
            "reason": {"type": "string"},
        },
    },
    "ActivityIn": {
        "type": "object",
        "required": ["name", "startsAt", "endsAt"],
        "properties": {
            "name": {"type": "string"},
            "type": {"type": "string", "enum": ["FIXED_PRICE", "FLASH_SALE"]},
            "status": {"type": "string", "enum": ["DRAFT", "ACTIVE", "DISABLED"]},
            "startsAt": {"type": "string", "example": "2026-11-08T00:00:00Z"},
            "endsAt": {"type": "string", "example": "2026-11-15T00:00:00Z"},
            "description": {"type": "string"},
            "skus": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "skuId": {"type": "integer"},
                        "activityPrice": {"type": "string", "example": "34.00"},
                        "saleQuota": {"type": "integer", "nullable": True},
                        "perUserLimit": {"type": "integer", "nullable": True},
                    },
                },
            },
        },
    },
}
SCHEMAS.update(EXTRA_SCHEMAS)


def main() -> None:
    document = {
        "openapi": "3.0.3",
        "info": {
            "title": "西二周边小店 API",
            "version": "1.0.0",
            "description": "第二至第四轮后端考核项目：用户、商品、购物车、订单、支付、活动、库存、履约与限量发售。",
        },
        "servers": [{"url": "http://127.0.0.1:8000", "description": "本机"}],
        "tags": [
            {"name": "认证"},
            {"name": "用户"},
            {"name": "地址"},
            {"name": "商品"},
            {"name": "购物车"},
            {"name": "订单"},
            {"name": "支付"},
            {"name": "活动"},
            {"name": "秒杀"},
            {"name": "履约"},
            {"name": "管理-类目"},
            {"name": "管理-商品"},
            {"name": "管理-SKU"},
            {"name": "管理-库存"},
            {"name": "管理-订单"},
            {"name": "管理-履约"},
            {"name": "管理-任务"},
            {"name": "管理-概览"},
            {"name": "管理-活动"},
        ],
        "paths": PATHS,
        "components": {
            "securitySchemes": {
                "bearerAuth": {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"}
            },
            "schemas": SCHEMAS,
        },
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(document, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"写入 {OUTPUT}（{len(PATHS)} 个路径）")


if __name__ == "__main__":
    main()
