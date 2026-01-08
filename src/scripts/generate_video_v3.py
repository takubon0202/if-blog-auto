#!/usr/bin/env python3
"""
Video Generation V3 - Marp Slides to Video (SlideMovie_WorkFlow style)

正しいフロー:
1. Marp Markdown スライド生成 (Gemini)
2. Marp CLI → PNG画像変換 (--images png)
3. ナレーションスクリプト生成 (Gemini)
4. TTS音声生成 (Gemini TTS)
5. タイミング計算 (音声長ベース)
6. Remotion動画レンダリング

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
from dataclasses import dataclass
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
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("Error: Pillow not installed")
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
    default_slide_duration: float = 5.0
    min_slide_duration: float = 3.0
    max_slide_duration: float = 30.0
    audio_padding: float = 0.5


# トピック別カラースキーム
TOPIC_COLORS = {
    "psychology": {
        "primary": "#00b4d8",
        "secondary": "#90e0ef",
        "bg": "#1a1a2e",
        "bg_secondary": "#16213e",
        "name": "心理学・メンタルヘルス"
    },
    "education": {
        "primary": "#10b981",
        "secondary": "#6ee7b7",
        "bg": "#1a1a2e",
        "bg_secondary": "#0d1f22",
        "name": "教育・学習科学"
    },
    "startup": {
        "primary": "#f59e0b",
        "secondary": "#fcd34d",
        "bg": "#1a1a2e",
        "bg_secondary": "#1f1a0d",
        "name": "起業家育成"
    },
    "investment": {
        "primary": "#14b8a6",
        "secondary": "#5eead4",
        "bg": "#1a1a2e",
        "bg_secondary": "#0d1f1d",
        "name": "投資教育"
    },
    "ai_tools": {
        "primary": "#3b82f6",
        "secondary": "#93c5fd",
        "bg": "#1a1a2e",
        "bg_secondary": "#0d1528",
        "name": "AIツール"
    },
    "inclusive_education": {
        "primary": "#06b6d4",
        "secondary": "#67e8f9",
        "bg": "#1a1a2e",
        "bg_secondary": "#0d1f22",
        "name": "インクルーシブ教育"
    },
    "weekly_summary": {
        "primary": "#0ea5e9",
        "secondary": "#7dd3fc",
        "bg": "#1a1a2e",
        "bg_secondary": "#0d1825",
        "name": "週間総括"
    }
}


# =============================================================================
# Step 1: Marp Markdown Generator
# =============================================================================

class MarpSlideGenerator:
    """Marp Markdown形式のスライド生成"""

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
        num_slides: int = 6,
        output_dir: Path = None
    ) -> Dict[str, Any]:
        """Marp Markdownスライドを生成"""

        colors = TOPIC_COLORS.get(topic, TOPIC_COLORS["ai_tools"])
        topic_name = topic_info.get("name", colors.get("name", topic))

        prompt = f"""あなたはMarp形式のプレゼンテーション作成の専門家です。
以下のリサーチデータから、{num_slides}枚のスライドで構成されるMarp Markdownを作成してください。

【リサーチデータ】
{research_data[:5000]}

【トピック】{topic_name}

【出力形式】
必ず以下のMarp形式で出力してください:

```markdown
---
marp: true
theme: default
paginate: true
backgroundColor: {colors['bg']}
color: #ffffff
style: |
  section {{
    font-family: 'Noto Sans JP', 'Hiragino Sans', sans-serif;
    background: linear-gradient(135deg, {colors['bg']} 0%, {colors['bg_secondary']} 100%);
  }}
  h1 {{
    color: {colors['primary']};
    font-size: 64px;
    font-weight: 800;
    text-shadow: 0 4px 20px rgba(0,0,0,0.5);
  }}
  h2 {{
    color: {colors['secondary']};
    font-size: 48px;
    font-weight: 700;
  }}
  ul {{
    font-size: 36px;
    line-height: 1.8;
  }}
  li {{
    margin-bottom: 16px;
  }}
---

<!-- _class: lead -->

# メインタイトル

## サブタイトル

---

# スライド2のタイトル

- ポイント1
- ポイント2
- ポイント3

---

(以下、各スライドを --- で区切る)
```

