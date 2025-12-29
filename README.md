# if(塾) Blog Automation System

Gemini API を活用した、最新トレンド情報を自動収集して画像付きブログ記事を生成・GitHub Pagesに自動投稿するシステム。

## 公開URL

**https://takubon0202.github.io/if-blog-auto/**

## システム概要

```
┌─────────────────────────────────────────────────────────────────┐
│                    Blog Automation System                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │ Deep Research │ → │ Gemini 3 Pro │ → │ Gemini 2.5   │      │
│  │  (情報収集)   │    │ (記事生成)   │    │ Flash(画像) │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│         │                   │                   │               │
│         ▼                   ▼                   ▼               │
│  ┌──────────────────────────────────────────────────┐          │
│  │              SEO最適化 & 品質レビュー             │          │
│  └──────────────────────────────────────────────────┘          │
│                            │                                    │
│                            ▼                                    │
│  ┌──────────────────────────────────────────────────┐          │
│  │         GitHub Pages (Jekyll) 自動投稿           │          │
│  └──────────────────────────────────────────────────┘          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## 主要機能

| 機能 | 説明 | 使用モデル |
|------|------|-----------|
| **Deep Research** | 最新トレンド情報の包括的収集 | `deep-research-pro-preview-12-2025` |
| **記事生成** | SEO最適化されたブログ記事の執筆 | `gemini-3-pro-preview` |
| **画像生成** | 記事用アイキャッチ画像の生成 | `gemini-2.5-flash-image` |
| **SEO最適化** | メタデータ・キーワード最適化 | `gemini-2.0-flash` |
| **品質レビュー** | ファクトチェック・品質スコアリング | `gemini-2.0-flash` |
| **自動投稿** | GitHub Pages (Jekyll) への投稿 | Git Push |
| **スケジュール実行** | GitHub Actionsによる日次自動実行 | - |

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
│   │   ├── default.html
│   │   ├── post.html
│   │   └── home.html
│   ├── _posts/              # ブログ記事（自動投稿先）
│   ├── assets/
│   │   ├── css/style.css
│   │   └── images/          # 記事画像
│   ├── index.md
│   ├── about.md
│   └── categories.md
│
├── src/
│   ├── agents/              # サブエージェント定義
│   │   ├── deep-research-agent.md
│   │   ├── writing-agent.md
│   │   ├── image-agent.md
│   │   ├── seo-agent.md
│   │   ├── review-agent.md
│   │   ├── site-builder-agent.md
│   │   └── blog-publisher-agent.md
│   │
│   ├── skills/              # スキル定義
│   │   ├── gemini-research.md
│   │   ├── gemini-content.md
│   │   ├── image-generation.md
│   │   ├── cms-integration.md
│   │   ├── github-pages.md
│   │   └── jekyll-content.md
│   │
│   ├── config/
│   │   ├── topics.json      # トピック設定
│   │   └── settings.json    # システム設定
│   │
│   ├── lib/
│   │   └── gemini_client.py # Gemini APIクライアント
│   │
│   ├── scripts/
│   │   ├── main.py          # メインスクリプト
│   │   ├── research.py      # リサーチ実行
│   │   ├── generate_content.py  # 記事生成
│   │   ├── generate_image.py    # 画像生成
│   │   ├── seo_optimize.py      # SEO最適化
│   │   ├── review.py            # 品質レビュー
│   │   └── publish.py           # GitHub Pages投稿
│   │
│   └── templates/
│       ├── blog-post.md
│       └── meta-template.json
│
├── dashboard/               # 管理ダッシュボード
│   ├── index.html
│   ├── styles.css
│   ├── app.js
│   └── api/server.py
│
├── output/                  # 生成された記事（ローカル保存）
│   ├── posts/
│   └── images/
│
├── CLAUDE.md                # プロジェクトルール
├── requirements.txt         # Python依存関係
├── package.json             # Node.js依存関係
└── .env.example             # 環境変数サンプル
```

## サブエージェント

| エージェント | 役割 | 使用モデル |
|-------------|------|-----------|
| `deep-research-agent` | Deep Researchによる情報収集 | Deep Research API |
| `writing-agent` | ブログ記事の執筆 | Gemini 3 Pro |
| `image-agent` | アイキャッチ画像生成 | Gemini 2.5 Flash image |
| `seo-agent` | SEOメタデータ最適化 | Gemini 2.0 Flash |
| `review-agent` | 品質チェック・ファクトチェック | Gemini 2.0 Flash |
| `site-builder-agent` | Jekyllサイト構造管理 | - |
| `blog-publisher-agent` | GitHub Pages投稿処理 | - |

## スキル

| スキル | 目的 |
|--------|------|
| `gemini-research` | Deep Research API実行 |
| `gemini-content` | Gemini 3 Proコンテンツ生成 |
| `image-generation` | Gemini 2.5 Flash画像生成 |
| `github-pages` | GitHub Pages操作 |
| `jekyll-content` | Jekyll形式コンテンツ生成 |
| `cms-integration` | CMS連携（GitHub Pages） |

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
2. **Source**: `Deploy from a branch`
3. **Branch**: `main` / `docs`
4. **Save** をクリック
5. 数分後に公開: https://takubon0202.github.io/if-blog-auto/

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

# 利用可能なトピック
# psychology, education, startup, investment, ai_tools, school_refusal, neurodiversity
```

### 個別スクリプト実行

```bash
# リサーチのみ
python research.py --topic ai_tools --use-deep-research

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
| **AI モデル** | Gemini 3 Pro, Deep Research, Gemini 2.5 Flash image |
| **言語** | Python 3.11+, JavaScript (Node.js 20+) |
| **検索** | Google Search Tool (Gemini Built-in) |
| **静的サイト** | Jekyll (GitHub Pages) |
| **CI/CD** | GitHub Actions |
| **Web Framework** | FastAPI |

## API使用量の目安

| 操作 | 1記事あたり |
|------|------------|
| Deep Research | 1リクエスト（5分程度） |
| 記事生成 | 1-2リクエスト |
| 画像生成 | 1-3リクエスト |
| SEO/レビュー | 2リクエスト |

## ライセンス

MIT License

## 関連リンク

- [GitHub Repository](https://github.com/takubon0202/if-blog-auto)
- [公開ブログ](https://takubon0202.github.io/if-blog-auto/)
- [Google AI Studio](https://aistudio.google.com/)
