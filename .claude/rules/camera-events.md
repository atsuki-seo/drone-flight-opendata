---
paths:
  - "converter/analyzers/**"
---

# カメライベント判定基準

- ジンバルyawの1秒間の変化が **15度以上** の地点をカメライベントとして検出する
- 閾値は `converter/config.py` で一元管理する
- SRTデータが存在しない場合、camera_events は空配列 `[]` とする
