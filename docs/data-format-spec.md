# データフォーマット仕様書

本文書は、YANYANMAが処理する入力データ（DJI ドローンテレメトリ）と出力データのフォーマットを定義する。

## 1. ディレクトリ構造

### 入力データ

```
data/
└── {N}-{地域名}/          # 例: 1-石川県
    ├── ルート{M}/          # 例: ルート1
    │   ├── {地域}-ルート{M}-{K}-テレメトリ.csv
    │   └── {地域}-ルート{M}-{K}.SRT
    └── {地域}-ルート{M}-{K}-HD.mp4   # ルートフォルダの親に配置
```

- `{N}`: 連番（整数）
- `{地域名}`: 日本語の地域名（例: 石川県）
- `{地域}`: 地域名の短縮形（例: 石川）
- `{M}`: ルート番号（整数）
- `{K}`: 同一ルート内のフライト番号（整数、1始まり）

### 出力データ

```
output/
├── index.json                        # 全フライト一覧
├── .geocode_cache.json               # 逆ジオコーディングキャッシュ
├── flights/
│   └── {flight_id}.json              # 個別フライト詳細
└── extracts/
    ├── extract_manifest.json         # 抽出アセット一覧
    ├── hover_frames/{flight_id}_hover{N}.jpg
    ├── hover_clips/{flight_id}_hover{N}.mp4
    └── camera_event_frames/{flight_id}_cam{N}.jpg
```

## 2. CSVテレメトリファイル

### ファイル命名

`{地域}-ルート{M}-{K}-テレメトリ.csv`（例: `石川-ルート1-1-テレメトリ.csv`）

### カラム定義

| # | カラム名 | 型 | 単位 | null可 | 説明 |
|---|---------|-----|------|--------|------|
| 1 | `Datetime (UTC)` | string | ISO 8601 | No | タイムスタンプ（例: `2024-09-25T01:34:54.762000+00:00`） |
| 2 | `Latitude` | float | 度（WGS84） | No | 緯度（小数点以下6桁精度） |
| 3 | `Longitude` | float | 度（WGS84） | No | 経度（小数点以下6桁精度） |
| 4 | `GPS Altitude (ft MSL)` | float | フィート | No | GPS高度（平均海面基準）。コンバータでメートルに変換（×0.3048） |
| 5 | `Satellites` | int | - | Yes | 捕捉衛星数。機種によっては全行空欄 |
| 6 | `Horizontal Accuracy Estimate (+/- ft)` | float | フィート | Yes | 水平精度推定値。機種依存で空欄の場合あり |
| 7 | `Vertical Accuracy Estimate (+/- ft)` | float | フィート | Yes | 垂直精度推定値。機種依存で空欄の場合あり |
| 8 | `X Velocity (m/s)` | float | m/s | No | X軸速度（東西方向） |
| 9 | `Y Velocity (m/s)` | float | m/s | No | Y軸速度（南北方向） |
| 10 | `Z Velocity (m/s)` | float | m/s | No | Z軸速度（垂直方向、正=上昇） |
| 11 | `Speed (m/s)` | float | m/s | No | 対地速度（3軸合成） |
| 12 | `Velocity Accuracy Estimate (+/- m/s)` | float | m/s | Yes | 速度精度推定値。機種依存で空欄の場合あり |

### 記録特性

- **記録間隔**: 約1秒（正確にはミリ秒単位でばらつきあり）
- **タイムスタンプ形式**: ISO 8601 UTC、ミリ秒精度、タイムゾーン `+00:00` 付き
- **エンコーディング**: UTF-8
- **区切り文字**: カンマ（CSV）
- **ヘッダ行**: あり（1行目）
- **空欄の扱い**: カンマ間に値なし（例: `,,`）

### サンプル

```csv
Datetime (UTC),Latitude,Longitude,GPS Altitude (ft MSL),Satellites,Horizontal Accuracy Estimate (+/- ft),Vertical Accuracy Estimate (+/- ft),X Velocity (m/s),Y Velocity (m/s),Z Velocity (m/s),Speed (m/s),Velocity Accuracy Estimate (+/- m/s)
2024-09-25T01:34:54.762000+00:00,37.308839,136.797038,237.06036745312002,,,,0.0,0.0,0.0,0.0,
2024-09-25T01:34:55.795000+00:00,37.308839,136.797038,237.06036745312002,,,,0.0,0.0,-0.0,0.0,
```

## 3. SRTサブタイトルファイル

### ファイル命名

`{地域}-ルート{M}-{K}.SRT`（例: `石川-ルート1-1.SRT`）

### ブロック構造

SubRip (SRT) 形式で、各ブロックは以下の構成:

