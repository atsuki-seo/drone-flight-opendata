# ffmpegによる映像・画像抽出

## 前提条件

- ffmpeg がインストール済みであること
- フライトJSONの `source.video_file` が設定済みであること（`video-management.md` 参照）

## オフセット時間の計算

動画の先頭 = フライト開始時刻（`summary.start_time_utc`）と対応する。
各イベントの動画内オフセット:
```
offset_sec = event.time_utc - flight.summary.start_time_utc
```

## ホバリングクリップの抽出

### 動画クリップ（前後1秒のパディング付き）
```bash
ffmpeg -y -ss {max(0, offset_sec - 1)} -i {video_path} \
  -t {duration_sec + 2} -c copy -an \
  output/extracts/hover_clips/{flight_id}_hover{idx}.mp4
```

- `-c copy`: 再エンコードなし（高速）
- `-an`: 音声除去

### 代表フレーム画像（ホバリング中間地点）
```bash
ffmpeg -y -ss {offset_sec + duration_sec / 2} -i {video_path} \
  -frames:v 1 -q:v 2 \
  output/extracts/hover_frames/{flight_id}_hover{idx}.jpg
```

- `-q:v 2`: JPEG品質（1=最高、31=最低）

## カメライベントフレームの抽出

```bash
ffmpeg -y -ss {offset_sec} -i {video_path} \
  -frames:v 1 -q:v 2 \
  output/extracts/camera_event_frames/{flight_id}_cam{idx}.jpg
```

## 出力ディレクトリ構成

```
output/extracts/
  hover_clips/                    # ホバリング動画クリップ
    {flight_id}_hover{idx}.mp4
  hover_frames/                   # ホバリング代表フレーム
    {flight_id}_hover{idx}.jpg
  camera_event_frames/            # カメライベントフレーム
    {flight_id}_cam{idx}.jpg
  extract_manifest.json           # メタデータ（extract-manifest.md 参照）
```

## 命名規則

- `{flight_id}`: フライト識別子（例: `ishikawa-route1-2`）
- `{idx}`: フライト内でのインデックス（0始まり）
- ホバリング: `_hover{idx}`
- カメライベント: `_cam{idx}`

## 注意事項

- `source.video_file` が null のフライトはスキップする
- `-ss` を `-i` の前に置くことで高速シーク（キーフレームベース）
- クリップの `-c copy` は再エンコード不要で高速だが、キーフレーム境界で若干のずれが生じる場合がある
