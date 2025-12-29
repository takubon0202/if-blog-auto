# Blog Automation Project Rules - Gemini API Edition

## プロジェクト概要
Gemini 3 Pro PreviewとDeep Research APIを活用し、最新トレンド情報を自動収集して画像付きブログ記事を生成・投稿するシステム。

## 技術スタック
- **AI**: Gemini 3 Pro Preview, Deep Research Pro Preview
- **言語**: Python 3.11+, JavaScript (Node.js 20+)
- **検索**: Google Search Tool (Gemini Built-in)
- **画像生成**: Gemini 2.5 Flash image (`gemini-2.5-flash-image`)
- **CI/CD**: GitHub Actions
- **CMS**: GitHub Pages (Jekyll)
- **公開URL**: https://takubon0202.github.io/if-blog-auto/

## システムフロー
```
1. Deep Research (情報収集)
   └── deep-research-pro-preview-12-2025 で最新情報を調査

2. Gemini 3 Pro (ブログ生成)
   └── gemini-3-pro-preview で記事を執筆

3. 画像生成
   └── gemini-2.5-flash-image でアイキャッチ画像生成

4. SEO最適化 & レビュー
   └── gemini-2.0-flash で品質チェック

5. GitHub Pages投稿
   └── Git push → Jekyll自動ビルド → 公開
```

## Gemini API使用ルール

### モデル選択
| 用途 | モデル |
|------|--------|
| 情報収集 | `deep-research-pro-preview-12-2025`（非同期） |
| コンテンツ生成 | `gemini-3-pro-preview` |
| 画像生成 | `gemini-2.5-flash-image` |
| 軽量タスク | `gemini-2.0-flash` |

### API呼び出しパターン
```python
# 同期的なコンテンツ生成
response = ai.models.generate_content(
    model="gemini-3-pro-preview",
    contents=prompt
)

# 非同期Deep Research
interaction = client.interactions.create(
    input=research_query,
    agent="deep-research-pro-preview-12-2025",
    background=True
)

# 画像生成（Gemini 2.5 Flash image）
response = ai.models.generate_content(
    model="gemini-2.5-flash-image",
    contents=image_prompt
)
# レスポンスのinline_dataから画像を取得
```

### Google Search Tool使用
```python
# 検索ツール有効化
response = ai.models.generate_content(
    model="gemini-3-pro-preview",
    contents=prompt,
    config={
        "tools": [{"google_search": {}}]
    }
)
```

## サブエージェント呼び出し規則
```
Task: [具体的なタスク内容]
Agent: src/agents/[agent-name].md
Gemini Model: [使用モデル]
Input: [入力データ]
Expected Output: [期待する出力形式]
```

### 利用可能なサブエージェント
- `deep-research-agent.md`: Deep Researchによる情報収集
- `writing-agent.md`: Gemini 3 Proによる記事執筆
- `image-agent.md`: Gemini 2.5 Flash imageによる画像生成
- `seo-agent.md`: SEO最適化
- `review-agent.md`: 品質レビュー

## スキル使用規則
```
Skill: src/skills/[skill-name].md
Purpose: [使用目的]
API: [使用するGemini API]
```

### 利用可能なスキル
- `gemini-research.md`: Deep Research実行
- `gemini-content.md`: コンテンツ生成
- `image-generation.md`: 画像生成（Gemini 2.5 Flash image）
- `cms-integration.md`: CMS連携

## 品質基準
- ブログ記事: 最低1500文字
- SEOスコア: 80点以上目標
- 画像: 1記事につき最低2枚
- 情報ソース: Deep Researchで最低5つの信頼できるソース

## 禁止事項
- 著作権侵害コンテンツの生成
- 未検証情報の断定的記述
- APIキーのハードコーディング
- レート制限を無視した連続呼び出し
