# if(塾) Blog Automation System

Gemini API を活用した、最新トレンド情報を自動収集して画像付きブログ記事を生成・GitHub Pagesに自動投稿するシステム。

## 公開URL

**https://takubon0202.github.io/if-blog-auto/**

---

## 設計方針: Multi-Search（3回検索）メイン + Deep Research 週1回

| 曜日 | リサーチ方法 | 検索回数 | 処理時間 | 備考 |
|------|-------------|----------|---------|------|
| **月〜土** | Multi-Search | 3回 | 約10秒 | デフォルト・推奨 |
| **日曜日** | Deep Research API | 1回 | 約5分 | 週1回の深層調査 |
| **フォールバック** | Multi-Search | 3回 | 約10秒 | Deep Research失敗時 |
| **手動実行** | 選択可能 | - | - | GitHub Actionsで選択 |

**設計理由**:
- Deep ResearchはRPM 1/分の厳しいレート制限があるため、週1回（日曜日）のみ使用
- Multi-Search（3回検索）はDeep Research簡易版として、3つの視点から情報を収集し高品質なリサーチを実現
- Deep Research失敗時は自動的にMulti-Searchにフォールバック

---

## システムフロー

```
┌──────────────────────────────────────────────────────────────────────────┐
│                      Blog Automation System                               │
│                                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │                        Step 1: 情報収集                              │ │
│  │  ┌─────────────────────────────────────────────────────────────┐   │ │
│  │  │  【月〜土】Multi-Search 3回検索 (gemini-3-pro-preview)       │   │ │
│  │  │  【日曜日】Deep Research API (週1回の深層調査)               │   │ │
│  │  │  【失敗時】Multi-Search自動フォールバック                    │   │ │
│  │  │  → 7日以内の最新トレンド情報を収集                          │   │ │
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
│  │  │  思考モード: オフ（高速応答）                                 │   │ │
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

---

## 使用AIモデル

| ステップ | モデル | 曜日/タイミング | 検索回数 | 応答時間 |
|----------|--------|----------------|----------|----------|
| 情報収集（メイン） | `gemini-3-pro-preview` + Multi-Search | 月〜土 | 3回 | 約10秒 |
| 情報収集（深層） | `deep-research-pro-preview-12-2025` | 日曜のみ | 1回 | 約5分 |
| 情報収集（フォールバック） | `gemini-3-pro-preview` + Multi-Search | Deep Research失敗時 | 3回 | 約10秒 |
| 記事生成 | `gemini-3-pro-preview` | 全曜日 | - | 約30秒 |
| 画像生成 | `gemini-2.5-flash-image` | 全曜日 | - | 約5秒 |
| SEO最適化 | `gemini-3-flash-preview`（思考オフ） | 全曜日 | - | 約3-5秒 |
| 品質レビュー | `gemini-3-flash-preview`（思考オフ） | 全曜日 | - | 約5-8秒 |

---

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

# AIツールの記事を生成して投稿（Google Search使用）
python main.py --topic ai_tools --publish

# Deep Researchを使用して生成
python main.py --topic psychology --use-deep-research --publish

# ドライラン（投稿せずにテスト）
python main.py --topic education --dry-run

# 画像生成をスキップ
python main.py --topic startup --skip-images --publish
```

### 3. コマンドラインオプション

| オプション | 説明 | デフォルト |
|-----------|------|-----------|
| `--topic` | トピックID（必須） | - |
| `--use-deep-research` | Deep Research APIを使用 | False（Google Search） |
| `--skip-images` | 画像生成をスキップ | False |
| `--dry-run` | ドライラン（投稿なし） | False |
| `--publish` | GitHub Pagesに投稿 | True |

---

## GitHub Actions 自動実行

### 自動実行スケジュール

| 項目 | 設定 |
|------|------|
| 実行時刻 | 毎日 JST 5:00（UTC 20:00） |
| トピック選択 | 曜日別に自動選択 |
| リサーチ方法 | 日曜日のみDeep Research、他はGoogle Search |
| タイムゾーン | Asia/Tokyo（JST） |

### 手動実行

1. GitHub > Actions > **Manual Blog Generation**
2. **Run workflow** をクリック
3. パラメータを選択：
   - **topic**: トピックを選択
   - **research_method**: `google_search` または `deep_research`
   - **skip_images**: 画像生成をスキップするか

---

## サブエージェント構成

