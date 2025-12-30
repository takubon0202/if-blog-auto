#!/usr/bin/env python3
"""
動画生成スクリプト - Remotion Edition

ブログ記事の内容からRemotionを使用して動画を自動生成します。
- 標準動画（30秒、1920x1080）
- ショート動画（15秒、1080x1920 縦型）

使用方法:
    python generate_video.py --title "記事タイトル" --summary "記事概要" --topic ai_tools
"""
import asyncio
import json
import sys
import argparse
import logging
import subprocess
import os
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.timezone import get_timestamp_jst, format_date

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VideoGenerationError(Exception):
    """動画生成エラー"""
    pass


class BlogVideoGenerator:
    """ブログ用動画生成クラス"""

    def __init__(self):
        self.remotion_dir = Path(__file__).parent.parent.parent / "remotion"
        self.output_dir = Path(__file__).parent.parent.parent / "output" / "videos"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _check_dependencies(self) -> bool:
        """依存関係をチェック"""
        # Node.jsのチェック
        try:
            result = subprocess.run(
                ["node", "--version"],
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                logger.error("Node.js is not installed")
                return False
            logger.info(f"Node.js version: {result.stdout.strip()}")
        except FileNotFoundError:
            logger.error("Node.js is not found in PATH")
            return False

        # node_modulesのチェック
        node_modules = self.remotion_dir / "node_modules"
        if not node_modules.exists():
            logger.warning("node_modules not found. Installing dependencies...")
            try:
                subprocess.run(
                    ["npm", "install"],
                    cwd=str(self.remotion_dir),
                    check=True
                )
                logger.info("Dependencies installed successfully")
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to install dependencies: {e}")
                return False

        return True

    def _extract_points_from_content(self, content: str, max_points: int = 3) -> List[str]:
        """記事コンテンツからポイントを抽出"""
        points = []

        # 見出し（##）からポイントを抽出
        lines = content.split('\n')
        for line in lines:
            if line.startswith('## ') and not line.startswith('### '):
                point = line[3:].strip()
                # 特定のセクションをスキップ
                skip_keywords = ['まとめ', '参考', 'はじめに', '導入', '結論', '目次', '概要']
                if not any(kw in point for kw in skip_keywords):
                    points.append(point)
                    if len(points) >= max_points:
                        break

        # 見出しが足りない場合は箇条書きから抽出
        if len(points) < max_points:
            for line in lines:
                if line.strip().startswith('- ') or line.strip().startswith('* '):
                    point = line.strip()[2:].strip()
                    if len(point) > 10 and len(point) < 100:
                        points.append(point)
                        if len(points) >= max_points:
                            break

        return points[:max_points]

    async def generate_video(
        self,
        title: str,
        summary: str,
        points: List[str],
        topic: str,
        date: Optional[str] = None,
        author_name: str = "if(塾) Blog",
        generate_short: bool = True
    ) -> Dict:
        """
        ブログ動画を生成

        Args:
            title: 記事タイトル
            summary: 記事要約
            points: 主要ポイントのリスト
            topic: トピックID
            date: 日付文字列
            author_name: 著者名
            generate_short: ショート動画も生成するか

        Returns:
            生成結果の辞書
        """
        logger.info(f"Generating video for: {title}")

        # 依存関係チェック
        if not self._check_dependencies():
            raise VideoGenerationError("Dependencies not satisfied")

        # 日付の設定
        if not date:
            date = format_date(fmt='%Y年%m月%d日')  # JST

        timestamp = get_timestamp_jst()

        # propsデータを準備
        props_data = {
            "title": title,
            "summary": summary,
            "points": points,
            "topic": topic,
            "date": date,
            "authorName": author_name
        }

        # ショート用props
        props_data_short = {
            **props_data,
            "isShort": True
        }

        result = {
            "status": "success",
            "videos": {},
            "generated_at": timestamp
        }

        # propsをJSONファイルに保存
        props_file = self.remotion_dir / "props.json"
        props_short_file = self.remotion_dir / "props_short.json"

        with open(props_file, "w", encoding="utf-8") as f:
            json.dump(props_data, f, ensure_ascii=False, indent=2)

        if generate_short:
            with open(props_short_file, "w", encoding="utf-8") as f:
                json.dump(props_data_short, f, ensure_ascii=False, indent=2)

        try:
            # 標準動画をレンダリング
            standard_output = self.output_dir / f"blog_video_{timestamp}_{topic}.mp4"
            logger.info("Rendering standard video (30s, 1920x1080)...")

            await self._render_video(
                composition_id="BlogVideo",
                output_path=str(standard_output),
                props_file=str(props_file)
            )

            result["videos"]["standard"] = {
                "path": str(standard_output),
                "duration": 30,
                "resolution": "1920x1080",
                "size_bytes": os.path.getsize(standard_output) if standard_output.exists() else 0
            }
            logger.info(f"Standard video saved: {standard_output}")

            # ショート動画をレンダリング
            if generate_short:
                short_output = self.output_dir / f"blog_video_short_{timestamp}_{topic}.mp4"
                logger.info("Rendering short video (15s, 1080x1920)...")

                await self._render_video(
                    composition_id="BlogVideoShort",
                    output_path=str(short_output),
                    props_file=str(props_short_file)
                )

                result["videos"]["short"] = {
                    "path": str(short_output),
                    "duration": 15,
                    "resolution": "1080x1920",
                    "size_bytes": os.path.getsize(short_output) if short_output.exists() else 0
                }
                logger.info(f"Short video saved: {short_output}")

        except subprocess.CalledProcessError as e:
            logger.error(f"Video rendering failed: {e}")
            result["status"] = "error"
            result["error"] = str(e)
        finally:
            # クリーンアップ
            if props_file.exists():
                props_file.unlink()
            if props_short_file.exists():
                props_short_file.unlink()

        return result

    async def _render_video(
        self,
        composition_id: str,
        output_path: str,
        props_file: str
    ):
        """Remotionで動画をレンダリング"""
        render_script = self.remotion_dir / "render.mjs"

        cmd = [
            "node",
            str(render_script),
            composition_id,
            output_path,
            props_file
        ]

        logger.info(f"Running: {' '.join(cmd)}")

        process = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=str(self.remotion_dir),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()

        # 出力をログに記録
        if stdout:
            for line in stdout.decode().split('\n'):
                if line.strip():
                    logger.info(f"[Remotion] {line}")

        if stderr:
            stderr_text = stderr.decode()
            for line in stderr_text.split('\n'):
                if line.strip():
                    logger.warning(f"[Remotion stderr] {line}")

        if process.returncode != 0:
            error_msg = stderr.decode() if stderr else "Unknown error"
            logger.error(f"Remotion render failed with exit code {process.returncode}")
            logger.error(f"Error details: {error_msg}")
            raise subprocess.CalledProcessError(
                process.returncode,
                cmd,
                output=stdout,
                stderr=stderr
            )


async def generate_video(
    article: Dict,
    output_dir: Optional[str] = None,
    generate_short: bool = True
) -> Dict:
    """
    記事データから動画を生成（メインエントリーポイント）

    Args:
        article: 記事データ
            - title: 記事タイトル
            - summary/description: 記事概要
            - content: 記事本文（ポイント抽出用）
            - points: 主要ポイント（オプション）
            - topic_id/topic: トピックID
        output_dir: 出力ディレクトリ（オプション）
        generate_short: ショート動画も生成するか

    Returns:
        生成結果
    """
    generator = BlogVideoGenerator()

    if output_dir:
        generator.output_dir = Path(output_dir)
        generator.output_dir.mkdir(parents=True, exist_ok=True)

    title = article.get("title", "Untitled Article")
    summary = article.get("summary") or article.get("description", "")
    topic = article.get("topic_id") or article.get("topic", "ai_tools")
    content = article.get("content", "")

    # ポイントの取得または抽出
    points = article.get("points", [])
    if not points and content:
        points = generator._extract_points_from_content(content)

    # ポイントが空の場合はデフォルト
    if not points:
        points = [
            "最新トレンドの分析",
            "実践的なアドバイス",
            "今後の展望"
        ]

    try:
        result = await generator.generate_video(
            title=title,
            summary=summary,
            points=points,
            topic=topic,
            generate_short=generate_short
        )
        return result
    except VideoGenerationError as e:
        logger.error(f"Video generation failed: {e}")
        return {
            "status": "error",
            "error": str(e)
        }
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


def main():
    """CLIエントリーポイント"""
    parser = argparse.ArgumentParser(
        description="Generate blog video with Remotion"
    )
    parser.add_argument("--title", "-t", required=True, help="Article title")
    parser.add_argument("--summary", "-s", required=True, help="Article summary")
    parser.add_argument("--topic", type=str, default="ai_tools",
                        help="Topic ID (e.g., ai_tools, psychology)")
    parser.add_argument("--points", "-p", type=str,
                        help="JSON array of key points")
    parser.add_argument("--output", "-o", type=str, help="Output directory")
    parser.add_argument("--no-short", action="store_true",
                        help="Skip short video generation")

    args = parser.parse_args()

    article = {
        "title": args.title,
        "summary": args.summary,
        "topic_id": args.topic
    }

    if args.points:
        try:
            article["points"] = json.loads(args.points)
        except json.JSONDecodeError:
            logger.warning("Invalid points JSON, using defaults")

    result = asyncio.run(generate_video(
        article=article,
        output_dir=args.output,
        generate_short=not args.no_short
    ))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
