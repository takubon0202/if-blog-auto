# if(塾) Blog Automation System

Gemini API を活用した、最新トレンド情報を自動収集して画像付きブログ記事を生成・GitHub Pagesに自動投稿するシステム。

## 公開URL

**https://takubon0202.github.io/if-blog-auto/**

## 最新アップデート (2025-12-29)

### 新機能
- **7日以内最新情報限定**: Deep Researchで必ず7日以内の最新情報のみを収集
- **引用元必須**: 記事末尾に最低5つ以上の参考文献・引用元URLを自動記載
- **日本時間対応**: すべての日時処理をJST (UTC+9) に統一
- **リッチデザイン**: モダンでプレミアムなブログデザインに全面改修
- **目次自動生成**: 記事ページに目次を自動表示
- **シェアボタン**: Twitter, Facebook, はてなブックマーク対応

### 修正・改善
- **ライブラリバージョン更新**: `google-genai>=1.56.0` (Interactions API/Deep Research対応)
- **画像生成修正**: `response_modalities=["IMAGE"]` 設定追加で正常な画像生成を保証
- **画像検証強化**: PNGヘッダー検証・最低サイズ検証（10KB以上）
- **フォールバック機能**: Deep Research失敗時に自動的にGoogle Search Toolへフォールバック

## システム概要

```
┌──────────────────────────────────────────────────────────────────────────┐
│                      Blog Automation System                               │
│                                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │                        Step 1: 情報収集                              │ │
│  │  ┌─────────────────────────────────────────────────────────────┐   │ │
│  │  │  Deep Research API (deep-research-pro-preview-12-2025)      │   │ │
│  │  │  → 7日以内の最新トレンド情報を包括的に調査                   │   │ │
│  │  └─────────────────────────────────────────────────────────────┘   │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
│                                    ↓                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │                        Step 2: 記事生成                              │ │
│  │  ┌─────────────────────────────────────────────────────────────┐   │ │
│  │  │  Gemini 3 Pro Preview (gemini-3-pro-preview)                │   │ │
│  │  │  → 引用元付きSEO最適化ブログ記事を執筆                       │   │ │
│  │  └─────────────────────────────────────────────────────────────┘   │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
│                                    ↓                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │                        Step 3: 画像生成                              │ │
│  │  ┌─────────────────────────────────────────────────────────────┐   │ │
│  │  │  Gemini 2.5 Flash image (gemini-2.5-flash-image)            │   │ │
│  │  │  → アイキャッチ画像を自動生成                                │   │ │
│  │  └─────────────────────────────────────────────────────────────┘   │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
│                                    ↓                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │                   Step 4: SEO最適化 & 品質レビュー                   │ │
│  │  ┌─────────────────────────────────────────────────────────────┐   │ │
│  │  │  Gemini 3 Flash Preview (gemini-3-flash-preview)            │   │ │
│  │  │  🚀 思考モード: オフ（高速応答）                              │   │ │
│  │  │  → SEOスコアリング、ファクトチェック、品質評価               │   │ │
│  │  └─────────────────────────────────────────────────────────────┘   │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
│                                    ↓                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │                     Step 5: GitHub Pages 投稿                        │ │
│  │  ┌─────────────────────────────────────────────────────────────┐   │ │
│  │  │  Jekyll → Git Push → 自動ビルド → 公開                       │   │ │
│  │  └─────────────────────────────────────────────────────────────┘   │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
│                                                                           │
└──────────────────────────────────────────────────────────────────────────┘
```

## 使用AIモデル

| ステップ | モデル | 思考モード | 応答時間 |
|----------|--------|-----------|----------|
| 情報収集 | `deep-research-pro-preview-12-2025` | - | 約5分 |
| 記事生成 | `gemini-3-pro-preview` | オン | 約30秒 |
| 画像生成 | `gemini-2.5-flash-image` | - | 約5秒 |
| SEO最適化 | `gemini-3-flash-preview` | **オフ** | 約3-5秒 |
| 品質レビュー | `gemini-3-flash-preview` | **オフ** | 約5-8秒 |

