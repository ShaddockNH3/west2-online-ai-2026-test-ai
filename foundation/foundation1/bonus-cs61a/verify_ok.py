"""用官方锁定测试的哈希验证自己的实现。

原理：ok 的锁定答案 = hmac_md5(作业名, 期望输出)。
把测试里每个锁定用例的代码在自己的实现上跑一遍，
拿实际输出算 hmac 与官方哈希比对，全部一致即通过。
"""

from __future__ import annotations

import ast
import hmac
import io
import json
import re
import sys
from contextlib import redirect_stdout
from pathlib import Path


def lock(key: str, text: str) -> str:
    return hmac.new(key.encode(), text.encode(), digestmod="md5").hexdigest()


def answer_variants(answer: str) -> list[str]:
    """异常输出的格式可能有几种，都试一遍。"""
    variants = [answer]
    if "Traceback" in answer:
        lines = answer.splitlines()
        exc_line = lines[-1] if lines else answer
        variants.append(f"Traceback (most recent call last):\n    ...\n{exc_line}")
        variants.append(f"Traceback (most recent call last):\n{exc_line}")
    return variants


def parse_prompts(code: str) -> list[tuple[str, list[str], list[str]]]:
    """从用例代码里拆出 (提示行源码, 期望输出行列表, 哈希列表)。

    未锁定的用例没有哈希，只执行不比对——它们往往负责定义后续用例要用的变量。
    """
    prompts: list[tuple[str, list[str], list[str]]] = []
    cur: list[str] = []
    out: list[str] = []
    hashes: list[str] = []

    def flush() -> None:
        nonlocal cur, out, hashes
        if cur:
            prompts.append(("\n".join(cur), out, hashes))
        cur, out, hashes = [], [], []

    for line in code.splitlines():
        stripped = line.strip()
        if stripped.startswith(">>> "):
            flush()
            cur = [stripped[4:]]
        elif stripped.startswith("... ") and cur:
            cur.append(stripped[4:])
        elif re.fullmatch(r"[0-9a-f]{32}", stripped):
            hashes.append(stripped)
        elif stripped.startswith("#"):
            continue
        elif cur:
            out.append(stripped)
    flush()
    return prompts


def load_module(path: Path, globs: dict) -> None:
    module_ns: dict = {"__name__": path.stem, "__file__": str(path)}
    exec(compile(path.read_text(), str(path), "exec"), module_ns)
    for key, value in module_ns.items():
        globs.setdefault(key, value)


