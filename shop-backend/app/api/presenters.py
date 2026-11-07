"""实体/读模型 → JSON。所有 camelCase 字段名只在这一层出现。"""

from __future__ import annotations

from app.application.read_models import (
    ActivityDetail,
    CartLine,
    CartView,
    OrderPreview,
    Overview,
    ProductCard,
    ProductDetail,
    SkuCard,
)
from app.domain.entities import (
    Activity,
    Address,
    AdminOrderRow,
    Category,
    FlashSaleRequest,
    Fulfillment,
    InventoryLogEntry,
    InventoryRecord,
    InventoryRow,
    Job,
    Order,
    OrderLine,
    Payment,
    Product,
    Sku,
    User,
)
from app.domain.money import iso, yuan


def user(item: User) -> dict:
    return {
        "id": item.id,
        "username": item.username,
        "nickname": item.nickname,
        "email": item.email,
        "phone": item.phone,
        "role": item.role,
        "createdAt": iso(item.created_at),
        "updatedAt": iso(item.updated_at),
    }


def address(item: Address) -> dict:
    return {
        "id": item.id,
        "receiver": item.receiver,
        "phone": item.phone,
        "detail": item.detail,
        "isDefault": item.is_default,
        "createdAt": iso(item.created_at),
        "updatedAt": iso(item.updated_at),
    }


def category(item: Category) -> dict:
    return {
        "id": item.id,
        "name": item.name,
        "sortOrder": item.sort_order,
        "status": item.status,
        "createdAt": iso(item.created_at),
    }


def product_brief(item: Product) -> dict:
    return {
        "id": item.id,
        "name": item.name,
        "description": item.description,
        "coverUrl": item.cover_url,
        "status": item.status,
        "categoryId": item.category_id,
    }


def sku_brief(item: Sku, *, stock: int | None = None) -> dict:
    data = {
        "id": item.id,
        "code": item.sku_code,
        "specs": item.specs,
        "price": yuan(item.price_cents),
        "status": item.status,
    }
    if stock is not None:
        data["stock"] = stock
    return data


def product_card(item: ProductCard) -> dict:
    return {
        "id": item.id,
        "name": item.name,
        "coverUrl": item.cover_url,
        "categoryId": item.category_id,
        "categoryName": item.category_name,
        "minPrice": yuan(item.min_price_cents) if item.min_price_cents is not None else None,
        "maxPrice": yuan(item.max_price_cents) if item.max_price_cents is not None else None,
        "hasActivity": item.has_activity,
        "stockAvailable": item.stock_available,
        "createdAt": iso(item.created_at),
    }


def sku_card(item: SkuCard) -> dict:
    return {
        "id": item.id,
        "code": item.code,
        "specs": item.specs,
        "price": yuan(item.price_cents),
        "originalPrice": yuan(item.original_cents),
        "activityName": item.activity_name or None,
        "status": item.status,
        "availableStock": item.available_stock,
        "purchasable": item.purchasable,
    }


def product_detail(item: ProductDetail) -> dict:
    return {
        "id": item.id,
        "name": item.name,
        "description": item.description,
        "coverUrl": item.cover_url,
        "status": item.status,
        "category": category(item.category) if item.category else None,
        "skus": [sku_card(sku) for sku in item.skus],
        "createdAt": iso(item.created_at),
        "updatedAt": iso(item.updated_at),
    }


def cart_line(item: CartLine) -> dict:
    return {
        "id": item.id,
        "skuId": item.sku_id,
        "productId": item.product_id,
        "productName": item.product_name,
        "specs": item.specs,
        "price": yuan(item.price_cents),
        "originalPrice": yuan(item.original_cents),
        "activityName": item.activity_name or None,
        "quantity": item.quantity,
        "subtotal": yuan(item.subtotal_cents),
        "availableStock": item.available_stock,
        "purchasable": item.purchasable,
        "reason": item.reason or None,
    }