| エージェント | 役割 | モデル | 使用タイミング |
|-------------|------|--------|--------------|
| `google-search-agent` | Multi-Search情報収集（メイン） | Gemini 3 Pro + 3回検索 | 月〜土・フォールバック |
| `deep-research-agent` | 深層調査 | Deep Research API | 日曜のみ |
| `writing-agent` | ブログ記事の執筆 | Gemini 3 Pro | 全曜日 |
| `image-agent` | アイキャッチ画像生成（スマートプロンプト） | Gemini 2.5 Flash image + 記事分析 | 全曜日 |
| `seo-agent` | SEOメタデータ最適化 | Gemini 3 Flash（思考オフ） | 全曜日 |
| `review-agent` | 品質チェック・ファクトチェック | Gemini 3 Flash（思考オフ） | 全曜日 |
| `site-builder-agent` | Jekyllサイト構造管理 | - | 必要時 |
| `blog-publisher-agent` | GitHub Pages投稿処理 | - | 全曜日 |

---

## スキル構成

| スキル | 目的 | 使用API |
|--------|------|---------|
| `gemini-research` | 7日以内情報収集（Multi-Search 3回/Deep Research） | Gemini API |
| `gemini-content` | 引用元付きコンテンツ生成 | Gemini 3 Pro |
| `gemini-3-flash` | SEO/レビュー高速処理（思考オフ） | Gemini 3 Flash |
| `image-generation` | ブログ用画像生成（スマートプロンプト対応） | Gemini 2.5 Flash image |
| `timezone` | JST日時処理 | Python datetime |
| `github-pages` | GitHub Pages操作 | Git API |
| `jekyll-content` | Jekyll形式コンテンツ生成 | - |
| `cms-integration` | CMS連携 | - |

---

## 対象トピック（6種類 + 週間総括）

| ID | トピック | 曜日 | リサーチ方法 | キーワード例 |
|----|----------|------|-------------|-------------|
| `psychology` | 心理学・メンタルヘルス | 月曜 | Multi-Search | 心理学、カウンセリング、ストレス |
| `education` | 教育・学習科学 | 火曜 | Multi-Search | 教育、EdTech、学習法 |
| `startup` | 起業家育成・スタートアップ | 水曜 | Multi-Search | 起業、スタートアップ、経営 |
| `investment` | 投資教育・金融リテラシー | 木曜 | Multi-Search | 投資、NISA、資産形成 |
| `ai_tools` | AIツール・技術動向 | 金曜 | Multi-Search | AI、ChatGPT、Gemini |
| `inclusive_education` | インクルーシブ教育・多様な学び | 土曜 | Multi-Search | 不登校、発達障害、フリースクール |
| `weekly_summary` | **週間トレンド総括** | **日曜** | **Deep Research** | 6分野横断、週間まとめ |

### 週間総括（日曜日）

日曜日は6つのトピックを横断した「週間トレンド総括」記事をDeep Researchで生成します：

1. **今週のハイライト** - 全体の要約（3〜5行）
2. **各分野の注目ニュース** - 分野ごとに1〜2件
3. **分野横断的なトレンド分析**
4. **来週の注目ポイント**

---

## 重要なルール・制約

### 7日以内最新情報限定ルール

本システムは**必ず7日以内の最新情報のみ**を使用します。

| 項目 | 設定 |
|------|------|
| 情報の鮮度 | 過去7日以内のみ |
| 日付形式 | YYYY年MM月DD日 |
| タイムゾーン | 日本標準時 (JST = UTC+9) |
| 最低ソース数 | 5つ以上 |

### 引用元・参考文献必須ルール

すべての記事末尾に**引用元・参考文献**を自動記載します。

```markdown
---

## 参考文献・引用元

<div class="sources-section">

この記事は以下の情報源を参考に作成されました：

- [ソースタイトル1](https://example.com/article1)
- [ソースタイトル2](https://example.com/article2)
- [ソースタイトル3](https://example.com/article3)

</div>

---

*この記事はAIによって生成されました。*
```

### デザインガイドライン

