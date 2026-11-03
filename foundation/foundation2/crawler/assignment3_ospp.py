"""作业 3：抓接口爬取开源之夏 2026 的项目列表。

页面是典型的前后端分离：https://summer-ospp.ac.cn/org/projectlist 的 HTML 里
什么数据都没有，项目列表和详情都是 POST 回来的 JSON。抓包（或在 bundle 里翻
`/api/` 字符串）能看到两个接口：

    POST /api/getProList    {"pageNum": 1, "pageSize": 50}
         -> {"total": 102, "rows": [{programCode, proId, programName, difficulty, techTag, ...}]}
    POST /api/getProDetail  {"programId": 30}
         -> {programDesc, outputRequirement, techRequirement, ...}

注意详情接口的参数名是 `programId`，值取列表里的 `proId`（不是 programCode，
也不是 proId 这个字段名本身 —— 这几个都试过，只有 programId 能通）。

用法：
    python assignment3_ospp.py               # 爬列表 + 每个项目的详情
    python assignment3_ospp.py --pdf-dir pdf # Bonus：尝试下载申请书（需要登录态）
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import re
import sys
from pathlib import Path
from typing import Any

import requests
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import RateLimiter, build_session, clean_text, safe_filename  # noqa: E402

BASE = "https://summer.ospp.ac.cn"
LIST_API = BASE + "/api/getProList"
DETAIL_API = BASE + "/api/getProDetail"
APPLICATION_API = BASE + "/api/downloadApplication"

DATA_DIR = Path(__file__).resolve().parent / "data"
CSV_PATH = DATA_DIR / "ospp_projects.csv"
JSON_PATH = DATA_DIR / "ospp_projects.json"

HEADERS = {
    "Content-Type": "application/json",
    "Referer": BASE + "/",
    "Origin": BASE,
}

CSV_COLUMNS = [
    "项目编号",
    "项目名",
    "所属组织",
    "项目难度",
    "技术领域",
    "编程语言",
    "项目简述",
    "产出要求",
    "技术要求",
    "奖金",
    "详情链接",
]


def html_to_text(raw: str) -> str:
    """项目简述是 HTML 片段，转成可读纯文本（保留段落分隔）。"""
    if not raw:
        return ""
    soup = BeautifulSoup(raw, "lxml")
    for tag in soup(["script", "style"]):
        tag.decompose()
    # <p>/<br>/<li> 换成空格，避免句子粘在一起
    for tag in soup.find_all(["p", "br", "li", "div", "h1", "h2", "h3", "tr"]):
        tag.insert_before(" ")
    return clean_text(soup.get_text(" "), drop_brackets=False)


def parse_tech_tags(raw: str) -> list[str]:
    """techTag 是字符串形式的二维数组：[["datas","AI"],["datas","PyTorch"]]。"""
    if not raw:
        return []
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return [clean_text(raw)]
    tags: list[str] = []
    for entry in parsed:
        if isinstance(entry, list) and entry:
            tags.append(str(entry[-1]))
        elif isinstance(entry, str):
            tags.append(entry)
    # 去重但保持顺序
    return list(dict.fromkeys(tag for tag in tags if tag))


def parse_requirements(items: list[dict[str, Any]] | None) -> str:
    """产出要求/技术要求是 [{title, children}] 树，拍平成一句话。"""
    if not items:
        return ""
    parts: list[str] = []
    for item in items:
        # 接口里偶尔会混进 None，跳过就行
        if not isinstance(item, dict):
            continue
        title = clean_text(str(item.get("title", "")), drop_brackets=False)
        if title:
            parts.append(title)
        children = item.get("children") or []
        if not isinstance(children, list):
            continue
        for child in children:
            if not isinstance(child, dict):
                continue
            child_title = clean_text(str(child.get("title", "")), drop_brackets=False)
            if child_title:
                parts.append(child_title)
    return "；".join(parts)


def fetch_list(session: requests.Session, limiter: RateLimiter, page_size: int = 50) -> list[dict[str, Any]]:
    """翻页拿全量项目列表。"""
    rows: list[dict[str, Any]] = []
    page = 1
    total = None
    while True:
        limiter.wait()
        response = session.post(
            LIST_API, headers=HEADERS, json={"pageNum": page, "pageSize": page_size}, timeout=30
        )
        response.raise_for_status()
        payload = response.json()
        if total is None:
            total = payload.get("total", 0)
            print(f"接口报告共 {total} 个项目")
        batch = payload.get("rows") or []
        if not batch:
            break
        rows.extend(batch)
        print(f"  第 {page} 页 {len(batch)} 条（累计 {len(rows)}）")
        if total is not None and len(rows) >= total:
            break
        page += 1
    return rows


def fetch_detail(
    session: requests.Session, limiter: RateLimiter, pro_id: int
) -> dict[str, Any] | None:
    limiter.wait()
    response = session.post(DETAIL_API, headers=HEADERS, json={"programId": pro_id}, timeout=30)
    if response.status_code != 200:
        print(f"  项目 {pro_id} 详情失败：HTTP {response.status_code}")
        return None
    return response.json()


def detail_url(program_code: str) -> str:
    """前端详情页地址（路由参数用 programCode）。"""
    return f"{BASE}/projectDetail?programCode={program_code}"


def download_pdf(
    session: requests.Session, limiter: RateLimiter, pro_id: int, name: str, target_dir: Path
) -> str | None:
    """Bonus：下载项目申请书 PDF。

    这个接口需要登录态（未登录返回 401 Unauthorized），所以只有提供了
    `data/ospp_cookies.json`（浏览器里登录后导出的 cookie）才会成功。
    导出方法见 README。
    """
    limiter.wait()
    response = session.post(
        APPLICATION_API, headers=HEADERS, json={"programId": pro_id}, timeout=60
    )
    if response.status_code == 401:
        return None
    if response.status_code != 200:
        print(f"  申请书 {pro_id} 返回 {response.status_code}")
        return None
    content_type = response.headers.get("Content-Type", "")
    if "pdf" not in content_type and "octet-stream" not in content_type:
        print(f"  申请书 {pro_id} 不是文件：{response.text[:80]}")
        return None
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / f"{pro_id}_{safe_filename(name, 60)}.pdf"
    target.write_bytes(response.content)
    return str(target.relative_to(DATA_DIR))


def main() -> None:
    parser = argparse.ArgumentParser(description="爬取开源之夏 2026 项目列表")
    parser.add_argument("--interval", type=float, default=0.3, help="请求最小间隔（秒）")
    parser.add_argument("--pdf-dir", default="", help="Bonus：申请书 PDF 保存目录")
    parser.add_argument("--cookie-file", default="", help="登录 cookie 的 json 文件")
    args = parser.parse_args()

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    session = build_session()
    limiter = RateLimiter(args.interval)

    if args.cookie_file:
        cookie_path = Path(args.cookie_file)
        if cookie_path.exists():
            cookies = json.loads(cookie_path.read_text(encoding="utf-8"))
            session.cookies.update({item["name"]: item["value"] for item in cookies})
            print(f"已载入 {len(cookies)} 条 cookie")

    rows = fetch_list(session, limiter)
    if not rows:
        print("没有拿到项目列表，检查接口是否改了。")
        return

    projects: list[dict[str, Any]] = []
    for index, row in enumerate(rows, start=1):
        pro_id = row.get("proId")
        detail = fetch_detail(session, limiter, pro_id) if isinstance(pro_id, int) else None
        detail = detail or {}

        record = {
            "program_code": row.get("programCode", ""),
            "name": clean_text(row.get("programName", ""), drop_brackets=False),
            "org": clean_text(row.get("orgName", ""), drop_brackets=False),
            "difficulty": (row.get("difficulty") or "").split("/")[0],
            "tech": parse_tech_tags(row.get("techTag", "")),
            "languages": [
                item.strip().strip('"')
                for item in str(detail.get("programmingLanguageTag") or "").strip("[]").split(",")
                if item.strip()
            ],
            "desc": html_to_text(detail.get("programDesc", "")),
            "output": parse_requirements(detail.get("outputRequirement")),
            "tech_req": parse_requirements(detail.get("techRequirement")),
            "bonus": row.get("bonus", ""),
            "url": detail_url(row.get("programCode", "")),
        }

        if args.pdf_dir and isinstance(pro_id, int):
            saved = download_pdf(session, limiter, pro_id, record["name"], DATA_DIR / args.pdf_dir)
            if saved:
                record["pdf"] = saved

        projects.append(record)
        if index % 20 == 0:
            print(f"  详情进度 {index}/{len(rows)}")

    JSON_PATH.write_text(json.dumps(projects, ensure_ascii=False, indent=1), encoding="utf-8")

    with CSV_PATH.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for project in projects:
            writer.writerow(
                {
                    "项目编号": project["program_code"],
                    "项目名": project["name"],
                    "所属组织": project["org"],
                    "项目难度": project["difficulty"],
                    "技术领域": " / ".join(project["tech"]),
                    "编程语言": " / ".join(project["languages"]),
                    "项目简述": project["desc"],
                    "产出要求": project["output"],
                    "技术要求": project["tech_req"],
                    "奖金": project["bonus"],
                    "详情链接": project["url"],
                }
            )

    with_desc = sum(1 for project in projects if project["desc"])
    print(f"\n共 {len(projects)} 个项目，其中 {with_desc} 个拿到项目简述")
    print(f"导出到 {CSV_PATH}")
    if args.pdf_dir:
        saved = sum(1 for project in projects if project.get("pdf"))
        print(f"申请书已下载 {saved} 份（需要登录态，未登录时会被 401 拦住）")


if __name__ == "__main__":
    main()
