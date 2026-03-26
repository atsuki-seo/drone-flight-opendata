"""ホバリング地点検出"""

import pandas as pd

from converter.config import HOVER_MIN_DURATION_SEC, HOVER_SPEED_THRESHOLD_MS
from converter.analyzers.summary import format_utc


def detect(csv_df: pd.DataFrame, srt_df: pd.DataFrame | None = None) -> list[dict]:
    """ホバリング地点を検出して返す"""
    df = csv_df.copy()
    df["is_hover"] = df["speed"] < HOVER_SPEED_THRESHOLD_MS

    # 連続するホバリング区間をグループ化
    df["group"] = (df["is_hover"] != df["is_hover"].shift()).cumsum()
    hover_groups = df[df["is_hover"]].groupby("group")

    points = []
    for _, group in hover_groups:
        duration = (group["datetime_utc"].iloc[-1] - group["datetime_utc"].iloc[0]).total_seconds()
        if duration < HOVER_MIN_DURATION_SEC:
            continue

        lat = round(group["latitude"].median(), 6)
        lon = round(group["longitude"].median(), 6)
        alt = round(group["altitude_m"].median(), 1)
        start_time = group["datetime_utc"].iloc[0]

        # SRTからカメラyawを付加
        camera_yaw = None
        if srt_df is not None and not srt_df.empty:
            camera_yaw = _get_camera_yaw(srt_df, start_time)

        points.append({
            "lat": lat,
            "lon": lon,
            "alt_m": alt,
            "address": None,
            "start_time_utc": format_utc(start_time),
            "duration_sec": round(duration, 1),
            "camera_yaw_deg": camera_yaw,
        })

    return points


def _get_camera_yaw(srt_df: pd.DataFrame, target_time: pd.Timestamp) -> float | None:
    """指定時刻に最も近いSRTレコードのカメラyawを返す"""
    time_diffs = (srt_df["datetime_utc"] - target_time).abs()
    closest_idx = time_diffs.idxmin()
    # 1秒以内のマッチのみ採用
    if time_diffs.loc[closest_idx].total_seconds() <= 1.0:
        val = srt_df.loc[closest_idx, "gb_yaw"]
        if pd.notna(val):
            return round(float(val), 1)
    return None
