"""验证 CS61A Scheme 项目（Project 4）的锁定测试。

原理与 verify_ok.py 相同：锁定答案是 hmac_md5(作业名, 期望输出)。
这里直接在自己的解释器里逐条求值，把结果格式化成 REPL 的输出，
再与官方哈希比对。
"""

from __future__ import annotations

import hmac
import io
import json
import re
import sys
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, "")

import scheme  # noqa: E402
from scheme_classes import SchemeError  # noqa: E402
from scheme_utils import repl_str  # noqa: E402


def lock(key: str, text: str) -> str:
    return hmac.new(key.encode(), text.encode(), digestmod="md5").hexdigest()


def prompts_of(code: str) -> list[tuple[str, list[str]]]:
    """把 case 代码拆成 (源码, 哈希列表)。

    多行表达式在测试里也是每行一个 `scm> `，所以要一直拼到哈希出现为止。
    """
    prompts: list[tuple[str, list[str]]] = []
    cur: list[str] = []
    hashes: list[str] = []

    def flush() -> None:
        nonlocal cur, hashes
        if cur:
            prompts.append(("\n".join(cur), hashes))
        cur, hashes = [], []

    for line in code.splitlines():
        stripped = line.strip()
        if stripped.startswith("scm> "):
            cur.append(stripped[5:])
        elif stripped.startswith("...."):
            cur.append(stripped[4:].strip())
        elif re.fullmatch(r"[0-9a-f]{32}", stripped):
            # 哈希标记着一个提示的结束
            prompts.append(("\n".join(cur), [stripped]))
            cur = []
            hashes = []
    flush()
    return prompts


def run_prompt(source: str, env) -> str:
    """在 env 中求值一行，返回 REPL 会打印的内容。"""
    buffer = io.StringIO()
    try:
        with redirect_stdout(buffer):
            value = scheme.scheme_eval(scheme.read_line(source), env)
        printed = buffer.getvalue()
        if value is not None:
            printed += repl_str(value) + "\n"
        return printed.rstrip("\n")
    except SchemeError as error:
        return f"Error: {error}"
    except Exception as error:  # noqa: BLE001
        return f"Error: {type(error).__name__}: {error}"


def verify(assignment_dir: Path) -> tuple[int, int, list[tuple]]:
    ok_file = next(assignment_dir.glob("*.ok"))
    key = json.loads(ok_file.read_text())["name"]
    total = passed = 0
    failures: list[tuple] = []

    for test_file in sorted((assignment_dir / "tests").glob("*.py")):
        if test_file.name == "__init__.py":
            continue
        namespace: dict = {}
        exec(test_file.read_text(), namespace)
        test = namespace.get("test")
        if not test:
            continue
        for suite in test.get("suites", []):
            if suite.get("type") != "scheme":
                continue
            setup_prompts = prompts_of(suite.get("setup", "") or "")
            for case_index, case in enumerate(suite.get("cases", [])):
                env = scheme.create_global_frame()
                for source, _hashes in setup_prompts:
                    run_prompt(source, env)
                for source, hashes in prompts_of(case.get("code", "")):
                    answer = run_prompt(source, env)
                    if not hashes:
                        continue
                    total += 1
                    expected = hashes[0]
                    candidates = [answer]
                    if answer.startswith("Error:"):
                        candidates += ["SchemeError", "Error"]
                    if any(lock(key, c) == expected for c in candidates):
                        passed += 1
                    else:
                        failures.append((f'{test["name"]}#case{case_index}', source, answer, expected))
    return total, passed, failures


if __name__ == "__main__":
    directory = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    total, passed, failures = verify(directory.resolve())
    print(f"===== scheme: {passed}/{total} =====")
    for name, source, answer, expected in failures[:15]:
        print(f"[不一致] {name}\n  代码: {source!r}\n  输出: {answer!r}\n  哈希: {expected}")
    if len(failures) > 15:
        print(f"... 其余 {len(failures) - 15} 条")