```
{フレーム番号}
{開始タイムコード} --> {終了タイムコード}
<font size="28">FrameCnt: {N}, DiffTime: {ms}ms
{ローカル日時}
[iso: {値}] [shutter: {値}] [fnum: {値}] [ev: {値}] [color_md : {値}] [ae_meter_md: {値}] [focal_len: {値}] [dzoom_ratio: {値}], [latitude: {値}] [longitude: {値}] [rel_alt: {値} abs_alt: {値}] [gb_yaw: {値} gb_pitch: {値} gb_roll: {値}] </font>

```

各ブロックは空行で区切られる。

### タイムコード形式

`HH:MM:SS,mmm`（例: `00:00:00,033`）

- 33ms間隔（約30fps）
- DiffTime: 前フレームからの経過時間（33ms or 34ms）

### フィールド定義

| フィールド | 型 | 単位 | 説明 |
|-----------|-----|------|------|
| `FrameCnt` | int | - | 累積フレーム番号（1始まり） |
| `DiffTime` | int | ms | フレーム間隔（通常33-34ms） |
| ローカル日時 | string | - | `YYYY-MM-DD HH:MM:SS.mmm` 形式。タイムゾーン情報なし（JSTとして解釈し、UTC変換時に-9時間） |
| `iso` | int | - | ISO感度（例: 100） |
| `shutter` | string | - | シャッタースピード（例: `1/2818.96`） |
| `fnum` | float | - | F値（例: 2.8） |
| `ev` | int | - | 露出補正値 |
| `color_md` | string | - | カラーモード（例: `default`） |
| `ae_meter_md` | int | - | 測光モード |
| `focal_len` | float | mm | 焦点距離（例: 24.00） |
| `dzoom_ratio` | float | - | デジタルズーム倍率（例: 1.00） |
| `latitude` | float | 度（WGS84） | 緯度 |
| `longitude` | float | 度（WGS84） | 経度 |
| `rel_alt` | float | m | 離陸地点からの相対高度 |
| `abs_alt` | float | m | 絶対高度（海抜） |
| `gb_yaw` | float | 度 | ジンバルヨー角（水平方向） |
| `gb_pitch` | float | 度 | ジンバルピッチ角（上下方向） |
| `gb_roll` | float | 度 | ジンバルロール角（傾き） |

### 処理時の注意

- 30fpsデータを1秒間隔にダウンサンプリング（先頭フレーム採用）
- ローカル時刻はJST（UTC+9）。変換時に-9時間でUTCへ
- `gb_yaw` の1秒間の変化量が15度以上の場合、カメライベントとして検出

## 4. MP4動画ファイル

### ファイル命名

`{地域}-ルート{M}-{K}-HD.mp4`（例: `石川-ルート1-2-HD.mp4`）

- HD解像度（1080p以上）
- 全フライトに動画があるとは限らない
- 容量が大きいため `.gitignore` で除外

## 5. 出力データフォーマット

### Flight Log / Flight Index

JSON Schema で定義済み:

- [`schema/flight_log.schema.json`](../schema/flight_log.schema.json) — 個別フライト
- [`schema/flight_index.schema.json`](../schema/flight_index.schema.json) — インデックス

### Extract Manifest (`extract_manifest.json`)

ホバリングクリップとカメライベントフレームの抽出結果を管理するマニフェスト。

```json
{
  "hovers": [
    {
      "flight_id": "string",        // フライトID
      "hover_idx": 0,               // ホバーポイントのインデックス
      "address": "string",          // 住所（逆ジオコーディング結果）
      "offset_sec": 0.0,            // 動画開始からのオフセット（秒）
      "duration_sec": 5.0,          // クリップの長さ（秒）
      "clip_file": "hover_clips/{flight_id}_hover{N}.mp4",
      "frame_file": "hover_frames/{flight_id}_hover{N}.jpg",
      "lat": 0.0,                   // 緯度
      "lon": 0.0,                   // 経度
      "alt_m": 0.0,                 // 高度（m）
      "camera_yaw_deg": 0.0         // カメラヨー角（度）
    }
  ],
  "camera_events": [
    {
      "flight_id": "string",        // フライトID
      "event_idx": 0,               // イベントインデックス
      "offset_sec": 0.0,            // 動画開始からのオフセット（秒）
      "yaw_from_deg": 0.0,          // 変化前のヨー角（度）
      "yaw_to_deg": 0.0,            // 変化後のヨー角（度）
      "delta_deg": 0.0,             // ヨー角変化量（度）
      "frame_file": "camera_event_frames/{flight_id}_cam{N}.jpg",
      "lat": 0.0,                   // 緯度
      "lon": 0.0                    // 経度
    }
  ]
}
```

### Geocode Cache (`.geocode_cache.json`)

国土地理院逆ジオコーダAPIの結果キャッシュ。

- **キー形式**: `{lat:.4f}_{lon:.4f}`（小数点以下4桁に丸めた緯度経度）
- **値**: 日本語住所文字列（例: `"石川県輪島市門前町浦上"`）

```json
{
  "37.3088_136.7970": "石川県輪島市門前町浦上",
  "37.3140_136.7942": "石川県輪島市門前町浦上"
}
```
