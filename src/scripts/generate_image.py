#!/usr/bin/env python3
"""
画像生成スクリプト - Gemini 2.5 Flash Image Edition

ブログ記事用の画像をGemini 2.5 Flash imageモデルで生成します。

使用方法:
    python generate_image.py --title "記事タイトル" --summary "記事概要"
"""
import asyncio
import json
import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List

sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.gemini_client import GeminiClient, ImageGenerationResult

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BlogImageGenerator:
    """ブログ用画像生成クラス"""

    def __init__(self):
        self.client = GeminiClient()
        self.output_dir = Path(__file__).parent.parent.parent / "output" / "images"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    async def generate_hero_image(
        self,
        title: str,
        summary: str,
        style: str = "modern, minimalist, professional, tech-inspired"
    ) -> Dict:
        """
        ヒーロー画像を生成

        Args:
            title: 記事タイトル
            summary: 記事概要
            style: 画像スタイル

        Returns:
            生成結果の辞書
        """
        logger.info(f"Generating hero image for: {title}")

        result = await self.client.generate_blog_image(
            title=title,
            summary=summary,
            style=style,
            image_type="hero"
        )

        return await self._save_images(result, "hero", title)

    async def generate_section_images(
        self,
        title: str,
        sections: List[Dict[str, str]],
        style: str = "clean, illustrative, informative"
    ) -> List[Dict]:
        """
        セクション用画像を生成

        Args:
            title: 記事タイトル
            sections: セクション情報のリスト
            style: 画像スタイル

        Returns:
            生成結果のリスト
        """
        results = []
        for i, section in enumerate(sections):
            section_title = section.get("title", f"Section {i+1}")
            section_content = section.get("content", "")

            logger.info(f"Generating section image {i+1}: {section_title}")

            result = await self.client.generate_blog_image(
                title=f"{title} - {section_title}",
                summary=section_content[:200],
                style=style,
                image_type="section"
            )

            saved = await self._save_images(result, f"section_{i+1}", section_title)
            results.append(saved)

        return results

    async def _save_images(
        self,
        result: ImageGenerationResult,
        prefix: str,
        title: str
    ) -> Dict:
        """画像をファイルに保存"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        saved_files = []

        for i, image_data in enumerate(result.images):
            filename = f"{prefix}_{timestamp}_{i}.png"
            filepath = self.output_dir / filename

            with open(filepath, "wb") as f:
                f.write(image_data)

            logger.info(f"Saved image: {filepath}")
            saved_files.append({
                "file_path": str(filepath),
                "filename": filename,
                "size_bytes": len(image_data)
            })

        return {
            "type": prefix,
            "title": title,
            "prompt": result.prompt,
            "model": result.model,
            "images": saved_files,
            "text_response": result.text_response,
            "generated_at": timestamp
        }


async def generate_images(article: Dict) -> Dict:
    """
    記事用の画像を生成（メインエントリーポイント）

    Args:
        article: 記事データ
            - title: 記事タイトル
            - summary/description: 記事概要
            - sections: セクション情報（オプション）

    Returns:
        生成結果
    """
    generator = BlogImageGenerator()

    title = article.get("title", "Untitled Article")
    summary = article.get("summary") or article.get("description", "")
    sections = article.get("sections", [])

    results = {
        "status": "success",
        "hero": None,
        "sections": [],
        "total_images": 0
    }

    try:
        # ヒーロー画像生成
        hero_result = await generator.generate_hero_image(title, summary)
        results["hero"] = hero_result
        results["total_images"] += len(hero_result.get("images", []))

        # セクション画像生成（セクションがある場合）
        if sections:
            section_results = await generator.generate_section_images(
                title, sections[:3]  # 最大3セクション
            )
            results["sections"] = section_results
            for sr in section_results:
                results["total_images"] += len(sr.get("images", []))

        logger.info(f"Total images generated: {results['total_images']}")

    except Exception as e:
        logger.error(f"Image generation failed: {e}")
        results["status"] = "error"
        results["error"] = str(e)

    return results


def main():
    """CLIエントリーポイント"""
    parser = argparse.ArgumentParser(description="Generate blog images with Gemini 2.5 Flash")
    parser.add_argument("--title", "-t", required=True, help="Article title")
    parser.add_argument("--summary", "-s", required=True, help="Article summary")
    parser.add_argument("--sections", "-sec", type=str, help="JSON string of sections")
    parser.add_argument("--output", "-o", type=str, help="Output directory")

    args = parser.parse_args()

    article = {
        "title": args.title,
        "summary": args.summary
    }

    if args.sections:
        try:
            article["sections"] = json.loads(args.sections)
        except json.JSONDecodeError:
            logger.warning("Invalid sections JSON, ignoring")

    result = asyncio.run(generate_images(article))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
