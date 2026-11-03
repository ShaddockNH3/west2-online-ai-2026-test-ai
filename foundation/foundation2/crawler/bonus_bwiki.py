"""Bonus：用 MediaWiki API 抓 B-Wiki「方案舰娘」分类下的所有页面。

这里不用解析 HTML，而是走 MediaWiki 的 Action API：
    action=query & list=categorymembers & cmtitle=Category:方案舰娘
先拿到分类下的页面名，再对每个页面
    action=parse & page=标题 & prop=wikitext
拿原始 wikitext。题目说「不需要整理文本」，所以原样存文件，不洗数据。

API 的礼貌（题目里那几条）都在代码里体现了：
  * 每次请求间隔 ≥ 1 秒，串行请求，不并发；
  * 带 maxlag=5，服务器忙时它会返回 maxlag 错误，此时等 5 秒再试，试 3 次还不行就跳过；
  * User-Agent 里留联系方式，方便站长找你。

用法：
    python bonus_bwiki.py              # 抓分类列表 + 每页 wikitext
    python bonus_bwiki.py --list-only  # 只抓分类成员列表
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import RateLimiter, build_session, safe_filename  # noqa: E402

API_URL = "https://wiki.biligame.com/blhx/api.php"
CATEGORY = "Category:方案舰娘"
CATEGORY_PREFIX = "PR"  # 方案舰（PR 舰）的编号前缀，存文件时用得上

DATA_DIR = Path(__file__).resolve().parent / "data"
RAW_DIR = DATA_DIR / "bwiki_raw"
PAGES_CSV = DATA_DIR / "bwiki_pages.csv"
INDEX_JSON = DATA_DIR / "bwiki_index.json"

HEADERS = {
    # 留邮箱是 MediaWiki 的礼貌，出问题时管理员能联系到你
    "User-Agent": "MyCrawler/1.0 (contact: your_email@example.com)",
    "Accept-Encoding": "gzip",
}

BASE_PARAMS = {
    "format": "json",
    "formatversion": "2",
    "maxlag": "5",
}

MAXLAG_RETRIES = 3
MAXLAG_WAIT = 5.0


def api_get(session: Any, limiter: RateLimiter, params: dict[str, str]) -> dict[str, Any] | None:
    """带 maxlag 处理的一次 API 调用。"""
    for attempt in range(1, MAXLAG_RETRIES + 1):
        limiter.wait()
        response = session.get(API_URL, headers=HEADERS, params=params, timeout=40)
        if response.status_code != 200:
            print(f"  HTTP {response.status_code}，第 {attempt} 次")
            time.sleep(MAXLAG_WAIT)
            continue
        payload = response.json()
        error = payload.get("error")
        if not error:
            return payload
        code = error.get("code", "")
        if code == "maxlag":
            # 服务器说忙：它给了 Retry-After 就听它的，没给就等 5 秒
            wait = float(response.headers.get("Retry-After", MAXLAG_WAIT))
            print(f"  服务器繁忙（maxlag），等 {wait:.0f}s 后重试（{attempt}/{MAXLAG_RETRIES}）")
            time.sleep(wait)
            continue
        print(f"  接口报错：{code} {error.get('info', '')}")
        return None
    print("  maxlag 重试次数用完，跳过这一条")
    return None


def fetch_category_members(session: Any, limiter: RateLimiter) -> list[dict[str, Any]]:
    """拿分类下的全部页面，用 continue 翻页。"""
    members: list[dict[str, Any]] = []
    params: dict[str, str] = {
        "action": "query",
        "list": "categorymembers",
        "cmtitle": CATEGORY,
        "cmlimit": "500",
        "cmtype": "page",
        **BASE_PARAMS,
    }
    while True:
        payload = api_get(session, limiter, params)
        if payload is None:
            break
        batch = payload.get("query", {}).get("categorymembers", [])
        members.extend(batch)
        print(f"  分类成员累计 {len(members)}")
        cont = payload.get("continue")
        if not cont:
            break
        params = {**params, **cont}
    return members


def fetch_wikitext(session: Any, limiter: RateLimiter, title: str) -> str | None:
    params = {
        "action": "parse",
        "page": title,
        "prop": "wikitext",
        "redirects": "1",
        **BASE_PARAMS,
    }
    payload = api_get(session, limiter, params)
    if payload is None:
        return None
    return payload.get("parse", {}).get("wikitext")


def main() -> None:
    parser = argparse.ArgumentParser(description="B-Wiki 方案舰娘分类爬取")
    parser.add_argument("--list-only", action="store_true", help="只抓分类成员，不抓正文")
    parser.add_argument("--interval", type=float, default=1.1, help="请求间隔（API 建议 ≥1s）")
    args = parser.parse_args()

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    session = build_session()
    limiter = RateLimiter(args.interval, jitter=0.2)

    print(f"分类：{CATEGORY}")
    members = fetch_category_members(session, limiter)
    if not members:
        print("没有拿到分类成员，检查 CATEGORY 名字是否正确（注意是 Category: 而不是 分类:）。")
        return
    print(f"共 {len(members)} 个页面")

    index: list[dict[str, Any]] = []
    if not args.list_only:
        RAW_DIR.mkdir(parents=True, exist_ok=True)
        for position, member in enumerate(members, start=1):
            title = member.get("title", "")
            text = fetch_wikitext(session, limiter, title)
            if text is None:
                print(f"  [{position}/{len(members)}] {title} 失败")
                continue
            target = RAW_DIR / f"{CATEGORY_PREFIX}_{safe_filename(title, 80)}.txt"
            target.write_text(text, encoding="utf-8")
            index.append(
                {
                    "pageid": member.get("pageid"),
                    "title": title,
                    "category": CATEGORY,
                    "chars": len(text),
                    "file": str(target.relative_to(DATA_DIR)),
                }
            )
            print(f"  [{position}/{len(members)}] {title} ({len(text)} 字符)")
    else:
        index = [
            {"pageid": m.get("pageid"), "title": m.get("title", ""), "category": CATEGORY}
            for m in members
        ]

    INDEX_JSON.write_text(json.dumps(index, ensure_ascii=False, indent=1), encoding="utf-8")
    with PAGES_CSV.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["pageid", "title", "category", "chars", "file"])
        writer.writeheader()
        for row in index:
            writer.writerow({key: row.get(key, "") for key in writer.fieldnames})

    print(f"\n索引写入 {PAGES_CSV}")
    if not args.list_only:
        print(f"原始 wikitext 写入 {RAW_DIR}（共 {len(index)} 个文件）")


if __name__ == "__main__":
    main()
