#!/usr/bin/env python3
"""
コンテンツ生成スクリプト - 7日以内最新情報 & 引用元必須版

Design Guidelines:
- 絵文字禁止
- 紫色系禁止
- AIっぽい表現禁止
- 7日以内の最新情報のみ使用
- 引用元・参考文献を必ず記載
"""
import asyncio
import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from lib.gemini_client import GeminiClient
from lib.timezone import format_date, now_jst


# デザインガイドラインを定数として定義
DESIGN_GUIDELINES = """
【デザインガイドライン - 必ず遵守してください】

■ 絶対禁止事項
1. 絵文字の使用禁止 - タイトル、見出し、本文すべてで絵文字を使わないでください
2. AIっぽい表現の禁止:
   - 「革新的」「画期的」「驚くべき」などの陳腐な表現
   - 過度な感嘆符（！）の使用
   - 「さあ、始めましょう」などの押し付けがましい表現
   - 「〜してみてはいかがでしょうか」などの回りくどい表現

■ タイトルルール
- 具体的で価値が伝わるタイトル
- 数字を効果的に使用（例: 「5つの方法」「3つのポイント」）
- 60文字以内
- 絵文字は絶対に使用しない

■ 見出しルール
- H2: 主要セクションの区切り（5-7個程度）
- H3: サブトピック
- 見出しだけで記事の内容が把握できるように

■ 本文ルール
- 1段落は3-5文程度
- 専門用語は初出時に説明
- 箇条書きを効果的に使用
- 具体例やデータを必ず含める
- 根拠のない主張は避ける

■ トーン
- 専門的だが親しみやすい
- 押し付けがましくない
- 読者を尊重した表現
- 科学的・論理的なアプローチ
"""


def extract_sources_text(sources: list) -> str:
    """
    ソースリストからMarkdown形式のテキストを生成

    Args:
        sources: ソース情報のリスト

    Returns:
        Markdown形式のソーステキスト
    """
    if not sources:
        return "（調査結果から適切な参考文献を記載してください）"

    sources_list = []
    for source in sources:
        if isinstance(source, dict):
            title = source.get('title', '')
            url = source.get('url', source.get('uri', ''))
            if url:
                # URLが完全形式でない場合は補完
                if not url.startswith('http'):
                    url = f"https://{url}"
                sources_list.append(f"- [{title or url}]({url})")
        elif isinstance(source, str):
            if source.startswith('http'):
                sources_list.append(f"- [{source}]({source})")
            else:
                sources_list.append(f"- {source}")

    return "\n".join(sources_list) if sources_list else "（利用可能なソースがありません）"


async def generate_article(topic_id: str, research_data: dict) -> dict:
    """
    記事を生成（7日以内最新情報 & 引用元必須）

    Args:
        topic_id: トピックID
        research_data: 調査データ（sources, date_range含む）

    Returns:
        生成された記事データ（引用元セクション含む）
    """
    client = GeminiClient()

    topic_info = research_data.get('topic_info', {})
    today = format_date()  # JST date

    # リサーチ日付範囲を取得
    date_range = research_data.get('date_range', {})
    start_date = date_range.get('start', '')
    end_date = date_range.get('end', today)
    research_date = research_data.get('research_date', today)

    # ソース情報を抽出（必須）
    sources = research_data.get('sources', [])
    sources_text = extract_sources_text(sources)
    sources_count = len(sources)

    prompt = f"""
あなたはプロのブログライターです。以下の調査結果を基に、読者にとって価値のあるブログ記事を執筆してください。

【重要】本日は{research_date}です。記事内の情報は過去7日以内（{start_date}〜{end_date}）の最新情報のみを使用してください。

【トピック】{topic_info.get('name', topic_id)}
【ターゲット読者】{topic_info.get('target_audience', '一般読者')}
【調査期間】{start_date}〜{end_date}（7日以内の最新情報）

【調査結果】
{research_data.get('content', '')}

【参考文献・引用元（{sources_count}件 - 記事末尾に必ず記載すること）】
{sources_text}

{DESIGN_GUIDELINES}

【執筆ガイドライン】
- 文字数: 2000-3000文字
- 導入で読者の興味を引く問いかけや具体的な事実から始める
- 見出しは具体的で検索されやすいものに
- 専門用語は初出時に解説
- 具体的なデータ・事例を含める（日付を明記）
- 段落は3-4文で区切る
- 結論で読者に具体的な行動指針を示す
- 7日より古い情報は使用しない

【引用元記載ルール - 必須】
- 記事末尾に必ず「参考文献・引用元」セクションを設ける
- 上記の参考文献リストをそのまま記載する
- URLは必ずマークダウンリンク形式 [タイトル](URL) で記載
- <div class="sources-section">タグで囲む

【出力形式】
Markdown形式で、以下の構造で出力してください:

---
layout: post
title: "タイトル（絵文字なし、60文字以内）"
description: "メタディスクリプション（120文字以内）"
date: {today}
categories: [{topic_info.get('name', topic_id)}]
tags: [タグ1, タグ2, タグ3]
author: "AI Blog Generator"
---

導入文（読者の関心を引く問いかけまたは事実から開始）

## セクション1の見出し

本文（具体例やデータを含む、日付を明記）

## セクション2の見出し

本文...

## セクション3の見出し

本文...

## まとめ

結論と具体的な行動指針

---

## 参考文献・引用元

<div class="sources-section">

この記事は以下の情報源を参考に作成されました（{start_date}〜{end_date}の調査に基づく）：

{sources_text}

</div>

---

*この記事はAIによって生成されました。情報は{research_date}時点のものです。*
"""

    result = await client.generate_content(
        prompt=prompt,
        model=GeminiClient.MODEL_PRO,
        enable_search=True,
        temperature=0.7
    )

    content = result.text

    # 絵文字を除去（安全策として）
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # flags
        "\U00002702-\U000027B0"
        "\U000024C2-\U0001F251"
        "]+",
        flags=re.UNICODE
    )
    content = emoji_pattern.sub('', content)

    # 引用元セクションが含まれているか確認
    if "参考文献・引用元" not in content and sources:
        # 引用元セクションがない場合は追加
        sources_section = f"""

---

## 参考文献・引用元

<div class="sources-section">

この記事は以下の情報源を参考に作成されました（{start_date}〜{end_date}の調査に基づく）：

{sources_text}

</div>

---

*この記事はAIによって生成されました。情報は{research_date}時点のものです。*
"""
        content = content.rstrip() + sources_section

    # タイトルを抽出
    title_match = re.search(r'title:\s*["\']?(.+?)["\']?\s*\n', content)
    title = title_match.group(1) if title_match else f"{topic_info.get('name', topic_id)}に関する最新情報"

    # descriptionを抽出
    desc_match = re.search(r'description:\s*["\']?(.+?)["\']?\s*\n', content)
    description = desc_match.group(1) if desc_match else ""

    return {
        "topic": topic_id,
        "title": title,
        "description": description,
        "content": content,
        "word_count": len(content),
        "categories": [topic_info.get('name', topic_id)],
        "tags": [],
        "sources": sources,
        "research_date": research_date,
        "date_range": date_range
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate blog article with design guidelines")
    parser.add_argument('--topic', required=True, help='Topic ID')
    args = parser.parse_args()

    # Load research data from file or run research
    from research import run_research
    research_data = asyncio.run(run_research(args.topic))
    result = asyncio.run(generate_article(args.topic, research_data))
    print(result['content'])
