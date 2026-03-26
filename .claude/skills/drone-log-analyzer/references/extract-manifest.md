# extract_manifest.json の仕様

## 出力先

`output/extracts/extract_manifest.json`

## JSON構造

```json
{
  "hovers": [
    {
      "flight_id": "ishikawa-route1-2",
      "hover_idx": 0,
      "address": "石川県輪島市門前町浦上",
      "offset_sec": 41.0,
      "duration_sec": 5.0,
      "clip_file": "hover_clips/ishikawa-route1-2_hover0.mp4",
      "frame_file": "hover_frames/ishikawa-route1-2_hover0.jpg",
      "lat": 37.315072,
      "lon": 136.793466,
      "alt_m": 150.6,
      "camera_yaw_deg": -29.1
    }
  ],
  "camera_events": [
    {
      "flight_id": "ishikawa-route1-2",
      "event_idx": 0,
      "offset_sec": 76.0,
      "yaw_from_deg": -28.3,
      "yaw_to_deg": -63.3,
      "delta_deg": -35.0,
      "frame_file": "camera_event_frames/ishikawa-route1-2_cam0.jpg",
      "lat": 37.316014,
      "lon": 136.792827
    }
  ]
}
```

## hovers[] のフィールド

| フィールド | 型 | 説明 |
|-----------|-----|------|
| `flight_id` | string | フライト識別子 |
| `hover_idx` | integer | フライト内でのホバリングインデックス（0始まり） |
| `address` | string | 逆ジオコーディング住所 |
| `offset_sec` | number | フライト開始からの秒数 |
| `duration_sec` | number | ホバリング継続時間（秒） |
| `clip_file` | string | 動画クリップへの相対パス（extracts/からの相対） |
| `frame_file` | string | 代表フレーム画像への相対パス |
| `lat` | number | 緯度 |
| `lon` | number | 経度 |
| `alt_m` | number | 高度（MSL、メートル） |
| `camera_yaw_deg` | number/null | カメラ方位角（度） |

## camera_events[] のフィールド

| フィールド | 型 | 説明 |
|-----------|-----|------|
| `flight_id` | string | フライト識別子 |
| `event_idx` | integer | フライト内でのイベントインデックス（0始まり） |
| `offset_sec` | number | フライト開始からの秒数 |
| `yaw_from_deg` | number | 変化前の方位角（度） |
| `yaw_to_deg` | number | 変化後の方位角（度） |
| `delta_deg` | number | 変化量（度） |
| `frame_file` | string | フレーム画像への相対パス |
| `lat` | number | 緯度 |
| `lon` | number | 経度 |

## ファイルパスの規則

- `clip_file`, `frame_file` は `output/extracts/` からの相対パスで記録する
- 動画がないフライトのホバリング/イベントは含めない
