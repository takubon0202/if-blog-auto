#!/usr/bin/env python3
"""SEO最適化スクリプト"""
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from lib.gemini_client import GeminiClient

async def optimize_seo(article: dict) -> dict:
    """記事のSEO最適化"""
    client = GeminiClient()

    prompt = f"""
以下のブログ記事をSEO観点で分析し、最適化してください。

【記事】
{article.get('content', '')}

【分析・最適化項目】
1. タイトル（60文字以内、キーワード含有）
2. メタディスクリプション（120文字以内）
3. 見出し構造の最適化
4. キーワード密度チェック
5. 読みやすさの改善

最適化後の完全な記事をMarkdown形式で出力してください。
"""

    result = await client.generate_content(prompt=prompt)

    return {
        "topic": article.get('topic'),
        "content": result.text,
        "optimized": True
    }

if __name__ == "__main__":
    result = asyncio.run(optimize_seo({"content": "Test content"}))
    print(result['content'])
