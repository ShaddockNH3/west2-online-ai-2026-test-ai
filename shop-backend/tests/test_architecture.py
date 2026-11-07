"""架构约束：分层不能倒着依赖。

这几条断言比目录结构更能说明问题——它们会在有人图省事
「在 domain 里查一下数据库」时立刻失败。
"""

from __future__ import annotations

import ast
import pathlib

APP = pathlib.Path(__file__).resolve().parent.parent / "app"

FRAMEWORKS = ("sqlalchemy", "blacksheep", "redis", "pydantic")
OUTER_LAYERS = ("app.api", "app.infrastructure", "app.container", "app.worker")


def imports_of(path: pathlib.Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


def layer_files(layer: str) -> list[pathlib.Path]:
    return sorted((APP / layer).rglob("*.py"))


def assert_no_import(layer: str, forbidden: tuple[str, ...]) -> None:
    violations = []
    for path in layer_files(layer):
        for name in imports_of(path):
            if name.startswith(forbidden):
                violations.append(f"{path.relative_to(APP.parent)} -> {name}")
    assert not violations, "分层被打破：\n" + "\n".join(violations)


def test_domain_is_pure() -> None:
    """领域层只有标准库和同层模块。"""
    assert_no_import("domain", FRAMEWORKS + OUTER_LAYERS + ("app.core", "app.application"))


def test_application_does_not_touch_infrastructure() -> None:
    """应用层只认端口，不能直接 import 仓储实现、缓存实现或框架。"""
    assert_no_import("application", FRAMEWORKS + ("app.api", "app.infrastructure"))


def test_infrastructure_does_not_depend_on_api() -> None:
    assert_no_import("infrastructure", ("app.api", "app.container"))


def test_container_is_the_only_composition_root() -> None:
    """除了 container 和 main，别处不该出现「new 一个具体适配器」。"""
    offenders = []
    for path in (APP / "api").rglob("*.py"):
        for name in imports_of(path):
            if name.startswith("app.infrastructure"):
                offenders.append(f"{path.relative_to(APP.parent)} -> {name}")
    assert not offenders, "接口层直接依赖了基础设施：\n" + "\n".join(offenders)