【ルール】
1. 必ず{num_slides}枚のスライドを作成
2. 最初のスライドはタイトルスライド（<!-- _class: lead -->）
3. 最後のスライドはまとめ・CTAスライド
4. 各スライドは必ず`---`で区切る
5. 各スライドには必ずh1（#）の見出しを付ける
6. コンテンツスライドは3-5個の箇条書きポイント
7. 絵文字は使用しない
8. テキストは簡潔に（各ポイント30文字以内）

Marp Markdownのみを出力してください。"""

        try:
            config = types.GenerateContentConfig(
                temperature=0.7,
                max_output_tokens=4096
            )

            response = await asyncio.to_thread(
                self.client.models.generate_content,
                model=self.MODEL,
                contents=prompt,
                config=config
            )

            markdown_content = response.text.strip()

            # コードブロック除去
            if "```markdown" in markdown_content:
                markdown_content = markdown_content.split("```markdown")[1].split("```")[0]
            elif "```" in markdown_content:
                parts = markdown_content.split("```")
                if len(parts) >= 2:
                    markdown_content = parts[1]

            # Marpヘッダーが無い場合は追加
            if not markdown_content.strip().startswith("---"):
                markdown_content = self._add_marp_header(markdown_content, colors)

            # スライド数を数える
            slide_count = markdown_content.count("---") - 1  # 最初の---はヘッダー
            if slide_count < 1:
                slide_count = 1

            logger.info(f"Generated Marp markdown with {slide_count} slides")

            # ファイル保存
            if output_dir:
                md_path = output_dir / "slides.md"
                md_path.write_text(markdown_content, encoding="utf-8")
                logger.info(f"Saved: {md_path}")

            return {
                "markdown": markdown_content,
                "slide_count": slide_count,
                "topic": topic,
                "title": self._extract_title(markdown_content)
            }

        except Exception as e:
            logger.error(f"Marp generation failed: {e}")
            return self._create_fallback_marp(topic, topic_info, num_slides, colors)

    def _add_marp_header(self, content: str, colors: Dict) -> str:
        """Marpヘッダーを追加"""
        header = f"""---
marp: true
theme: default
paginate: true
backgroundColor: {colors['bg']}
color: #ffffff
style: |
  section {{
    font-family: 'Noto Sans JP', 'Hiragino Sans', sans-serif;
    background: linear-gradient(135deg, {colors['bg']} 0%, {colors['bg_secondary']} 100%);
  }}
  h1 {{ color: {colors['primary']}; font-size: 64px; font-weight: 800; }}
  h2 {{ color: {colors['secondary']}; font-size: 48px; }}
  ul {{ font-size: 36px; line-height: 1.8; }}
---

"""
        return header + content

    def _extract_title(self, markdown: str) -> str:
        """Markdownからタイトルを抽出"""
        match = re.search(r'^#\s+(.+)$', markdown, re.MULTILINE)
        if match:
            return match.group(1).strip()
        return "Untitled"

    def _create_fallback_marp(
        self,
        topic: str,
        topic_info: Dict,
        num_slides: int,
        colors: Dict
    ) -> Dict[str, Any]:
        """フォールバックMarpスライド"""

        topic_name = topic_info.get("name", topic)

        slides = []

        # タイトルスライド
        slides.append(f"""<!-- _class: lead -->

# {topic_name}

## 最新トレンド解説""")

        # コンテンツスライド
        for i in range(2, num_slides):
            slides.append(f"""# ポイント{i - 1}

- 重要なポイントを解説します
- 最新の情報をお届け
- 詳しくはブログで""")

        # エンディング
        slides.append("""<!-- _class: lead -->

# まとめ

## 詳しくはブログをご覧ください""")

        markdown = self._add_marp_header("\n\n---\n\n".join(slides), colors)

        return {
            "markdown": markdown,
            "slide_count": num_slides,
            "topic": topic,
            "title": topic_name
        }


# =============================================================================
# Step 2: Marp CLI to PNG Converter
# =============================================================================

