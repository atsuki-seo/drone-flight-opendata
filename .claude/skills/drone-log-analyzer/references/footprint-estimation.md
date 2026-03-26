# 撮影範囲（footprint）の推定

## DJIカメラ仕様

DJI Mavic 2 Enterprise Advanced（想定機種）:
- 水平FOV（HFOV）: 77度
- 垂直FOV（VFOV）: 60度

## 入力パラメータ

各ホバリング地点について:
- `lat`, `lon`: ドローンの位置
- `alt_m`: 高度（MSL、メートル）
- `camera_yaw_deg`: カメラの方位角（度、北=0）
- `camera_pitch_deg`: カメラの俯角（0=水平、-90=真下）。データがない場合は -45度を仮定

## 計算手法

### 1. カメラ中心の地上距離
```
pitch_rad = abs(pitch_deg) をラジアンに変換
center_ground_dist = alt_m / tan(pitch_rad)
```

ピッチが水平に近い場合（> -5度）は `alt_m * 5` でキャップする。

### 2. FOVの近端・遠端距離
```
half_v = VFOV / 2 をラジアンに変換
pitch_near = |pitch_rad| + half_v  (近端: より真下方向)
pitch_far  = |pitch_rad| - half_v  (遠端: より水平方向)

near_dist = alt_m / tan(pitch_near)
far_dist  = alt_m / tan(pitch_far)   ※ alt_m * 10 でキャップ
```

### 3. 中心距離での横幅
```
half_h = HFOV / 2 をラジアンに変換
width_at_center = 2 * center_ground_dist * tan(half_h)
```

### 4. 緯度経度への変換
```
m_per_deg_lat = 111320
m_per_deg_lon = 111320 * cos(lat * π / 180)

# カメラ方向（yaw）に沿って近端/遠端の4隅を計算
# 各隅: (距離, 横幅方向の符号) × yaw回転
dn = dist * cos(yaw_rad) + sign * (width/2) * (-sin(yaw_rad))
de = dist * sin(yaw_rad) + sign * (width/2) * cos(yaw_rad)

corner_lat = lat + dn / m_per_deg_lat
corner_lon = lon + de / m_per_deg_lon
```

### 5. 出力
- 撮影中心までの地上距離（m）
- 近端〜遠端距離（m）
- 中心での横幅（m）
- 4隅の座標とbbox（north, south, east, west）

## 注意事項

- ピッチ角データがない場合の -45度仮定は概算であり、実際の俯角が異なれば範囲は大きく変わる
- 真下撮影（-90度）の場合、footprintは高度のみに依存し比較的小さい
- 浅い角度（-20度）の場合、遠端が非常に遠くなる
- camera_yaw_deg が null の場合は北（0度）を仮定して計算する
