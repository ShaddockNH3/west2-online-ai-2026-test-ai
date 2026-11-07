"""把各域的路由聚到一起。main.py 只负责调用，不再逐个 import。"""

from __future__ import annotations

from blacksheep.server.routing import Router

from app.api.routes import (
    activities,
    addresses,
    admin,
    auth,
    cart,
    catalog,
    flashsale,
    orders,
    users,
)

MODULES = (
    auth,
    users,
    addresses,
    catalog,
    cart,
    orders,
    activities,
    flashsale,
    admin,
)


def register_routes(router: Router) -> None:
    for module in MODULES:
        module.register(router)
