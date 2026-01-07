#!/usr/bin/env python3
"""
スライドベース動画生成スクリプト - 統合ワークフロー

ブログ記事から高品質なスライド解説動画を自動生成:

【重要: 処理フロー（この順序で実行）】
Step 1: スライド生成（Gemini 3 Pro + 2.5 Flash image）
        - 記事からスライド構成を生成
        - 各スライドの画像を生成
Step 2: 音声生成（Gemini 2.5 Flash TTS）
        - スライド内容を元にナレーションスクリプトを生成
        - TTS音声を生成（WAV形式）
Step 3: ファイル配置
        - スライド画像をpublic/slides/にコピー
        - 音声ファイルをpublic/narration.wavに保存
Step 4: 動画レンダリング（Remotion）
        - スライド画像と音声を統合
        - MP4動画を出力

注意:
- 動画は30秒以内に制限（6スライド x 5秒）
- 品質評価は行わない（記事のみ品質評価対象）
- 音声生成に失敗した場合も動画は生成される（無音）

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

    async def _step1_generate_slides(
        self,
        article: Dict,
        target_slides: int
    ) -> Dict[str, Any]:
        """
        Step 1: スライド生成

        Args:
            article: 記事データ
            target_slides: 目標スライド枚数

        Returns:
            スライド生成結果
        """
        logger.info("=" * 60)
        logger.info("STEP 1: スライド生成")
        logger.info("=" * 60)
        logger.info(f"  目標スライド数: {target_slides}枚")

        slides_result = await generate_slides(article, target_slides)

        if slides_result.get("status") == "error":
            logger.error(f"  スライド生成失敗: {slides_result.get('error')}")
            return slides_result

        slides = slides_result.get("slides", [])
        slide_images = slides_result.get("slide_images", [])

        logger.info(f"  生成スライド数: {len(slides)}枚")
        logger.info(f"  生成画像数: {len(slide_images)}枚")

        # 各スライドの内容をログ
        for i, slide in enumerate(slides):
            logger.info(f"  スライド{i+1}: {slide.get('type', 'content')} - {slide.get('heading', '')[:30]}...")

        return slides_result

    async def _step2_generate_audio(
        self,
        slides: List[Dict],
        title: str,
        topic: str,
        voice: str,
        slide_duration: int
    ) -> Dict[str, Any]:
        """
        Step 2: 音声生成（スライド内容を元にTTS音声を生成）

        Args:
            slides: スライドデータ
            title: 記事タイトル
            topic: トピックID
            voice: 音声タイプ
            slide_duration: 各スライドの表示時間

        Returns:
            音声生成結果（audio_dataを含む）
        """
        logger.info("=" * 60)
        logger.info("STEP 2: 音声生成（スライド内容からナレーション）")
        logger.info("=" * 60)
        logger.info(f"  音声タイプ: {voice}")
        logger.info(f"  スライド数: {len(slides)}枚")
        logger.info(f"  目標時間: {len(slides) * slide_duration}秒")

        client = self._get_gemini_client()

        try:
            narration = await client.generate_slide_narration(
                slides=slides,
                title=title,
                topic=topic,
                voice=voice,
                slide_duration=slide_duration
            )

            if narration.get("status") == "success":
                audio_data = narration.get("audio_data")
                script = narration.get("script", "")
                audio_size = narration.get("audio_size_bytes", 0)

                # 音声データの検証（最低10KB以上であること）
                MIN_AUDIO_SIZE = 10000  # 10KB
                if audio_data and len(audio_data) >= MIN_AUDIO_SIZE:
                    logger.info(f"  音声生成成功!")
                    logger.info(f"  スクリプト長: {len(script)}文字")
                    logger.info(f"  音声サイズ: {len(audio_data):,} bytes")
                    logger.info(f"  スクリプト冒頭: {script[:100]}...")

                    return {
                        "status": "success",
                        "audio_data": audio_data,
                        "script": script,
                        "audio_size_bytes": len(audio_data),
                        "voice": voice
                    }
                else:
                    actual_size = len(audio_data) if audio_data else 0
                    logger.warning(f"  音声データが小さすぎます: {actual_size} bytes (最低 {MIN_AUDIO_SIZE} bytes 必要)")
                    return {
                        "status": "failed",
                        "error": f"Audio data too small: {actual_size} bytes",
                        "audio_data": None
                    }
            else:
                logger.warning(f"  音声生成失敗: {narration.get('error')}")
                return {
                    "status": "failed",
                    "error": narration.get("error"),
                    "audio_data": None
                }

        except Exception as e:
            logger.error(f"  音声生成エラー: {e}")
            return {
                "status": "error",
                "error": str(e),
                "audio_data": None
            }

    async def _step3_prepare_files(
        self,
        slide_images: List[str],
        audio_data: Optional[bytes],
        slides_result: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Step 3: ファイル配置（public/ディレクトリにファイルを配置）

        Args:
            slide_images: スライド画像パスのリスト
            audio_data: 音声バイナリデータ（WAV形式）
            slides_result: スライド生成結果全体（代替画像パス用）

        Returns:
            配置されたファイル情報
        """
        logger.info("=" * 60)
        logger.info("STEP 3: ファイル配置")
        logger.info("=" * 60)

        result = {
            "audio_file": None,
            "slide_files": [],
            "slides_dir": None,
            "has_audio": False
        }

        # publicディレクトリを確保
        self.public_dir.mkdir(parents=True, exist_ok=True)

        # slidesディレクトリを作成（既存があれば削除）
        slides_dir = self.public_dir / "slides"
        if slides_dir.exists():
            shutil.rmtree(slides_dir)
        slides_dir.mkdir(parents=True, exist_ok=True)
        result["slides_dir"] = str(slides_dir)
        logger.info(f"  スライドディレクトリ: {slides_dir}")

        # 使用可能な画像パスを収集（複数のソースから）
        available_images = []

        # 1. slide_imagesから（PDF変換後の画像またはAI生成画像）
        for path in slide_images:
            if path and Path(path).exists():
                available_images.append(path)
                logger.info(f"  画像発見(slide_images): {Path(path).name}")

        # 2. slides_resultのgenerated_imagesから（AI生成画像、バックアップ）
        if slides_result and len(available_images) == 0:
            generated = slides_result.get("generated_images", [])
            for path in generated:
                if path and Path(path).exists():
                    available_images.append(path)
                    logger.info(f"  画像発見(generated_images): {Path(path).name}")

        logger.info(f"  利用可能な画像数: {len(available_images)}")

        # スライド画像をコピー
        copied_count = 0
        for i, image_path in enumerate(available_images):
            try:
                source = Path(image_path)
                if source.exists():
                    dest = slides_dir / f"slide_{i+1:02d}.png"
                    shutil.copy(str(source), str(dest))
                    result["slide_files"].append(str(dest))
                    copied_count += 1
                    logger.info(f"  コピー: {source.name} → {dest.name} ({source.stat().st_size:,} bytes)")
                else:
                    logger.warning(f"  画像が見つかりません: {image_path}")
            except Exception as e:
                logger.error(f"  画像コピー失敗: {image_path} - {e}")

        logger.info(f"  コピーした画像数: {copied_count}/{len(available_images)}")

        # 音声ファイルを保存
        if audio_data:
            audio_path = self.public_dir / "narration.wav"
            try:
                with open(audio_path, "wb") as f:
                    f.write(audio_data)
                logger.info(f"  音声ファイル保存: {audio_path} ({len(audio_data):,} bytes)")

                # WAVファイルの検証
                file_size = audio_path.stat().st_size
                is_valid_audio = False

                if file_size < 10000:  # 10KB以下
                    logger.warning(f"  警告: 音声ファイルが小さすぎます ({file_size} bytes)")
                else:
                    # WAVヘッダーを確認
                    with open(audio_path, "rb") as f:
                        header = f.read(12)
                        if header[:4] == b'RIFF' and header[8:12] == b'WAVE':
                            logger.info(f"  WAVファイル検証: 有効なWAVフォーマット ({file_size:,} bytes)")
                            is_valid_audio = True
                        else:
                            logger.warning(f"  警告: WAVヘッダーが不正です (header: {header[:4]}...{header[8:12]})")

                if is_valid_audio:
                    result["audio_file"] = "narration.wav"
                    result["has_audio"] = True
                    logger.info(f"  音声ファイル: 有効 ✓")
                else:
                    # 無効な音声ファイルを削除
                    audio_path.unlink(missing_ok=True)
                    result["audio_file"] = None
                    result["has_audio"] = False
                    logger.warning(f"  音声ファイル: 無効（削除しました）")

            except Exception as e:
                logger.error(f"  音声ファイル保存失敗: {e}")
                result["audio_file"] = None
                result["has_audio"] = False
        else:
            logger.warning("  音声データなし（無音動画になります）")
            result["audio_file"] = None
            result["has_audio"] = False

        return result

    def _normalize_slides_for_remotion(self, slides: List[Dict]) -> List[Dict]:
        """
        スライドデータをRemotionのSlideVideoコンポーネント用に正規化

        SlideVideo.tsxが期待する形式:
        - heading: string
        - subheading?: string
        - points?: string[]
        - type: "title" | "content" | "ending"
        - imageUrl?: string (自動生成されるのでオプション)
        - narrationText?: string
        """
        normalized = []
        for i, slide in enumerate(slides):
            # typeの正規化（title, content, ending のいずれかに）
            original_type = slide.get("type", "content")
            if i == 0:
                # 最初のスライドは必ずtitle
                slide_type = "title"
            elif i == len(slides) - 1:
                # 最後のスライドは必ずending
                slide_type = "ending"
            elif original_type in ["title", "ending"]:
                # 中間スライドでtitleやendingが指定されていたらcontentに
                slide_type = "content"
            else:
                slide_type = "content"

            normalized_slide = {
                "heading": slide.get("heading", f"スライド {i+1}"),
                "subheading": slide.get("subheading", ""),
                "points": slide.get("points", []),
                "type": slide_type
            }

            # narrationTextがあれば追加
            if slide.get("narrationText"):
                normalized_slide["narrationText"] = slide["narrationText"]

            normalized.append(normalized_slide)
            logger.info(f"  スライド{i+1}: type='{original_type}' → '{slide_type}', heading='{normalized_slide['heading'][:30]}...'")

        return normalized

    async def _step4_render_video(
        self,
        slides: List[Dict],
        output_path: str,
        topic: str,
        audio_file: Optional[str],
        slide_duration: int
    ) -> bool:
        """
        Step 4: Remotionでスライド動画をレンダリング

        Args:
            slides: スライドデータ
            output_path: 出力パス
            topic: トピックID
            audio_file: 音声ファイル名（publicディレクトリ内）
            slide_duration: 各スライドの表示時間

        Returns:
            成功かどうか
        """
        logger.info("=" * 60)
        logger.info("STEP 4: 動画レンダリング（Remotion）")
        logger.info("=" * 60)

        # スライドデータをRemotionの期待する形式に正規化
        logger.info("スライドデータを正規化中...")
        normalized_slides = self._normalize_slides_for_remotion(slides)

        # propsを準備
        props = {
            "title": normalized_slides[0].get("heading", "Presentation") if normalized_slides else "Presentation",
            "slides": normalized_slides,
            "topic": topic,
            "authorName": "if(塾) Blog",
            "audioUrl": audio_file,
            "slideImagePrefix": "slide_",
            "slideDuration": slide_duration
        }

        logger.info(f"  タイトル: {props['title']}")
        logger.info(f"  スライド数: {len(slides)}")
        logger.info(f"  各スライド: {slide_duration}秒")
        logger.info(f"  音声ファイル: {audio_file or 'なし'}")
        logger.info(f"  出力先: {output_path}")

        # propsをJSONファイルに保存
        props_file = self.remotion_dir / "props_slides.json"
        with open(props_file, "w", encoding="utf-8") as f:
            json.dump(props, f, ensure_ascii=False, indent=2)
        logger.info(f"  Props保存: {props_file}")

        render_script = self.remotion_dir / "render.mjs"
        cmd = [
            "node",
            str(render_script),
            "SlideVideo",
            output_path,
            str(props_file)
        ]

        logger.info(f"  レンダリングコマンド: {' '.join(cmd)}")

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
                        logger.info(f"  [Remotion] {line}")

            if process.returncode == 0:
                logger.info(f"  レンダリング成功!")
                return True
            else:
                logger.error(f"  レンダリング失敗:")
                for line in stderr.decode().split('\n'):
                    if line.strip():
                        logger.error(f"  [Remotion Error] {line}")
                return False

        except Exception as e:
            logger.error(f"  レンダリングエラー: {e}")
            return False
        finally:
            if props_file.exists():
                props_file.unlink()

    def _cleanup_public_files(self):
        """public/ディレクトリをクリーンアップ"""
        logger.info("クリーンアップ中...")

        for item in ["narration.wav"]:
            path = self.public_dir / item
            if path.exists():
                try:
                    path.unlink()
                except Exception as e:
                    logger.warning(f"  クリーンアップ失敗: {e}")

        slides_dir = self.public_dir / "slides"
        if slides_dir.exists():
            try:
                shutil.rmtree(slides_dir)
            except Exception as e:
                logger.warning(f"  Slidesディレクトリ削除失敗: {e}")

    async def generate_slide_video(
        self,
        article: Dict,
        target_slides: int = 6,
        slide_duration: int = 5
    ) -> Dict[str, Any]:
        """
        記事からスライド動画を生成

        処理フロー:
        Step 1: スライド生成 → Step 2: 音声生成 → Step 3: ファイル配置 → Step 4: 動画レンダリング

        Args:
            article: 記事データ
            target_slides: 目標スライド枚数（デフォルト6枚 = 30秒）
            slide_duration: 各スライドの表示時間（秒）

        Returns:
            生成結果
        """
        timestamp = get_timestamp_jst()
        topic = article.get("topic_id") or article.get("topic", "ai_tools")
        title = article.get("title", "Untitled")

        # 30秒以内に制限（最大6スライド x 5秒 = 30秒）
        MAX_VIDEO_DURATION = 30
        max_slides = MAX_VIDEO_DURATION // slide_duration
        target_slides = min(target_slides, max_slides)

        logger.info("=" * 60)
        logger.info("スライドベース動画生成開始")
        logger.info("=" * 60)
        logger.info(f"タイトル: {title}")
        logger.info(f"トピック: {topic}")
        logger.info(f"目標スライド数: {target_slides}枚")
        logger.info(f"各スライド表示時間: {slide_duration}秒")
        logger.info(f"最大動画長: {MAX_VIDEO_DURATION}秒")

        result = {
            "status": "in_progress",
            "topic": topic,
            "generated_at": timestamp,
            "target_duration": target_slides * slide_duration
        }

        # 依存関係チェック
        deps = self._check_dependencies()
        logger.info(f"依存関係: {deps}")
        if not deps.get("node"):
            result["status"] = "error"
            result["error"] = "Node.js is not available"
            return result

        try:
            # ========================================
            # Step 1: スライド生成
            # ========================================
            slides_result = await self._step1_generate_slides(article, target_slides)

            if slides_result.get("status") == "error":
                result["status"] = "error"
                result["error"] = slides_result.get("error")
                return result

            slides = slides_result.get("slides", [])
            slide_images = slides_result.get("slide_images", [])

            # スライド数を30秒以内に制限
            if len(slides) > max_slides:
                logger.info(f"スライドを{len(slides)}枚から{max_slides}枚に制限")
                slides = slides[:max_slides]
                slide_images = slide_images[:max_slides]

            result["slides"] = slides_result

            # ========================================
            # Step 2: 音声生成（スライド内容を元に）
            # ========================================
            voice = TOPIC_VOICES.get(topic, "default")
            audio_result = await self._step2_generate_audio(
                slides=slides,
                title=title,
                topic=topic,
                voice=voice,
                slide_duration=slide_duration
            )

            audio_data = audio_result.get("audio_data")
            result["narration"] = {
                "status": audio_result.get("status"),
                "script": audio_result.get("script"),
                "audio_size_bytes": audio_result.get("audio_size_bytes"),
                "voice": voice
            }

            # ========================================
            # Step 3: ファイル配置
            # ========================================
            public_files = await self._step3_prepare_files(
                slide_images,
                audio_data,
                slides_result  # バックアップ画像パス用
            )

            # ========================================
            # Step 4: 動画レンダリング
            # ========================================
            videos_dir = self.output_dir / "videos"
            videos_dir.mkdir(parents=True, exist_ok=True)
            video_path = videos_dir / f"slide_video_{timestamp}_{topic}.mp4"

            render_success = await self._step4_render_video(
                slides=slides,
                output_path=str(video_path),
                topic=topic,
                audio_file=public_files.get("audio_file"),
                slide_duration=slide_duration
            )

            # 結果の設定
            if render_success and video_path.exists():
                actual_duration = len(slides) * slide_duration
                result["video"] = {
                    "status": "success",
                    "path": str(video_path),
                    "resolution": "1920x1080",
                    "duration": actual_duration,
                    "size_bytes": video_path.stat().st_size,
                    "has_audio": public_files.get("has_audio", False),
                    "slide_count": len(slides)
                }
                result["status"] = "success"

                logger.info("=" * 60)
                logger.info("動画生成完了!")
                logger.info("=" * 60)
                logger.info(f"  動画パス: {video_path}")
                logger.info(f"  動画長: {actual_duration}秒")
                logger.info(f"  スライド数: {len(slides)}枚")
                logger.info(f"  音声: {'あり' if public_files.get('has_audio') else 'なし'}")
                logger.info(f"  ファイルサイズ: {video_path.stat().st_size:,} bytes")
            else:
                result["video"] = {"status": "error", "error": "Render failed"}
                result["status"] = "error"
                logger.error("動画レンダリング失敗")

        except Exception as e:
            logger.error(f"動画生成エラー: {e}")
            result["status"] = "error"
            result["error"] = str(e)

        finally:
            # クリーンアップ
            self._cleanup_public_files()

        return result


async def generate_slide_video(
    article: Dict,
    target_slides: int = 6,
    slide_duration: int = 5
) -> Dict[str, Any]:
    """
    スライド動画生成のエントリーポイント

    処理フロー:
    1. スライド生成（記事からスライド構成 + 画像を生成）
    2. 音声生成（スライド内容からTTSナレーション）
    3. ファイル配置（スライド画像 + 音声をpublic/に配置）
    4. 動画レンダリング（Remotionで統合）

    Args:
        article: 記事データ
        target_slides: 目標スライド枚数（デフォルト6枚 = 30秒）
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
    parser.add_argument("--slides", "-n", type=int, default=6,
                        help="Target slide count (max 6 for 30s video)")
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
