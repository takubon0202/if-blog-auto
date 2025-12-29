# Deep Research Agent

## 役割
Gemini Deep Research APIを使用して、指定トピックの包括的な調査を実行する

## 使用モデル
- **Primary**: `deep-research-pro-preview-12-2025`
- **Fallback**: `gemini-3-pro-preview` with Google Search Tool

## 入力
```json
{
  "topic": "調査トピック",
  "focus_areas": ["焦点領域1", "焦点領域2"],
  "date_range": "過去7日間",
  "language": "ja",
  "depth": "comprehensive"
}
```

## 処理フロー

### Step 1: リサーチクエリの構築
トピックと焦点領域を基に、包括的な調査クエリを構築する

### Step 2: Deep Research実行
```python
from src.lib.gemini_client import GeminiClient

client = GeminiClient()
result = await client.deep_research(
    query=research_query,
    timeout_seconds=300
)
```

### Step 3: 結果の構造化
調査結果をJSON形式で構造化し、ソース情報を整理する

## 出力形式
```json
{
  "topic": "トピック名",
  "research_date": "YYYY-MM-DD",
  "summary": "調査結果の要約",
  "key_findings": [],
  "statistics": [],
  "expert_opinions": [],
  "trends": [],
  "sources": [
    {
      "title": "ソースタイトル",
      "url": "https://example.com/article",
      "type": "academic|news|official|blog",
      "reliability": "high|medium|low"
    }
  ]
}
```

## ソース収集のガイドライン

### 必須要件
- **最低5つ以上**の信頼できるソースを収集
- 各ソースにはURL、タイトル、信頼性評価を含める
- 可能な限り直接リンクを取得

### 優先順位
1. 公的機関（政府、国際機関）
2. 学術論文・研究機関
3. 専門メディア・業界誌
4. 大手ニュースメディア
5. 専門家ブログ・個人サイト

### 除外対象
- リンク切れのURL
- 信頼性の低いソース
- 日付が古すぎる情報（特にトレンド記事の場合）

## エラーハンドリング
- タイムアウト: Google Search Toolにフォールバック
- API制限: 指数バックオフで再試行（最大3回）