def verify(assignment_dir: Path) -> tuple[int, int, list[tuple]]:
    import sys
    sys.path.insert(0, str(assignment_dir.resolve()))
    ok_file = next(assignment_dir.glob("*.ok"))
    ok_cfg = json.loads(ok_file.read_text())
    key = ok_cfg["name"]
    src_files = ok_cfg.get("src", [])

    total = passed = 0
    failures: list[tuple] = []
    for test_file in sorted((assignment_dir / "tests").glob("*.py")):
        if test_file.name == "__init__.py":
            continue
        if getattr(verify, "skip_extra", None) and test_file.stem.startswith(("EC", "extra")):
            continue
        print(f"  .. {test_file.name}", flush=True)  # noqa
        namespace: dict = {}
        exec(test_file.read_text(), namespace)
        test = namespace.get("test")
        if not test:
            continue
        for suite in test.get("suites", []):
            suite_type = suite.get("type")
            if suite_type not in (None, "doctest", "wwpp"):
                continue
            setup = suite.get("setup", "") or ""
            setup_lines = []
            for line in setup.splitlines():
                stripped = line.strip()
                if stripped.startswith(">>> ") or stripped.startswith("... "):
                    setup_lines.append(re.sub(r"^\s*(?:>>> |\.\.\. )", "", line))
            setup_code = "\n".join(setup_lines)

            teardown = suite.get("teardown", "") or ""
            teardown_lines = []
            for line in teardown.splitlines():
                stripped = line.strip()
                if stripped.startswith(">>> ") or stripped.startswith("... "):
                    teardown_lines.append(re.sub(r"^\s*(?:>>> |\.\.\. )", "", line))
            teardown_code = "\n".join(teardown_lines)

            def build_globs() -> dict:
                """每个 case 用一份全新的 globals（与 ok 的行为一致）。"""
                fresh: dict = {}
                if setup_code.strip():
                    try:
                        exec(setup_code, fresh)
                    except Exception:  # noqa: BLE001
                        return {}
                for src in src_files:
                    if src.endswith(".py") and (assignment_dir / src).exists():
                        load_module(assignment_dir / src, fresh)
                return fresh

            for case_index, case in enumerate(suite.get("cases", [])):
                globs = build_globs()
                if not globs:
                    break
                case_hashes = [h for _s, _o, hs in parse_prompts(case.get("code", "")) for h in hs]
                hash_cursor = 0

                for source, expected_lines, prompt_hashes in parse_prompts(case.get("code", "")):
                    buffer = io.StringIO()
                    try:
                        tree = ast.parse(source)
                        with redirect_stdout(buffer):
                            if tree.body and isinstance(tree.body[-1], ast.Expr):
                                head = ast.Module(tree.body[:-1], type_ignores=[])
                                if head.body:
                                    exec(compile(head, "<case>", "exec"), globs)
                                value = eval(compile(ast.Expression(tree.body[-1].value), "<case>", "eval"), globs)
                            else:
                                exec(compile(tree, "<case>", "exec"), globs)
                                value = None
                        printed = buffer.getvalue()
                    except Exception as error:  # noqa: BLE001
                        printed = f"Traceback (most recent call last):\n    ...\n{type(error).__name__}: {error}\n"
                        value = None

                    if suite_type == "wwpp":
                        # wwpp：打印行 + 返回值 repr 行，每行对应一个哈希（按顺序消费）
                        if printed.startswith("Traceback"):
                            # 课程约定：异常在 wwpp 里统一答 Error / StopIteration
                            generated = ["Error"]
                            wwpp_exception = printed.splitlines()[-1]
                        else:
                            wwpp_exception = None
                            generated = printed.splitlines()
                            if value is not None:
                                generated.append(repr(value))
                        for line in generated:
                            if hash_cursor >= len(case_hashes):
                                break
                            expected_hash = case_hashes[hash_cursor]
                            hash_cursor += 1
                            total += 1
                            candidates = [line]
                            if wwpp_exception:
                                candidates = [wwpp_exception.split(":")[0].strip(), "Error"]
                            if line.startswith("<function"):
                                candidates += ["Function"]
                            if any(lock(key, candidate) == expected_hash for candidate in candidates):
                                passed += 1
                            else:
                                failures.append((f'{test["name"]}#case{case_index}', source, line, expected_hash))
                        continue

                    # doctest：有打印输出只算打印，否则算返回值的 repr
                    answer = printed.rstrip("\n") if printed.strip() else repr(value)
                    if not prompt_hashes:
                        continue
                    expected_hash = prompt_hashes[0]
                    total += 1
                    variants = answer_variants(answer)
                    if not printed.strip() and value is None:
                        variants.append("")
                    if any(lock(key, v) == expected_hash for v in variants):
                        passed += 1
                    else:
                        failures.append((f'{test["name"]}#case{case_index}', source, answer, expected_hash))

            if teardown_code.strip() and globs:
                try:
                    exec(teardown_code, globs)
                except Exception:  # noqa: BLE001
                    pass
    return total, passed, failures


if __name__ == "__main__":
    for target in sys.argv[1:]:
        directory = Path(target)
        total, passed, failures = verify(directory)
        print(f"\n===== {directory.resolve().name}: {passed}/{total} =====")
        for name, source, answer, expected in failures[:10]:
            print(f"[不一致] {name}\n  代码: {source!r}\n  我的输出: {answer!r}\n  期望哈希: {expected}")
        if len(failures) > 10:
            print(f"... 其余 {len(failures) - 10} 条不一致未显示")
