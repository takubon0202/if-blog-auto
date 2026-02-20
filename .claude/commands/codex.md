# Codex CLI連携スキル

OpenAI Codex CLIを使用してコード生成・エラー解決を行います。
**ChatGPT Plusサブスクリプション**に含まれており、追加費用なしで利用できます。

## 使用方法

```
/codex タスク内容
```

## 実行されるコマンド

$ARGUMENTS を受け取り、Codex CLIを**非対話モード**で実行します：

```bash
codex exec "$ARGUMENTS"
```

**重要**: `codex exec` は非対話モードで動作し、パイプ環境（Claude Code等）でも正常に動作します。

## コマンド例

```bash
# 非対話モード（推奨）
codex exec "配列をシャッフルする関数を作成"
codex exec "エラーを修正してください"

# ヘルパースクリプト経由
node scripts/codex-helper.js "タスク内容"
node scripts/codex-helper.js --error "エラーメッセージ"
node scripts/codex-helper.js --file path/to/file.js "修正内容"

# 対話モード（ターミナル直接使用時のみ）
codex --interactive
node scripts/codex-helper.js --interactive
```

## if-blog-auto プロジェクト固有のタスク例

```bash
# ブログ生成関連
codex exec "generate_video_v3.pyのエラーハンドリングを改善"
codex exec "SlideVideoV3.tsxにKen Burnsエフェクトを追加"

# Remotion動画生成
codex exec "render.mjsのプロパティ検証を強化"

# Gemini API
codex exec "gemini_client.pyにリトライロジックを追加"
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

## 非対話モードの注意点

- `codex exec` は標準入力を必要としないため、パイプ環境で安定動作
- 環境変数 `CI=true` を設定すると自動的に非対話モードになる
- `--json` オプションでJSONL形式の出力が可能
