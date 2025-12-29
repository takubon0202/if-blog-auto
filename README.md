# Blog Automation System - Gemini API Edition

Gemini 3 Pro PreviewとDeep Research APIを活用した、最新トレンド情報を自動収集して画像付きブログ記事を生成・投稿するシステム。

## 機能

- **Deep Research**: Gemini Deep Research APIによる包括的な情報収集
- **自動記事生成**: SEO最適化されたブログ記事の自動執筆
- **画像生成**: Imagen 3による記事用画像の自動生成
- **品質管理**: ファクトチェックと品質スコアリング
- **自動公開**: WordPress/Notion への自動投稿
- **スケジュール実行**: GitHub Actionsによる日次自動実行

## 対象トピック

- 心理学・メンタルヘルス
- 教育・学習科学
- 起業家育成・スタートアップ
- 投資教育・金融リテラシー
- AIツール・技術動向
- 不登校支援
- 発達障害・ニューロダイバーシティ

## セットアップ

### 1. 依存関係のインストール

```bash
# Python依存関係
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Node.js依存関係
npm install
```

### 2. 環境変数の設定

`.env.example`をコピーして`.env`を作成し、APIキーを設定:

```bash
cp .env.example .env
```

必要な環境変数:
- `GOOGLE_AI_API_KEY`: Google AI Studio APIキー

### 3. GitHub Secrets設定（GitHub Actions使用時）

リポジトリ設定で以下のSecretsを追加:
- `GOOGLE_AI_API_KEY`

### 4. GitHub Pages設定

1. リポジトリのSettings > Pages
2. Source: `Deploy from a branch`
3. Branch: `main` / `docs`
4. 保存して数分待つと公開される

## 使い方

### ローカル実行

```bash
# 記事生成（トピック指定）
python src/scripts/main.py --topic ai_tools

# ドライラン（ファイル保存なし）
python src/scripts/main.py --topic psychology --dry-run
```

### ダッシュボード起動

```bash
cd dashboard
uvicorn api.server:app --reload
# http://localhost:8000 でアクセス
```

### GitHub Actions

- **自動実行**: 毎日日本時間5時に自動実行
- **手動実行**: Actions > Manual Blog Generation > Run workflow

## プロジェクト構造

```
blog-automation/
├── .github/workflows/      # GitHub Actions
├── src/
│   ├── agents/            # サブエージェント定義
│   ├── skills/            # スキル定義
│   ├── templates/         # テンプレート
│   ├── config/            # 設定ファイル
│   ├── lib/               # ライブラリ
│   └── scripts/           # 実行スクリプト
├── dashboard/             # 管理ダッシュボード
├── output/                # 生成された記事
├── CLAUDE.md              # プロジェクトルール
├── requirements.txt       # Python依存関係
└── package.json           # Node.js依存関係
```

## 技術スタック

- **AI**: Gemini 3 Pro Preview, Deep Research Pro Preview
- **言語**: Python 3.11+, JavaScript (Node.js 20+)
- **検索**: Google Search Tool (Gemini Built-in)
- **画像生成**: Gemini 2.5 Flash image (`gemini-2.5-flash-image`)
- **Web Framework**: FastAPI
- **CI/CD**: GitHub Actions
- **CMS**: GitHub Pages (Jekyll)
- **公開URL**: https://takubon0202.github.io/if-blog-auto/

## システムフロー

```
┌─────────────────┐
│  1. Deep Research │  ← deep-research-pro-preview-12-2025
│    (情報収集)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  2. Gemini 3 Pro │  ← gemini-3-pro-preview
│   (ブログ生成)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 3. Gemini 2.5    │  ← gemini-2.5-flash-image
│ Flash (画像生成) │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  4. SEO最適化   │  ← gemini-2.0-flash
│   & レビュー    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 5. GitHub Pages │
│     投稿        │
└─────────────────┘
```

## ライセンス

MIT License
