"""DJI SRTパーサー"""

import re
from datetime import timedelta

import pandas as pd

from converter.config import SRT_TIMEZONE_OFFSET_HOURS


# SRTブロック内のキーバリューペアを抽出
_KV_PATTERN = re.compile(r'\[(\w+):\s*([^\]]+)\]')
# タイムスタンプ行を抽出
_TIMESTAMP_PATTERN = re.compile(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+)')


def parse(srt_path: str) -> pd.DataFrame:
    """DJI SRTを読み込み、1秒間隔にダウンサンプリング済みDataFrameを返す"""
    with open(srt_path, "r", encoding="utf-8-sig") as f:
        content = f.read()

    # SRTブロックを空行で分割
    blocks = content.strip().split("\n\n")

    records = []
    for block in blocks:
        ts_match = _TIMESTAMP_PATTERN.search(block)
        if not ts_match:
            continue

        kv_pairs = dict(_KV_PATTERN.findall(block))
        if not kv_pairs:
            continue

        record = {
            "datetime_local": pd.Timestamp(ts_match.group(1)),
            "latitude": _to_float(kv_pairs.get("latitude")),
            "longitude": _to_float(kv_pairs.get("longitude")),
            "rel_alt": _to_float(kv_pairs.get("rel_alt")),
            "abs_alt": _to_float(kv_pairs.get("abs_alt")),
            "gb_yaw": _to_float(kv_pairs.get("gb_yaw")),
            "gb_pitch": _to_float(kv_pairs.get("gb_pitch")),
            "gb_roll": _to_float(kv_pairs.get("gb_roll")),
            "iso": _to_float(kv_pairs.get("iso")),
            "shutter": kv_pairs.get("shutter", "").strip(),
            "fnum": _to_float(kv_pairs.get("fnum")),
            "focal_len": _to_float(kv_pairs.get("focal_len")),
            "dzoom_ratio": _to_float(kv_pairs.get("dzoom_ratio")),
        }
        records.append(record)

    df = pd.DataFrame(records)
    if df.empty:
        return df

    # JST → UTC変換
    offset = timedelta(hours=SRT_TIMEZONE_OFFSET_HOURS)
    df["datetime_utc"] = df["datetime_local"].apply(
        lambda ts: (ts - offset).tz_localize("UTC")
    )
    df = df.drop(columns=["datetime_local"])

    # 1秒間隔にダウンサンプリング（各秒の先頭フレームを採用）
    df["second_key"] = df["datetime_utc"].dt.floor("s")
    df = df.drop_duplicates(subset=["second_key"], keep="first")
    df = df.drop(columns=["second_key"])
    df = df.reset_index(drop=True)

    return df


def _to_float(value: str | None) -> float | None:
    if value is None:
        return None
    try:
        # "0.000 abs_alt: 72.256" のようなケースで先頭の数値だけ取る
        return float(value.strip().split()[0])
    except (ValueError, IndexError):
        return None
