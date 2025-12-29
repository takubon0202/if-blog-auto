# Blog Automation Project Rules - Gemini API Edition

## プロジェクト概要
Gemini 3 Pro PreviewとDeep Research APIを活用し、最新トレンド情報を自動収集して画像付きブログ記事を生成・投稿するシステム。

## 技術スタック
- **AI**: Gemini 3 Pro Preview, Deep Research Pro Preview
- **言語**: Python 3.11+, JavaScript (Node.js 20+)
- **検索**: Google Search Tool (Gemini Built-in)
- **画像生成**: Imagen 3 / Gemini Image Generation
- **CI/CD**: GitHub Actions
- **CMS**: WordPress REST API / Notion API

## Gemini API使用ルール

### モデル選択
- 情報収集: `deep-research-pro-preview-12-2025`（非同期）
- コンテンツ生成: `gemini-3-pro-preview`
- 軽量タスク: `gemini-2.0-flash`

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

## スキル使用規則
```
Skill: src/skills/[skill-name].md
Purpose: [使用目的]
API: [使用するGemini API]
```

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