def cart_view(item: CartView) -> dict:
    return {
        "items": [cart_line(line) for line in item.items],
        "totalQuantity": item.total_quantity,
        "totalAmount": yuan(item.total_amount_cents),
    }


def order_preview(item: OrderPreview) -> dict:
    return {
        "items": [
            {
                "skuId": line.sku_id,
                "productId": line.product_id,
                "productName": line.product_name,
                "specs": line.specs,
                "quantity": line.quantity,
                "unitPrice": yuan(line.unit_price_cents),
                "originalUnitPrice": yuan(line.original_unit_price_cents),
                "subtotal": yuan(line.subtotal_cents),
                "discount": yuan(line.discount_cents),
                "activityName": line.activity_name or None,
                "purchasable": line.purchasable,
                "issue": line.issue or None,
            }
            for line in item.items
        ],
        "originalAmount": yuan(item.original_amount_cents),
        "discountAmount": yuan(item.discount_amount_cents),
        "totalAmount": yuan(item.total_amount_cents),
        "issues": [{"productName": name, "reason": reason} for name, reason in item.issues],
        "address": {
            "id": item.address.id,
            "receiver": item.address.receiver,
            "phone": item.address.phone,
            "detail": item.address.detail,
        },
        "priceLocked": False,
        "note": item.note,
    }


def order_summary(item: Order, item_count: int = 0) -> dict:
    return {
        "orderNo": item.order_no,
        "status": item.status,
        "totalAmount": yuan(item.total_amount_cents),
        "originalAmount": yuan(item.original_amount_cents),
        "discountAmount": yuan(item.discount_amount_cents),
        "itemCount": item_count,
        "createdAt": iso(item.created_at),
        "paidAt": iso(item.paid_at),
        "expireAt": iso(item.expire_at),
        "receiver": item.receiver,
    }


def admin_order_row(row: AdminOrderRow, item_count: int) -> dict:
    return {**order_summary(row.order, item_count), "username": row.username}


def order_detail(item) -> dict:
    order = item.order
    return {
        "orderNo": order.order_no,
        "status": order.status,
        "originalAmount": yuan(order.original_amount_cents),
        "discountAmount": yuan(order.discount_amount_cents),
        "totalAmount": yuan(order.total_amount_cents),
        "receiver": order.receiver,
        "phone": order.phone,
        "addressDetail": order.address_detail,
        "remark": order.remark,
        "createdAt": iso(order.created_at),
        "paidAt": iso(order.paid_at),
        "shippedAt": iso(order.shipped_at),
        "completedAt": iso(order.completed_at),
        "cancelledAt": iso(order.cancelled_at),
        "cancelReason": order.cancel_reason or None,
        "expireAt": iso(order.expire_at),
        "items": [order_item(line) for line in item.lines],
        "payments": [payment(row) for row in item.payments],
        "fulfillment": fulfillment_brief(item.fulfillment) if item.fulfillment else None,
    }


def order_item(item: OrderLine) -> dict:
    return {
        "productName": item.product_name,
        "skuId": item.sku_id,
        "specs": item.specs,
        "quantity": item.quantity,
        "unitPrice": yuan(item.unit_price_cents),
        "originalUnitPrice": yuan(item.original_unit_price_cents),
        "subtotal": yuan(item.subtotal_cents),
        "discount": yuan(item.discount_cents),
        "activityName": item.activity_name or None,
    }


def payment(item: Payment) -> dict:
    return {
        "paymentNo": item.payment_no,
        "amount": yuan(item.amount_cents),
        "status": item.status,
        "channel": item.channel,
        "transactionNo": item.transaction_no or None,
        "failureReason": item.failure_reason or None,
        "createdAt": iso(item.created_at),
        "paidAt": iso(item.paid_at),
    }


def payment_with_order(item: Payment) -> dict:
    return {**payment(item), "orderNo": item.order_no}


