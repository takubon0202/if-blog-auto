#!/usr/bin/env python3
"""コンテンツ生成スクリプト"""
import asyncio
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from lib.gemini_client import GeminiClient

async def generate_article(topic_id: str, research_data: dict) -> dict:
    """記事を生成"""
    client = GeminiClient()

    topic_info = research_data.get('topic_info', {})

    prompt = f"""
あなたはプロのブログライターです。以下の調査結果を基に、読者にとって価値のあるブログ記事を執筆してください。

【トピック】{topic_info.get('name', topic_id)}
【ターゲット読者】{topic_info.get('target_audience', '一般読者')}

【調査結果】
{research_data.get('content', '')}

【執筆ガイドライン】
- 文字数: 2000文字程度
- 導入で読者の興味を引く問いかけや驚きの事実から始める
- 見出しは具体的で検索されやすいものに
- 専門用語は初出時に解説
- 具体的なデータ・事例を含める
- 段落は3-4文で区切る
- 結論で読者に行動を促す

【出力形式】
Markdown形式で、以下の構造で出力:

---
title: "タイトル"
description: "メタディスクリプション（120文字以内）"
date: {今日の日付}
categories: [カテゴリ]
tags: [タグ1, タグ2, タグ3]
---

# タイトル

導入文...

## セクション1
本文...

## セクション2
本文...

## まとめ
結論...

## 参考文献
- [タイトル](URL)
"""

    result = await client.generate_content(
        prompt=prompt,
        enable_search=True
    )

    return {
        "topic": topic_id,
        "content": result.text,
        "word_count": len(result.text)
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--topic', required=True)
    args = parser.parse_args()

    # Load research data from file or run research
    from research import run_research
    research_data = asyncio.run(run_research(args.topic))
    result = asyncio.run(generate_article(args.topic, research_data))
    print(result['content'])
