"""模型按业务域拆分；统一在这里导出，外部继续 `from app.models import X`。"""

from app.infrastructure.persistence.models.activity import Activity, ActivitySku, FlashSaleRequest
from app.infrastructure.persistence.models.base import Base, TimestampMixin
from app.infrastructure.persistence.models.catalog import Category, Product, Sku
from app.infrastructure.persistence.models.fulfillment import Fulfillment
from app.infrastructure.persistence.models.ops import Job
from app.infrastructure.persistence.models.trade import CartItem, Order, OrderItem, Payment
from app.infrastructure.persistence.models.user import Address, AuthSession, User
from app.infrastructure.persistence.models.warehouse import Inventory, InventoryLog, Warehouse

__all__ = [
    "Base",
    "TimestampMixin",
    "User",
    "AuthSession",
    "Address",
    "Category",
    "Product",
    "Sku",
    "CartItem",
    "Order",
    "OrderItem",
    "Payment",
    "Activity",
    "ActivitySku",
    "FlashSaleRequest",
    "Warehouse",
    "Inventory",
    "InventoryLog",
    "Fulfillment",
    "Job",
]
