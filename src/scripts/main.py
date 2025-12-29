#!/usr/bin/env python3
"""
ブログ自動生成メインスクリプト
"""
import asyncio
import argparse
import json
import logging
from pathlib import Path
from datetime import datetime

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    parser = argparse.ArgumentParser(description='Blog Auto Generator')
    parser.add_argument('--topic', required=True, help='Topic ID')
    parser.add_argument('--dry-run', action='store_true', help='Dry run mode')
    parser.add_argument('--use-deep-research', action='store_true', default=True)
    args = parser.parse_args()

    logger.info(f"Starting blog generation for topic: {args.topic}")

    # Import modules
    from research import run_research
    from generate_content import generate_article
    from generate_image import generate_images
    from seo_optimize import optimize_seo
    from review import review_article

    # Step 1: Research
    logger.info("Step 1: Running research...")
    research_data = await run_research(args.topic, args.use_deep_research)

    # Step 2: Generate content
    logger.info("Step 2: Generating content...")
    article = await generate_article(args.topic, research_data)

    # Step 3: Generate images
    logger.info("Step 3: Generating images...")
    images = await generate_images(article)

    # Step 4: SEO optimization
    logger.info("Step 4: SEO optimization...")
    optimized = await optimize_seo(article)

    # Step 5: Review
    logger.info("Step 5: Reviewing...")
    final = await review_article(optimized)

    # Save output
    output_dir = Path(__file__).parent.parent.parent / "output" / "posts"
    output_file = output_dir / f"{datetime.now().strftime('%Y%m%d')}_{args.topic}.md"

    if not args.dry_run:
        output_file.write_text(final['content'], encoding='utf-8')
        logger.info(f"Saved to: {output_file}")

    logger.info("Blog generation completed!")
    return final

if __name__ == "__main__":
    asyncio.run(main())
