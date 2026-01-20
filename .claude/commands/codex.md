# Codex CLI連携スキル

OpenAI Codex CLIを使用してコード生成・エラー解決を行います。
**ChatGPT Plusサブスクリプション**に含まれており、追加費用なしで利用できます。

## 使用方法

```
/codex タスク内容
```

## 実行されるコマンド

$ARGUMENTS を受け取り、Codex CLIを実行します：

```bash
codex "$ARGUMENTS"
```

## コマンド例

```bash
# 一般的なタスク
codex "配列をシャッフルする関数を作成"

# 対話モード
codex

# ヘルパースクリプト
node scripts/codex-helper.js --error "エラーメッセージ"
node scripts/codex-helper.js --file path/to/file.js "修正内容"
```

## if-blog-auto プロジェクト固有のタスク例

```bash
# ブログ生成関連
codex "generate_video_v3.pyのエラーハンドリングを改善"
codex "SlideVideoV3.tsxにKen Burnsエフェクトを追加"

# Remotion動画生成
codex "render.mjsのプロパティ検証を強化"

# Gemini API
codex "gemini_client.pyにリトライロジックを追加"
```

## 自動発動条件

- 同じエラーが3回以上発生
- 「Codexで」「GPTで」と明示的に依頼
- Claude単体では解決困難なタスク

## セットアップ

```bash
npm install -g @openai/codex
codex --login
```

## 必要なもの

- **ChatGPT Plus** ($20/月)
- Node.js

## 使用量上限に関する注意

上限エラーが発生した場合は即座に報告し、制限が回復するまで使用を停止します。
追加課金を防ぐための重要なルールです。
