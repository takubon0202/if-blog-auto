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

# 高品質記事のための追加ガイドライン
QUALITY_GUIDELINES = """
【高品質記事のための必須要件】

■ 読者価値の最大化
1. 問題解決型アプローチ
   - 読者が抱える具体的な課題を明確にする
   - 実践可能な解決策を提示する
   - 「なぜ」と「どうやって」を必ず説明する

2. 具体性の担保
   - 抽象的な説明ではなく具体例を必ず含める
   - 数値データ、統計、調査結果を積極的に引用
   - 「多くの」「さまざまな」などの曖昧な表現を避け、具体的に書く

3. 信頼性の確保
   - すべての主張に根拠（ソース）を明記
   - 専門家の見解や研究結果を引用
   - 反論や異なる視点も公平に紹介

■ 記事構成のベストプラクティス

1. 導入（リード文）- 最初の100字が勝負
   - 読者の課題や疑問に共感を示す
   - この記事を読むメリットを明確に伝える
   - 具体的な数値や事実で注意を引く
   例: 「2025年のAIツール市場は前年比40%成長...」

2. 本文 - 価値の提供
   - 各セクションで1つの明確なポイントを伝える
   - 抽象→具体の流れで説明
   - 箇条書きと段落文を効果的に組み合わせる

3. 結論 - 行動への促し
   - 記事の要点を簡潔にまとめる
   - 読者が今日からできる具体的なアクションを提示
   - 次のステップや関連情報への誘導

■ SEO最適化

1. タイトル
   - 検索意図に合致したキーワードを自然に含める
   - クリックしたくなる具体的なベネフィットを示す
   - 「2025年最新」「専門家が解説」など時事性・権威性を示す

2. 見出し（H2/H3）
   - 検索されやすいキーワードを含める
   - 質問形式も効果的（例: 「なぜ〜なのか」「〜する方法」）
   - スキャンリーダーにも内容が伝わるように

3. メタディスクリプション
   - 120字以内で記事の価値を凝縮
   - 検索結果でクリックしたくなる内容
"""


