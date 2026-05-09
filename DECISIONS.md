# 自律判断ログ (DECISIONS.md)

## LLM選定: Gemini 2.0 Flash（無料枠）
- **判断**: Anthropic Claude API（有料）の代わりにGoogle Gemini 2.0 Flash無料枠を採用
- **理由**: ユーザーが「完全無料」を要求。Gemini無料枠は1日1,500リクエストまで無料で、20記事/日の運用には十分
- **代替案**: Ollama（ローカル）、LLMなし（RSS切り詰め）もconfig.yamlで選択可能

## プロバイダ設計: プラガブルアーキテクチャ
- **判断**: LLMProviderをProtocolとして抽象化し、Gemini/Ollama/Noneを差し替え可能に設計
- **理由**: 将来のプロバイダ変更に対応し、テスト時もモックなしでNoLLMProviderが使える

## feedparser + httpx の分離
- **判断**: feedparser単体のHTTP機能を使わず、httpxでDLしてfeedparserでパース
- **理由**: feedparserのHTTPはタイムアウト制御とUser-Agent設定が困難。httpxなら両方制御できる

## SQLiteの採用
- **判断**: 外部DB不要のSQLiteで30日間の送信済みURL管理
- **理由**: ゼロインフラ。1日最大20件の記録なら性能上の問題なし

## dry_runはファイルを常に書き出す
- **判断**: `--dry-run`でもdigestファイルは書き出す
- **理由**: 出力フォーマットの確認がdry-runの主目的。ファイルが出力されなければ確認できない

## カテゴリの重複許容
- **判断**: AI・PCの両キーワードにマッチする記事は両セクションに掲載
- **理由**: 「IntelのAIチップ」など両分野にまたがる記事は両方の読者にとって価値がある

## max_articles_per_category: 10
- **判断**: デフォルトで1カテゴリ最大10件に制限
- **理由**: Gemini API呼び出しを1日21件（AI10+PC10+trend1）に抑える。無料枠の1.4%

## テスト戦略: 実ネットワーク接続なし
- **判断**: 全テストでネットワーク・LLM API呼び出しをモックまたはdry-run
- **理由**: CIでの安定実行とコスト削減。テスト自体がAPIを消費しないよう設計