| 禁止事項 | 推奨事項 |
|---------|---------|
| 絵文字の使用 | クリーンでミニマルなデザイン |
| 紫色系の使用 | Deep Navy (#1a1a2e) 基調 |
| AIっぽい表現（「革新的」「画期的」等） | 専門的だが親しみやすいトーン |

### 画像生成（スマートプロンプト機能）

記事タイトルを分析して、内容に合った具体的で多様な画像を自動生成します。

| 分析項目 | 説明 |
|---------|------|
| main_subject | メインの視覚的対象（例: "glowing neural network"） |
| visual_metaphor | 記事の核心を表すメタファー |
| mood | 感情的トーン（明るい、落ち着いた等） |
| key_elements | 含めるべき具体的な視覚要素 |
| composition | ランダム選択される構図スタイル |

**トピック別カラースキーム（自動適用）**:
- `psychology`: calming blue (#2b6cb0)
- `education`: growth green (#2f855a)
- `startup`: energetic orange (#c05621)
- `investment`: trustworthy gold-brown (#744210)
- `ai_tools`: tech navy blue (#1a365d)
- `inclusive_education`: supportive teal (#285e61)
- `weekly_summary`: insightful indigo (#553c9a)

---

## プロジェクト構造

```
if-blog-auto/
├── .github/
│   └── workflows/
│       ├── daily-blog-generation.yml  # 日次自動生成
│       ├── manual-trigger.yml         # 手動実行
│       └── deploy-pages.yml           # ページデプロイ
│
├── docs/                    # GitHub Pages サイト (Jekyll)
│   ├── _config.yml          # Jekyll設定 (timezone: Asia/Tokyo)
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
│   ├── agents/              # サブエージェント定義（8種類）
│   │   ├── google-search-agent.md   # メイン（月〜土）
│   │   ├── deep-research-agent.md   # 日曜のみ
│   │   ├── writing-agent.md
│   │   ├── image-agent.md
│   │   ├── seo-agent.md
│   │   ├── review-agent.md
│   │   ├── site-builder-agent.md
│   │   └── blog-publisher-agent.md
│   │
│   ├── skills/              # スキル定義（8種類）
│   │   ├── gemini-research.md
│   │   ├── gemini-content.md
│   │   ├── gemini-3-flash.md
│   │   ├── image-generation.md
│   │   ├── timezone.md
│   │   ├── github-pages.md
│   │   ├── jekyll-content.md
│   │   └── cms-integration.md
│   │
│   ├── config/
│   │   ├── topics.json      # トピック設定
│   │   └── settings.json    # システム設定
│   │
│   ├── lib/
│   │   ├── gemini_client.py # Gemini APIクライアント
│   │   └── timezone.py      # タイムゾーンユーティリティ (JST)
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
├── output/                  # 生成された記事（ローカル保存）
├── CLAUDE.md                # プロジェクトルール
├── requirements.txt         # Python依存関係
└── package.json             # Node.js依存関係
```

---

## GeminiClient API リファレンス

### 主要メソッド

```python
from lib.gemini_client import GeminiClient

client = GeminiClient()

# コンテンツ生成
result = await client.generate_content(
    prompt="プロンプト",
    model="gemini-3-pro-preview",
    enable_search=False,
    thinking_mode=True
)

# Google Search + 生成
result = await client.search_and_generate(
    query="検索クエリ",
    generation_prompt="生成プロンプト"
)

# Multi-Search（3回検索、メイン）
result = await client.multi_search_research(
    topic="トピック名",
    topic_info=topic_info,
    date_range={"start": "2025年12月22日", "end": "2025年12月29日"},
    search_count=3  # デフォルト: 3回
)

# Deep Research（日曜日用）
result = await client.deep_research(
    query="調査クエリ",
    timeout_seconds=1800
)

# 画像生成（スマートプロンプト対応）
result = await client.generate_blog_image(
    title="記事タイトル",
    summary="記事概要",
    topic_id="ai_tools",  # トピック別カラースキーム自動適用
    use_smart_prompt=True  # 記事分析を有効化（デフォルト）
)
```

### モデル定数

```python
GeminiClient.MODEL_PRO = "gemini-3-pro-preview"
GeminiClient.MODEL_FLASH = "gemini-2.0-flash"
GeminiClient.MODEL_FLASH_3 = "gemini-3-flash-preview"
GeminiClient.MODEL_IMAGE = "gemini-2.5-flash-image"
GeminiClient.AGENT_DEEP_RESEARCH = "deep-research-pro-preview-12-2025"
```

---

## タイムゾーンユーティリティ

```python
from lib.timezone import (
    now_jst,              # 現在の日本時間
    format_date,          # 日付フォーマット
    format_datetime_jst,  # Jekyll用日時
    get_weekday_name_jst  # 曜日名取得
)

# 使用例
today = now_jst()
date_str = format_date()  # "2025-12-29"
jekyll_date = format_datetime_jst()  # "2025-12-29 16:50:44 +0900"
weekday = get_weekday_name_jst()  # "sunday"
```

---

## トラブルシューティング

### Deep Research 400エラー

```
google.genai._interactions.BadRequestError: Error code: 400 - {'error': {'message': 'Request contains an invalid argument.'}}
```

**考えられる原因と解決策**:

1. **レート制限超過（最も多い原因）**
   - 原因: Deep ResearchのRPMは**1リクエスト/分**と非常に厳しい
   - 解決: 1分以上間隔を空けて再実行、または翌日に再試行
   - 注意: 月〜土はGoogle Searchを使用すれば回避可能

2. **課金設定がない**
   - 原因: Deep Research APIは**有料プラン専用**
   - 解決: [Google AI Studio](https://aistudio.google.com/) で Billing を有効化
   - 注意: 課金なしでも自動的にGoogle Searchにフォールバック

3. **ライブラリバージョンが古い**
   - 原因: `google-genai`が古いバージョン
   - 解決: `pip install google-genai>=1.56.0`

### 画像生成エラー

```
Error: Image generation failed
```

- **原因**: `response_modalities=["IMAGE"]`設定が不足
- **解決**: 最新のコードでは自動設定されています
- **回避**: `--skip-images`オプションで画像生成をスキップ

### フォールバック動作

Deep Research失敗時は自動的にMulti-Search（3回検索）にフォールバックします：

```
┌─────────────────────────┐
│ Deep Research API 呼び出し│
└────────────┬────────────┘
             │
      失敗？ ─┴─ 成功？
      │           │
   ┌──▼──────────┐  │
   │ エラーログ   │  └→ 深層調査結果を使用
   │ 出力        │
   └──┬──────────┘
      │
   ┌──▼──────────────────────┐
   │ Multi-Search（3回検索）  │
   │ にフォールバック        │
   │ ・最新ニュース検索      │
   │ ・専門家見解検索        │
   │ ・事例・統計検索        │
   └──────────────────────────┘
```

### Multi-Search（3回検索）の仕組み

3つの異なる視点から検索を行い、情報を統合します：

| 検索 | 視点 | 目的 |
|------|------|------|
| 1回目 | 最新ニュース・公式発表 | 直近の重要なニュースや発表を収集 |
| 2回目 | 専門家の見解・研究データ | 学術的知見やエビデンスを収集 |
| 3回目 | 実践事例・統計情報 | 具体的な事例と数値データを収集 |

#### トピック別専門クエリ（2025年12月30日改善）

各トピックに最適化された検索クエリを使用することで、より関連性の高い情報を収集します：

| トピック | 専門クエリ例 |
|----------|-------------|
| psychology | 心理学 メンタルヘルス 最新研究 論文発表 |
| education | 教育改革 学習指導要領 文部科学省 発表 |
| startup | スタートアップ 資金調達 IPO M&A ニュース |
| investment | 新NISA iDeCo 制度変更 金融庁 発表 |
| ai_tools | 生成AI ChatGPT Claude Gemini 新機能 アップデート |
| inclusive_education | 不登校 支援制度 フリースクール 教育機会確保法 |

これにより、Deep Research簡易版として高品質な情報収集を実現します。

### 高品質記事生成（2025年12月30日改善）

記事生成の品質向上のため、以下の機能を実装：

1. **トピック別ライティング指示**
   - 各トピックに最適化された執筆ガイドライン
   - 読者層に合わせた文体・トーンの調整

2. **読者価値最大化**
   - 問題解決型アプローチ
   - 具体的なデータ・事例の必須化
   - 実践可能なアクションポイントの提示

3. **品質チェックリスト**
   - 文字数: **4000-5500文字**（充実した長めの記事）
   - 具体的数値・データ最低5箇所
   - 各主張に根拠を明記
   - 7日以内の情報のみ使用
   - 参考文献は必ず**ハイパーリンク形式**で記載

---

## 技術スタック

| カテゴリ | 技術 |
|---------|------|
| **AI モデル** | Gemini 3 Pro, Gemini 3 Flash, Deep Research, Gemini 2.5 Flash image |
| **言語** | Python 3.11+, JavaScript (Node.js 20+) |
| **ライブラリ** | `google-genai>=1.56.0` |
| **検索** | Google Search Tool (Gemini Built-in) |
| **静的サイト** | Jekyll (GitHub Pages) |
| **CI/CD** | GitHub Actions |

---

## ライセンス

MIT License

---

## 関連リンク

- [GitHub Repository](https://github.com/takubon0202/if-blog-auto)
- [公開ブログ](https://takubon0202.github.io/if-blog-auto/)
- [Google AI Studio](https://aistudio.google.com/)
- [Gemini API ドキュメント](https://ai.google.dev/gemini-api/docs)
