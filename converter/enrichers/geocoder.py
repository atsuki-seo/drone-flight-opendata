"""逆ジオコーディング（国土地理院 逆ジオコーダ）"""

import json
import time
import urllib.request
from pathlib import Path

from converter.config import GEOCODE_CACHE_PRECISION

GSI_ENDPOINT = "https://mreversegeocoder.gsi.go.jp/reverse-geocoder/LonLatToAddress"
MUNI_CODES_PATH = Path(__file__).parent.parent / "data" / "muni_codes.json"

_muni_codes: dict[str, str] | None = None


def _load_muni_codes() -> dict[str, str]:
    global _muni_codes
    if _muni_codes is None:
        with open(MUNI_CODES_PATH, encoding="utf-8") as f:
            _muni_codes = json.load(f)
    return _muni_codes


def _cache_key(lat: float, lon: float) -> str:
    """キャッシュキーを生成（小数点以下を丸めて同一地点の重複を防止）"""
    p = GEOCODE_CACHE_PRECISION
    return f"{lat:.{p}f}_{lon:.{p}f}"


def reverse_geocode(lat: float, lon: float, cache: dict[str, str]) -> str | None:
    """座標から住所文字列を返す。失敗時はNone。"""
    key = _cache_key(lat, lon)
    if key in cache:
        return cache[key]

    address = _call_gsi_api(lat, lon)
    if address is not None:
        cache[key] = address
    return address


def _call_gsi_api(lat: float, lon: float) -> str | None:
    """国土地理院の逆ジオコーダAPIを呼び出す"""
    url = f"{GSI_ENDPOINT}?lat={lat}&lon={lon}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "YANYANMA-converter"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None

    results = data.get("results")
    if not results:
        return None

    muni_cd = results.get("muniCd", "")
    lv01_nm = results.get("lv01Nm", "")

    # muniCd辞書から都道府県+市区町村名を取得
    muni_codes = _load_muni_codes()
    pref_city = muni_codes.get(muni_cd, "")

    if pref_city and lv01_nm:
        return f"{pref_city}{lv01_nm}"
    elif pref_city:
        return pref_city
    elif lv01_nm:
        return lv01_nm
    return None


def enrich_flight(flight_data: dict, cache: dict[str, str]) -> None:
    """flight_dataのregionとaddressを逆ジオコーディングで埋める"""
    # summary.region を start_point の座標で設定
    sp = flight_data["summary"]["start_point"]
    region = reverse_geocode(sp["lat"], sp["lon"], cache)
    flight_data["summary"]["region"] = region

    # hover_points[].address を各座標で設定
    for hp in flight_data["hover_points"]:
        address = reverse_geocode(hp["lat"], hp["lon"], cache)
        hp["address"] = address

    # API レート制限対策（1秒間隔）
    time.sleep(0.1)


def load_cache(path: Path) -> dict[str, str]:
    """キャッシュファイルを読み込む"""
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_cache(cache: dict[str, str], path: Path) -> None:
    """キャッシュファイルを保存"""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)
        f.write("\n")