def fulfillment(item: Fulfillment) -> dict:
    return {
        "fulfillmentNo": item.fulfillment_no,
        "orderNo": item.order_no,
        "status": item.status,
        "receiver": item.receiver,
        "phone": item.phone,
        "addressDetail": item.address_detail,
        "items": item.items,
        "trackingNo": item.tracking_no or None,
        "attempts": item.attempts,
        "lastError": item.last_error or None,
        "shippedAt": iso(item.shipped_at),
        "completedAt": iso(item.completed_at),
        "createdAt": iso(item.created_at),
        "updatedAt": iso(item.updated_at),
    }


def fulfillment_brief(item: Fulfillment) -> dict:
    return {
        "fulfillmentNo": item.fulfillment_no,
        "status": item.status,
        "trackingNo": item.tracking_no or None,
        "attempts": item.attempts,
        "lastError": item.last_error or None,
        "shippedAt": iso(item.shipped_at),
        "completedAt": iso(item.completed_at),
    }


def flash_request(item: FlashSaleRequest) -> dict:
    return {
        "requestId": item.request_id,
        "activityId": item.activity_id,
        "activityName": item.activity_name,
        "skuId": item.sku_id,
        "quantity": item.quantity,
        "unitPrice": yuan(item.unit_price_cents),
        "status": item.status,
        "orderNo": item.order_no,
        "message": item.message or None,
        "createdAt": iso(item.created_at),
        "updatedAt": iso(item.updated_at),
    }


def activity_item(item: Activity) -> dict:
    return {
        "id": item.id,
        "name": item.name,
        "type": item.type,
        "status": item.status,
        "description": item.description,
        "startsAt": iso(item.starts_at),
        "endsAt": iso(item.ends_at),
    }


def activity_detail(item: ActivityDetail) -> dict:
    return {
        **activity_item(item.activity),
        "running": item.running,
        "skus": [
            {
                "skuId": sku.sku_id,
                "skuCode": sku.sku_code,
                "originalPrice": yuan(sku.original_cents),
                "activityPrice": yuan(sku.activity_cents),
                "saleQuota": sku.sale_quota,
                "soldCount": sku.sold_count,
                "perUserLimit": sku.per_user_limit,
            }
            for sku in item.skus
        ],
    }


def inventory_record(item: InventoryRecord, sku_code: str | None = None) -> dict:
    return {
        "skuId": item.sku_id,
        "skuCode": sku_code,
        "warehouseId": item.warehouse_id,
        "available": item.available,
        "reserved": item.reserved,
        "sold": item.sold,
        "updatedAt": iso(item.updated_at),
    }


def inventory_log(item: InventoryLogEntry) -> dict:
    return {
        "id": item.id,
        "skuId": item.sku_id,
        "orderNo": item.order_no,
        "changeType": item.change_type,
        "quantity": item.quantity,
        "availableBefore": item.available_before,
        "availableAfter": item.available_after,
        "reason": item.reason,
        "createdAt": iso(item.created_at),
    }


def inventory_row(item: InventoryRow) -> dict:
    return {
        **inventory_record(item.inventory, item.sku_code),
        "productId": item.product_id,
        "productName": item.product_name,
        "specs": item.sku_specs,
        "skuStatus": item.sku_status,
        "productStatus": item.product_status,
    }


def job(item: Job) -> dict:
    return {
        "id": item.id,
        "type": item.job_type,
        "status": item.status,
        "attempts": item.attempts,
        "maxAttempts": item.max_attempts,
        "nextRunAt": iso(item.next_run_at),
        "lastError": item.last_error or None,
        "payload": item.payload,
        "createdAt": iso(item.created_at),
        "updatedAt": iso(item.updated_at),
    }


def overview(item: Overview) -> dict:
    return {
        "ordersByStatus": item.orders_by_status,
        "paidAmount": yuan(item.paid_amount_cents),
        "pendingFulfillments": item.pending_fulfillments,
        "pendingJobs": item.pending_jobs,
        "failedJobs": item.failed_jobs,
        "lowStockSkus": [inventory_row(row) for row in item.low_stock],
    }
