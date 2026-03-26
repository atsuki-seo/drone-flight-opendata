"""市区町村コード辞書を生成するスクリプト

総務省「全国地方公共団体コード」のExcelファイルをダウンロードし、
muniCd（5桁） → 「都道府県名+市区町村名」のJSON辞書を生成する。

Usage:
    python -m converter.scripts.generate_muni_codes
"""

import json
import urllib.request
from pathlib import Path

import xlrd

SOUMU_XLS_URL = "https://www.soumu.go.jp/main_content/000925835.xls"
OUTPUT_PATH = Path(__file__).parent.parent / "data" / "muni_codes.json"


def download_xls(url: str) -> bytes:
    """Excelファイルをダウンロード"""
    print(f"Downloading: {url}")
    req = urllib.request.Request(url, headers={"User-Agent": "YANYANMA-converter"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read()


def parse_xls(xls_data: bytes) -> dict[str, str]:
    """Excelをパースして muniCd → 名称 の辞書を返す"""
    wb = xlrd.open_workbook(file_contents=xls_data)
    codes = {}

    for sheet_idx in range(wb.nsheets):
        ws = wb.sheet_by_index(sheet_idx)
        for row_idx in range(1, ws.nrows):
            code_raw = ws.cell_value(row_idx, 0)
            pref = ws.cell_value(row_idx, 1).strip()
            city = ws.cell_value(row_idx, 2).strip()

            if not code_raw or not pref:
                continue

            # 6桁コードの先頭5桁 = muniCd
            code_str = str(code_raw).strip()
            if len(code_str) == 6:
                muni_cd = code_str[:5]
            elif len(code_str) == 5:
                muni_cd = code_str
            else:
                continue

            # 都道府県のみの行（市区町村名が空）はスキップ
            if not city:
                continue

            codes[muni_cd] = f"{pref}{city}"

    return codes


def main():
    xls_data = download_xls(SOUMU_XLS_URL)
    codes = parse_xls(xls_data)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(codes, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print(f"Generated: {OUTPUT_PATH} ({len(codes)} entries)")


if __name__ == "__main__":
    main()
