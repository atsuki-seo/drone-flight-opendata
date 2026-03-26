"""DJI テレメトリCSVパーサー"""

import pandas as pd

from converter.config import FT_TO_M


COLUMN_MAP = {
    "Datetime (UTC)": "datetime_utc",
    "Latitude": "latitude",
    "Longitude": "longitude",
    "GPS Altitude (ft MSL)": "altitude_ft",
    "Satellites": "satellites",
    "Horizontal Accuracy Estimate (+/- ft)": "h_accuracy_ft",
    "Vertical Accuracy Estimate (+/- ft)": "v_accuracy_ft",
    "X Velocity (m/s)": "velocity_x",
    "Y Velocity (m/s)": "velocity_y",
    "Z Velocity (m/s)": "velocity_z",
    "Speed (m/s)": "speed",
    "Velocity Accuracy Estimate (+/- m/s)": "velocity_accuracy",
}


def parse(csv_path: str) -> pd.DataFrame:
    """DJI CSVを読み込み、正規化・単位変換済みDataFrameを返す"""
    df = pd.read_csv(csv_path)
    df = df.rename(columns=COLUMN_MAP)

    # タイムスタンプをUTC datetimeに変換
    df["datetime_utc"] = pd.to_datetime(df["datetime_utc"], utc=True)

    # ft → m 変換
    df["altitude_m"] = df["altitude_ft"] * FT_TO_M
    df["h_accuracy_m"] = df["h_accuracy_ft"] * FT_TO_M
    df["v_accuracy_m"] = df["v_accuracy_ft"] * FT_TO_M

    # 不要カラムを削除
    df = df.drop(columns=["altitude_ft", "h_accuracy_ft", "v_accuracy_ft"])

    return df
