# YANYANMA

**Yet Another Navigation Yield: Aerial Navigation Mapping & Analytics**

> 頭文字: **Y**-**A**-**N**-**Y**-**A**-**N**-**M**-**A** → ヤンヤンマ

ドローン飛行ログを LLM が分析しやすいオープンデータに変換するための規格とツール。

## Background

災害対応で収集されるドローン飛行ログ（DJI CSV/SRT等）は以下の課題を抱えている:

| 課題 | 詳細 |
|---|---|
| メーカーロックイン | DJI, Skydio, Autel 等でCSVカラムが異なる |
| 単位混在 | 高度がft、速度がm/s、精度がft等 |
| 冗長データ | SRTは30fpsで記録（1秒あたり同一情報が30行） |
| コンテキスト欠如 | 「なぜ飛んだか」「どのエリアを調査したか」の情報がない |
| LLM非対応 | 数値CSVの羅列はトークン効率が悪く、意味を読み取りにくい |

本仕様は、これらの生データを **LLM（Function Calling / Tool Use）で分析しやすい統一フォーマット** に変換するための規格を定義する。

## フォーマット概要

2層構造で設計されている:

- **Layer 1: Flight Index** (`index.json`) — 全フライトの一覧。LLMに最初に渡して全体像を把握させる。
- **Layer 2: Flight Log** (`flights/{flight_id}.json`) — 個別フライトの詳細。必要なフライトだけ参照する。

### スキーマ定義

OpenAI Function Calling 互換の JSON Schema 形式で定義:

- [`schema/flight_log.schema.json`](schema/flight_log.schema.json) — 1フライト分のデータスキーマ
- [`schema/flight_index.schema.json`](schema/flight_index.schema.json) — インデックスのスキーマ

### 出力例

- [`examples/ishikawa-route1-1.json`](examples/ishikawa-route1-1.json) — 個別フライトの出力例
- [`examples/index.json`](examples/index.json) — インデックスの出力例

## 規約ルール

データフォーマット規約（単位、欠損値の扱い）、ホバリング判定基準、カメライベント判定基準、スキーマ規約は [`.claude/rules/`](.claude/rules/) にルールファイルとして定義されている。

## 同梱データ

`data/sample/` に、コンバータの動作確認用ダミーデータを同梱している。

| ファイル | 内容 |
|---------|------|
| `サンプル-ルート1-1-テレメトリ.csv` | 10行のダミーテレメトリ（架空座標） |
| `サンプル-ルート1-1.SRT` | 300フレーム（10秒分）のダミーSRT |

### 変換実行例

```bash
python -m converter.main data/sample output --region sample --no-geocode
```

### 入力データフォーマット

CSV/SRTの詳細なフォーマット仕様は [`docs/data-format-spec.md`](docs/data-format-spec.md) を参照。

## 実装

コンバータの実装設計は [`docs/implementation-guide.md`](docs/implementation-guide.md) を参照。

## Claude Code 連携

本リポジトリは Claude Code のルール・スキル機能と統合されている:

- `.claude/rules/` — データフォーマット規約、判定基準等をルールとして定義
- `.claude/skills/drone-log-analyzer/` — 変換済みJSONの分析時にスキーマをリファレンスとして自動適用

## License

TBD
