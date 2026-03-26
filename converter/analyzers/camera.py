"""カメライベント検出"""

import pandas as pd

from converter.config import CAMERA_YAW_THRESHOLD_DEG
from converter.analyzers.summary import format_utc


def detect(srt_df: pd.DataFrame | None) -> list[dict]:
    """カメラ方向が急変した地点を検出して返す"""
    if srt_df is None or srt_df.empty:
        return []

    df = srt_df.copy()
    if "gb_yaw" not in df.columns:
        return []

    df["yaw_diff"] = df["gb_yaw"].diff()
    df["yaw_diff_abs"] = df["yaw_diff"].abs()

    events = []
    for _, row in df[df["yaw_diff_abs"] > CAMERA_YAW_THRESHOLD_DEG].iterrows():
        prev_yaw = row["gb_yaw"] - row["yaw_diff"]
        events.append({
            "time_utc": format_utc(row["datetime_utc"]),
            "lat": round(float(row["latitude"]), 6),
            "lon": round(float(row["longitude"]), 6),
            "yaw_from_deg": round(float(prev_yaw), 1),
            "yaw_to_deg": round(float(row["gb_yaw"]), 1),
            "delta_deg": round(float(row["yaw_diff"]), 1),
        })

    return events
