#!/usr/bin/env python3
"""
リサーチ実行スクリプト - 7日以内最新情報限定版

Google Search Tool（デフォルト）またはDeep Research APIを使用して、
必ず7日以内の最新情報のみを収集します。
すべての日時処理は日本標準時(JST)を使用します。

設計方針:
- Google Search Tool: 日常的な情報収集（メイン）
- Deep Research: 週1回（日曜日）の深層調査
"""
import asyncio
import argparse
import json
import sys
from pathlib import Path
from datetime import timedelta

sys.path.insert(0, str(Path(__file__).parent.parent))
from lib.gemini_client import GeminiClient
from lib.timezone import now_jst, format_date

# 最新情報の期間制限（日数）
MAX_AGE_DAYS = 7


def get_date_range_jst() -> tuple[str, str]:
    """
    7日以内の日付範囲を取得（JST基準）

    Returns:
        tuple: (開始日, 終了日) の文字列タプル
    """
    today = now_jst()
    start_date = today - timedelta(days=MAX_AGE_DAYS)
    return (
        start_date.strftime("%Y年%m月%d日"),
        today.strftime("%Y年%m月%d日")
    )


async def run_research(topic_id: str, use_deep_research: bool = False) -> dict:
    """
    リサーチを実行（7日以内の最新情報限定）

    Args:
        topic_id: トピックID
        use_deep_research: Deep Research APIを使用するか（デフォルト: False = Google Search）

    Returns:
        dict: リサーチ結果（sources含む）

    Note:
        - デフォルトはGoogle Search Tool（高速・安定）
        - Deep Researchは週1回（日曜日）または手動指定時のみ推奨
        - Deep ResearchはRPM 1/分の制限があるため注意
    """
    # トピック設定を読み込み
    config_path = Path(__file__).parent.parent / "config" / "topics.json"
    with open(config_path, encoding="utf-8") as f:
        topics_config = json.load(f)

    topic_info = next(
        (t for t in topics_config["topics"] if t["id"] == topic_id),
        None
    )

    if not topic_info:
        raise ValueError(f"Unknown topic: {topic_id}")

    client = GeminiClient()

    # 日付範囲を取得（JST基準）
    start_date, end_date = get_date_range_jst()
    today_jst = format_date(fmt="%Y年%m月%d日")

    research_query = f"""
【重要】本日は{today_jst}です。必ず過去7日以内（{start_date}〜{end_date}）の最新情報のみを調査してください。

【調査トピック】{topic_info['name']}

【調査要件 - 必須遵守】
1. 期間制限: {start_date}〜{end_date}の7日以内の情報のみ
   - 7日より古い情報は絶対に含めないでください
   - 各情報には必ず具体的な日付（YYYY年MM月DD日）を明記してください
2. 言語: 日本語優先（英語ソースも可）
3. 焦点: {', '.join(topic_info['research_focus'])}
4. キーワード: {', '.join(topic_info['keywords'])}

【必要な情報】
1. 最新ニュース・動向（具体的な日付必須）
2. 専門家の見解・研究結果（発表日付必須）
3. 統計データ・調査結果（調査日付必須）
4. 具体的な事例（発生日付必須）
5. 今後の展望

【ソース・引用元の記載 - 必須】
- 各情報の引用元URL（ソースURL）を必ず含めてください
- 信頼できるソース（公的機関、学術論文、専門メディア）を優先してください
- 最低5つ以上の異なるソースを使用してください
- URLは完全な形式で記載してください（https://で始まる完全URL）

【出力形式】
- 日付は「YYYY年MM月DD日」形式で統一
- ソースURLは[タイトル](URL)のMarkdown形式で記載
"""

    if use_deep_research:
        try:
            result = await client.deep_research(research_query)

            # ソース情報を強化（日付範囲を追加）
            sources = result.sources or []
            enhanced_sources = []
            for source in sources:
                enhanced_source = dict(source)
                enhanced_source["research_date_range"] = f"{start_date}〜{end_date}"
                enhanced_sources.append(enhanced_source)

            return {
                "topic": topic_id,
                "topic_info": topic_info,
                "content": result.content,
                "sources": enhanced_sources,
                "research_date": today_jst,
                "date_range": {
                    "start": start_date,
                    "end": end_date,
                    "max_age_days": MAX_AGE_DAYS
                },
                "method": "deep_research"
            }
        except Exception as e:
            # Deep Researchが失敗した場合、Google Searchにフォールバック
            import logging
            logger = logging.getLogger(__name__)

            # 重要: フォールバック発生を明確に通知
            logger.error("=" * 60)
            logger.error("【重要】Deep Research APIが失敗しました")
            logger.error(f"エラー内容: {e}")
            logger.error("フォールバック: Google Search Tool (gemini-3-pro-preview) を使用します")
            logger.error("=" * 60)

            use_deep_research = False  # フォールバック
            fallback_error = str(e)

    if not use_deep_research:
        # Google Search Toolを使用（フォールバック）
        import logging
        logger = logging.getLogger(__name__)
        logger.info("【フォールバック実行中】Google Search Tool + Gemini 3 Pro Preview")

        result = await client.search_and_generate(
            query=f"{topic_info['name']} 最新 {today_jst}",
            generation_prompt=research_query
        )

        logger.info("【フォールバック完了】Google Searchでの情報収集が完了しました")

        return {
            "topic": topic_id,
            "topic_info": topic_info,
            "content": result.text,
            "sources": result.grounding_sources or [],
            "research_date": today_jst,
            "date_range": {
                "start": start_date,
                "end": end_date,
                "max_age_days": MAX_AGE_DAYS
            },
            "method": "google_search",
            "fallback_reason": fallback_error if 'fallback_error' in dir() else "Deep Research not used"
        }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="7日以内の最新情報を収集（デフォルト: Google Search）"
    )
    parser.add_argument('--topic', required=True, help='トピックID')
    parser.add_argument('--use-deep-research', action='store_true', default=False,
                        help='Deep Research APIを使用（週1回の深層調査向け）')
    parser.add_argument('--use-google-search', action='store_true', default=True,
                        help='Google Search Toolを使用（デフォルト・推奨）')
    args = parser.parse_args()

    # --use-deep-research が指定された場合のみDeep Researchを使用
    use_deep = args.use_deep_research
    result = asyncio.run(run_research(args.topic, use_deep))

    # 結果を出力
    print(f"\n=== リサーチ結果 ({result['research_date']}) ===")
    print(f"期間: {result['date_range']['start']} 〜 {result['date_range']['end']}")
    print(f"ソース数: {len(result['sources'])}")
    print(json.dumps(result, ensure_ascii=False, indent=2))
