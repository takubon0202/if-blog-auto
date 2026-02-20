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

try:
    from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception
except ImportError:
    print("Warning: tenacity not installed, retries disabled")
    # フォールバック: デコレータを無効化
    def retry(*args, **kwargs):
        def decorator(func):
            return func
        return decorator
    stop_after_attempt = lambda x: None
    wait_exponential = lambda **kwargs: None
    retry_if_exception = lambda x: None


def is_retryable_error(exception):
    """リトライすべきエラー判定 (429 Resource Exhaustedなど)"""
    err_str = str(exception)
    return "429" in err_str or "ResourceExhausted" in err_str or "rate" in err_str.lower()

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

    MODEL = "gemini-3-flash-preview"  # Gemini 3.1 Flash with thinking off

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
                max_output_tokens=4096,
                thinking_config=types.ThinkingConfig(thinking_level="minimal")  # 思考モードオフ
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

    # タイムアウト設定 (60秒)
    TIMEOUT = 60

    async def convert(
        self,
        markdown_path: Path,
        output_dir: Path
    ) -> List[str]:
        """Marp MarkdownをPNG画像に変換（タイムアウト・柔軟なファイル探索対応）"""

        output_dir.mkdir(parents=True, exist_ok=True)

        # 出力パス（Marpは自動で番号付け）
        output_base = output_dir / "slide.png"

        # Marpコマンドを複数パターンで試行
        marp_commands = [
            ["marp", str(markdown_path), "--images", "png", "--allow-local-files", "-o", str(output_base)],
            ["npx", "@marp-team/marp-cli", str(markdown_path), "--images", "png", "--allow-local-files", "-o", str(output_base)],
            ["npx", "marp", str(markdown_path), "--images", "png", "--allow-local-files", "-o", str(output_base)],
        ]

        for cmd in marp_commands:
            logger.info(f"Trying Marp CLI: {' '.join(cmd)}")

            try:
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=str(markdown_path.parent)
                )

                try:
                    # タイムアウト付きで待機
                    stdout, stderr = await asyncio.wait_for(
                        process.communicate(),
                        timeout=self.TIMEOUT
                    )
                except asyncio.TimeoutError:
                    logger.warning(f"Marp CLI timed out after {self.TIMEOUT}s: {cmd[0]}")
                    try:
                        process.kill()
                        await process.wait()
                    except ProcessLookupError:
                        pass
                    continue

                if process.returncode == 0:
                    logger.info(f"Marp CLI succeeded with: {cmd[0]}")

                    # 生成されたPNGをすべて検索（Marp出力形式差異に対応）
                    # 例: slide.png / slide.001.png / slide-1.png / slide_01.png
                    png_files = [
                        f for f in output_dir.iterdir()
                        if f.is_file() and f.suffix.lower() == ".png"
                    ]

                    def sort_key(path: Path) -> Tuple[int, int, str]:
                        name = path.name.lower()
                        if name == "slide.png":
                            return (0, 1, name)
                        match = re.search(r"(\d+)(?=\.png$)", name)
                        if match:
                            return (0, int(match.group(1)), name)
                        return (1, 0, name)

                    png_files.sort(key=sort_key)

                    if png_files:
                        logger.info(f"Converted {len(png_files)} slides to PNG")

                        # 標準化した名前に変換 (slide_01.png, slide_02.png)
                        standardized_paths = []
                        for i, src_path in enumerate(png_files):
                            dst_path = output_dir / f"slide_{i+1:02d}.png"
                            if src_path != dst_path:
                                shutil.copy2(src_path, dst_path)
                            standardized_paths.append(str(dst_path))

                        return standardized_paths
                    else:
                        logger.warning("Marp succeeded but no PNG images were found")
                else:
                    # エラーログを詳細化（最大2000文字）
                    stderr_text = stderr.decode()
                    logger.warning(f"Marp CLI failed (exit code {process.returncode})")
                    logger.warning(f"Marp stderr: {stderr_text[:2000]}")

            except FileNotFoundError:
                logger.warning(f"Command not found: {cmd[0]}")
                continue
            except Exception as e:
                logger.warning(f"Marp error with {cmd[0]}: {e}")
                continue

        logger.error("All Marp CLI attempts failed")
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

    MODEL = "gemini-3-flash-preview"  # Gemini 3.1 Flash with thinking off

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
                response_mime_type="application/json",
                thinking_config=types.ThinkingConfig(thinking_level="minimal")  # 思考モードオフ
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

    @retry(
        wait=wait_exponential(multiplier=1, min=4, max=60),
        stop=stop_after_attempt(3),
        retry=retry_if_exception(is_retryable_error),
        before_sleep=lambda retry_state: logger.warning(
            f"TTS retry {retry_state.attempt_number}/3 after error: {retry_state.outcome.exception()}"
        )
    )
    async def _synthesize(self, text: str, output_path: Path) -> float:
        """テキストを音声に変換（リトライ付き: 指数バックオフ、最大3回）"""

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
            raise ValueError("No audio data returned from TTS API")

        # PCMデータサイズ検証
        if len(pcm_data) < 1000:
            raise ValueError(f"Audio data too small: {len(pcm_data)} bytes")

        # WAV保存
        wav_data = self._pcm_to_wav(pcm_data)
        with open(output_path, 'wb') as f:
            f.write(wav_data)

        # 時間計算
        duration = len(pcm_data) / (self.SAMPLE_RATE * 2)
        logger.debug(f"TTS synthesized: {len(pcm_data)} bytes, {duration:.1f}s")
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
                "audioPath": audio.get("audio_path"),
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
        public_slides_dir = self.remotion_dir / "public" / "slides_v3"
        public_audio_dir = self.remotion_dir / "public" / "audio_v3"
        public_slides_dir.mkdir(parents=True, exist_ok=True)
        public_audio_dir.mkdir(parents=True, exist_ok=True)

        for i, timing in enumerate(timings.get("slides", [])):
            # 画像をRemotion public配下にコピーして、staticFile参照用パスを保持
            slide_image_path = ""
            if i < len(image_paths):
                src_path = Path(image_paths[i])
                if src_path.exists():
                    dst_filename = f"slide_{i+1:02d}.png"
                    dst_path = public_slides_dir / dst_filename
                    if src_path.resolve() != dst_path.resolve():
                        shutil.copy2(src_path, dst_path)
                    slide_image_path = f"slides_v3/{dst_filename}"
                else:
                    logger.warning(f"Slide image not found: {src_path}")
            else:
                logger.warning(f"No slide image provided for slide index: {i}")

            slide_images.append(slide_image_path)

            # 音声をRemotion public配下にコピー（Base64の代替として確実に参照できるように）
            audio_src = None
            audio_path_value = timing.get("audioPath")
            if audio_path_value:
                src_audio_path = Path(audio_path_value)
                if src_audio_path.exists():
                    dst_audio_filename = f"slide_{i+1:02d}.wav"
                    dst_audio_path = public_audio_dir / dst_audio_filename
                    if src_audio_path.resolve() != dst_audio_path.resolve():
                        shutil.copy2(src_audio_path, dst_audio_path)
                    audio_src = f"audio_v3/{dst_audio_filename}"
                else:
                    logger.warning(f"Slide audio not found: {src_audio_path}")

            slide_data = {
                "type": "title" if i == 0 else ("ending" if i == len(timings["slides"]) - 1 else "content"),
                "heading": f"スライド{i + 1}",
                "subheading": "",
                "points": [],
                "startFrame": timing.get("startFrame", i * 150),
                "endFrame": timing.get("endFrame", (i + 1) * 150),
                "duration": timing.get("duration", 5.0),
                "audioSrc": audio_src,
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
        """Remotionレンダリングを実行（詳細ログ付き）"""

        render_script = self.remotion_dir / "render.mjs"

        if not render_script.exists():
            raise FileNotFoundError(f"render.mjs not found: {render_script}")

        # propsファイルの検証
        if props_path.exists():
            props_size = props_path.stat().st_size
            logger.info(f"Props file size: {props_size:,} bytes ({props_size / 1024:.1f} KB)")
            if props_size > 50 * 1024 * 1024:  # 50MB以上は警告
                logger.warning(f"Props file is very large ({props_size / 1024 / 1024:.1f} MB), may cause memory issues")

        cmd = [
            "node",
            str(render_script),
            "SlideVideoV3",
            str(output_path),  # render.mjs expects: outputPath as args[1]
            str(props_path)    # render.mjs expects: propsFile as args[2]
        ]

        logger.info(f"Rendering: {' '.join(cmd)}")
        logger.info(f"Working directory: {self.remotion_dir}")

        try:
            import time
            start_time = time.time()

            # 非同期でsubprocessを実行（イベントループをブロックしない）
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=str(self.remotion_dir),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            try:
                stdout_bytes, stderr_bytes = await asyncio.wait_for(
                    process.communicate(),
                    timeout=600
                )
                stdout_text = stdout_bytes.decode('utf-8', errors='replace')
                stderr_text = stderr_bytes.decode('utf-8', errors='replace')
                returncode = process.returncode
            except asyncio.TimeoutError:
                logger.error("Remotion rendering timed out after 600 seconds")
                try:
                    process.kill()
                    await process.wait()
                except ProcessLookupError:
                    pass
                raise RuntimeError("Rendering timeout (600s)")

            elapsed = time.time() - start_time
            logger.info(f"Remotion process completed in {elapsed:.1f}s (exit code: {returncode})")

            if returncode != 0:
                # エラーログを詳細化
                logger.error("=" * 60)
                logger.error("REMOTION RENDER FAILED")
                logger.error("=" * 60)
                logger.error(f"Exit code: {returncode}")
                logger.error(f"Elapsed time: {elapsed:.1f}s")

                # stderr を最大5000文字表示
                if stderr_text:
                    logger.error(f"STDERR ({len(stderr_text)} chars):")
                    logger.error(stderr_text[:5000])

                # stdout も確認（エラー情報が含まれることがある）
                if stdout_text:
                    logger.error(f"STDOUT ({len(stdout_text)} chars):")
                    logger.error(stdout_text[:3000])

                logger.error("=" * 60)

                # よくあるエラーパターンを検出
                error_hints = []
                if "ENOMEM" in stderr_text or "out of memory" in stderr_text.lower():
                    error_hints.append("メモリ不足: Base64画像サイズを削減するか、スライド数を減らしてください")
                if "swiftshader" in stderr_text.lower() or "gl" in stderr_text.lower():
                    error_hints.append("GL/レンダリングエラー: CI環境ではREMOTION_GL=swiftshader を設定してください")
                if "timeout" in stderr_text.lower():
                    error_hints.append("タイムアウト: スライド数を減らすか、解像度を下げてください")

                if error_hints:
                    logger.error("考えられる原因と対策:")
                    for hint in error_hints:
                        logger.error(f"  - {hint}")

                raise RuntimeError(f"SlideVideoV3 render failed (exit code {returncode})")

            if output_path.exists():
                size = output_path.stat().st_size
                size_mb = size / 1024 / 1024
                logger.info(f"Video created successfully:")
                logger.info(f"  Path: {output_path}")
                logger.info(f"  Size: {size:,} bytes ({size_mb:.2f} MB)")
                logger.info(f"  Render time: {elapsed:.1f}s")
                return str(output_path)
            else:
                raise RuntimeError("Video file not created after successful render")

        except Exception as e:
            if "timeout" not in str(e).lower():
                logger.error(f"Unexpected error during rendering: {e}")
            raise


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
