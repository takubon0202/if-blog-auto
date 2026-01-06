#!/usr/bin/env python3
"""
スライドベース動画生成スクリプト - 統合ワークフロー

ブログ記事から高品質なスライド解説動画を自動生成:
1. スライド生成（Gemini 3 Pro + 2.5 Flash image）
2. Marp PDF エクスポート
3. PDF → 画像変換
4. Remotion 動画生成
5. Gemini 2.5 Flash TTS 音声生成
6. 品質評価（95%以上合格）

使用方法:
    python generate_slide_video.py --article-file "output/posts/article.json"
"""
import asyncio
import argparse
import json
import logging
import subprocess
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.timezone import get_timestamp_jst, format_date
from lib.gemini_client import GeminiClient
from scripts.generate_slides import generate_slides
from scripts.quality_evaluator import QualityEvaluator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# トピック別推奨TTS音声
TOPIC_VOICES = {
    "psychology": "default",
    "education": "default",
    "startup": "bright",
    "investment": "default",
    "ai_tools": "bright",
    "inclusive_education": "calm",
    "weekly_summary": "warm"
}


class SlideVideoGenerator:
    """スライドベース動画生成クラス"""

    def __init__(self):
        self.output_dir = Path(__file__).parent.parent.parent / "output"
        self.remotion_dir = Path(__file__).parent.parent.parent / "remotion"
        self.public_dir = self.remotion_dir / "public"
        self.gemini_client = None
        self.quality_evaluator = QualityEvaluator()

    def _get_gemini_client(self) -> GeminiClient:
        """GeminiClientを取得"""
        if self.gemini_client is None:
            self.gemini_client = GeminiClient()
        return self.gemini_client

    def _check_dependencies(self) -> Dict[str, bool]:
        """依存関係をチェック"""
        deps = {
            "node": False,
            "remotion": False,
            "marp_cli": False
        }

        # Node.js チェック
        try:
            result = subprocess.run(
                ["node", "--version"],
                capture_output=True, text=True, timeout=10
            )
            deps["node"] = result.returncode == 0
        except Exception:
            pass

        # Remotion チェック
        node_modules = self.remotion_dir / "node_modules"
        deps["remotion"] = node_modules.exists()

        # Marp CLI チェック
        try:
            result = subprocess.run(
                ["npx", "@marp-team/marp-cli", "--version"],
                capture_output=True, text=True, timeout=30
            )
            deps["marp_cli"] = result.returncode == 0
        except Exception:
            pass

        return deps

    async def _prepare_public_files(
        self,
        slide_images: List[str],
        audio_data: Optional[bytes]
    ) -> Dict[str, Any]:
        """
        public/ディレクトリにファイルを配置

        Args:
            slide_images: スライド画像パスのリスト
            audio_data: 音声バイナリデータ

        Returns:
            配置されたファイル情報
        """
        result = {
            "audio_file": None,
            "slide_files": [],
            "slides_dir": None
        }

        # slidesディレクトリを作成
        slides_dir = self.public_dir / "slides"
        slides_dir.mkdir(parents=True, exist_ok=True)
        result["slides_dir"] = str(slides_dir)

        # スライド画像をコピー
        for i, image_path in enumerate(slide_images):
            if Path(image_path).exists():
                dest = slides_dir / f"slide_{i+1:02d}.png"
                shutil.copy(image_path, dest)
                result["slide_files"].append(str(dest))
                logger.info(f"Copied slide image: {dest}")

        # 音声ファイルを保存
        if audio_data:
            audio_path = self.public_dir / "narration.wav"
            try:
                with open(audio_path, "wb") as f:
                    f.write(audio_data)
                result["audio_file"] = "narration.wav"
                logger.info(f"Audio saved: {audio_path}")
            except Exception as e:
                logger.error(f"Failed to save audio: {e}")

        return result

    def _cleanup_public_files(self):
        """public/ディレクトリをクリーンアップ"""
        for item in ["narration.wav"]:
            path = self.public_dir / item
            if path.exists():
                try:
                    path.unlink()
                except Exception as e:
                    logger.warning(f"Cleanup failed: {e}")

        slides_dir = self.public_dir / "slides"
        if slides_dir.exists():
            try:
                shutil.rmtree(slides_dir)
            except Exception as e:
                logger.warning(f"Slides cleanup failed: {e}")

    async def _render_slide_video(
        self,
        slides: List[Dict],
        output_path: str,
        topic: str,
        audio_file: Optional[str],
        slide_duration: int = 5
    ) -> bool:
        """
        Remotionでスライド動画をレンダリング

        Args:
            slides: スライドデータ
            output_path: 出力パス
            topic: トピックID
            audio_file: 音声ファイル名（publicディレクトリ内）
            slide_duration: 各スライドの表示時間

        Returns:
            成功かどうか
        """
        # propsを準備
        props = {
            "title": slides[0].get("heading", "Presentation") if slides else "Presentation",
            "slides": slides,
            "topic": topic,
            "authorName": "if(塾) Blog",
            "audioUrl": audio_file,
            "slideImagePrefix": "slide_",
            "slideDuration": slide_duration
        }

        # propsをJSONファイルに保存
        props_file = self.remotion_dir / "props_slides.json"
        with open(props_file, "w", encoding="utf-8") as f:
            json.dump(props, f, ensure_ascii=False, indent=2)

        # 動画の長さを計算
        total_frames = len(slides) * slide_duration * 30  # 30fps

        render_script = self.remotion_dir / "render.mjs"
        cmd = [
            "node",
            str(render_script),
            "SlideVideo",
            output_path,
            str(props_file)
        ]

        logger.info(f"Rendering slide video: {' '.join(cmd)}")

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=str(self.remotion_dir),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()

            if stdout:
                for line in stdout.decode().split('\n'):
                    if line.strip():
                        logger.info(f"[Remotion] {line}")

            if process.returncode == 0:
                logger.info(f"Slide video rendered: {output_path}")
                return True
            else:
                logger.error(f"Render failed: {stderr.decode()}")
                return False

        except Exception as e:
            logger.error(f"Render error: {e}")
            return False
        finally:
            if props_file.exists():
                props_file.unlink()

    async def generate_slide_video(
        self,
        article: Dict,
        target_slides: int = 12,
        slide_duration: int = 5,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """
        記事からスライド動画を生成（品質95%達成まで再試行）

        Args:
            article: 記事データ
            target_slides: 目標スライド枚数
            slide_duration: 各スライドの表示時間（秒）
            max_retries: 最大再試行回数

        Returns:
            生成結果
        """
        timestamp = get_timestamp_jst()
        topic = article.get("topic_id") or article.get("topic", "ai_tools")
        title = article.get("title", "Untitled")
        content = article.get("content", "")

        result = {
            "status": "in_progress",
            "topic": topic,
            "generated_at": timestamp,
            "attempts": 0
        }

        # 依存関係チェック
        deps = self._check_dependencies()
        logger.info(f"Dependencies: {deps}")
        if not deps.get("node"):
            result["status"] = "error"
            result["error"] = "Node.js is not available"
            return result

        for attempt in range(max_retries):
            result["attempts"] = attempt + 1
            logger.info(f"Attempt {attempt + 1}/{max_retries}")

            try:
                # Step 1: スライド生成
                logger.info("=" * 50)
                logger.info("Step 1: Generating slides...")
                logger.info("=" * 50)
                slides_result = await generate_slides(article, target_slides)

                if slides_result.get("status") == "error":
                    logger.error(f"Slide generation failed: {slides_result.get('error')}")
                    continue

                slides = slides_result.get("slides", [])
                slide_images = slides_result.get("slide_images", [])
                result["slides"] = slides_result

                # Step 2: 音声生成
                logger.info("=" * 50)
                logger.info("Step 2: Generating narration...")
                logger.info("=" * 50)
                client = self._get_gemini_client()
                voice = TOPIC_VOICES.get(topic, "default")

                narration = await client.generate_slide_narration(
                    slides=slides,
                    title=title,
                    topic=topic,
                    voice=voice,
                    slide_duration=slide_duration
                )

                audio_data = None
                if narration.get("status") == "success":
                    audio_data = narration.get("audio_data")
                    result["narration"] = {
                        "status": "success",
                        "script": narration.get("script"),
                        "audio_size_bytes": narration.get("audio_size_bytes"),
                        "voice": voice
                    }
                    logger.info(f"Narration generated: {narration.get('audio_size_bytes')} bytes")
                else:
                    logger.warning(f"Narration failed: {narration.get('error')}")
                    result["narration"] = {"status": "skipped"}

                # Step 3: public/にファイル配置
                logger.info("=" * 50)
                logger.info("Step 3: Preparing public files...")
                logger.info("=" * 50)
                public_files = await self._prepare_public_files(slide_images, audio_data)

                # Step 4: Remotion動画レンダリング
                logger.info("=" * 50)
                logger.info("Step 4: Rendering video...")
                logger.info("=" * 50)
                videos_dir = self.output_dir / "videos"
                videos_dir.mkdir(parents=True, exist_ok=True)
                video_path = videos_dir / f"slide_video_{timestamp}_{topic}.mp4"

                render_success = await self._render_slide_video(
                    slides=slides,
                    output_path=str(video_path),
                    topic=topic,
                    audio_file=public_files.get("audio_file"),
                    slide_duration=slide_duration
                )

                if render_success and video_path.exists():
                    result["video"] = {
                        "status": "success",
                        "path": str(video_path),
                        "resolution": "1920x1080",
                        "duration": len(slides) * slide_duration,
                        "size_bytes": video_path.stat().st_size,
                        "has_audio": audio_data is not None
                    }
                else:
                    result["video"] = {"status": "error", "error": "Render failed"}
                    logger.warning("Video render failed, retrying...")
                    continue

                # Step 5: 品質評価
                logger.info("=" * 50)
                logger.info("Step 5: Quality evaluation...")
                logger.info("=" * 50)
                quality_result = self.quality_evaluator.evaluate_all(
                    article=article,
                    slides_data=slides_result,
                    video_data={"videos": {"standard": result["video"]}, "narration": result.get("narration", {})}
                )
                result["quality"] = quality_result

                overall = quality_result.get("overall", {})
                logger.info(f"Quality score: {overall.get('percentage')}%")

                if overall.get("passed"):
                    result["status"] = "success"
                    logger.info("Quality check PASSED!")
                    break
                else:
                    logger.warning(f"Quality check FAILED. Issues: {quality_result.get('all_issues')}")
                    if attempt < max_retries - 1:
                        logger.info("Retrying with adjustments...")
                        # 次回の試行で調整
                        if len(slides) < 10:
                            target_slides += 2
                        elif any("テキスト" in i for i in quality_result.get("all_issues", [])):
                            # テキスト量を減らす指示
                            pass

            except Exception as e:
                logger.error(f"Attempt {attempt + 1} failed: {e}")
                result["error"] = str(e)

            finally:
                # クリーンアップ
                self._cleanup_public_files()

        # 最終結果の確認
        if result.get("status") != "success":
            result["status"] = "partial" if result.get("video", {}).get("status") == "success" else "error"

        return result


async def generate_slide_video(
    article: Dict,
    target_slides: int = 12,
    slide_duration: int = 5
) -> Dict[str, Any]:
    """
    スライド動画生成のエントリーポイント

    Args:
        article: 記事データ
        target_slides: 目標スライド枚数
        slide_duration: 各スライドの表示時間

    Returns:
        生成結果
    """
    generator = SlideVideoGenerator()
    return await generator.generate_slide_video(
        article=article,
        target_slides=target_slides,
        slide_duration=slide_duration
    )


def main():
    """CLIエントリーポイント"""
    parser = argparse.ArgumentParser(
        description="Generate slide-based video from blog article"
    )
    parser.add_argument("--article-file", "-f", type=str,
                        help="Path to article JSON file")
    parser.add_argument("--title", "-t", type=str,
                        help="Article title (if not using file)")
    parser.add_argument("--content", "-c", type=str,
                        help="Article content (if not using file)")
    parser.add_argument("--topic", type=str, default="ai_tools",
                        help="Topic ID")
    parser.add_argument("--slides", "-n", type=int, default=12,
                        help="Target slide count")
    parser.add_argument("--duration", "-d", type=int, default=5,
                        help="Slide duration in seconds")
    parser.add_argument("--output", "-o", type=str,
                        help="Output directory")

    args = parser.parse_args()

    # 記事データの読み込み
    if args.article_file:
        article = json.loads(Path(args.article_file).read_text(encoding="utf-8"))
    else:
        if not args.title or not args.content:
            print("Error: --article-file or both --title and --content required")
            sys.exit(1)
        article = {
            "title": args.title,
            "content": args.content,
            "topic_id": args.topic
        }

    result = asyncio.run(generate_slide_video(
        article=article,
        target_slides=args.slides,
        slide_duration=args.duration
    ))

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
