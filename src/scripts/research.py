#!/usr/bin/env python3
"""リサーチ実行スクリプト"""
import asyncio
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from lib.gemini_client import GeminiClient

async def run_research(topic_id: str, use_deep_research: bool = True) -> dict:
    """リサーチを実行"""
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

    research_query = f"""
【調査トピック】{topic_info['name']}

【調査要件】
- 期間: 過去7日間の最新情報
- 言語: 日本語優先
- 焦点: {', '.join(topic_info['research_focus'])}
- キーワード: {', '.join(topic_info['keywords'])}

【必要な情報】
1. 最新ニュース・動向（具体的な日付付き）
2. 専門家の見解・研究結果
3. 統計データ・調査結果
4. 具体的な事例
5. 今後の展望

各情報のソースURLを必ず含めてください。
"""

    if use_deep_research:
        result = await client.deep_research(research_query)
        return {
            "topic": topic_id,
            "topic_info": topic_info,
            "content": result.content,
            "sources": result.sources
        }
    else:
        result = await client.search_and_generate(
            query=f"{topic_info['name']} 最新",
            generation_prompt=research_query
        )
        return {
            "topic": topic_id,
            "topic_info": topic_info,
            "content": result.text,
            "sources": result.grounding_sources or []
        }

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--topic', required=True)
    parser.add_argument('--use-deep-research', action='store_true', default=True)
    parser.add_argument('--use-google-search', action='store_true')
    args = parser.parse_args()

    use_deep = not args.use_google_search
    result = asyncio.run(run_research(args.topic, use_deep))
    print(json.dumps(result, ensure_ascii=False, indent=2))