class MarpToPngConverter:
    """Marp CLIを使用してPNG画像に変換"""

    async def convert(
        self,
        markdown_path: Path,
        output_dir: Path
    ) -> List[str]:
        """Marp MarkdownをPNG画像に変換"""

        output_dir.mkdir(parents=True, exist_ok=True)

        # 出力パス（Marpは自動で番号付け）
        output_base = output_dir / "slide.png"

        cmd = [
            "npx", "@marp-team/marp-cli",
            str(markdown_path),
            "--images", "png",
            "--allow-local-files",
            "-o", str(output_base)
        ]

        logger.info(f"Running Marp CLI: {' '.join(cmd)}")

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(markdown_path.parent)
            )

            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                logger.error(f"Marp CLI error: {stderr.decode()}")
                return []

            # 生成された画像を検索
            # Marpは slide.001.png, slide.002.png 形式で出力
            image_files = sorted(output_dir.glob("slide.*.png"))

            if not image_files:
                # 別のパターンも試す
                image_files = sorted(output_dir.glob("slide*.png"))

            image_paths = [str(f) for f in image_files]

            logger.info(f"Converted {len(image_paths)} slides to PNG")

            # 標準化した名前に変換 (slide_01.png, slide_02.png)
            standardized_paths = []
            for i, src_path in enumerate(image_paths):
                dst_path = output_dir / f"slide_{i+1:02d}.png"
                if Path(src_path) != dst_path:
                    shutil.copy2(src_path, dst_path)
                standardized_paths.append(str(dst_path))

            return standardized_paths

        except Exception as e:
            logger.error(f"Marp conversion failed: {e}")
            return []

    def create_fallback_images(
        self,
        slide_count: int,
        topic: str,
        output_dir: Path
    ) -> List[str]:
        """フォールバック画像を生成"""

        output_dir.mkdir(parents=True, exist_ok=True)
        colors = TOPIC_COLORS.get(topic, TOPIC_COLORS["ai_tools"])

        image_paths = []

        for i in range(1, slide_count + 1):
            image_path = output_dir / f"slide_{i:02d}.png"
            self._create_gradient_image(
                image_path,
                colors["primary"],
                colors["bg"]
            )
            image_paths.append(str(image_path))

        logger.info(f"Created {len(image_paths)} fallback images")
        return image_paths

    def _create_gradient_image(
        self,
        output_path: Path,
        color1: str,
        color2: str
    ):
        """グラデーション画像を生成"""

        width, height = 1920, 1080

        def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
            hex_color = hex_color.lstrip('#')
            return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

        c1 = hex_to_rgb(color1)
        c2 = hex_to_rgb(color2)

        img = Image.new('RGB', (width, height))
        pixels = img.load()

        for y in range(height):
            ratio = y / height
            r = int(c1[0] * (1 - ratio) + c2[0] * ratio)
            g = int(c1[1] * (1 - ratio) + c2[1] * ratio)
            b = int(c1[2] * (1 - ratio) + c2[2] * ratio)
            for x in range(width):
                pixels[x, y] = (r, g, b)

        img.save(output_path, 'PNG')


# =============================================================================
# Step 3: Narration Script Generator
# =============================================================================

class NarrationGenerator:
    """スライドごとのナレーションスクリプト生成"""

    MODEL = "gemini-2.0-flash"

    def __init__(self):
        api_key = os.getenv("GOOGLE_AI_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_AI_API_KEY is required")
        self.client = genai.Client(api_key=api_key)

    async def generate(
        self,
        markdown_content: str,
        slide_count: int
    ) -> List[Dict]:
        """各スライドのナレーションを生成"""

        prompt = f"""以下のMarpスライドから、各スライドのナレーション（読み上げテキスト）を生成してください。

【スライド内容】
{markdown_content}

【出力形式】JSON配列
```json
[
  {{
    "slide_id": 1,
    "heading": "スライドの見出し",
    "narration": "このスライドを説明するナレーション。50-100文字程度。"
  }},
  {{
    "slide_id": 2,
    "heading": "次のスライドの見出し",
    "narration": "説明ナレーション。話し言葉で自然に。"
  }}
]
```

【ルール】
1. 必ず{slide_count}枚分のナレーションを生成
2. 各ナレーションは50-150文字程度
3. 「です・ます」調で自然な話し言葉
4. スライドの内容を分かりやすく説明
5. 最初のスライドは導入、最後はまとめ

JSONのみを出力してください。"""

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

            narrations = json.loads(text)

            # スライド数を調整
            while len(narrations) < slide_count:
                narrations.append({
                    "slide_id": len(narrations) + 1,
                    "heading": f"スライド{len(narrations) + 1}",
                    "narration": "続いてのポイントをご紹介します。"
                })

            logger.info(f"Generated {len(narrations)} narrations")
            return narrations[:slide_count]

        except Exception as e:
            logger.error(f"Narration generation failed: {e}")
            return self._create_fallback_narrations(slide_count)

    def _create_fallback_narrations(self, slide_count: int) -> List[Dict]:
        """フォールバックナレーション"""
        narrations = []

        for i in range(1, slide_count + 1):
            if i == 1:
                text = "今回のテーマについて解説していきます。"
            elif i == slide_count:
                text = "以上が今回のまとめです。ぜひブログ記事もご覧ください。"
            else:
                text = f"ポイント{i - 1}について説明します。"

            narrations.append({
                "slide_id": i,
                "heading": f"スライド{i}",
                "narration": text
            })

        return narrations


