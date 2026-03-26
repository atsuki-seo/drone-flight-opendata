"""JSON出力 + スキーマバリデーション"""

import json
import math
from datetime import datetime, timezone
from pathlib import Path

import jsonschema
import pandas as pd

from converter.config import SCHEMA_VERSION


def _json_default(obj):
    """pandas/numpy型のJSON変換"""
    if isinstance(obj, pd.Timestamp):
        return obj.strftime("%Y-%m-%dT%H:%M:%SZ")
    if isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
        return None
    if hasattr(obj, "item"):
        # numpy scalar → Python scalar
        return obj.item()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


def write_flight(flight_data: dict, output_dir: Path, schema: dict | None = None) -> Path:
    """個別フライトJSONを出力"""
    flights_dir = output_dir / "flights"
    flights_dir.mkdir(parents=True, exist_ok=True)

    flight_id = flight_data["flight_id"]
    out_path = flights_dir / f"{flight_id}.json"

    if schema:
        _validate(flight_data, schema)

    _write_json(flight_data, out_path)
    return out_path


def write_index(flights: list[dict], output_dir: Path, schema: dict | None = None) -> Path:
    """index.jsonを出力"""
    output_dir.mkdir(parents=True, exist_ok=True)

    total_duration = sum(f["summary"]["duration_sec"] for f in flights)

    # 全フライトを包含するbbox
    all_norths = [f["summary"]["bbox"]["north"] for f in flights]
    all_souths = [f["summary"]["bbox"]["south"] for f in flights]
    all_easts = [f["summary"]["bbox"]["east"] for f in flights]
    all_wests = [f["summary"]["bbox"]["west"] for f in flights]

    index_data = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "total_flights": len(flights),
        "total_duration_sec": round(total_duration, 1),
        "coverage_bbox": {
            "north": max(all_norths),
            "south": min(all_souths),
            "east": max(all_easts),
            "west": min(all_wests),
        },
        "flights": [_flight_summary(f) for f in flights],
    }

    if schema:
        _validate(index_data, schema)

    out_path = output_dir / "index.json"
    _write_json(index_data, out_path)
    return out_path


def _flight_summary(flight: dict) -> dict:
    """index用のフライトサマリーを生成"""
    s = flight["summary"]
    return {
        "flight_id": flight["flight_id"],
        "date": s["date"],
        "start_time_utc": s["start_time_utc"],
        "duration_sec": s["duration_sec"],
        "region": s.get("region"),
        "bbox": s["bbox"],
        "total_distance_m": s["total_distance_m"],
        "hover_count": len(flight["hover_points"]),
        "detail_file": f"flights/{flight['flight_id']}.json",
    }


def _validate(data: dict, schema: dict):
    """JSON Schemaでバリデーション"""
    # OpenAI Function Calling形式のスキーマから parameters を取り出す
    json_schema = schema.get("parameters", schema)
    jsonschema.validate(instance=data, schema=json_schema)


def _write_json(data: dict, path: Path):
    """JSONファイルを書き出す"""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=_json_default)
        f.write("\n")
