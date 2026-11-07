"""组合根：所有实现类在这里被 new 出来，并绑到各自的接口/服务类型上。

应用服务只认 Protocol 和彼此的类型，不认 SQLAlchemy、Redis 或 BlackSheep。
换掉任何一个适配器，只需要改这个文件。
"""

from __future__ import annotations

from dataclasses import dataclass

from app.application.ports.uow import UowFactory
from app.application.services.activities import ActivityService
from app.application.services.addresses import AddressService
from app.application.services.auth import AuthService, PrincipalService
from app.application.services.cart import CartService
from app.application.services.catalog import CatalogService
from app.application.services.flashsale import FlashSaleService
from app.application.services.fulfillment import FulfillmentService
from app.application.services.inventory import InventoryService
from app.application.services.jobs import InventoryReader, JobService, OverviewService
from app.application.services.orders import OrderService
from app.application.services.payments import PaymentService
from app.core.config import Settings
from app.core.db import db
from app.infrastructure.cache.redis import RedisCache
from app.infrastructure.clock import SystemClock
from app.infrastructure.logistics.client import MockLogistics
from app.infrastructure.payment.mock import MockPaymentGateway
from app.infrastructure.persistence.uow import make_uow_factory


@dataclass(slots=True)
class Container:
    settings: Settings
    uow_factory: UowFactory
    cache: RedisCache
    auth: AuthService
    principal: PrincipalService
    addresses: AddressService
    catalog: CatalogService
    cart: CartService
    orders: OrderService
    payments: PaymentService
    inventory: InventoryService
    activities: ActivityService
    flash_sales: FlashSaleService
    fulfillments: FulfillmentService
    jobs: JobService
    overview: OverviewService


def build_container(settings: Settings) -> Container:
    if db.session_factory is None:
        raise RuntimeError("数据库尚未初始化，请先调用 db.configure()")

    uow = make_uow_factory(db.session_factory)
    clock = SystemClock()
    cache = RedisCache()
    gateway = MockPaymentGateway()
    logistics = MockLogistics()

    orders = OrderService(uow, clock)
    inventory_reader = InventoryReader(uow)

    return Container(
        settings=settings,
        uow_factory=uow,
        cache=cache,
        auth=AuthService(uow, clock),
        principal=PrincipalService(uow, clock),
        addresses=AddressService(uow),
        catalog=CatalogService(uow, clock, cache),
        cart=CartService(uow, clock),
        orders=orders,
        payments=PaymentService(uow, clock, gateway),
        inventory=InventoryService(uow, cache),
        activities=ActivityService(uow, clock, cache),
        flash_sales=FlashSaleService(uow, clock, orders),
        fulfillments=FulfillmentService(uow, clock, logistics),
        jobs=JobService(uow),
        overview=OverviewService(uow, inventory_reader),
    )
