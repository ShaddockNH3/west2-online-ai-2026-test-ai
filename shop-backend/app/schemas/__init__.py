"""请求模型按业务域拆分；统一导出，外部继续 `from app.schemas import X`。"""

from app.schemas.activity import ActivityIn, ActivityPatch, ActivitySkuIn, FlashSaleIn
from app.schemas.base import Json, StrictModel
from app.schemas.catalog import (
    CategoryIn,
    CategoryPatch,
    ProductIn,
    ProductPatch,
    ProductStatusIn,
    SkuIn,
    SkuPatch,
)
from app.schemas.ops import InventoryIn, InventorySetIn, JobRetryIn, ShipIn
from app.schemas.trade import CartAddIn, CartItemIdsIn, CartPatch, CreateOrderIn, PaymentIn
from app.schemas.user import (
    AddressIn,
    AddressPatch,
    ChangePasswordIn,
    LoginIn,
    RefreshIn,
    RegisterIn,
    UpdateMeIn,
)

__all__ = [
    "Json",
    "StrictModel",
    "RegisterIn",
    "LoginIn",
    "RefreshIn",
    "UpdateMeIn",
    "ChangePasswordIn",
    "AddressIn",
    "AddressPatch",
    "CategoryIn",
    "CategoryPatch",
    "ProductIn",
    "ProductPatch",
    "ProductStatusIn",
    "SkuIn",
    "SkuPatch",
    "CartAddIn",
    "CartPatch",
    "CartItemIdsIn",
    "CreateOrderIn",
    "PaymentIn",
    "ActivitySkuIn",
    "ActivityIn",
    "ActivityPatch",
    "FlashSaleIn",
    "InventoryIn",
    "InventorySetIn",
    "ShipIn",
    "JobRetryIn",
]
