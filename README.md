# ニュース自動配信システム

毎朝7:00 JSTに AI業界・PC業界のニュースを自動収集・要約・配信するシステム。

## 特徴

- **完全無料**: LLMは Google Gemini 2.0 Flash 無料枠を使用（クレジットカード不要）
- **冪等設計**: 同じ日に複数回実行しても重複配信しない（SQLiteで管理）
- **プラガブルLLM**: Gemini / Ollama / LLMなし を config.yaml で切り替え可能

## セットアップ

### 1. 依存パッケージのインストール

```bash
pip install -e ".[dev]"
```

### 2. 設定ファイルの作成

```bash
cp .env.example .env
```

`.env` を編集してAPIキーを設定:

```env
# Google AI Studio: https://aistudio.google.com/ → "Get API key"（無料）
GEMINI_API_KEY=AIzaSy...
```

### 3. 動作確認（dry-run）

```bash
python -m src.main --dry-run
```

`output/digest_YYYY-MM-DD.md` が生成されれば成功。

### 4. 本番実行

```bash
python -m src.main
```

## 設定

`config.yaml` で以下を変更できます:

| 設定 | 説明 | デフォルト |
|------|------|-----------|
| `llm.provider` | LLMプロバイダ (`gemini`/`ollama`/`none`) | `gemini` |
| `llm.max_articles_per_category` | 1カテゴリの最大記事数 | `10` |
| `llm.model` | Geminiモデル名 | `gemini-2.0-flash` |
| `notification.slack_enabled` | Slack通知を有効化 | `true` |
| `notification.discord_enabled` | Discord通知を有効化 | `true` |
| `database.retention_days` | 送信済みURLの保持日数 | `30` |

## スケジューラー設定

### Windows タスクスケジューラー

1. タスクスケジューラーを開く
2. 「タスクの作成」→ 毎日 07:00
3. 操作: `python -m src.main`（プロジェクトディレクトリから実行）

### Cron (WSL/Linux)

```cron
# 毎朝7:00 JST (= UTC 22:00 前日)
0 22 * * * cd /path/to/project && python -m src.main >> logs/news.log 2>&1
```

## テスト

```bash
pytest tests/ -v
```

## LLMプロバイダの切り替え

`config.yaml` の `llm.provider` を変更:

```yaml
llm:
  provider: "none"   # LLMなし（RSS本文をそのまま使用）
```

### Ollamaを使う場合

1. https://ollama.com からOllamaをインストール
2. モデルをDL: `ollama pull qwen2.5:3b`
3. `config.yaml` を変更:
   ```yaml
   llm:
     provider: "ollama"
     ollama_model: "qwen2.5:3b"
   ```

## トラブルシュート

| 症状 | 対処 |
|------|------|
| `GEMINI_API_KEY が設定されていません` | `.env` に `GEMINI_API_KEY=...` を追加 |
| RSS取得で空リストになる | ソースURLが変更されていないか確認 |
| テストが失敗する | `pip install -e ".[dev]"` が完了しているか確認 |
| 出力ファイルが空 | キーワードがニュースにマッチしていない可能性。`config.yaml` のキーワードを確認 |
