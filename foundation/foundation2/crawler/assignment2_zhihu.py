"""作业 2：用操控浏览器的方式爬知乎话题「机器学习」的高赞回答。

知乎对 requests 这类「裸请求」非常敏感：没有 cookie、没有浏览器指纹、
没有正常的 TLS 握手顺序，几乎必然被弹到登录墙或者直接 403。所以这里用
Playwright 驱动真实 Chrome —— 它本来就是个浏览器，反爬要判断的那些特征它都有。

登录态的处理：
    python assignment2_zhihu.py --login     # 弹出有头浏览器，扫码登录后自动保存 cookie
    python assignment2_zhihu.py             # 复用 data/zhihu_state.json 里的登录态抓取

cookie 是等同于账号密码的东西，所以：
  1. 只存在本地 data/ 目录，不进 git（见 .gitignore）；
  2. 用 Playwright 的 storage_state 格式（含 localStorage），不是明文复制粘贴；
  3. 换机器/换项目时记得手动删掉。
泄露 cookie 的后果可以看题目里那篇「学生误泄 Gemini API 密钥背上巨额账单」——
钥匙丢了，账单是你的。

用法：
    python assignment2_zhihu.py --questions 20 --answers 10
"""

from __future__ import annotations

import argparse
import csv
import random
import re
import sys
import time
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import clean_text  # noqa: E402

DATA_DIR = Path(__file__).resolve().parent / "data"
STATE_PATH = DATA_DIR / "zhihu_state.json"
CSV_PATH = DATA_DIR / "zhihu_topic_answers.csv"

TOPIC_URL = "https://www.zhihu.com/topic/19554298/top-answers"  # 机器学习
QUESTION_LINK_RE = re.compile(r"/question/(\d+)")

CSV_COLUMNS = ["问题名", "问题内容", "回答信息", "问题链接", "回答序号"]


def build_context(playwright: Any, state_path: Path | None = None) -> tuple[Any, Any]:
    """启动本机 Chrome（不下载 Playwright 自带的 chromium）。"""
    browser = playwright.chromium.launch(
        channel="chrome",
        headless=False,
        args=["--disable-blink-features=AutomationControlled"],
    )
    context = browser.new_context(
        viewport={"width": 1440, "height": 900},
        locale="zh-CN",
        storage_state=str(state_path) if state_path and state_path.exists() else None,
        user_agent=(
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
        ),
    )
    # 抹掉最明显的自动化标记
    context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return browser, context


def login() -> None:
    """扫码登录，把 storage_state 存下来复用。"""
    from playwright.sync_api import sync_playwright

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser, context = build_context(playwright)
        page = context.new_page()
        page.goto("https://www.zhihu.com/signin", wait_until="domcontentloaded")
        print("浏览器已打开，请扫码登录。登录成功后本脚本会自动保存 cookie……")

        deadline = time.time() + 300
        while time.time() < deadline:
            cookies = {item["name"]: item["value"] for item in context.cookies()}
            if cookies.get("z_c0"):
                context.storage_state(path=str(STATE_PATH))
                print(f"登录成功，cookie 已保存到 {STATE_PATH}")
                break
            time.sleep(2)
        else:
            print("5 分钟内没有检测到登录，未保存。")
        browser.close()


def has_login(state_path: Path) -> bool:
    import json

    if not state_path.exists():
        return False
    state = json.loads(state_path.read_text(encoding="utf-8"))
    return any(cookie.get("name") == "z_c0" for cookie in state.get("cookies", []))


def scroll_until(page: Any, target: int, selector: str, max_rounds: int = 12) -> int:
    """边滚边数，直到收集到 target 个候选元素。"""
    seen = 0
    for _ in range(max_rounds):
        seen = len(page.query_selector_all(selector))
        if seen >= target:
            break
        page.mouse.wheel(0, 2200)
        time.sleep(random.uniform(1.2, 2.0))
    return seen


