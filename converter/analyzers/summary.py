"""フライトサマリー計算"""

import math

import pandas as pd


def compute(csv_df: pd.DataFrame) -> dict:
    """CSVパース済みDataFrameからsummary dictを生成"""
    first = csv_df.iloc[0]
    last = csv_df.iloc[-1]

    start_time = first["datetime_utc"]
    end_time = last["datetime_utc"]
    duration = (end_time - start_time).total_seconds()

    # 総飛行距離
    total_distance = _total_distance(csv_df)

    # bbox
    bbox = {
        "north": round(csv_df["latitude"].max(), 6),
        "south": round(csv_df["latitude"].min(), 6),
        "east": round(csv_df["longitude"].max(), 6),
        "west": round(csv_df["longitude"].min(), 6),
    }

    # satellites / accuracy の平均（全NaNならnull）
    satellites_avg = _nullable_mean(csv_df, "satellites")
    gps_accuracy_h_m = _nullable_mean(csv_df, "h_accuracy_m")

    return {
        "date": start_time.strftime("%Y-%m-%d"),
        "start_time_utc": format_utc(start_time),
        "end_time_utc": format_utc(end_time),
        "duration_sec": round(duration, 1),
        "region": None,
        "start_point": {
            "lat": round(first["latitude"], 6),
            "lon": round(first["longitude"], 6),
            "alt_m": round(first["altitude_m"], 1),
        },
        "end_point": {
            "lat": round(last["latitude"], 6),
            "lon": round(last["longitude"], 6),
            "alt_m": round(last["altitude_m"], 1),
        },
        "bbox": bbox,
        "total_distance_m": round(total_distance, 1),
        "max_alt_m": round(csv_df["altitude_m"].max(), 1),
        "min_alt_m": round(csv_df["altitude_m"].min(), 1),
        "max_speed_ms": round(csv_df["speed"].max(), 2),
        "avg_speed_ms": round(csv_df["speed"].mean(), 2),
        "satellites_avg": satellites_avg,
        "gps_accuracy_h_m": gps_accuracy_h_m,
    }


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """2点間の距離をメートルで返す"""
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _total_distance(df: pd.DataFrame) -> float:
    total = 0.0
    lats = df["latitude"].values
    lons = df["longitude"].values
    for i in range(1, len(lats)):
        total += haversine(lats[i - 1], lons[i - 1], lats[i], lons[i])
    return total


def _nullable_mean(df: pd.DataFrame, col: str) -> float | None:
    if col not in df.columns:
        return None
    series = df[col].dropna()
    if series.empty:
        return None
    return round(series.mean(), 1)


def format_utc(ts: pd.Timestamp) -> str:
    """秒精度のUTC ISO 8601文字列を返す"""
    return ts.strftime("%Y-%m-%dT%H:%M:%SZ")
