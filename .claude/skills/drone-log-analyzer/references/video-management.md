# 動画ファイル管理手順

## 動画ファイルの配置

### 配置先
```
data/{region}/
  石川-ルート1-2-HD.mp4
  石川-ルート2-1-HD.mp4
  ...
```

`{region}` はデータセットの地域名（例: `1-石川県`）。

### 命名規則
DJIの動画ファイル名とフライトIDの対応:
```
flight_id: ishikawa-route{N}-{seq}
動画ファイル: 石川-ルート{N}-{seq}-HD.mp4
```

## .gitignore への登録

動画ファイルは大容量のためGit管理外とする。`.gitignore` に以下を追加:
```
*.mp4
```

## フライトJSONの video_file 参照更新

各フライトJSONの `source.video_file` フィールドを更新する:

1. `data/{region}/` ディレクトリ内の動画ファイル一覧を取得
2. flight_id から期待される動画ファイル名を生成（上記命名規則に従う）
3. 動画ファイルが存在する場合、`source.video_file` にファイル名を設定
4. 存在しない場合は `null` のまま

### 更新コード例
```python
import json, os

for flight_json in glob.glob("output/flights/*.json"):
    d = json.load(open(flight_json))
    parts = d["flight_id"].replace("ishikawa-route", "")
    video_name = f"石川-ルート{parts}-HD.mp4"

    if os.path.exists(f"data/1-石川県/{video_name}"):
        d["source"]["video_file"] = video_name
        json.dump(d, open(flight_json, "w"), ensure_ascii=False, indent=2)
```

## 注意事項

- 全フライトに動画があるとは限らない（DJIの録画設定やSDカード容量による）
- 動画ファイル名の命名パターンはデータセットにより異なる場合がある
- 動画のコピー元パスはユーザーに確認すること
