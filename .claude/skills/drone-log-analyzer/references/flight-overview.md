# フライト全体概要の把握

## 手順

1. `output/index.json` を読み込む
2. トップレベルの統計を確認: `total_flights`, `total_duration_sec`, `coverage_bbox`
3. `flights[]` 配列をルート別にグルーピングして集計する

## ルート別グルーピング

`flight_id` のパターン `{region}-route{N}-{seq}` からルート番号を抽出する。

```
ishikawa-route1-1  → route1
ishikawa-route1-2  → route1
ishikawa-route6-3  → route6
```

## 算出すべき統計

各ルートについて:
- フライト数
- 合計飛行時間（`duration_sec` の合計）
- 合計飛行距離（`total_distance_m` の合計）
- ホバリング回数合計（`hover_count` の合計）
- 主な地域（`region` の最頻値）

全体について:
- 飛行日の一覧（`date` のユニーク値）
- カバー範囲（`coverage_bbox`）
- 総飛行時間を分・時間に換算

## 出力フォーマット例

| ルート | フライト数 | 主な地域 | ホバリング計 |
|--------|-----------|----------|-------------|
| route1 | 3 | 門前町浦上 | 4 |
| route2 | 3 | 門前町浦上 | 5 |
| ... | ... | ... | ... |
