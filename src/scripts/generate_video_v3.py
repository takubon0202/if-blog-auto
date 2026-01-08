#!/usr/bin/env python3
"""
Video Generation V3 - SlideMovie_WorkFlow方式

SlideMovie_WorkFlowリポジトリを参考に、以下の改善を実装:
1. 音声の長さに基づいたスライド時間
2. video_timings.json形式のタイミングデータ
3. 字幕セグメントの自動生成
4. 確実なフォールバック画像生成

Workflow:
1. Script Generation - スライドごとのナレーション生成
2. Audio Synthesis - 各スライドの音声を個別生成・時間計測
3. Timing Calculation - フレームベースのタイミング計算
4. Image Generation - 全スライドの画像生成（フォールバック保証）
5. Video Assembly - Remotionでの動画生成

Usage:
    from generate_video_v3 import VideoGeneratorV3

    generator = VideoGeneratorV3()
    result = await generator.generate(
        research_data=research_result,
        topic="ai_tools",
        topic_info=topic_info
    )
"""

import asyncio
import base64
import io
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import wave
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Load .env
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass

# Third-party
try:
    from google import genai
    from google.genai import types
except ImportError:
    print("Error: google-generativeai not installed")
    sys.exit(1)

try:
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
except ImportError:
    print("Error: Pillow not installed")
    sys.exit(1)

try:
    import numpy as np
except ImportError:
    print("Error: numpy not installed")
    sys.exit(1)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# =============================================================================
# Configuration
# =============================================================================

@dataclass
class VideoConfig:
    """動画設定"""
    width: int = 1920
    height: int = 1080
    fps: int = 30
    default_slide_duration: float = 5.0  # 音声なしの場合のデフォルト
    min_slide_duration: float = 3.0
    max_slide_duration: float = 30.0
    audio_padding: float = 0.5  # 音声後の余白


# トピック別カラースキーム
TOPIC_COLORS = {
    "psychology": ("#2b6cb0", "#4299e1"),
    "education": ("#2f855a", "#48bb78"),
    "startup": ("#c05621", "#ed8936"),
    "investment": ("#744210", "#d69e2e"),
    "ai_tools": ("#1a365d", "#3182ce"),
    "inclusive_education": ("#285e61", "#38b2ac"),
    "weekly_summary": ("#1e3a5f", "#2196f3"),
}


# =============================================================================
# Script Generator
# =============================================================================

