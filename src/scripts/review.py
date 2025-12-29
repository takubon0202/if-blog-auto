#!/usr/bin/env python3
"""レビュースクリプト"""
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from lib.gemini_client import GeminiClient

async def review_article(article: dict) -> dict:
    """記事の最終レビュー"""
    client = GeminiClient()

    prompt = f"""
以下のブログ記事の品質をレビューし、必要に応じて修正してください。

【記事】
{article.get('content', '')}

【評価基準】
1. 情報の正確性
2. 読みやすさ・構成
3. オリジナリティ・価値
4. SEO最適化

問題があれば修正し、最終版をMarkdown形式で出力してください。
"""

    result = await client.generate_content(
        prompt=prompt,
        enable_search=True
    )

    return {
        "topic": article.get('topic'),
        "content": result.text,
        "reviewed": True,
        "status": "approved"
    }

if __name__ == "__main__":
    result = asyncio.run(review_article({"content": "Test content"}))
    print(result['content'])
