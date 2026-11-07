"""领域常量：状态、角色、任务类型。模型里统一存字符串，便于 SQL 排查。"""

from __future__ import annotations


class Role:
    USER = "USER"
    ADMIN = "ADMIN"


class UserStatus:
    ACTIVE = "ACTIVE"
    DISABLED = "DISABLED"


class ProductStatus:
    ON_SALE = "ON_SALE"
    OFF_SALE = "OFF_SALE"


class CategoryStatus:
    ENABLED = "ENABLED"
    DISABLED = "DISABLED"


class OrderStatus:
    PENDING_PAYMENT = "PENDING_PAYMENT"
    PAID = "PAID"
    SHIPPED = "SHIPPED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

    # 只有待支付订单允许取消/支付
    UNPAID = (PENDING_PAYMENT,)
    # 已付款但还能继续流转的状态
    PAID_STATES = (PAID, SHIPPED)


class PaymentStatus:
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class ActivityType:
    FIXED_PRICE = "FIXED_PRICE"
    FLASH_SALE = "FLASH_SALE"


class ActivityStatus:
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    DISABLED = "DISABLED"


class FulfillmentStatus:
    PENDING = "PENDING"  # 待备货
    READY_TO_SHIP = "READY_TO_SHIP"  # 备货完成，待发货
    SHIPPED = "SHIPPED"
    COMPLETED = "COMPLETED"
    EXCEPTION = "EXCEPTION"


class JobStatus:
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"


class JobType:
    CLOSE_EXPIRED_ORDER = "CLOSE_EXPIRED_ORDER"
    BUILD_FULFILLMENT = "BUILD_FULFILLMENT"
    SEND_ORDER_NOTIFICATION = "SEND_ORDER_NOTIFICATION"
    CREATE_FLASH_ORDER = "CREATE_FLASH_ORDER"
    RELEASE_FLASH_RESERVATION = "RELEASE_FLASH_RESERVATION"


class InventoryChange:
    INBOUND = "INBOUND"
    ADJUST = "ADJUST"
    RESERVE = "RESERVE"
    RELEASE = "RELEASE"
    DEDUCT = "DEDUCT"


class FlashSaleStatus:
    QUEUED = "QUEUED"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    REJECTED = "REJECTED"


DEFAULT_WAREHOUSE_ID = 1
