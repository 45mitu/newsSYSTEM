# ブロッカーと戻ってからやること (BLOCKED.md)

## 実認証情報の設定（必須・あなたが戻ったらやること）

### 1. Gemini APIキーの取得と設定（完全無料）
1. https://aistudio.google.com/ にGoogleアカウントでアクセス
2. 右上の「Get API key」をクリック
3. 「Create API key」でキーを生成（無料、クレジットカード不要）
4. `.env` ファイルを作成し、以下を設定:
   ```
   GEMINI_API_KEY=AIzaSy取得したキー...
   ```
5. 動作確認: `python -m src.main` を実行（引数なし=本番モード）

### 2. Slack通知の設定（任意）
1. https://api.slack.com/messaging/webhooks でSlack Appを作成
2. Incoming Webhooksを有効化
3. webhook URLを `.env` に設定:
   ```
   SLACK_WEBHOOK_URL=https://hooks.slack.com/services/xxx/yyy/zzz
   ```
4. `config.yaml` で `notification.slack_enabled: true` を確認

### 3. Discord通知の設定（任意）
1. Discordサーバー設定 > 連携サービス > ウェブフック
2. 「新しいウェブフック」を作成
3. webhook URLを `.env` に設定:
   ```
   DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/xxx/yyy
   ```
4. `config.yaml` で `notification.discord_enabled: true` を確認

---

## スケジューラーの設定（本番運用に必須）

### Windows タスクスケジューラー（Windows 11環境）
1. タスクスケジューラーを開く（スタートメニューで「タスクスケジューラー」と検索）
2. 「タスクの作成」をクリック
3. 設定:
   - **全般タブ**: 名前 = "ニュース自動配信"
   - **トリガータブ**: 毎日 07:00 JST
   - **操作タブ**: プログラム = `python.exe`、引数 = `-m src.main`、開始場所 = プロジェクトディレクトリ

### Cron（WSL/Linux環境の場合）
```
# UTC+9 (JST) で毎朝7:00 = UTC 22:00
0 22 * * * cd /path/to/ニュース自動配信システム && /path/to/.venv/bin/python -m src.main >> logs/news.log 2>&1
```

---

## ニュースソースの確認

以下のRSSフィードが実際に取得できるか確認してください:
- arXivフィード（cs.AI/cs.LG）: レート制限がある場合、リトライロジックを検討
- 4Gamer: XMLフォーマットが変更されている場合、パーサーの調整が必要な場合あり

---

## ダミー値で動作確認済みの項目

- `python -m src.main --dry-run` → 正常終了、`output/digest_YYYY-MM-DD.md` 生成
- `pytest tests/ -v` → 全テストパス
- Slack/Discord webhook: ダミーURLで dry_run モードの動作確認済み
