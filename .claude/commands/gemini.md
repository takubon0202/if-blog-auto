# Gemini CLI連携スキル

Google Gemini CLIを使用してコード生成・エラー解決を行います。
**Gemini AI Pro サブスクリプション**に含まれており、追加費用なしで利用できます。

## 使用方法

```
/gemini タスク内容
```

## 実行されるコマンド

$ARGUMENTS を受け取り、Gemini CLIを実行します：

```bash
gemini -m gemini-3-pro-preview "$ARGUMENTS"
```

## 利用可能なモデル

### メイン（常にこちらを使用）

| モデル | 説明 | 用途 |
|--------|------|------|
| `gemini-3-pro-preview` | **推奨** - 最高品質の推論・コーディング | 複雑なタスク、設計、分析 |
| `gemini-3-flash-preview` | **高速** - 低レイテンシ | 単純なタスク、素早い回答 |

### フォールバック（エラー時のみ）

| モデル | 説明 |
|--------|------|
| `gemini-2.5-pro` | Gemini 3がエラーの場合のみ使用 |
| `gemini-2.5-flash` | Gemini 3 Flashがエラーの場合のみ使用 |

> **注意**: 2.5系は通常使用しません。Gemini 3系でエラーが発生した場合のみフォールバックとして使用してください。

## コマンド例

```bash
# 推奨：Gemini 3 Pro（デフォルト）
gemini "タスク内容"
gemini -m gemini-3-pro-preview "複雑なアルゴリズムを実装"

# 高速処理：Gemini 3 Flash
gemini -m gemini-3-flash-preview "簡単な質問に答えて"

# 自動承認モード（YOLO）
gemini -y "ファイルを修正して"
gemini --yolo "テストを実行"

# 対話モード
gemini
```

## if-blog-auto プロジェクト固有のタスク例

```bash
# ブログ生成関連
gemini -m gemini-3-pro-preview "記事生成プロンプトを最適化"
gemini -m gemini-3-flash-preview "SEOメタデータを生成"

# 画像生成
gemini "gemini-2.5-flash-imageの画像生成プロンプトを改善"

# 動画生成
gemini "Remotion SlideVideoV3のタイミング制御を修正"
```

## フォールバック使用例（エラー時のみ）

```bash
# Gemini 3 Proがエラーの場合のみ
gemini -m gemini-2.5-pro "タスク内容"

# Gemini 3 Flashがエラーの場合のみ
gemini -m gemini-2.5-flash "タスク内容"
```

## Agent Skills

```bash
gemini skills list       # スキル一覧
gemini skills enable X   # スキル有効化
gemini skills disable X  # スキル無効化
```

## 拡張機能

```bash
gemini extensions list        # 拡張機能一覧
gemini extensions install X   # インストール
```

## セットアップ

```bash
npm install -g @google/gemini-cli
gemini  # 初回起動時にGoogleログイン
```

## 必要なもの

- **Gemini AI Pro** サブスクリプション ($19.99/月)
- Node.js

OAuth認証のみで利用可能。APIキーは不要です。

## 使用量上限に関する注意

上限エラーが発生した場合は即座に報告し、制限が回復するまで使用を停止します。
追加課金を防ぐための重要なルールです。
