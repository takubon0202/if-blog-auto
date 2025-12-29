# Gemini Research Skill - 7日以内最新情報限定版

## 概要
Gemini Deep ResearchとGoogle Search Toolを使用した情報収集スキル。
**必ず7日以内の最新情報のみを収集**します。

## 重要: 課金要件

**Deep Research APIは有料プラン専用です。**

| 項目 | 要件 |
|------|------|
| 課金設定 | [Google AI Studio](https://aistudio.google.com/) で Billing 有効化が必須 |
| 料金体系 | Gemini 3 Pro レート |
| 無料枠 | 使用不可 → 自動的にGoogle Search Toolにフォールバック |
| 必須パラメータ | `background=True` + `store=True` |

## 必須ライブラリバージョン

**重要**: Interactions API (Deep Research) を使用するには以下が必要です：
```
google-genai>=1.56.0
```

古いバージョン（0.5.0等）では400エラーが発生し、自動的にGoogle Searchにフォールバックします。

## 重要な制約条件

### 7日以内限定ルール（必須遵守）
```python
from lib.timezone import now_jst, format_date
from datetime import timedelta

MAX_AGE_DAYS = 7

# 日付範囲を計算（JST基準）
today = now_jst()
start_date = (today - timedelta(days=MAX_AGE_DAYS)).strftime("%Y年%m月%d日")
end_date = today.strftime("%Y年%m月%d日")

# クエリに日付制約を必ず含める
query = f"""
【重要】本日は{end_date}です。
必ず過去7日以内（{start_date}〜{end_date}）の最新情報のみを調査してください。
7日より古い情報は絶対に含めないでください。
"""
```

## API設定

### Deep Research（7日以内限定クエリ）
```python
from lib.timezone import now_jst, format_date
from datetime import timedelta

# 日付範囲を計算
today = now_jst()
start_date = (today - timedelta(days=7)).strftime("%Y年%m月%d日")
end_date = today.strftime("%Y年%m月%d日")

# 日付制約付きクエリを構築
research_query = f"""
【重要】本日は{end_date}です。
必ず過去7日以内（{start_date}〜{end_date}）の最新情報のみを調査してください。

【調査トピック】{topic}

【調査要件】
- 7日より古い情報は絶対に含めない
- 各情報に日付を明記（YYYY年MM月DD日形式）
- ソースURLを必ず含める（https://完全URL）
- 最低5つ以上の信頼できるソースを使用
"""

# 非同期リサーチの実行（client.aioを使用）
# 重要: asyncio.to_thread()ではなく、ネイティブの非同期クライアントを使用
# 重要: background=True には store=True が必須
interaction = await client.aio.interactions.create(
    input=research_query,
    agent="deep-research-pro-preview-12-2025",
    background=True,
    store=True  # background=True requires store=True
)

# ポーリングで結果取得（非同期）
while True:
    result = await client.aio.interactions.get(interaction.id)
    if result.status == "completed":
        return result.outputs[-1].text
    elif result.status == "failed":
        raise Exception(result.error)
    await asyncio.sleep(10)
```

### Google Search Tool（フォールバック）
```python
from lib.timezone import format_date

today_jst = format_date(fmt="%Y年%m月%d日")

# 検索ツール有効化（日付付きクエリ）
response = client.models.generate_content(
    model="gemini-3-pro-preview",
    contents=f"{topic} 最新 {today_jst} 過去7日間",
    config={
        "tools": [{"google_search": {}}]
    }
)

# Grounding情報の取得
if response.grounding_metadata:
    for source in response.grounding_metadata.sources:
        print(f"Source: {source.uri}")
```

## リサーチクエリテンプレート

### トレンド調査（7日以内限定）
```
【重要】本日は{today}です。
必ず過去7日以内（{start_date}〜{end_date}）の最新情報のみを調査してください。

【調査依頼】{topic}に関する最新動向

調査期間: {start_date}〜{end_date}（7日間）
優先言語: 日本語、英語

必要な情報:
1. 最新ニュース・発表（日付必須）
2. 業界動向・市場分析（日付必須）
3. 専門家の見解（発表日付必須）
4. 統計データ（調査日付必須）
5. 今後の予測

出力要件:
- 各情報のソースURL必須（https://完全URL）
- 日付情報を「YYYY年MM月DD日」形式で明記
- 7日より古い情報は含めない
- 最低5つ以上の信頼できるソースを使用
```

## ソース収集の必須要件

### URLの記載形式
```markdown
- [ソースタイトル](https://example.com/full/url/path)
- [記事タイトル2](https://another-source.com/article)
```

### 必須チェックリスト
- [ ] 7日以内の情報のみか
- [ ] 各情報に日付が明記されているか
- [ ] ソースURLが完全形式か（https://で始まる）
- [ ] 最低5つ以上のソースがあるか
- [ ] 信頼できるソースを優先しているか

## エラーハンドリング
```python
async def safe_research(query: str, timeout: int = 300) -> dict:
    try:
        result = await client.deep_research(query, timeout)
        return result
    except TimeoutError:
        # フォールバック: Google Search（日付付きクエリ）
        from lib.timezone import format_date
        today = format_date(fmt="%Y年%m月%d日")
        return await client.search_and_generate(
            query=f"{query} 最新 {today}",
            generation_prompt="検索結果を構造化してJSON形式で出力（7日以内のみ）"
        )
    except RateLimitError:
        await asyncio.sleep(60)
        return await safe_research(query, timeout)
```

## 関連スキル
- `timezone.md`: JST日時処理
- `gemini-content.md`: 記事生成（引用元付き）
