# フライト連続性分析

## DJI録画分割の特性

DJIドローンは約228秒（3分48秒）でテレメトリCSVとSRTを自動分割する。
これにより、1回の連続飛行が複数のフライトIDに分割される。

## 同一ルート内の連続性判定

以下の条件をすべて満たす場合、同一連続飛行と判定する:

1. **flight_id のroute番号が同一** （例: route1-1 と route1-2）
2. **前フライトの end_point と次フライトの start_point が近接** （通常 < 1m）
3. **前フライトの end_time_utc と次フライトの start_time_utc の差が数秒以内** （通常 0〜2秒）

## ルート間の判定

ルート番号が異なるフライト間:
- 時刻差: 通常 3〜10分（バッテリー交換、離陸地点の移動に相当）
- 距離差: 数十〜数百m（次の調査地点への移動）

## 分析手順

1. 全フライトの `summary.start_point`, `summary.end_point`, `summary.start_time_utc`, `summary.end_time_utc` を取得
2. 同一ルート内のフライトを時系列順に並べる
3. 隣接フライトの end_point → start_point の距離と時刻差を計算
4. 距離差 < 100m かつ 時刻差 < 5秒 → 録画分割
5. 距離差 < 1km かつ 時刻差 < 15分 → ルート間移動

## 距離計算

Haversine公式で2点間の距離を算出する。簡易計算:
```
Δlat_m = (lat2 - lat1) * 111320
Δlon_m = (lon2 - lon1) * 111320 * cos(lat1 * π/180)
distance = sqrt(Δlat_m² + Δlon_m²)
```