# =============================================================================
# Step 4: TTS Audio Generator
# =============================================================================

class TTSGenerator:
    """Gemini TTSを使用した音声生成"""

    MODEL = "gemini-2.5-flash-preview-tts"
    VOICE = "Aoede"
    SAMPLE_RATE = 24000

    def __init__(self):
        api_key = os.getenv("GOOGLE_AI_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_AI_API_KEY is required")
        self.client = genai.Client(api_key=api_key)

    async def generate_all(
        self,
        narrations: List[Dict],
        output_dir: Path
    ) -> List[Dict]:
        """全スライドの音声を生成"""

        audio_dir = output_dir / "audio"
        audio_dir.mkdir(parents=True, exist_ok=True)

        results = []

        for narration in narrations:
            slide_id = narration.get("slide_id", len(results) + 1)
            text = narration.get("narration", "")

            result = {
                "slide_id": slide_id,
                "audio_path": None,
                "audio_base64": None,
                "duration": 5.0,
                "narration": text
            }

            if text and text.strip():
                try:
                    audio_path = audio_dir / f"slide_{slide_id:02d}.wav"
                    duration = await self._synthesize(text, audio_path)

                    # Base64エンコード
                    with open(audio_path, 'rb') as f:
                        audio_bytes = f.read()
                    audio_base64 = f"data:audio/wav;base64,{base64.b64encode(audio_bytes).decode('utf-8')}"

                    result["audio_path"] = str(audio_path)
                    result["audio_base64"] = audio_base64
                    result["duration"] = duration

                    logger.info(f"Audio slide {slide_id}: {duration:.1f}s")

                except Exception as e:
                    logger.warning(f"TTS failed for slide {slide_id}: {e}")

            results.append(result)
            await asyncio.sleep(1)  # レート制限

        return results

    async def _synthesize(self, text: str, output_path: Path) -> float:
        """テキストを音声に変換"""

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

        # PCMデータ抽出
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
        duration = len(pcm_data) / (self.SAMPLE_RATE * 2)
        return duration

    def _pcm_to_wav(self, pcm: bytes, rate: int = 24000) -> bytes:
        """PCM -> WAV変換"""
        buf = io.BytesIO()
        with wave.open(buf, 'wb') as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(rate)
            w.writeframes(pcm)
        return buf.getvalue()


# =============================================================================
# Step 5: Timing Calculator
# =============================================================================

class TimingCalculator:
    """video_timings.json形式のタイミング計算"""

    def __init__(self, fps: int = 30):
        self.fps = fps

    def calculate(
        self,
        audio_results: List[Dict],
        narrations: List[Dict],
        config: VideoConfig
    ) -> Dict:
        """フレームベースのタイミングを計算"""

        timings = {
            "fps": self.fps,
            "totalFrames": 0,
            "slides": []
        }

        current_frame = 0

        for i, audio in enumerate(audio_results):
            # 音声の長さに基づいて時間を決定
            if audio.get("duration"):
                duration = audio["duration"] + config.audio_padding
            else:
                duration = config.default_slide_duration

            # 範囲制限
            duration = max(config.min_slide_duration, min(config.max_slide_duration, duration))
            duration_frames = int(duration * self.fps)

            # 字幕生成
            narration_text = audio.get("narration", "")
            subtitles = self._generate_subtitles(narration_text, current_frame, duration_frames)

            slide_timing = {
                "index": i,
                "slide_id": audio.get("slide_id", i + 1),
                "startFrame": current_frame,
                "endFrame": current_frame + duration_frames,
                "duration": duration,
                "audioBase64": audio.get("audio_base64"),
                "subtitles": subtitles
            }

            timings["slides"].append(slide_timing)
            current_frame += duration_frames

        timings["totalFrames"] = current_frame

        total_seconds = current_frame / self.fps
        logger.info(f"Timings: {len(timings['slides'])} slides, {current_frame} frames ({total_seconds:.1f}s)")

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
        frames_per_segment = total_frames // len(sentences)
        current = start_frame

        for i, sentence in enumerate(sentences):
            # 長い文は分割
            if len(sentence) > max_chars:
                display_text = sentence[:max_chars] + "..."
            else:
                display_text = sentence

            end = current + frames_per_segment
            if i == len(sentences) - 1:
                end = start_frame + total_frames

            subtitles.append({
                "text": display_text,
                "startFrame": current,
                "endFrame": end
            })

            current = end

        return subtitles


