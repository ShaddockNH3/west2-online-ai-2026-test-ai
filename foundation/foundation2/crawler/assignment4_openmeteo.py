"""作业 4：Open-Meteo —— 只发一次请求，拿福州大学旗山校区 2024 全年的天气数据。

题目要求「只允许发起一次请求」，所以这里把 hourly 和 daily 变量塞进同一个
/archive 请求里。Open-Meteo 的 historical API 支持同时返回两组数据，
返回体里 hourly 有 8784 行（2024 是闰年，366×24），daily 有 366 行。

用法：
    python assignment4_openmeteo.py

一个小坑：题目里写的是 `cloud_cover_total`，但 archive API 的实际字段名是
`cloud_cover`（`cloud_cover_total` 会 400）。这里按可用的字段名请求，并在
CSV 里保留题目要求的语义（总云量）。
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path
from typing import Any

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import build_session  # noqa: E402

API_URL = "https://archive-api.open-meteo.com/v1/archive"
DATA_DIR = Path(__file__).resolve().parent / "data"

# 福州大学旗山校区
LATITUDE = 26.05942
LONGITUDE = 119.198
START_DATE = "2024-01-01"
END_DATE = "2024-12-31"

HOURLY_VARS = [
    "temperature_2m",
    "relative_humidity_2m",
    "apparent_temperature",
    "precipitation",
    "weather_code",
    "cloud_cover",
    "wind_speed_10m",
    "wind_direction_10m",
    "shortwave_radiation_instant",
    "is_day",
]

DAILY_VARS = [
    "temperature_2m_mean",
    "temperature_2m_max",
    "temperature_2m_min",
    "precipitation_sum",
    "sunshine_duration",
]

# WMO 天气代码 -> 中文，纯本地映射，不额外发请求
WEATHER_CODES = {
    0: "晴",
    1: "基本晴",
    2: "局部多云",
    3: "阴",
    45: "雾",
    48: "雾凇",
    51: "小毛毛雨",
    53: "毛毛雨",
    55: "大毛毛雨",
    56: "冻毛毛雨",
    57: "强冻毛毛雨",
    61: "小雨",
    63: "中雨",
    65: "大雨",
    66: "冻雨",
    67: "强冻雨",
    71: "小雪",
    73: "中雪",
    75: "大雪",
    77: "雪粒",
    80: "小阵雨",
    81: "阵雨",
    82: "强阵雨",
    85: "小阵雪",
    86: "强阵雪",
    95: "雷阵雨",
    96: "雷阵雨伴小冰雹",
    99: "雷阵雨伴大冰雹",
}


def fetch_once() -> dict[str, Any]:
    """唯一的一次网络请求。"""
    session = build_session(total_retries=2)
    params = {
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "start_date": START_DATE,
        "end_date": END_DATE,
        "hourly": ",".join(HOURLY_VARS),
        "daily": ",".join(DAILY_VARS),
        "timezone": "Asia/Shanghai",
    }
    response = session.get(API_URL, params=params, timeout=90)
    response.raise_for_status()
    payload = response.json()
    if "hourly" not in payload:
        raise RuntimeError(f"接口没有返回 hourly 数据：{payload}")
    return payload


def write_hourly(payload: dict[str, Any], path: Path) -> int:
    hourly = payload["hourly"]
    columns = ["time", *HOURLY_VARS, "weather_desc"]
    rows = len(hourly["time"])
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(columns)
        for index in range(rows):
            code = hourly["weather_code"][index]
            writer.writerow(
                [hourly[name][index] for name in ["time", *HOURLY_VARS]]
                + [WEATHER_CODES.get(code, f"未知({code})")]
            )
    return rows


def write_daily(payload: dict[str, Any], path: Path) -> int:
    daily = payload["daily"]
    columns = ["time", *DAILY_VARS]
    rows = len(daily["time"])
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(columns)
        for index in range(rows):
            writer.writerow([daily[name][index] for name in columns])
    return rows


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    print(f"请求 {API_URL}（这是唯一一次请求）")
    payload = fetch_once()

    (DATA_DIR / "openmeteo_2024_raw.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    hourly_rows = write_hourly(payload, DATA_DIR / "openmeteo_2024_hourly.csv")
    daily_rows = write_daily(payload, DATA_DIR / "openmeteo_2024_daily.csv")

    units = payload.get("hourly_units", {})
    print(f"站点：{payload['latitude']}, {payload['longitude']}（海拔 {payload['elevation']}m）")
    print(f"时区：{payload['timezone']}")
    print(f"小时数据 {hourly_rows} 行 -> data/openmeteo_2024_hourly.csv")
    print(f"每日数据 {daily_rows} 行 -> data/openmeteo_2024_daily.csv")
    print(f"温度单位：{units.get('temperature_2m')}，降水单位：{units.get('precipitation')}")


if __name__ == "__main__":
    main()
