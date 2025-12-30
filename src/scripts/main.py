#!/usr/bin/env python3
"""
ブログ自動生成メインスクリプト - GitHub Pages Edition

システムフロー:
1. 情報収集（Google Search: 通常、Deep Research: 日曜のみ）
2. Gemini 3 Pro (ブログ生成)
3. Gemini 2.5 Flash (画像生成)
4. Remotion (動画生成)
5. SEO最適化 & レビュー
6. GitHub Pages投稿

設計方針:
- Google Search Tool: 日常的な情報収集（メイン・デフォルト）
- Deep Research: 週1回（日曜日）の深層調査
- Remotion: ブログ記事から動画を自動生成
"""
import asyncio
import argparse
import json
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from lib.timezone import format_date

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    parser = argparse.ArgumentParser(description='Blog Auto Generator - GitHub Pages Edition')
    parser.add_argument('--topic', required=True, help='Topic ID')
    parser.add_argument('--dry-run', action='store_true', help='Dry run mode (no publish)')
    parser.add_argument('--use-deep-research', action='store_true', default=False,
                        help='Use Deep Research API (default: False, use Google Search)')
    parser.add_argument('--skip-images', action='store_true', help='Skip image generation')
    parser.add_argument('--skip-video', action='store_true', help='Skip video generation')
    parser.add_argument('--publish', action='store_true', default=True,
                        help='Publish to GitHub Pages (default: True)')
    args = parser.parse_args()

    logger.info(f"Starting blog generation for topic: {args.topic}")
    logger.info(f"Mode: {'Dry run' if args.dry_run else 'Production'}")

    # Import modules
    from research import run_research
    from generate_content import generate_article
    from generate_image import generate_images
    from generate_video import generate_video
    from seo_optimize import optimize_seo
    from review import review_article
    from publish import publish_to_github_pages

    result = {
        "topic": args.topic,
        "status": "in_progress",
        "steps": {}
    }

    try:
        # Step 1: 情報収集（Google Search or Deep Research）
        logger.info("=" * 50)
        research_method = "Deep Research" if args.use_deep_research else "Google Search"
        logger.info(f"Step 1: Running {research_method}...")
        logger.info("=" * 50)
        research_data = await run_research(args.topic, args.use_deep_research)
        result["steps"]["research"] = {
            "status": "completed",
            "sources_count": len(research_data.get("sources", []))
        }
        logger.info(f"Research completed. Found {len(research_data.get('sources', []))} sources.")

        # Step 2: Gemini 3 Pro (ブログ生成)
        logger.info("=" * 50)
        logger.info("Step 2: Generating content with Gemini 3 Pro...")
        logger.info("=" * 50)
        article = await generate_article(args.topic, research_data)
        result["steps"]["content"] = {
            "status": "completed",
            "word_count": article.get("word_count", 0)
        }
        logger.info(f"Content generated. Word count: {article.get('word_count', 0)}")

        # Step 3: Gemini 2.5 Flash (画像生成)
        images = {"status": "skipped"}
        if not args.skip_images:
            logger.info("=" * 50)
            logger.info("Step 3: Generating images with Gemini 2.5 Flash...")
            logger.info("=" * 50)
            images = await generate_images(article)
            result["steps"]["images"] = {
                "status": images.get("status", "error"),
                "total_images": images.get("total_images", 0)
            }
            logger.info(f"Images generated: {images.get('total_images', 0)}")
        else:
            logger.info("Step 3: Skipping image generation")
            result["steps"]["images"] = {"status": "skipped"}

        # Step 4: Remotion (動画生成)
        videos = {"status": "skipped"}
        if not args.skip_video:
            logger.info("=" * 50)
            logger.info("Step 4: Generating video with Remotion...")
            logger.info("=" * 50)
            videos = await generate_video(article)
            result["steps"]["videos"] = {
                "status": videos.get("status", "error"),
                "videos": videos.get("videos", {})
            }
            if videos.get("status") == "success":
                logger.info(f"Videos generated: standard + short")
            else:
                logger.warning(f"Video generation failed: {videos.get('error', 'Unknown error')}")
        else:
            logger.info("Step 4: Skipping video generation")
            result["steps"]["videos"] = {"status": "skipped"}

        # Step 5: SEO最適化
        logger.info("=" * 50)
        logger.info("Step 5: SEO optimization...")
        logger.info("=" * 50)
        optimized = await optimize_seo(article)
        result["steps"]["seo"] = {"status": "completed"}
        logger.info("SEO optimization completed.")

        # Step 6: レビュー
        logger.info("=" * 50)
        logger.info("Step 6: Quality review...")
        logger.info("=" * 50)
        final = await review_article(optimized)
        result["steps"]["review"] = {
            "status": "completed",
            "quality_score": final.get("quality_score", 0)
        }
        logger.info(f"Review completed. Quality score: {final.get('quality_score', 0)}")

        # ローカル保存（日本時間）
        output_dir = Path(__file__).parent.parent.parent / "output" / "posts"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / f"{format_date(fmt='%Y%m%d')}_{args.topic}.md"  # JST date

        if not args.dry_run:
            output_file.write_text(final['content'], encoding='utf-8')
            logger.info(f"Saved locally: {output_file}")

        # Step 7: GitHub Pages投稿
        if args.publish and not args.dry_run:
            logger.info("=" * 50)
            logger.info("Step 7: Publishing to GitHub Pages...")
            logger.info("=" * 50)

            # 記事データを構築
            publish_data = {
                "title": final.get("title", article.get("title", "Untitled")),
                "content": final.get("content", ""),
                "description": final.get("description", "")[:120],
                "categories": final.get("categories", [research_data.get("topic_info", {}).get("name", "未分類")]),
                "tags": final.get("tags", []),
                "images": images,
                "videos": videos
            }

            publish_result = await publish_to_github_pages(publish_data)
            result["steps"]["publish"] = {
                "status": publish_result.get("status"),
                "public_url": publish_result.get("public_url"),
                "message": publish_result.get("message")
            }

            if publish_result.get("status") == "success":
                logger.info(f"Published! URL: {publish_result.get('public_url')}")
            else:
                logger.error(f"Publish failed: {publish_result.get('message')}")
        else:
            logger.info("Step 7: Skipping publish (dry-run mode)")
            result["steps"]["publish"] = {"status": "skipped"}

        result["status"] = "completed"
        logger.info("=" * 50)
        logger.info("Blog generation completed successfully!")
        logger.info("=" * 50)

    except Exception as e:
        logger.error(f"Error during blog generation: {e}")
        result["status"] = "error"
        result["error"] = str(e)
        raise

    return result


if __name__ == "__main__":
    result = asyncio.run(main())
    print(json.dumps(result, ensure_ascii=False, indent=2))