def extract_sources_text(sources: list) -> str:
    """
    ソースリストからMarkdown形式のハイパーリンクテキストを生成

    Args:
        sources: ソース情報のリスト

    Returns:
        Markdown形式のソーステキスト（ハイパーリンク付き）
    """
    if not sources:
        return "（調査結果から適切な参考文献を記載してください）"

    sources_list = []
    seen_urls = set()  # 重複URL防止

    for source in sources:
        if isinstance(source, dict):
            title = source.get('title', '').strip()
            url = source.get('url', source.get('uri', '')).strip()

            if url:
                # URLが完全形式でない場合は補完
                if not url.startswith('http'):
                    url = f"https://{url}"

                # 重複チェック
                if url in seen_urls:
                    continue
                seen_urls.add(url)

                # タイトルがない場合はURLからドメイン名を抽出
                if not title:
                    try:
                        from urllib.parse import urlparse
                        parsed = urlparse(url)
                        title = parsed.netloc or url
                    except:
                        title = url

                # Markdown ハイパーリンク形式
                sources_list.append(f"- [{title}]({url})")

        elif isinstance(source, str):
            source = source.strip()
            if source.startswith('http') and source not in seen_urls:
                seen_urls.add(source)
                sources_list.append(f"- [{source}]({source})")
            elif source and source not in seen_urls:
                # URLなしのテキストソースは除外（ハイパーリンクにできないため）
                pass

    if not sources_list:
        return "（URLを含む参考文献が見つかりませんでした）"

    return "\n".join(sources_list)


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

    # トピック別のライティング指示
    topic_writing_tips = {
        "psychology": "読者のメンタルヘルスに寄り添う温かみのある文体で。具体的なセルフケア方法を提示する。",
        "education": "教育現場で実践できる具体的なヒントを含める。保護者と教育者両方の視点を意識する。",
        "startup": "起業を検討している読者に勇気を与えつつ、リスクも現実的に伝える。成功・失敗両方の事例を。",
        "investment": "初心者にもわかりやすく。リスクについて必ず言及する。具体的な数値と制度の説明を。",
        "ai_tools": "実際に使える具体的なツールや活用法を紹介。技術的な内容も噛み砕いて説明する。",
        "inclusive_education": "当事者や保護者の気持ちに寄り添う。具体的な支援制度や相談先を紹介する。",
        "weekly_summary": "1週間の動向を俯瞰的に整理。各分野のつながりや傾向を分析する。"
    }
    writing_tip = topic_writing_tips.get(topic_id, "読者にとって実践的で価値のある情報を提供する。")

    prompt = f"""
あなたは{topic_info.get('name', topic_id)}分野の専門知識を持つプロのブログライターです。
以下の調査結果を基に、**読者が「読んでよかった」と思える高品質なブログ記事**を執筆してください。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
【基本情報】
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- 本日: {research_date}
- トピック: {topic_info.get('name', topic_id)}
- ターゲット読者: {topic_info.get('target_audience', '一般読者')}
- 調査期間: {start_date}〜{end_date}（7日以内の最新情報のみ使用）
- 参考ソース数: {sources_count}件

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
【調査結果（これを基に記事を執筆）】
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{research_data.get('content', '')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
【参考文献・引用元（記事末尾に必ず記載）】
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{sources_text}

{DESIGN_GUIDELINES}

{QUALITY_GUIDELINES}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
【このトピック特有の執筆ポイント】
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{writing_tip}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
【記事構成の必須要件】
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. 導入（リード文）
   - 読者の課題や関心に共感を示す一文から開始
   - この記事で得られる価値を明確に伝える
   - 具体的な数値やファクトで注意を引く

2. 本文（5-7セクション）
   - 各セクションで1つの明確なポイントを伝える
   - 具体的なデータ、事例、専門家の見解を必ず含める
   - 抽象的な説明の後に必ず具体例を示す
   - 「〜と言われています」ではなく「〇〇の調査によると」と根拠を明記

3. まとめ
   - 記事の要点を3つ程度に凝縮
   - 読者が今日から実践できる具体的なアクション
   - 「次に何をすべきか」を明確に示す

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
【品質チェックリスト（執筆後に確認）】
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
□ 文字数: 4000-5500文字（長めの充実した記事）
□ 絵文字を一切使用していないか
□ 具体的な数値・データを最低5箇所以上含めたか
□ 各主張に根拠（ソース）を明記したか
□ 読者が実践できる具体的なアクションを示したか
□ 7日より古い情報を含めていないか
□ 専門用語は初出時に説明したか
□ 各セクションに十分な内容（300-500字）があるか

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
【出力形式】
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Markdown形式で以下の構造で出力してください:

---
layout: post
title: "タイトル（具体的でSEOを意識、絵文字なし、60文字以内）"
description: "メタディスクリプション（この記事で得られる価値を凝縮、120文字以内）"
date: {today}
categories: [{topic_info.get('name', topic_id)}]
tags: [関連性の高いタグを3-5個]
author: "AI Blog Generator"
---

【リード文】読者の課題や関心に寄り添う導入。具体的な数値や事実で始める。（200-300字）

## 見出し1（検索キーワードを含む具体的な見出し）

本文（具体例やデータを含む、300-500字）

### サブ見出し1-1（必要に応じて）

詳細な説明

### サブ見出し1-2（必要に応じて）

詳細な説明

## 見出し2（重要なポイント）

本文（具体例やデータを含む、300-500字）

### サブ見出し2-1

詳細な説明

## 見出し3（実践的な内容）

本文（300-500字）

## 見出し4（データや事例）

本文（300-500字）

## 見出し5（専門家の見解や研究）

本文（300-500字）

## 見出し6（今後の展望）

本文（300-500字）

## まとめ：今日から始める3つのアクション

記事の要点を振り返り、読者が今日から実践できる具体的なアクションを提示（300-400字）

1. **アクション1**: 具体的な行動指針と期待される効果
2. **アクション2**: 具体的な行動指針と期待される効果
3. **アクション3**: 具体的な行動指針と期待される効果

---

## 参考文献・引用元

この記事は以下の情報源を参考に作成されました（{start_date}〜{end_date}の調査に基づく）：

**重要**: 必ず以下の形式でハイパーリンクを記載してください：
- [記事タイトル](https://完全なURL)

{sources_text}

---

*この記事は{research_date}時点の情報に基づいて作成されました。最新情報は各公式サイトでご確認ください。*
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
