---
paths:
  - "schema/**"
---

# スキーマ規約

- OpenAI Function Calling 互換の JSON Schema 形式で記述する
- `$defs` で共通型（`geo_point`, `track_point`）を定義して再利用する
- `required` フィールドは最小限にする（nullable なオプションは required に含めない）
  - ただし、空配列 `[]` でも常に存在するフィールド（例: `hover_points`, `camera_events`）は required に含める
- `description` はLLMが各フィールドの意味を理解できるよう日本語で記述する
