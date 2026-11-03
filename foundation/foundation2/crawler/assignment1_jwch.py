"""作业 1：爬取福州大学教务处教学通知。

用法：
    python assignment1_jwch.py                # 爬 600 条并导出 CSV
    python assignment1_jwch.py --target 1200  # 想多爬一点
    python assignment1_jwch.py --download     # Bonus：把附件也下载下来
    python assignment1_jwch.py --export-only  # 只把已有 jsonl 重新导成 CSV

站点结构（2026-11 实测）：
    列表页  https://jwch.fzu.edu.cn/jxtz.htm           第 1 页
            https://jwch.fzu.edu.cn/jxtz/215.htm       第 2 页（页码是倒着编的）
            ...
            https://jwch.fzu.edu.cn/jxtz/1.htm         最后一页（第 216 页）
    详情页  ul.list-gl > li 里有日期、通知人（【】包着）和标题链接。
            正文在 div.v_news_content，发布时间是「发布时间：YYYY-MM-DD」。
    附件    详情页底部的 li 形如
            附件【<a href="...download.jsp?...wbfileid=18563163">名字.pdf</a>】已下载
            <span id="nattach18563163"><script>getClickTimes(18563163,1744984858,
            "wbnewsfile","attach")</script></span>次
            下载次数是 JS 渲染的，requests 拿不到，得自己请求它的 Ajax 接口。
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
import time
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urljoin, urlparse

from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import JsonlStore, RateLimiter, build_session, clean_text, human_size  # noqa: E402

BASE = "https://jwch.fzu.edu.cn/"
LIST_FIRST = BASE + "jxtz.htm"
# 站点用的是「倒序页码」：第 n 页对应 217-n。
LAST_PAGE = 216

DATA_DIR = Path(__file__).resolve().parent / "data"
JSONL_PATH = DATA_DIR / "jwch_notices.jsonl"
CSV_PATH = DATA_DIR / "jwch_notices.csv"
ATTACH_DIR = DATA_DIR / "attachments"

DATE_RE = re.compile(r"发布时间[:：]\s*(\d{4}-\d{2}-\d{2})")
NOTIFIER_RE = re.compile(r"【([^】]+)】")
ARTICLE_ID_RE = re.compile(r"/info/\d+/(\d+)\.htm")
# 附件 li：文件名、链接、文件 id、owner
ATTACH_RE = re.compile(
    r'附件【\s*<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>\s*】.*?id="nattach(\d+)"',
    re.S,
)
OWNER_RE = re.compile(r"owner=(\d+)")

CSV_COLUMNS = [
    "通知人",
    "标题",
    "发布时间",
    "详情链接",
    "正文",
    "附件名",
    "附件下载次数",
    "附件链接",
    "附件数量",
    "正文长度",
]


def list_page_url(page: int) -> str:
    """第 page 页的地址（page 从 1 开始）。"""
    if page == 1:
        return LIST_FIRST
    return f"{BASE}jxtz/{LAST_PAGE + 1 - page}.htm"


def parse_list_page(html: str) -> list[dict[str, str]]:
    """从列表页 HTML 里抠出「日期 / 通知人 / 标题 / 链接」。"""
    soup = BeautifulSoup(html, "lxml")
    items: list[dict[str, str]] = []
    for li in soup.select("ul.list-gl > li"):
        link = li.find("a", href=True)
        if link is None:
            continue
        raw_text = li.get_text(" ", strip=True)
        date_node = li.select_one("span.doclist_time")
        date_text = clean_text(date_node.get_text(" ", strip=True)) if date_node else ""
        notifier_match = NOTIFIER_RE.search(raw_text)
        raw_title = link.get("title")
        title = str(raw_title) if raw_title else link.get_text(" ", strip=True)
        items.append(
            {
                "publish_date": date_text,
                "notifier": clean_text(notifier_match.group(1)) if notifier_match else "",
                "title": clean_text(title),
                "url": urljoin(BASE, str(link["href"])),
            }
        )
    return items


def article_id(url: str) -> str:
    """详情页的唯一 id：优先用 info/1036/14858.htm 里的数字，其次用 wbnewsid。"""
    match = ARTICLE_ID_RE.search(url)
    if match:
        return match.group(1)
    query = parse_qs(urlparse(url).query)
    news_id = query.get("wbnewsid")
    if news_id:
        return news_id[0]
    return str(abs(hash(url)) % 10**8)


def fetch_download_count(session: Any, file_id: str, owner: str, referer: str) -> int | None:
    """请求附件下载次数的 Ajax 接口。

    这个接口就是页面里 getClickTimes() 调用的那个，返回
    {"wbshowtimes": 86, "randomid": "nattach", "wbnewsid": 18563163}。
    """
    url = BASE + "system/resource/code/news/click/clicktimes.jsp"
    params = {
        "wbnewsid": file_id,
        "owner": owner,
        "type": "wbnewsfile",
        "randomid": "nattach",
    }
    try:
        response = session.get(url, params=params, headers={"Referer": referer}, timeout=15)
        payload = response.json()
    except Exception:  # noqa: BLE001 - 单个附件失败不该拖垮整条通知
        return None
    value = payload.get("wbshowtimes")
    return int(value) if isinstance(value, (int, str)) and str(value).isdigit() else None


def parse_detail(html: str, page_url: str, session: Any, limiter: RateLimiter) -> dict[str, Any]:
    """解析详情页：发布时间、正文、附件（含下载次数）。"""
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style"]):
        tag.decompose()

    plain = soup.get_text(" ", strip=True)
    date_match = DATE_RE.search(plain)
    publish_date = date_match.group(1) if date_match else ""

    body_node = soup.select_one("div.v_news_content")
    body = clean_text(body_node.get_text(" ", strip=True)) if body_node else ""

    attachments: list[dict[str, Any]] = []
    for href, name, file_id in ATTACH_RE.findall(html):
        owner_match = OWNER_RE.search(href)
        owner = owner_match.group(1) if owner_match else ""
        limiter.wait()
        count = fetch_download_count(session, file_id, owner, page_url)
        attachments.append(
            {
                "name": clean_text(BeautifulSoup(name, "lxml").get_text()),
                "download_url": urljoin(BASE, href),
                "file_id": file_id,
                "download_count": count,
            }
        )

    return {"publish_date": publish_date, "body": body, "attachments": attachments}


def download_attachment(session: Any, attachment: dict[str, Any], target_dir: Path) -> str:
    """Bonus：把附件存到本地，返回相对路径。"""
    target_dir.mkdir(parents=True, exist_ok=True)
    name = attachment["name"] or f"attachment_{attachment['file_id']}"
    suffix = Path(name).suffix or ".bin"
    target = target_dir / f"{attachment['file_id']}{suffix}"
    if target.exists() and target.stat().st_size > 0:
        return str(target.relative_to(DATA_DIR))

    response = session.get(
        attachment["download_url"],
        timeout=60,
        stream=True,
        headers={"Referer": BASE},
    )
    response.raise_for_status()
    with target.open("wb") as handle:
        for chunk in response.iter_content(chunk_size=64 * 1024):
            if chunk:
                handle.write(chunk)
    attachment["size"] = human_size(target.stat().st_size)
    attachment["local_path"] = str(target.relative_to(DATA_DIR))
    return attachment["local_path"]


def crawl(target: int, download: bool, interval: float) -> None:
    session = build_session()
    limiter = RateLimiter(interval)
    store = JsonlStore(JSONL_PATH)
    done = store.existing_ids("id")
    if done:
        print(f"检测到已有 {len(done)} 条记录，将从断点继续。")

    page = 1
    while store.count() < target and page <= LAST_PAGE:
        url = list_page_url(page)
        limiter.wait()
        response = session.get(url, timeout=20)
        response.encoding = response.apparent_encoding
        if response.status_code != 200:
            print(f"列表第 {page} 页返回 {response.status_code}，停止。")
            break

        items = parse_list_page(response.text)
        if not items:
            print(f"列表第 {page} 页没有解析到条目，停止。")
            break

        print(f"[列表] 第 {page} 页 {len(items)} 条（累计目标 {target}）")
        for item in items:
            if store.count() >= target:
                break
            aid = article_id(item["url"])
            if aid in done:
                continue

            limiter.wait()
            try:
                detail_response = session.get(item["url"], timeout=25)
            except Exception as error:  # noqa: BLE001
                print(f"  跳过 {item['url']}：{type(error).__name__}")
                continue
            if detail_response.status_code != 200:
                print(f"  跳过 {item['url']}：HTTP {detail_response.status_code}")
                continue
            detail_response.encoding = detail_response.apparent_encoding

            detail = parse_detail(detail_response.text, item["url"], session, limiter)
            record = {
                "id": aid,
                **item,
                "publish_date": detail["publish_date"] or item["publish_date"],
                "body": detail["body"],
                "attachments": detail["attachments"],
            }

            if download:
                for attachment in record["attachments"]:
                    try:
                        download_attachment(session, attachment, ATTACH_DIR / aid)
                    except Exception as error:  # noqa: BLE001
                        print(f"    附件下载失败：{type(error).__name__}")

            store.append(record)
            done.add(aid)

            if store.count() % 25 == 0:
                print(f"  已保存 {store.count()} 条")

        page += 1

    print(f"\n共 {store.count()} 条记录写入 {JSONL_PATH}")


def export_csv() -> None:
    """把 jsonl 汇总成 CSV：一条通知一行，多个附件用「 | 」拼在同一格里。"""
    store = JsonlStore(JSONL_PATH)
    records = list(store.read_all())
    if not records:
        print("还没有数据，先跑一次爬取。")
        return

    records.sort(key=lambda item: (item.get("publish_date", ""), item.get("id", "")), reverse=True)
    with CSV_PATH.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for record in records:
            attachments = record.get("attachments") or []
            writer.writerow(
                {
                    "通知人": record.get("notifier", ""),
                    "标题": record.get("title", ""),
                    "发布时间": record.get("publish_date", ""),
                    "详情链接": record.get("url", ""),
                    "正文": record.get("body", ""),
                    "附件名": " | ".join(a.get("name", "") for a in attachments),
                    "附件下载次数": " | ".join(
                        str(a.get("download_count")) if a.get("download_count") is not None else ""
                        for a in attachments
                    ),
                    "附件链接": " | ".join(a.get("download_url", "") for a in attachments),
                    "附件数量": len(attachments),
                    "正文长度": len(record.get("body", "")),
                }
            )

    with_attach = sum(1 for record in records if record.get("attachments"))
    print(f"导出 {len(records)} 条到 {CSV_PATH}")
    print(f"其中 {with_attach} 条带附件，共 {sum(len(r.get('attachments') or []) for r in records)} 个附件")


def main() -> None:
    parser = argparse.ArgumentParser(description="爬取福大教务通知")
    parser.add_argument("--target", type=int, default=600, help="目标条数（题目要求至少 500）")
    parser.add_argument("--download", action="store_true", help="Bonus：下载附件")
    parser.add_argument("--export-only", action="store_true", help="只重新导出 CSV")
    parser.add_argument("--interval", type=float, default=0.25, help="请求最小间隔（秒）")
    args = parser.parse_args()

    if args.export_only:
        export_csv()
        return

    started = time.monotonic()
    try:
        crawl(args.target, args.download, args.interval)
    except KeyboardInterrupt:
        print("\n收到中断信号，已爬到的内容都在 jsonl 里，下次运行会接着爬。")
    finally:
        export_csv()
        print(f"耗时 {time.monotonic() - started:.1f}s")


if __name__ == "__main__":
    main()