class ScriptGenerator:
    """スライドスクリプト生成"""

    MODEL = "gemini-2.0-flash"

    def __init__(self):
        api_key = os.getenv("GOOGLE_AI_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_AI_API_KEY is required")
        self.client = genai.Client(api_key=api_key)

    async def generate(
        self,
        research_data: str,
        topic: str,
        topic_info: Dict[str, Any],
        num_slides: int = 6
    ) -> Dict[str, Any]:
        """動画用スクリプトを生成"""

        topic_name = topic_info.get("name", topic)

        prompt = f"""あなたはプロのプレゼンテーション作成者です。
以下のリサーチデータから、{num_slides}枚のスライドで構成される解説動画のスクリプトを作成してください。

【リサーチデータ】
{research_data[:4000]}

【トピック】{topic_name}

【出力形式】JSON
{{
  "title": "動画タイトル（30文字以内）",
  "slides": [
    {{
      "slide_id": 1,
      "type": "title",
      "heading": "タイトル",
      "subheading": "サブタイトル",
      "points": [],
      "narration": "ナレーション文（50-100文字）",
      "image_prompt": "English image prompt for this slide"
    }},
    {{
      "slide_id": 2,
      "type": "content",
      "heading": "ポイント1",
      "subheading": "",
      "points": ["要点1", "要点2", "要点3"],
      "narration": "ナレーション文（80-150文字）",
      "image_prompt": "English image prompt"
    }}
  ]
}}

【ルール】
1. スライド構成:
   - slide 1: title（導入）
   - slide 2-{num_slides-1}: content（本編）
   - slide {num_slides}: ending（まとめ）

2. ナレーション:
   - 話し言葉で自然に
   - 「です・ます」調
   - 50-150文字程度

3. 画像プロンプト:
   - 必ず英語で記述
   - "16:9 aspect ratio, professional, clean design" を含める
   - テキストや文字は含めない指示

4. 要点:
   - contentスライドは2-4個のポイント
   - 簡潔に（各20文字以内）

JSONのみを出力してください。
"""

        try:
            config = types.GenerateContentConfig(
                temperature=0.7,
                max_output_tokens=4096,
                response_mime_type="application/json"
            )

            response = await asyncio.to_thread(
                self.client.models.generate_content,
                model=self.MODEL,
                contents=prompt,
                config=config
            )

            text = response.text.strip()

            # コードブロック除去
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]

            script = json.loads(text)

            # スライド数調整
            if len(script.get("slides", [])) != num_slides:
                script = self._adjust_slides(script, num_slides, topic_name)

            logger.info(f"Script generated: {len(script['slides'])} slides")
            return script

        except Exception as e:
            logger.error(f"Script generation failed: {e}")
            return self._create_fallback_script(topic, topic_info, num_slides)

    def _adjust_slides(self, script: Dict, target: int, topic_name: str) -> Dict:
        """スライド数を調整"""
        slides = script.get("slides", [])

        while len(slides) < target:
            idx = len(slides) + 1
            slides.append({
                "slide_id": idx,
                "type": "content" if idx < target else "ending",
                "heading": f"ポイント{idx - 1}",
                "subheading": "",
                "points": ["詳細は本編で"],
                "narration": "続いてのポイントをご紹介します。",
                "image_prompt": "Professional abstract background, gradient, minimalist, 16:9 aspect ratio"
            })

        if len(slides) > target:
            slides = slides[:target]

        if slides:
            slides[-1]["type"] = "ending"

        script["slides"] = slides
        return script

    def _create_fallback_script(self, topic: str, topic_info: Dict, num_slides: int) -> Dict:
        """フォールバックスクリプト"""
        topic_name = topic_info.get("name", topic)

        slides = []
        for i in range(1, num_slides + 1):
            if i == 1:
                slide_type = "title"
                heading = topic_name
                narration = f"今回は{topic_name}について解説します。"
                points = []
            elif i == num_slides:
                slide_type = "ending"
                heading = "まとめ"
                narration = "以上が今回のまとめです。ぜひブログ記事もご覧ください。"
                points = []
            else:
                slide_type = "content"
                heading = f"ポイント{i - 1}"
                narration = f"ポイント{i - 1}について説明します。"
                points = ["要点A", "要点B"]

            slides.append({
                "slide_id": i,
                "type": slide_type,
                "heading": heading,
                "subheading": "",
                "points": points,
                "narration": narration,
                "image_prompt": "Professional presentation slide background, gradient colors, clean minimalist design, 16:9 aspect ratio, no text"
            })

        return {
            "title": topic_name,
            "slides": slides
        }


# =============================================================================
# Audio Synthesizer (Per-Slide)
# =============================================================================

