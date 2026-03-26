"""CLIエントリポイント"""

import argparse
import json
import re
from pathlib import Path

import pandas as pd

from converter.config import SCHEMA_VERSION
from converter.parsers import dji_csv, dji_srt
from converter.analyzers import summary, hover, camera
from converter.analyzers.summary import format_utc
from converter.enrichers import geocoder
from converter.output import writer


def find_flight_pairs(input_dir: Path) -> list[dict]:
    """入力ディレクトリからCSV/SRTペアを探索"""
    pairs = []

    for route_dir in sorted(input_dir.iterdir()):
        if not route_dir.is_dir():
            continue

        csvs = sorted(route_dir.glob("*テレメトリ.csv"))
        srts = {s.stem: s for s in route_dir.glob("*.SRT")}

        for csv_path in csvs:
            # "石川-ルート1-1-テレメトリ.csv" → prefix "石川-ルート1-1"
            prefix = csv_path.stem.replace("-テレメトリ", "")
            srt_path = srts.get(prefix)

            pairs.append({
                "csv_path": csv_path,
                "srt_path": srt_path,
                "prefix": prefix,
                "route_dir": route_dir.name,
            })

    return pairs


def generate_flight_id(prefix: str, region_name: str) -> str:
    """日本語ファイル名プレフィックスからflight_idを生成

    例: "石川-ルート1-1" + region_name="ishikawa" → "ishikawa-route1-1"
    """
    # "石川-ルート1-1" → ["石川", "ルート1", "1"]
    parts = prefix.split("-")

    # ルート部分を変換: "ルート1" → "route1"
    route_parts = []
    for part in parts[1:]:
        m = re.match(r"ルート(\d+)", part)
        if m:
            route_parts.append(f"route{m.group(1)}")
        else:
            route_parts.append(part)

    flight_id = f"{region_name}-{'-'.join(route_parts)}"

    # バリデーション
    if not re.match(r"^[a-z][a-z0-9-]+$", flight_id):
        raise ValueError(f"Invalid flight_id: {flight_id}")

    return flight_id


def build_track(csv_df: pd.DataFrame, srt_df: pd.DataFrame | None) -> list[dict]:
    """trackポイント列を構築"""
    track = []
    for _, row in csv_df.iterrows():
        point = {
            "t": format_utc(row["datetime_utc"]),
            "lat": round(float(row["latitude"]), 6),
            "lon": round(float(row["longitude"]), 6),
            "alt_m": round(float(row["altitude_m"]), 1),
            "speed_ms": round(float(row["speed"]), 2) if pd.notna(row["speed"]) else None,
            "camera_yaw_deg": None,
            "camera_pitch_deg": None,
        }
        track.append(point)

    # SRTデータがあればカメラ情報を付加
    if srt_df is not None and not srt_df.empty:
        _merge_camera_to_track(track, csv_df, srt_df)

    return track


def _merge_camera_to_track(
    track: list[dict], csv_df: pd.DataFrame, srt_df: pd.DataFrame
):
    """trackにSRTのカメラ情報をマージ"""
    # merge_asof用にソート済みであることを確認
    csv_times = csv_df[["datetime_utc"]].copy().reset_index(drop=True)
    srt_subset = srt_df[["datetime_utc", "gb_yaw", "gb_pitch"]].copy()

    merged = pd.merge_asof(
        csv_times.sort_values("datetime_utc"),
        srt_subset.sort_values("datetime_utc"),
        on="datetime_utc",
        tolerance=pd.Timedelta("1s"),
        direction="nearest",
    ).reset_index(drop=True)

    for i, row in merged.iterrows():
        if i < len(track):
            if pd.notna(row.get("gb_yaw")):
                track[i]["camera_yaw_deg"] = round(float(row["gb_yaw"]), 1)
            if pd.notna(row.get("gb_pitch")):
                track[i]["camera_pitch_deg"] = round(float(row["gb_pitch"]), 1)


def process_flight(
    pair: dict, region_name: str, flight_log_schema: dict | None,
    geocode_cache: dict[str, str] | None = None,
) -> dict:
    """1フライト分の変換処理"""
    csv_df = dji_csv.parse(str(pair["csv_path"]))

    srt_df = None
    if pair["srt_path"] is not None:
        srt_df = dji_srt.parse(str(pair["srt_path"]))

    flight_id = generate_flight_id(pair["prefix"], region_name)

    has_srt = srt_df is not None and not srt_df.empty
    original_format = "dji_csv_srt" if has_srt else "dji_csv"

    flight_data = {
        "schema_version": SCHEMA_VERSION,
        "flight_id": flight_id,
        "source": {
            "telemetry_file": pair["csv_path"].name,
            "srt_file": pair["srt_path"].name if pair["srt_path"] else None,
            "video_file": None,
            "original_format": original_format,
        },
        "summary": summary.compute(csv_df),
        "hover_points": hover.detect(csv_df, srt_df),
        "camera_events": camera.detect(srt_df),
        "track": build_track(csv_df, srt_df),
    }

    # 逆ジオコーディング
    if geocode_cache is not None:
        geocoder.enrich_flight(flight_data, geocode_cache)

    return flight_data


def main():
    parser = argparse.ArgumentParser(description="ドローン飛行ログをYANYANMA形式に変換")
    parser.add_argument("input_dir", help="入力ディレクトリ（例: data/1-石川県）")
    parser.add_argument("output_dir", help="出力ディレクトリ")
    parser.add_argument("--region", required=True, help="地域英名（例: ishikawa）")
    parser.add_argument("--no-geocode", action="store_true", help="逆ジオコーディングをスキップ")
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)

    # スキーマ読み込み
    schema_dir = Path(__file__).parent.parent / "schema"
    flight_log_schema = None
    flight_index_schema = None
    if schema_dir.exists():
        fl_path = schema_dir / "flight_log.schema.json"
        fi_path = schema_dir / "flight_index.schema.json"
        if fl_path.exists():
            with open(fl_path, encoding="utf-8") as f:
                flight_log_schema = json.load(f)
        if fi_path.exists():
            with open(fi_path, encoding="utf-8") as f:
                flight_index_schema = json.load(f)

    # ジオコーディングキャッシュ
    geocode_cache = None
    cache_path = output_dir / ".geocode_cache.json"
    if not args.no_geocode:
        geocode_cache = geocoder.load_cache(cache_path)
        print(f"Geocoding: enabled (cache: {len(geocode_cache)} entries)")
    else:
        print("Geocoding: disabled")

    # ファイルペアを探索
    pairs = find_flight_pairs(input_dir)
    print(f"Found {len(pairs)} flight(s)")

    # 各フライトを処理
    all_flights = []
    for pair in pairs:
        flight_id = generate_flight_id(pair["prefix"], args.region)
        print(f"  Processing: {flight_id}")

        flight_data = process_flight(pair, args.region, flight_log_schema, geocode_cache)

        # 個別JSON出力
        out_path = writer.write_flight(flight_data, output_dir, flight_log_schema)
        print(f"    → {out_path}")

        all_flights.append(flight_data)

    # ジオコーディングキャッシュを保存
    if geocode_cache is not None:
        geocoder.save_cache(geocode_cache, cache_path)
        print(f"Cache saved: {len(geocode_cache)} entries")

    # index.json出力
    index_path = writer.write_index(all_flights, output_dir, flight_index_schema)
    print(f"  Index: {index_path}")
    print(f"Done: {len(all_flights)} flight(s) converted")


if __name__ == "__main__":
    main()