# =============================================================================
# Step 6: Remotion Video Renderer
# =============================================================================

class RemotionRenderer:
    """Remotionによる動画レンダリング"""

    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path(__file__).parent.parent.parent
        self.remotion_dir = self.project_root / "remotion"

    async def render(
        self,
        image_paths: List[str],
        timings: Dict,
        title: str,
        topic: str,
        output_path: Path
    ) -> str:
        """動画をレンダリング"""

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # props構築
        props = self._build_props(image_paths, timings, title, topic)

        # props.json保存
        props_path = self.remotion_dir / "public" / "props_v3.json"
        props_path.parent.mkdir(parents=True, exist_ok=True)
        with open(props_path, 'w', encoding='utf-8') as f:
            json.dump(props, f, ensure_ascii=False, indent=2)

        logger.info(f"Props saved: {props_path}")

        # レンダリング
        return await self._execute_render(props_path, output_path)

    def _build_props(
        self,
        image_paths: List[str],
        timings: Dict,
        title: str,
        topic: str
    ) -> Dict:
        """Remotion用propsを構築"""

        slides = []
        slide_images = []

        for i, timing in enumerate(timings.get("slides", [])):
            # 画像をBase64エンコード
            if i < len(image_paths):
                with open(image_paths[i], 'rb') as f:
                    image_data = f.read()
                image_base64 = f"data:image/png;base64,{base64.b64encode(image_data).decode('utf-8')}"
            else:
                image_base64 = ""

            slide_images.append(image_base64)

            slide_data = {
                "type": "title" if i == 0 else ("ending" if i == len(timings["slides"]) - 1 else "content"),
                "heading": f"スライド{i + 1}",
                "subheading": "",
                "points": [],
                "startFrame": timing.get("startFrame", i * 150),
                "endFrame": timing.get("endFrame", (i + 1) * 150),
                "duration": timing.get("duration", 5.0),
                "audioBase64": timing.get("audioBase64"),
                "subtitles": timing.get("subtitles", [])
            }

            slides.append(slide_data)

        props = {
            "title": title,
            "topic": topic,
            "fps": timings.get("fps", 30),
            "totalFrames": timings.get("totalFrames", len(slides) * 150),
            "slides": slides,
            "slideImages": slide_images
        }

        logger.info(f"Props: {len(slides)} slides, {props['totalFrames']} frames")

        return props

    async def _execute_render(self, props_path: Path, output_path: Path) -> str:
        """Remotionレンダリングを実行"""

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
                logger.info("Trying fallback: SlideVideo")
                result = subprocess.run(
                    cmd,
                    cwd=str(self.remotion_dir),
                    capture_output=True,
                    text=True,
                    timeout=600
                )

            if output_path.exists():
                size = output_path.stat().st_size
                logger.info(f"Video created: {output_path} ({size:,} bytes)")
                return str(output_path)
            else:
                raise RuntimeError("Video file not created")

        except subprocess.TimeoutExpired:
            raise RuntimeError("Rendering timeout (600s)")


# =============================================================================
# Main VideoGeneratorV3 Class
# =============================================================================

