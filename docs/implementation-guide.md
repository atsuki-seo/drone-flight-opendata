# 実装ガイド

ドローン飛行ログを YANYANMA 形式に変換するコンバータの実装設計。

## 入力データ

変換対象のデータは `data/1-石川県/` に配置されている。

```
data/1-石川県/
├── ルート1/
│   ├── 石川-ルート1-1-テレメトリ.csv
│   ├── 石川-ルート1-1.SRT
│   └── ...
├── ルート2/
│   └── ...
└── ルート11/
    └── ...
```

- CSV: テレメトリデータ（毎秒記録、高度はft、速度はm/s）
- SRT: カメラメタデータ（30fps記録、ジンバル角度・カメラ設定含む）
- CSVとSRTはファイル名のプレフィックスでペアリングする（例: `石川-ルート1-1`）
- SRTが存在しないCSVもある（ルート6, ルート11の一部）

実行例:
```bash
python -m converter.main data/1-石川県 output
```

## ディレクトリ構成

```
converter/
├── __init__.py
├── main.py                     # CLI エントリポイント
├── config.py                   # 閾値等の設定値
├── parsers/
│   ├── __init__.py
│   ├── dji_csv.py              # DJI CSV パーサー
│   └── dji_srt.py              # DJI SRT パーサー
├── analyzers/
│   ├── __init__.py
│   ├── summary.py              # サマリー計算
│   ├── hover.py                # ホバリング地点検出
│   └── camera.py               # カメライベント検出
├── enrichers/
│   ├── __init__.py
│   └── geocoder.py             # 逆ジオコーディング
└── output/
    ├── __init__.py
    └── writer.py               # JSON出力 + バリデーション
```

## データフロー

```
[入力]                   [パース]              [分析]              [付加]           [出力]
DJI CSV ─→ dji_csv.py ─→ DataFrame ─┐
                                     ├─→ summary.py ─→ enricher ─→ writer.py ─→ JSON
DJI SRT ─→ dji_srt.py ─→ DataFrame ─┘   hover.py       geocoder
                                          camera.py
```

## 各モジュールの責務

### `converter/config.py`

```python
"""コンバータ設定"""
HOVER_SPEED_THRESHOLD_MS = 0.3   # ホバリング判定速度閾値（m/s）
HOVER_MIN_DURATION_SEC = 5       # ホバリング最小継続時間（秒）
CAMERA_YAW_THRESHOLD_DEG = 15    # カメラ方向変化の閾値（度）
TRACK_INTERVAL_SEC = 1           # trackの出力間隔（秒）
FT_TO_M = 0.3048                 # フィート → メートル変換係数
SRT_TIMEZONE_OFFSET_HOURS = 9    # SRTタイムスタンプのUTCオフセット（日本: +9）
```

### `converter/parsers/dji_csv.py`

| 項目 | 内容 |
|---|---|
| 入力 | DJI テレメトリCSVファイルパス |
| 出力 | pandas DataFrame（カラム名正規化・単位変換済み） |

処理:
1. CSVを `pandas.read_csv` で読み込み
2. カラム名を正規化（スネークケース）
3. 高度: ft → m に変換（x 0.3048）
4. 精度: ft → m に変換（x 0.3048）
5. タイムスタンプをUTC datetimeに変換
6. 欠損値はNaN/Noneのまま保持（JSON出力時にwriter.pyでnullに変換）

### `converter/parsers/dji_srt.py`

| 項目 | 内容 |
|---|---|
| 入力 | DJI SRTファイルパス |
| 出力 | pandas DataFrame（1秒間隔にダウンサンプリング済み） |

処理:
1. 正規表現でSRTブロックをパース: `r'\[(\w+):\s*([^\]]+)\]'`
2. 抽出フィールド: `latitude`, `longitude`, `rel_alt`, `abs_alt`, `gb_yaw`, `gb_pitch`, `gb_roll`, `iso`, `shutter`, `fnum`, `focal_len`, `dzoom_ratio`
3. 30fps → 1秒間隔にダウンサンプリング（各秒の先頭フレームを採用）
4. タイムスタンプはJST（UTC+9、タイムゾーン情報なし）として解釈し、9時間減算してUTC datetimeに変換

注: CSVとSRTのマージはタイムスタンプ（秒精度）をキーに左結合（CSV基準）。
タイムスタンプが完全一致しない場合は最近傍マッチ（`pandas.merge_asof`、tolerance=1s）を使用。

### `converter/analyzers/summary.py`

| 項目 | 内容 |
|---|---|
| 入力 | CSVパース済みDataFrame |
| 出力 | summary dict |