class AudioSynthesizer:
    """スライドごとの音声合成"""

    MODEL = "gemini-2.5-flash-preview-tts"
    VOICE = "Aoede"  # 日本語対応の声
    SAMPLE_RATE = 24000

    def __init__(self):
        api_key = os.getenv("GOOGLE_AI_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_AI_API_KEY is required")
        self.client = genai.Client(api_key=api_key)

    async def synthesize_all(
        self,
        slides: List[Dict],
        output_dir: Path
    ) -> List[Dict]:
        """全スライドの音声を生成し、各スライドに音声データと時間を追加"""

        output_dir.mkdir(parents=True, exist_ok=True)
        audio_dir = output_dir / "audio"
        audio_dir.mkdir(exist_ok=True)

        results = []

        for slide in slides:
            slide_id = slide.get("slide_id", len(results) + 1)
            narration = slide.get("narration", "")

            audio_result = {
                "slide_id": slide_id,
                "audio_path": None,
                "audio_base64": None,
                "duration": 5.0,  # デフォルト
                "narration": narration
            }

            if narration and narration.strip():
                try:
                    audio_path = audio_dir / f"slide_{slide_id:02d}.wav"
                    duration, audio_data = await self._synthesize(narration, audio_path)

                    # Base64エンコード
                    with open(audio_path, 'rb') as f:
                        audio_bytes = f.read()
                    audio_base64 = f"data:audio/wav;base64,{base64.b64encode(audio_bytes).decode('utf-8')}"

                    audio_result["audio_path"] = str(audio_path)
                    audio_result["audio_base64"] = audio_base64
                    audio_result["duration"] = duration

                    logger.info(f"Audio slide {slide_id}: {duration:.1f}s")

                except Exception as e:
                    logger.warning(f"Audio synthesis failed for slide {slide_id}: {e}")

            results.append(audio_result)

            # レート制限
            await asyncio.sleep(1)

        return results

    async def _synthesize(self, text: str, output_path: Path) -> Tuple[float, bytes]:
        """単一テキストを音声化"""

        config = types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name=self.VOICE
                    )
                )
            )
        )

        response = await asyncio.to_thread(
            self.client.models.generate_content,
            model=self.MODEL,
            contents=text,
            config=config
        )

        # PCM抽出
        pcm_data = None
        if response.candidates:
            for part in response.candidates[0].content.parts:
                if hasattr(part, 'inline_data') and part.inline_data:
                    data = part.inline_data.data
                    pcm_data = base64.b64decode(data) if isinstance(data, str) else data
                    break

        if not pcm_data:
            raise ValueError("No audio data returned")

        # WAV保存
        wav_data = self._pcm_to_wav(pcm_data)
        with open(output_path, 'wb') as f:
            f.write(wav_data)

        # 時間計算
        duration = len(pcm_data) / (self.SAMPLE_RATE * 2)  # 16-bit mono
        return duration, pcm_data

    def _pcm_to_wav(self, pcm: bytes, rate: int = 24000) -> bytes:
        """PCM -> WAV"""
        buf = io.BytesIO()
        with wave.open(buf, 'wb') as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(rate)
            w.writeframes(pcm)
        return buf.getvalue()


# =============================================================================
# Timing Generator
# =============================================================================

class TimingGenerator:
    """video_timings.json形式のタイミング生成"""

    def __init__(self, fps: int = 30):
        self.fps = fps

    def generate(
        self,
        slides: List[Dict],
        audio_results: List[Dict],
        config: VideoConfig
    ) -> Dict:
        """フレームベースのタイミングデータを生成"""

        timings = {
            "fps": self.fps,
            "totalFrames": 0,
            "slides": []
        }

        current_frame = 0

        for i, slide in enumerate(slides):
            # 対応する音声データを取得
            audio = audio_results[i] if i < len(audio_results) else None

            # 時間計算
            if audio and audio.get("duration"):
                duration = audio["duration"] + config.audio_padding
            else:
                duration = config.default_slide_duration

            # 範囲制限
            duration = max(config.min_slide_duration, min(config.max_slide_duration, duration))
            duration_frames = int(duration * self.fps)

            # 字幕セグメント生成
            narration = slide.get("narration", "")
            subtitles = self._generate_subtitles(narration, current_frame, duration_frames)

            slide_timing = {
                "index": i,
                "slide_id": slide.get("slide_id", i + 1),
                "type": slide.get("type", "content"),
                "startFrame": current_frame,
                "endFrame": current_frame + duration_frames,
                "duration": duration,
                "audioBase64": audio.get("audio_base64") if audio else None,
                "subtitles": subtitles
            }

            timings["slides"].append(slide_timing)
            current_frame += duration_frames

        timings["totalFrames"] = current_frame

        logger.info(f"Timings generated: {len(timings['slides'])} slides, {current_frame} frames ({current_frame/self.fps:.1f}s)")
        return timings

    def _generate_subtitles(
        self,
        text: str,
        start_frame: int,
        total_frames: int,
        max_chars: int = 30
    ) -> List[Dict]:
        """字幕セグメントを生成"""

        if not text or not text.strip():
            return []

        # 文を分割
        sentences = re.split(r'[。、！？]', text)
        sentences = [s.strip() for s in sentences if s.strip()]

        if not sentences:
            return [{
                "text": text[:max_chars * 2],
                "startFrame": start_frame,
                "endFrame": start_frame + total_frames
            }]

        subtitles = []
        frames_per_segment = total_frames // len(sentences) if sentences else total_frames
        current = start_frame

        for i, sentence in enumerate(sentences):
            # 長い文は分割
            if len(sentence) > max_chars:
                lines = [sentence[j:j+max_chars] for j in range(0, len(sentence), max_chars)]
                display_text = "\n".join(lines[:2])  # 最大2行
            else:
                display_text = sentence

            end = current + frames_per_segment
            if i == len(sentences) - 1:
                end = start_frame + total_frames  # 最後のセグメントは終端まで

            subtitles.append({
                "text": display_text,
                "startFrame": current,
                "endFrame": end
            })

            current = end

        return subtitles