### 思考モードについて
- **オン**: 深い推論が必要なタスク（記事生成）
- **オフ**: 高速応答が必要なタスク（SEO/レビュー）→ `thinking_budget: 0`

## クイックスタート

### 前提条件
- Python 3.11以上
- Git
- Google AI API Key（[Google AI Studio](https://aistudio.google.com/)から取得）

### 1. セットアップ（初回のみ）

```bash
# リポジトリをクローン
git clone https://github.com/takubon0202/if-blog-auto.git
cd if-blog-auto

# Python仮想環境を作成・有効化
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Mac/Linux

# 依存関係をインストール
pip install -r requirements.txt

# 環境変数を設定
copy .env.example .env         # Windows
# cp .env.example .env         # Mac/Linux
```

`.env`ファイルを編集してAPIキーを設定：
```
GOOGLE_AI_API_KEY=your_actual_api_key_here
```

### 2. 記事を生成

```bash
cd src/scripts

# AIツールの記事を生成して投稿
python main.py --topic ai_tools

# ドライラン（投稿せずにテスト）
python main.py --topic psychology --dry-run

# 画像生成をスキップ
python main.py --topic education --skip-images
```

### 3. 実行結果

実行すると以下の処理が自動で行われます：

```
Step 1: Deep Research    → 最新情報を収集（約5分）
Step 2: 記事生成         → ブログ記事を作成（約30秒）
Step 3: 画像生成         → アイキャッチ画像を生成（約5秒）
Step 4: SEO最適化        → メタデータを最適化（約3-5秒）
Step 5: 品質レビュー     → ファクトチェック（約5-8秒）
Step 6: GitHub投稿       → サイトに自動公開
```

生成された記事は自動的に https://takubon0202.github.io/if-blog-auto/ に公開されます。

## 主要機能

| 機能 | 説明 |
|------|------|
| **7日以内限定リサーチ** | Deep Research APIで**過去7日以内の最新情報のみ**を収集 |
| **自動記事生成** | Gemini 3 ProでSEO最適化されたブログ記事を自動執筆 |
| **引用元必須記載** | 記事末尾に**最低5つ以上**の参考文献URLを自動記載 |
| **画像生成** | Gemini 2.5 Flash imageで記事用アイキャッチ画像を生成 |
| **SEO最適化** | Gemini 3 Flash（思考オフ）でメタデータ・キーワード最適化 |
| **品質レビュー** | Gemini 3 Flash（思考オフ）でファクトチェック・品質スコアリング |
| **自動投稿** | GitHub Pages (Jekyll) へ自動投稿 |
| **スケジュール実行** | GitHub Actionsで毎日JST 5:00に自動実行 |

## 7日以内最新情報限定ルール

本システムは**必ず7日以内の最新情報のみ**を使用します。

### 制約条件
| 項目 | 設定 |
|------|------|
| 情報の鮮度 | 過去7日以内のみ |
| 日付形式 | YYYY年MM月DD日 |
| タイムゾーン | 日本標準時 (JST = UTC+9) |
| 最低ソース数 | 5つ以上 |

### 日付範囲の自動計算
```python
from lib.timezone import now_jst
from datetime import timedelta

today = now_jst()
start_date = today - timedelta(days=7)
# 例: 2025年12月22日〜2025年12月29日
```

### リサーチクエリ例
```
【重要】本日は2025年12月29日です。
必ず過去7日以内（2025年12月22日〜2025年12月29日）の最新情報のみを調査してください。
7日より古い情報は絶対に含めないでください。
```

## 引用元・参考文献必須ルール

すべての記事末尾に**引用元・参考文献**を自動記載します。

### 必須要件
| 項目 | 要件 |
|------|------|
| ソース数 | 最低5つ以上 |
| URL形式 | 完全形式（https://で始まる） |
| 記載形式 | Markdownリンク `[タイトル](URL)` |
| HTMLタグ | `<div class="sources-section">` で囲む |

### 引用元セクション例
```markdown
## 参考文献・引用元

<div class="sources-section">

この記事は以下の情報源を参考に作成されました（2025年12月22日〜2025年12月29日の調査に基づく）：

- [ソースタイトル1](https://example.com/article1)
- [ソースタイトル2](https://example.com/article2)
- [ソースタイトル3](https://example.com/article3)
- [ソースタイトル4](https://example.com/article4)
- [ソースタイトル5](https://example.com/article5)

</div>

*この記事はAIによって生成されました。情報は2025年12月29日時点のものです。*
```

## タイムゾーン設定

本システムはすべての日時処理で **日本標準時 (JST = UTC+9)** を使用します。

| 設定箇所 | 設定値 |
|---------|--------|
| Python スクリプト | `src/lib/timezone.py` モジュール使用 |
| Jekyll | `timezone: Asia/Tokyo` |
| GitHub Actions | `TZ: 'Asia/Tokyo'` 環境変数 |
| スケジュール実行 | 毎日 JST 5:00 (UTC 20:00) |

### タイムゾーンユーティリティ

```python
from lib.timezone import now_jst, format_date, format_datetime_jst

# 現在の日本時間
current_time = now_jst()

# 日付フォーマット
date_str = format_date()  # "2025-12-29"

# Jekyll用日時
jekyll_date = format_datetime_jst()  # "2025-12-29 16:50:44 +0900"
```

## 対象トピック

| ID | トピック | 曜日 |
|----|----------|------|
| `psychology` | 心理学・メンタルヘルス | 月曜 |
| `education` | 教育・学習科学 | 火曜 |
| `startup` | 起業家育成・スタートアップ | 水曜 |
| `investment` | 投資教育・金融リテラシー | 木曜 |
| `ai_tools` | AIツール・技術動向 | 金曜 |
| `school_refusal` | 不登校支援 | 土曜 |
| `neurodiversity` | 発達障害・ニューロダイバーシティ | 日曜 |

## プロジェクト構造

```
if-blog-auto/
├── .github/
│   └── workflows/
│       ├── daily-blog-generation.yml  # 日次自動生成
│       └── manual-trigger.yml         # 手動実行
│
├── docs/                    # GitHub Pages サイト (Jekyll)
│   ├── _config.yml          # Jekyll設定
│   ├── _layouts/            # レイアウトテンプレート
│   ├── _posts/              # ブログ記事（自動投稿先）
│   ├── assets/
│   │   ├── css/style.css
│   │   └── images/          # 記事画像
│   ├── index.md
│   ├── about.md
│   └── categories.md
│
├── src/
│   ├── agents/              # サブエージェント定義（7種類）
│   │   ├── deep-research-agent.md
│   │   ├── writing-agent.md
│   │   ├── image-agent.md
│   │   ├── seo-agent.md         # Gemini 3 Flash（思考オフ）
│   │   ├── review-agent.md      # Gemini 3 Flash（思考オフ）
│   │   ├── site-builder-agent.md
│   │   └── blog-publisher-agent.md
│   │
│   ├── skills/              # スキル定義（7種類）
│   │   ├── gemini-research.md
│   │   ├── gemini-content.md
│   │   ├── gemini-3-flash.md    # 思考オフ高速処理
│   │   ├── image-generation.md
│   │   ├── github-pages.md
│   │   ├── jekyll-content.md
│   │   └── cms-integration.md
│   │
│   ├── config/
│   │   ├── topics.json      # トピック設定
│   │   └── settings.json    # システム設定（モデル・思考モード）
│   │
│   ├── lib/
│   │   ├── gemini_client.py # Gemini APIクライアント
│   │   └── timezone.py      # タイムゾーンユーティリティ (JST)
│   │
│   ├── scripts/
│   │   ├── main.py          # メインスクリプト
│   │   ├── research.py      # Deep Research実行
│   │   ├── generate_content.py  # Gemini 3 Pro記事生成
│   │   ├── generate_image.py    # Gemini 2.5 Flash画像生成
│   │   ├── seo_optimize.py      # Gemini 3 Flash SEO最適化
│   │   ├── review.py            # Gemini 3 Flash品質レビュー
│   │   └── publish.py           # GitHub Pages投稿
│   │
│   └── templates/
│       ├── blog-post.md
│       └── meta-template.json
│
├── dashboard/               # 管理ダッシュボード
├── output/                  # 生成された記事（ローカル保存）
├── CLAUDE.md                # プロジェクトルール
├── requirements.txt         # Python依存関係
└── package.json             # Node.js依存関係
```

## サブエージェント

| エージェント | 役割 | モデル | 思考モード |
|-------------|------|--------|-----------|
| `deep-research-agent` | 最新情報の包括的収集 | Deep Research API | - |
| `writing-agent` | ブログ記事の執筆 | Gemini 3 Pro | オン |
| `image-agent` | アイキャッチ画像生成 | Gemini 2.5 Flash image | - |
| `seo-agent` | SEOメタデータ最適化 | Gemini 3 Flash | **オフ** |
| `review-agent` | 品質チェック・ファクトチェック | Gemini 3 Flash | **オフ** |
| `site-builder-agent` | Jekyllサイト構造管理 | - | - |
| `blog-publisher-agent` | GitHub Pages投稿処理 | - | - |

## スキル

| スキル | 目的 | モデル |
|--------|------|--------|
| `gemini-research` | Deep Research API実行 | Deep Research |
| `gemini-content` | 記事生成（引用元付き） | Gemini 3 Pro |
| `gemini-3-flash` | SEO/レビュー高速処理 | Gemini 3 Flash（思考オフ） |
| `image-generation` | 画像生成 | Gemini 2.5 Flash image |
| `timezone` | 日本時間 (JST) 処理 | - |
| `github-pages` | GitHub Pages操作 | - |
| `jekyll-content` | Jekyll形式コンテンツ生成 | - |
| `cms-integration` | CMS連携 | - |

## セットアップ

### 1. リポジトリのクローン

```bash
git clone https://github.com/takubon0202/if-blog-auto.git
cd if-blog-auto
```

### 2. 依存関係のインストール

```bash
# Python仮想環境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Node.js依存関係
npm install
```

### 3. 環境変数の設定

```bash
cp .env.example .env
```

`.env`ファイルを編集:
```
GOOGLE_AI_API_KEY=your_google_ai_api_key_here
```

### 4. GitHub Secrets設定

リポジトリの Settings > Secrets and variables > Actions で追加:
- `GOOGLE_AI_API_KEY`

### 5. GitHub Pages有効化

1. リポジトリの **Settings** > **Pages**
2. **Build and deployment** > **Source**: `GitHub Actions` を選択
3. **Settings** > **Actions** > **General**で:
   - **Workflow permissions**: `Read and write permissions` を選択
   - `Allow GitHub Actions to create and approve pull requests` にチェック
4. **Actions** > **Deploy to GitHub Pages** を手動実行
5. 数分後に公開: https://takubon0202.github.io/if-blog-auto/

詳細は [GitHub Pages 設定ガイド](docs/GITHUB_PAGES_SETUP.md) を参照してください。

## 使い方

### ローカル実行

```bash
cd src/scripts

# 記事生成＆GitHub Pages投稿
python main.py --topic ai_tools

# ドライラン（投稿なし）
python main.py --topic psychology --dry-run

# 画像生成スキップ
python main.py --topic education --skip-images
```

### 利用可能なトピック
```
psychology, education, startup, investment, ai_tools, school_refusal, neurodiversity
```

### 個別スクリプト実行

```bash
# リサーチのみ
python research.py --topic ai_tools --use-deep-research

# SEO最適化のみ
python seo_optimize.py --file article.md

# 品質レビューのみ
python review.py --file article.md

# 画像生成のみ
python generate_image.py --title "タイトル" --summary "概要"
```

### GitHub Actions

| ワークフロー | トリガー | 説明 |
|-------------|---------|------|
| Daily Blog Generation | 毎日 JST 5:00 | 自動記事生成＆投稿 |
| Manual Trigger | 手動 | 任意のタイミングで実行 |

**手動実行方法**:
1. GitHub > Actions > Daily Blog Generation with Gemini
2. Run workflow をクリック
3. トピックを選択（空白で自動選択）
4. Run workflow

### ダッシュボード

```bash
cd dashboard
uvicorn api.server:app --reload
# http://localhost:8000 でアクセス
```

## 技術スタック

| カテゴリ | 技術 |
|---------|------|
| **AI モデル** | Gemini 3 Pro, Gemini 3 Flash（思考オフ）, Deep Research, Gemini 2.5 Flash image |
| **言語** | Python 3.11+, JavaScript (Node.js 20+) |
| **ライブラリ** | `google-genai>=1.56.0` (Interactions API対応必須) |
| **検索** | Google Search Tool (Gemini Built-in) |
| **静的サイト** | Jekyll (GitHub Pages) |
| **CI/CD** | GitHub Actions |
| **Web Framework** | FastAPI |

## API使用量の目安

| 操作 | 1記事あたり | 応答時間 |
|------|------------|----------|
| Deep Research | 1リクエスト | 約5分 |
| 記事生成 | 1-2リクエスト | 約30秒 |
| 画像生成 | 1-3リクエスト | 約5秒 |
| SEO最適化 | 1リクエスト | 約3-5秒 |
| 品質レビュー | 1リクエスト | 約5-8秒 |

## パフォーマンス

### Gemini 3 Flash Preview（思考モードオフ）の効果

| タスク | 思考モードオン | 思考モードオフ | 改善 |
|--------|--------------|--------------|------|
| SEO最適化 | 10-15秒 | 3-5秒 | **70%高速化** |
| 品質レビュー | 15-25秒 | 5-8秒 | **65%高速化** |

## トラブルシューティング

### APIキーエラー
```
Error: Invalid API key
```
→ `.env`ファイルの`GOOGLE_AI_API_KEY`が正しく設定されているか確認してください。

### モジュールが見つからない
```
ModuleNotFoundError: No module named 'google.genai'
```
→ 仮想環境が有効化されているか確認し、`pip install -r requirements.txt`を再実行してください。

### Deep Research 400エラー
```
google.genai._interactions.BadRequestError: Error code: 400 - {'error': {'message': 'Request contains an invalid argument.'}}
```
**考えられる原因と解決策**:

1. **ライブラリバージョンが古い**
   - 原因: `google-genai`が0.5.0等の古いバージョン
   - 解決: `pip install google-genai>=1.56.0` でアップグレード

2. **無効なパラメータの指定**
   - 原因: `interactions.create()`にサポートされていないパラメータを指定
   - 解決: 公式ドキュメントに従ったパラメータのみを使用
   ```python
   # 正しい使用方法（公式ドキュメント準拠）
   interaction = client.interactions.create(
       input=query,
       agent="deep-research-pro-preview-12-2025",
       background=True
   )
   ```

→ **フォールバック**: エラー発生時は自動的にGoogle Search Toolにフォールバックします

### Git pushエラー
```
Error: Permission denied
```
→ GitHubの認証情報を確認してください。Personal Access Tokenの設定が必要な場合があります。

### 画像生成エラー
```
Error: Image generation failed
```
→ **原因**: `response_modalities=["IMAGE"]`設定が不足している可能性
→ **解決**: 最新のコードでは自動的に設定されています
→ **回避**: `--skip-images`オプションで画像生成をスキップして実行できます

### 画像が小さすぎる/破損
```
Warning: Image too small (xxx bytes), likely corrupted
```
→ 画像生成APIのレスポンスが正常でない場合に発生します
→ 再実行するか、`--skip-images`オプションで画像生成をスキップしてください

## 内部動作フロー

### Deep Research フォールバックフロー

Deep Researchが失敗した場合、自動的にGoogle Search Toolにフォールバックします。
**失敗時は必ずログに通知が出力されます。**

```
┌──────────────────────────────────────┐
│ run_research(topic, use_deep=True)  │
└─────────────────┬────────────────────┘
                  │
        ┌─────────▼─────────┐
        │ Deep Research API │
        │ 呼び出し          │
        └─────────┬─────────┘
                  │
          成功？ ─┴─ 失敗？
          │           │
          │    ┌──────▼──────────────────────────┐
          │    │ 【重要】エラー通知ログ出力       │
          │    │ ============                    │
          │    │ Deep Research APIが失敗しました │
          │    │ エラー内容: {詳細}              │
          │    │ フォールバック: Google Search   │
          │    │ ============                    │
          │    └──────┬──────────────────────────┘
          │           │
          │    ┌──────▼──────────────┐
          │    │ Google Search Tool │
          │    │ + gemini-3-pro     │
          │    └──────┬──────────────┘
          │           │
    ┌─────▼───────────▼─────┐
    │ 結果返却               │
    │ method: deep_research │
    │  or google_search     │
    │ fallback_reason: ...  │
    └───────────────────────┘
```

### 画像生成フロー

```
┌────────────────────────────────────┐
│ generate_images(article)           │
└─────────────────┬──────────────────┘
                  │
        ┌─────────▼─────────────────┐
        │ response_modalities=      │
        │ ["IMAGE"] を設定（必須）  │
        └─────────┬─────────────────┘
                  │
        ┌─────────▼─────────────────┐
        │ Gemini 2.5 Flash image    │
        │ で画像生成                │
        └─────────┬─────────────────┘
                  │
        ┌─────────▼─────────────────┐
        │ 画像サイズ検証（1KB以上） │
        └─────────┬─────────────────┘
                  │
          有効？ ─┴─ 無効？
          │           │
          │    ┌──────▼──────────────┐
          │    │ 警告: "Image too   │
          │    │  small" ログ出力   │
          │    └──────┬──────────────┘
          │           │
    ┌─────▼───────────▼─────────────┐
    │ output/images/ に保存         │
    └─────────────────┬─────────────┘
                      │
        ┌─────────────▼─────────────┐
        │ publish時にPNGヘッダー検証 │
        │ (10KB以上 + 正しいヘッダー)│
        └─────────────┬─────────────┘
                      │
    ┌─────────────────▼─────────────┐
    │ docs/assets/images/ にコピー  │
    └───────────────────────────────┘
```

## デザインガイドライン

本システムでは以下のデザインガイドラインを遵守しています。

### 禁止事項
- 絵文字の使用禁止
- 紫色系の使用禁止
- AIっぽい表現（「革新的」「画期的」など）の禁止

### 推奨スタイル
- クリーンでミニマルなデザイン
- Deep Navy (#0a192f) を基調とした配色
- 専門的だが親しみやすいトーン

### 記事構成
- 参考文献・引用元を記事末尾に必ず記載
- 目次を自動生成
- シェアボタン（Twitter, Facebook, はてなブックマーク）

詳細は `src/config/design-guidelines.md` を参照してください。

## ライセンス

MIT License

## 関連リンク

- [GitHub Repository](https://github.com/takubon0202/if-blog-auto)
- [公開ブログ](https://takubon0202.github.io/if-blog-auto/)
- [Google AI Studio](https://aistudio.google.com/)
- [Gemini API ドキュメント](https://ai.google.dev/gemini-api/docs)