class VideoGeneratorV3:
    """
    動画生成V3 - Marp Slides to Video

    フロー:
    1. Marp Markdown生成
    2. Marp CLI → PNG変換
    3. ナレーション生成
    4. TTS音声生成
    5. タイミング計算
    6. Remotionレンダリング
    """

    def __init__(self):
        self.config = VideoConfig()
        self.marp_generator = MarpSlideGenerator()
        self.marp_converter = MarpToPngConverter()
        self.narration_generator = NarrationGenerator()
        self.tts_generator = TTSGenerator()
        self.timing_calculator = TimingCalculator(fps=self.config.fps)
        self.renderer = RemotionRenderer()

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
            # Step 1: Marp Markdownスライド生成
            logger.info("=" * 50)
            logger.info("Step 1: Generating Marp Markdown slides...")
            logger.info("=" * 50)

            marp_result = await self.marp_generator.generate(
                research_data=research_data,
                topic=topic,
                topic_info=topic_info,
                num_slides=num_slides,
                output_dir=output_dir
            )

            markdown_path = output_dir / "slides.md"
            markdown_path.write_text(marp_result["markdown"], encoding="utf-8")
            slide_count = marp_result["slide_count"]
            title = marp_result["title"]

            logger.info(f"Generated {slide_count} slides: {markdown_path}")

            # Step 2: Marp CLI → PNG変換
            logger.info("=" * 50)
            logger.info("Step 2: Converting Marp slides to PNG images...")
            logger.info("=" * 50)

            images_dir = output_dir / "images"
            image_paths = await self.marp_converter.convert(markdown_path, images_dir)

            # Marp変換失敗時はフォールバック画像
            if not image_paths:
                logger.warning("Marp conversion failed, creating fallback images")
                image_paths = self.marp_converter.create_fallback_images(
                    slide_count, topic, images_dir
                )

            logger.info(f"Created {len(image_paths)} slide images")

            # Step 3: ナレーション生成
            logger.info("=" * 50)
            logger.info("Step 3: Generating narration scripts...")
            logger.info("=" * 50)

            narrations = await self.narration_generator.generate(
                marp_result["markdown"],
                len(image_paths)
            )

            logger.info(f"Generated {len(narrations)} narrations")

            # Step 4: TTS音声生成
            logger.info("=" * 50)
            logger.info("Step 4: Generating TTS audio...")
            logger.info("=" * 50)

            audio_results = await self.tts_generator.generate_all(
                narrations,
                output_dir
            )

            logger.info(f"Generated {len(audio_results)} audio files")

            # Step 5: タイミング計算
            logger.info("=" * 50)
            logger.info("Step 5: Calculating timings...")
            logger.info("=" * 50)

            timings = self.timing_calculator.calculate(
                audio_results,
                narrations,
                self.config
            )

            # タイミングJSON保存
            timings_path = output_dir / "video_timings.json"
            with open(timings_path, 'w', encoding='utf-8') as f:
                json.dump(timings, f, ensure_ascii=False, indent=2)

            logger.info(f"Timings saved: {timings_path}")

            # Step 6: Remotion動画レンダリング
            logger.info("=" * 50)
            logger.info("Step 6: Rendering video with Remotion...")
            logger.info("=" * 50)

            video_path = output_dir / f"video_{timestamp}_{topic}.mp4"

            await self.renderer.render(
                image_paths=image_paths,
                timings=timings,
                title=title,
                topic=topic,
                output_path=video_path
            )

            total_duration = timings["totalFrames"] / self.config.fps

            logger.info("=" * 50)
            logger.info(f"Video generation complete!")
            logger.info(f"Output: {video_path}")
            logger.info(f"Duration: {total_duration:.1f}s")
            logger.info("=" * 50)

            return {
                "status": "success",
                "video_path": str(video_path),
                "duration": total_duration,
                "slides_count": len(image_paths),
                "title": title,
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

    parser = argparse.ArgumentParser(description="Video Generator V3 - Marp to Video")
    parser.add_argument("--topic", default="ai_tools", help="Topic ID")
    parser.add_argument("--slides", type=int, default=6, help="Number of slides")
    args = parser.parse_args()

    # テスト用データ
    test_research = """
    2026年のAIツール最新動向について解説します。
    ChatGPT、Claude、Geminiなどの生成AIが急速に進化しています。
    企業での活用事例も増加し、業務効率化に貢献しています。

    主なトレンド:
    1. マルチモーダルAIの普及
    2. AIエージェントの実用化
    3. ローカルLLMの発展
    4. AI規制とガバナンス
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