# =============================================================================
# Image Generator (with Fallback)
# =============================================================================

class ImageGenerator:
    """スライド画像生成（確実なフォールバック付き）"""

    MODEL = "gemini-2.0-flash-exp"

    def __init__(self):
        api_key = os.getenv("GOOGLE_AI_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_AI_API_KEY is required")
        self.client = genai.Client(api_key=api_key)

    async def generate_all(
        self,
        slides: List[Dict],
        topic_id: str,
        output_dir: Path
    ) -> List[Dict]:
        """全スライドの画像を生成（フォールバック保証）"""

        images_dir = output_dir / "images"
        images_dir.mkdir(parents=True, exist_ok=True)

        results = []
        colors = TOPIC_COLORS.get(topic_id, ("#1a365d", "#3182ce"))

        for slide in slides:
            slide_id = slide.get("slide_id", len(results) + 1)
            prompt = slide.get("image_prompt", "")
            heading = slide.get("heading", "")

            image_path = images_dir / f"slide_{slide_id:02d}.png"

            # 画像生成を試行
            success = False
            if prompt:
                success = await self._generate_image(prompt, image_path)

            # 失敗時はフォールバック
            if not success:
                logger.info(f"Using fallback image for slide {slide_id}")
                self._create_fallback_image(heading, colors, image_path)

            # Base64エンコード
            with open(image_path, 'rb') as f:
                image_bytes = f.read()
            image_base64 = f"data:image/png;base64,{base64.b64encode(image_bytes).decode('utf-8')}"

            results.append({
                "slide_id": slide_id,
                "image_path": str(image_path),
                "image_base64": image_base64,
                "generated": success
            })

            # レート制限
            await asyncio.sleep(2)

        logger.info(f"Images: {sum(1 for r in results if r['generated'])}/{len(results)} generated")
        return results

    async def _generate_image(self, prompt: str, output_path: Path) -> bool:
        """Geminiで画像生成"""

        for attempt in range(3):
            try:
                config = types.GenerateContentConfig(
                    response_modalities=["IMAGE"]
                )

                response = await asyncio.to_thread(
                    self.client.models.generate_content,
                    model=self.MODEL,
                    contents=prompt,
                    config=config
                )

                # 画像データ抽出
                if response.candidates:
                    for part in response.candidates[0].content.parts:
                        if hasattr(part, 'inline_data') and part.inline_data:
                            mime_type = part.inline_data.mime_type
                            if 'image' in mime_type:
                                data = part.inline_data.data
                                image_data = base64.b64decode(data) if isinstance(data, str) else data

                                # 画像を開いてリサイズ
                                img = Image.open(io.BytesIO(image_data))
                                img = img.resize((1920, 1080), Image.Resampling.LANCZOS)
                                img.save(output_path, 'PNG')

                                return True

                return False

            except Exception as e:
                logger.warning(f"Image generation attempt {attempt + 1}/3 failed: {e}")
                if attempt < 2:
                    await asyncio.sleep(3)

        return False

    def _create_fallback_image(
        self,
        heading: str,
        colors: Tuple[str, str],
        output_path: Path
    ):
        """フォールバック画像を生成（グラデーション + テキスト）"""

        width, height = 1920, 1080
        primary, secondary = colors

        # グラデーション背景
        img = Image.new('RGB', (width, height))
        pixels = img.load()

        # 色をRGBに変換
        def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
            hex_color = hex_color.lstrip('#')
            return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

        c1 = hex_to_rgb(primary)
        c2 = hex_to_rgb(secondary)

        for y in range(height):
            ratio = y / height
            r = int(c1[0] * (1 - ratio) + c2[0] * ratio)
            g = int(c1[1] * (1 - ratio) + c2[1] * ratio)
            b = int(c1[2] * (1 - ratio) + c2[2] * ratio)
            for x in range(width):
                pixels[x, y] = (r, g, b)

        # テキスト描画
        draw = ImageDraw.Draw(img)

        # フォント（システムフォントを使用）
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 72)
        except:
            try:
                font = ImageFont.truetype("C:/Windows/Fonts/meiryo.ttc", 72)
            except:
                font = ImageFont.load_default()

        # テキスト中央配置
        if heading:
            bbox = draw.textbbox((0, 0), heading, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            x = (width - text_width) // 2
            y = (height - text_height) // 2

            # 影
            draw.text((x + 3, y + 3), heading, fill=(0, 0, 0, 128), font=font)
            # テキスト
            draw.text((x, y), heading, fill=(255, 255, 255), font=font)

        img.save(output_path, 'PNG')


# =============================================================================
# Video Assembler (Remotion)
# =============================================================================

class VideoAssembler:
    """Remotion統合による動画生成"""

    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path(__file__).parent.parent.parent
        self.remotion_dir = self.project_root / "remotion"

    async def assemble(
        self,
        script: Dict,
        timings: Dict,
        image_results: List[Dict],
        audio_results: List[Dict],
        output_path: Path,
        topic: str
    ) -> str:
        """動画を生成"""

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # propsを構築
        props = self._build_props(script, timings, image_results, audio_results, topic)

        # props.jsonを保存
        props_path = self.remotion_dir / "public" / "props_v3.json"
        props_path.parent.mkdir(parents=True, exist_ok=True)
        with open(props_path, 'w', encoding='utf-8') as f:
            json.dump(props, f, ensure_ascii=False, indent=2)

        logger.info(f"Props saved: {props_path}")

        # Remotionでレンダリング
        return await self._render(props_path, output_path)

    def _build_props(
        self,
        script: Dict,
        timings: Dict,
        image_results: List[Dict],
        audio_results: List[Dict],
        topic: str
    ) -> Dict:
        """Remotion用propsを構築"""

        slides = []
        slide_images = []

        for i, slide_script in enumerate(script.get("slides", [])):
            # タイミング情報
            timing = timings["slides"][i] if i < len(timings["slides"]) else {}

            # 画像
            img_result = image_results[i] if i < len(image_results) else {}
            image_base64 = img_result.get("image_base64", "")
            slide_images.append(image_base64)

            # 音声
            audio_result = audio_results[i] if i < len(audio_results) else {}

            slide_data = {
                "type": slide_script.get("type", "content"),
                "heading": slide_script.get("heading", ""),
                "subheading": slide_script.get("subheading", ""),
                "points": slide_script.get("points", []),
                "startFrame": timing.get("startFrame", i * 150),
                "endFrame": timing.get("endFrame", (i + 1) * 150),
                "duration": timing.get("duration", 5.0),
                "audioBase64": audio_result.get("audio_base64"),
                "subtitles": timing.get("subtitles", [])
            }

            slides.append(slide_data)

        props = {
            "title": script.get("title", ""),
            "topic": topic,
            "fps": timings.get("fps", 30),
            "totalFrames": timings.get("totalFrames", len(slides) * 150),
            "slides": slides,
            "slideImages": slide_images
        }

        logger.info(f"Props built: {len(slides)} slides, {len(slide_images)} images, {props['totalFrames']} frames")

        return props

    async def _render(self, props_path: Path, output_path: Path) -> str:
        """Remotionでレンダリング"""

        render_script = self.remotion_dir / "render.mjs"

        if not render_script.exists():
            raise FileNotFoundError(f"render.mjs not found: {render_script}")

        cmd = [
            "node",
            str(render_script),
            "SlideVideoV3",
            str(props_path),
            str(output_path)
        ]

        logger.info(f"Rendering: {' '.join(cmd)}")

        try:
            result = subprocess.run(
                cmd,
                cwd=str(self.remotion_dir),
                capture_output=True,
                text=True,
                timeout=600
            )

            if result.returncode != 0:
                logger.error(f"Render error: {result.stderr}")
                # フォールバック: SlideVideoを使用
                cmd[2] = "SlideVideo"
                logger.info("Trying fallback composition: SlideVideo")
                result = subprocess.run(
                    cmd,
                    cwd=str(self.remotion_dir),
                    capture_output=True,
                    text=True,
                    timeout=600
                )

            if output_path.exists():
                logger.info(f"Video created: {output_path} ({output_path.stat().st_size} bytes)")
                return str(output_path)
            else:
                raise RuntimeError("Video file not created")

        except subprocess.TimeoutExpired:
            raise RuntimeError("Rendering timeout (600s)")
        except Exception as e:
            raise RuntimeError(f"Rendering failed: {e}")


# =============================================================================
# Main Generator Class
# =============================================================================

class VideoGeneratorV3:
    """動画生成V3 - SlideMovie_WorkFlow方式"""

    def __init__(self):
        self.config = VideoConfig()
        self.script_gen = ScriptGenerator()
        self.audio_synth = AudioSynthesizer()
        self.timing_gen = TimingGenerator(fps=self.config.fps)
        self.image_gen = ImageGenerator()
        self.assembler = VideoAssembler()

    async def generate(
        self,
        research_data: str,
        topic: str,
        topic_info: Dict[str, Any],
        num_slides: int = 6
    ) -> Dict[str, Any]:
        """
        完全な動画生成ワークフロー

        Returns:
            {
                "status": "success" | "error",
                "video_path": str,
                "duration": float,
                "slides_count": int,
                "title": str,
                "error": str (if error)
            }
        """

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = Path(__file__).parent.parent.parent / "output" / "videos" / f"{timestamp}_{topic}"
        output_dir.mkdir(parents=True, exist_ok=True)

        try:
            # Step 1: スクリプト生成
            logger.info("Step 1: Generating script...")
            script = await self.script_gen.generate(
                research_data, topic, topic_info, num_slides
            )

            # Step 2: 音声合成
            logger.info("Step 2: Synthesizing audio...")
            audio_results = await self.audio_synth.synthesize_all(
                script["slides"], output_dir
            )

            # Step 3: タイミング計算
            logger.info("Step 3: Calculating timings...")
            timings = self.timing_gen.generate(
                script["slides"], audio_results, self.config
            )

            # Step 4: 画像生成
            logger.info("Step 4: Generating images...")
            image_results = await self.image_gen.generate_all(
                script["slides"], topic, output_dir
            )

            # Step 5: 動画生成
            logger.info("Step 5: Assembling video...")
            video_filename = f"slide_video_{timestamp}_{topic}.mp4"
            video_path = output_dir / video_filename

            await self.assembler.assemble(
                script, timings, image_results, audio_results,
                video_path, topic
            )

            total_duration = timings["totalFrames"] / self.config.fps

            logger.info(f"Video generation complete: {video_path}")

            return {
                "status": "success",
                "video_path": str(video_path),
                "duration": total_duration,
                "slides_count": len(script["slides"]),
                "title": script.get("title", ""),
                "timings": timings
            }

        except Exception as e:
            logger.error(f"Video generation failed: {e}")
            import traceback
            traceback.print_exc()

            return {
                "status": "error",
                "error": str(e),
                "video_path": None,
                "duration": 0,
                "slides_count": 0,
                "title": ""
            }


# =============================================================================
# CLI Entry Point
# =============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Video Generator V3")
    parser.add_argument("--topic", default="ai_tools", help="Topic ID")
    parser.add_argument("--slides", type=int, default=6, help="Number of slides")
    args = parser.parse_args()

    # テスト用リサーチデータ
    test_research = """
    2026年のAIツール最新動向について解説します。
    ChatGPT、Claude、Geminiなどの生成AIが急速に進化しています。
    企業での活用事例も増加し、業務効率化に貢献しています。
    """

    test_topic_info = {
        "name": "AIツール・技術動向",
        "keywords": ["AI", "ChatGPT", "生成AI"]
    }

    generator = VideoGeneratorV3()
    result = asyncio.run(generator.generate(
        research_data=test_research,
        topic=args.topic,
        topic_info=test_topic_info,
        num_slides=args.slides
    ))

    print(json.dumps(result, ensure_ascii=False, indent=2))
