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
  "sources_used": []
}
```

## エラーハンドリング
- タイムアウト: Google Search Toolにフォールバック
- API制限: 指数バックオフで再試行（最大3回）
