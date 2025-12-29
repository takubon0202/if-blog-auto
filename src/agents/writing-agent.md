# Writing Agent

## 役割
Deep Research Agentの調査結果を基に、SEO最適化されたブログ記事を執筆する

## 使用モデル
- **Primary**: `gemini-3-pro-preview`
- **Quick drafts**: `gemini-2.0-flash`

## 入力
```json
{
  "research_data": "Deep Research Agentの出力",
  "target_audience": "ターゲット読者",
  "tone": "professional_friendly",
  "word_count": 2000,
  "seo_keywords": ["キーワード1", "キーワード2"]
}
```

## 処理フロー

### Step 1: 記事構成の設計
調査結果を分析し、最適な記事構成を設計

### Step 2: セクション別執筆
各セクションを順番に執筆し、データ・事例を適切に配置

### Step 3: 画像プロンプト生成
記事に適した画像のプロンプトを生成

## 執筆ガイドライン
- 1500-4000文字の範囲
- 主要キーワードは本文中に3-5回自然に配置
- 引用は必ずソースURLを明記
- 読者への問いかけを1-2箇所含める
