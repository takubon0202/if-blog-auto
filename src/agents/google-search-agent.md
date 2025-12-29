# Google Search Agent

## 役割
Google Search Toolを使用して、**7日以内の最新情報のみ**を高速に収集する

## 使用タイミング（メイン）

| 実行タイミング | リサーチ方法 |
|--------------|-------------|
| **月〜土曜日（デフォルト）** | Google Search Tool |
| **手動指定時** | Google Search Tool |
| **Deep Research失敗時** | フォールバックとしてGoogle Search |

**設計方針**: Google Search Toolを日常的なリサーチのメインとして使用します。
高速（数秒）で安定しており、レート制限も緩やかです。

## 特徴

| 項目 | Google Search Tool | Deep Research |
|------|-------------------|---------------|
| 処理時間 | **数秒** | 約5分 |
| レート制限 | 緩やか | RPM 1/分（厳しい） |
| 課金 | 無料枠あり | 有料のみ |
| 情報深度 | 表面的〜中程度 | 包括的・深層 |
| 推奨用途 | 日常リサーチ | 週1回の深層調査 |

## 使用モデル
- **Primary**: `gemini-3-pro-preview` + Google Search Tool

## 重要な制約条件

### 7日以内限定ルール（必須遵守）
- **調査対象期間**: 現在日（JST）から過去7日間のみ
- 7日より古い情報は絶対に含めない
- すべての情報に具体的な日付（YYYY年MM月DD日）を明記
- 日時処理はすべて日本標準時（JST = UTC+9）を使用

### 日付範囲の計算
```python
from lib.timezone import now_jst
from datetime import timedelta

today = now_jst()
start_date = today - timedelta(days=7)
# 例: 2025年12月22日〜2025年12月29日
```

## 入力
```json
{
  "topic": "調査トピック",
  "focus_areas": ["焦点領域1", "焦点領域2"],
  "date_range": "過去7日間（自動計算）",
  "language": "ja"
}
```

## 処理フロー

### Step 1: 日付範囲の確定（JST基準）
```python
from lib.timezone import now_jst, format_date
from datetime import timedelta

today = now_jst()
start_date = (today - timedelta(days=7)).strftime("%Y年%m月%d日")
end_date = today.strftime("%Y年%m月%d日")
```

### Step 2: Google Search実行
```python
from src.lib.gemini_client import GeminiClient

client = GeminiClient()
result = await client.search_and_generate(
    query=f"{topic} 最新 {today_jst}",
    generation_prompt=research_query
)
# Google Search Toolを有効にしてGemini 3 Proで検索＆生成
```

### Step 3: 結果の構造化
検索結果をJSON形式で構造化し、ソース情報を整理する

## 出力形式
```json
{
  "topic": "トピック名",
  "research_date": "2025年12月29日",
  "date_range": {
    "start": "2025年12月22日",
    "end": "2025年12月29日",
    "max_age_days": 7
  },
  "summary": "調査結果の要約",
  "key_findings": [
    {
      "finding": "発見内容",
      "date": "2025年12月28日",
      "source_url": "https://example.com/article"
    }
  ],
  "sources": [
    {
      "title": "ソースタイトル",
      "url": "https://example.com/article"
    }
  ],
  "method": "google_search"
}
```

## ソース収集のガイドライン（必須遵守）

### 必須要件
- **最低5つ以上**の信頼できるソースを収集
- 各ソースには必ず**完全なURL**を含める（https://で始まる）
- **7日以内に公開された情報のみ**を採用
- URLはマークダウンリンク形式 `[タイトル](URL)` で記載

### 優先順位
1. 公的機関（政府、国際機関）
2. 学術論文・研究機関
3. 専門メディア・業界誌
4. 大手ニュースメディア
5. 専門家ブログ・個人サイト

## クエリテンプレート
```
【重要】本日は{today_jst}です。必ず過去7日以内（{start_date}〜{end_date}）の最新情報のみを調査してください。

【調査トピック】{topic_name}

【調査要件 - 必須遵守】
1. 期間制限: {start_date}〜{end_date}の7日以内の情報のみ
2. 各情報には必ず具体的な日付（YYYY年MM月DD日）を明記

【ソース・引用元の記載 - 必須】
- 各情報の引用元URL（ソースURL）を必ず含めてください
- 最低5つ以上の異なるソースを使用してください
- URLは完全な形式で記載してください（https://で始まる完全URL）
```

## 関連エージェント
- `deep-research-agent.md`: 週1回（日曜日）の深層調査

## 関連スキル
- `gemini-research.md`: リサーチ実行
- `timezone.md`: JST日時処理