def collect_question_links(page: Any, want: int) -> list[str]:
    """从话题页收集问题链接（去重，保序）。"""
    page.goto(TOPIC_URL, wait_until="domcontentloaded", timeout=60000)
    time.sleep(random.uniform(2.0, 3.5))

    # 登录墙判断：出现「登录/注册」弹窗且没有内容
    if page.query_selector(".Modal-wrapper") and not page.query_selector(".ContentItem"):
        raise RuntimeError("被登录墙拦住了，先用 --login 登录并把 cookie 保存下来。")

    scroll_until(page, want * 2, ".ContentItem", max_rounds=10)
    links: list[str] = []
    for anchor in page.query_selector_all('a[href*="/question/"]'):
        href = anchor.get_attribute("href") or ""
        match = QUESTION_LINK_RE.search(href)
        if not match:
            continue
        url = f"https://www.zhihu.com/question/{match.group(1)}"
        if url not in links:
            links.append(url)
        if len(links) >= want:
            break
    return links


def expand_answers(page: Any) -> None:
    """点掉「阅读全文」，否则长回答只拿到前几行。"""
    for button in page.query_selector_all(".ContentItem-expandButton, button:has-text('阅读全文')"):
        try:
            button.click(timeout=800)
            time.sleep(0.2)
        except Exception:  # noqa: BLE001
            continue


def extract_question(page: Any, url: str, want_answers: int) -> list[dict[str, str]]:
    """打开一个问题，抽出标题、问题描述和前 N 个回答的纯文本。"""
    page.goto(url, wait_until="domcontentloaded", timeout=60000)
    time.sleep(random.uniform(1.8, 3.0))

    title_node = page.query_selector("h1.QuestionHeader-title") or page.query_selector("h1")
    title = clean_text(title_node.inner_text()) if title_node else ""

    desc_node = page.query_selector(".QuestionRichText") or page.query_selector(
        ".QuestionHeader-detail"
    )
    description = clean_text(desc_node.inner_text()) if desc_node else ""

    scroll_until(page, want_answers, ".AnswerItem, .ContentItem", max_rounds=8)
    expand_answers(page)

    answers: list[str] = []
    for item in page.query_selector_all(".AnswerItem, .ContentItem"):
        node = item.query_selector(".RichText") or item.query_selector(".RichContent-inner")
        if node is None:
            continue
        text = clean_text(node.inner_text(), drop_brackets=False)
        if len(text) < 20:  # 折叠的、广告位的、空壳的都跳过
            continue
        answers.append(text)
        if len(answers) >= want_answers:
            break

    return [
        {
            "问题名": title,
            "问题内容": description,
            "回答信息": answer,
            "问题链接": url,
            "回答序号": str(index + 1),
        }
        for index, answer in enumerate(answers)
    ]


def crawl(question_count: int, answer_count: int) -> None:
    from playwright.sync_api import sync_playwright

    if not has_login(STATE_PATH):
        raise SystemExit(
            "没有可用的登录态。先运行：\n"
            "    python assignment2_zhihu.py --login\n"
            "扫码登录后会生成 data/zhihu_state.json。"
        )

    rows: list[dict[str, str]] = []
    with sync_playwright() as playwright:
        browser, context = build_context(playwright, STATE_PATH)
        page = context.new_page()

        links = collect_question_links(page, question_count)
        print(f"话题页收集到 {len(links)} 个问题链接")

        for index, url in enumerate(links[:question_count], start=1):
            try:
                question_rows = extract_question(page, url, answer_count)
            except Exception as error:  # noqa: BLE001
                print(f"  [{index}] 失败 {url}：{type(error).__name__}")
                continue
            name = question_rows[0]["问题名"][:30] if question_rows else "(空)"
            print(f"  [{index}/{question_count}] {name} -> {len(question_rows)} 条回答")
            rows.extend(question_rows)
            time.sleep(random.uniform(1.5, 3.0))

        browser.close()

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with CSV_PATH.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"共 {len(rows)} 条回答写入 {CSV_PATH}")


def main() -> None:
    parser = argparse.ArgumentParser(description="爬知乎话题高赞回答（Playwright）")
    parser.add_argument("--login", action="store_true", help="扫码登录并保存 cookie")
    parser.add_argument("--questions", type=int, default=20, help="爬几个问题")
    parser.add_argument("--answers", type=int, default=10, help="每个问题爬几条回答")
    args = parser.parse_args()

    if args.login:
        login()
        return
    crawl(args.questions, args.answers)


if __name__ == "__main__":
    main()
