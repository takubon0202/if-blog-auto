# Gemini Research Skill

## 概要
Gemini Deep ResearchとGoogle Search Toolを使用した情報収集スキル

## API設定

### Deep Research
```python
# 非同期リサーチの実行
interaction = client.interactions.create(
    input=research_query,
    agent="deep-research-pro-preview-12-2025",
    background=True
)

# ポーリングで結果取得
while True:
    result = client.interactions.get(interaction.id)
    if result.status == "completed":
        return result.outputs[-1].text
    elif result.status == "failed":
        raise Exception(result.error)
    await asyncio.sleep(10)
```

### Google Search Tool
```python
# 検索ツール有効化
response = client.models.generate_content(
    model="gemini-3-pro-preview",
    contents="最新のAI動向について調べてください",
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

### トレンド調査
```
【調査依頼】{topic}に関する最新動向

調査期間: 過去{days}日間
優先言語: 日本語、英語

必要な情報:
1. 最新ニュース・発表
2. 業界動向・市場分析
3. 専門家の見解
4. 統計データ
5. 今後の予測

出力要件:
- 各情報のソースURL必須
- 日付情報を明記
- 信頼性の高い情報源を優先
```

## エラーハンドリング
```python
async def safe_research(query: str, timeout: int = 300) -> dict:
    try:
        result = await client.deep_research(query, timeout)
        return result
    except TimeoutError:
        # フォールバック: Google Search
        return await client.search_and_generate(
            query=query,
            generation_prompt="検索結果を構造化してJSON形式で出力"
        )
    except RateLimitError:
        await asyncio.sleep(60)
        return await safe_research(query, timeout)
```