処理:
1. `date`: 最初のタイムスタンプからdate部分を取得
2. `start_time_utc` / `end_time_utc`: 最初/最後のタイムスタンプ
3. `duration_sec`: end - start の秒数
4. `start_point` / `end_point`: 最初/最後の行のlat, lon, alt
5. `bbox`: lat/lonのmin/maxから算出
6. `total_distance_m`: 隣接点間のhaversine距離を累計
7. `max_alt_m` / `min_alt_m`: altカラムのmax/min
8. `max_speed_ms` / `avg_speed_ms`: speedカラムのmax/mean
9. `satellites_avg`: satellitesカラムのmean（NaNなら null）
10. `gps_accuracy_h_m`: horizontal accuracyのmean（NaNなら null）

#### haversine距離計算（外部ライブラリ不要）

```python
import math

def haversine(lat1, lon1, lat2, lon2):
    """2点間の距離をメートルで返す"""
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlam/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
```

### `converter/analyzers/hover.py`

| 項目 | 内容 |
|---|---|
| 入力 | CSVパース済みDataFrame + 閾値設定 |
| 出力 | hover_points list[dict] |

処理:
1. `speed < HOVER_SPEED_THRESHOLD` (0.3 m/s) の行にフラグ
2. 連続するフラグ区間をグループ化
3. `HOVER_MIN_DURATION` (5秒) 以上の区間を抽出
4. 各区間の代表点（中央値のlat/lon）、開始時刻、継続時間を計算
5. SRTデータがあればその時刻の `camera_yaw` を付加

### `converter/analyzers/camera.py`

| 項目 | 内容 |
|---|---|
| 入力 | SRTパース済みDataFrame + 閾値設定 |
| 出力 | camera_events list[dict] |

処理:
1. `gb_yaw` の1秒間の差分を計算
2. 差分の絶対値 > `CAMERA_YAW_THRESHOLD` (15度) の地点を抽出
3. 各イベントの time, lat, lon, yaw_from, yaw_to を記録

### `converter/enrichers/geocoder.py`

| 項目 | 内容 |
|---|---|
| 入力 | 緯度経度の座標（代表点のみ） |
| 出力 | 住所文字列 |

処理:
1. geopyの `Nominatim`（無料、レート制限あり）を使用
2. 事前変換モード: 全座標を一括変換してキャッシュ保存
3. リアルタイムモード: 必要時にAPI呼び出し（1秒間隔のレート制限遵守）
4. API呼び出し失敗時は `null` を返す

### `converter/output/writer.py`

| 項目 | 内容 |
|---|---|
| 入力 | 全分析結果 |
| 出力 | JSONファイル（フライト個別 + インデックス） |

処理:
1. 各フライトのデータを `flight_log` スキーマに組み立て
2. `jsonschema` でバリデーション
3. bboxの整合性チェック（north >= south, east >= west）
4. `flights/` フォルダに個別JSON出力
5. 全フライトのsummaryを集約して `index.json` 出力
6. JSON出力時: `ensure_ascii=False`, `indent=2`
7. pandas NaN/None → JSON `null` に変換（`default`引数で処理）

### `converter/main.py`

```
CLI: python -m converter.main <input_dir> <output_dir>
```

処理フロー:
1. `input_dir` 配下のCSV/SRTファイルを探索
2. ファイル名から `flight_id` を生成
   - 形式: `{地域英名}-route{番号}-{フライト番号}`（例: `ishikawa-route1-1`）
   - 小文字英数字+ハイフンのみ使用（正規表現: `^[a-z][a-z0-9-]+$`）
   - 日本語ファイル名からの変換テーブルを config.py に定義
3. CSVとSRTをペアリング（同名ベースでマッチ）
4. 各ペアに対して: パース → 分析 → 付加 → 出力
   - `original_format` の決定: CSVのみ → `"dji_csv"`、CSV+SRT → `"dji_csv_srt"`
5. 全フライトの `index.json` を生成

## 依存ライブラリ

```
pandas>=2.0
geopy>=2.4
jsonschema>=4.20
```

## 実装優先度

### Must（コア）

1. `dji_csv.py` — CSVパーサー + 単位変換
2. `dji_srt.py` — SRTパーサー
3. `summary.py` — サマリー計算
4. `hover.py` — ホバリング検出
5. `camera.py` — カメライベント検出
6. `writer.py` — JSON出力 + JSON Schemaバリデーション
7. `main.py` — CLI

### Should（余裕があれば）

8. `geocoder.py` — 逆ジオコーディング
9. Streamlitによる可視化デモ

## 検証方法

1. `python -m converter.main ./課題1データ ./output` を実行
2. `output/index.json` が生成され、全フライトが列挙されていること
3. `output/flights/*.json` が各フライトごとに生成されていること
4. 任意のJSONファイルを `jsonschema` でバリデーションしてエラーがないこと
5. summaryの値が妥当か手動確認（飛行時間、距離、高度レンジ等）
6. hover_pointsが実際にCSVの低速区間と一致するか確認
