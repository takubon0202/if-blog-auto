#!/usr/bin/env python3
"""
Gemini API クライアントライブラリ

Gemini 3 Pro Preview, Deep Research, Google Search Toolを
統合的に扱うためのラッパークラス
"""

import os
import asyncio
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)


@dataclass
class ResearchResult:
    """Deep Research結果のデータクラス"""
    interaction_id: str
    status: str
    content: str
    sources: List[Dict[str, str]]
    error: Optional[str] = None


@dataclass
class GenerationResult:
    """コンテンツ生成結果のデータクラス"""
    text: str
    model: str
    usage: Optional[Dict[str, int]] = None
    grounding_sources: Optional[List[Dict]] = None


@dataclass
class ImageGenerationResult:
    """画像生成結果のデータクラス"""
    images: List[bytes]
    model: str
    prompt: str
    text_response: Optional[str] = None


class GeminiClient:
    """Gemini API統合クライアント"""

    # モデル定数
    MODEL_PRO = "gemini-3-pro-preview"
    MODEL_FLASH = "gemini-2.0-flash"
    MODEL_FLASH_3 = "gemini-3-flash-preview"  # SEO/Review用
    MODEL_IMAGE = "gemini-2.5-flash-image"
    AGENT_DEEP_RESEARCH = "deep-research-pro-preview-12-2025"

    def __init__(self, api_key: Optional[str] = None):
        """
        Args:
            api_key: Google AI API Key（省略時は環境変数から取得）
        """
        self.api_key = api_key or os.getenv("GOOGLE_AI_API_KEY")
        if not self.api_key:
            raise ValueError("GOOGLE_AI_API_KEY is required")

        self.client = genai.Client(api_key=self.api_key)
        # 注意: self.client.aio（非同期クライアント）は使用しない
        # Deep Researchは公式ドキュメント通り同期クライアントを使用
        logger.info("GeminiClient initialized")

    async def generate_content(
        self,
        prompt: str,
        model: str = MODEL_PRO,
        enable_search: bool = False,
        system_instruction: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 8192,
        thinking_mode: bool = False
    ) -> GenerationResult:
        """
        コンテンツを生成する

        Args:
            prompt: プロンプト
            model: 使用モデル
            enable_search: Google Search Toolを有効化
            system_instruction: システム指示
            temperature: 生成温度
            max_tokens: 最大トークン数
            thinking_mode: 思考モード（False=オフ、高速応答）

        Returns:
            GenerationResult: 生成結果
        """
        config = {
            "temperature": temperature,
            "max_output_tokens": max_tokens,
        }

        # 思考モードの設定（Gemini 3 Flash Preview用）
        if not thinking_mode and "flash" in model.lower():
            # 思考モードをオフにして高速応答
            config["thinking_config"] = {"thinking_budget": 0}

        # Google Search Tool有効化
        tools = []
        if enable_search:
            tools.append({"google_search": {}})
            config["tools"] = tools

        try:
            response = await asyncio.to_thread(
                self.client.models.generate_content,
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(**config)
            )

            # Grounding情報の抽出
            grounding_sources = None
            if hasattr(response, 'grounding_metadata'):
                grounding_sources = response.grounding_metadata

            return GenerationResult(
                text=response.text,
                model=model,
                usage=getattr(response, 'usage_metadata', None),
                grounding_sources=grounding_sources
            )

        except Exception as e:
            logger.error(f"Content generation failed: {e}")
            raise

    def _sync_deep_research(
        self,
        query: str,
        timeout_seconds: int,
        poll_interval: int
    ) -> ResearchResult:
        """
        Deep Research APIを同期的に実行（公式ドキュメント準拠）

        公式コード: https://ai.google.dev/gemini-api/docs/deep-research
        """
        import time

        logger.info(f"Starting Deep Research (sync): {query[:50]}...")

        # 公式ドキュメント通りの同期呼び出し
        interaction = self.client.interactions.create(
            input=query,
            agent=self.AGENT_DEEP_RESEARCH,
            background=True
        )

        interaction_id = interaction.id
        logger.info(f"Research started: {interaction_id}")

        # ポーリングで完了を待機（公式コード準拠）
        elapsed = 0
        while elapsed < timeout_seconds:
            interaction = self.client.interactions.get(interaction_id)

            if interaction.status == "completed":
                content = interaction.outputs[-1].text if interaction.outputs else ""
                sources = self._extract_sources(interaction)

                logger.info(f"Research completed: {interaction_id}")
                return ResearchResult(
                    interaction_id=interaction_id,
                    status="completed",
                    content=content,
                    sources=sources
                )

            elif interaction.status == "failed":
                logger.error(f"Research failed: {interaction.error}")
                return ResearchResult(
                    interaction_id=interaction_id,
                    status="failed",
                    content="",
                    sources=[],
                    error=str(interaction.error)
                )

            time.sleep(poll_interval)
            elapsed += poll_interval
            logger.debug(f"Research in progress... ({elapsed}s)")

        # タイムアウト
        return ResearchResult(
            interaction_id=interaction_id,
            status="timeout",
            content="",
            sources=[],
            error=f"Research timed out after {timeout_seconds} seconds"
        )

    async def deep_research(
        self,
        query: str,
        timeout_seconds: int = 1800,  # 30分（Deep Researchは時間がかかる）
        poll_interval: int = 10
    ) -> ResearchResult:
        """
        Deep Research APIで深層調査を実行

        公式ドキュメント準拠: 同期クライアントをasyncio.to_thread()でラップ
        https://ai.google.dev/gemini-api/docs/deep-research

        Args:
            query: 調査クエリ
            timeout_seconds: タイムアウト秒数（デフォルト30分）
            poll_interval: ポーリング間隔秒数

        Returns:
            ResearchResult: 調査結果
        """
        try:
            # 同期メソッドをasyncio.to_thread()で非同期実行
            return await asyncio.to_thread(
                self._sync_deep_research,
                query,
                timeout_seconds,
                poll_interval
            )
        except Exception as e:
            logger.error(f"Deep Research error: {e}")
            # 詳細なエラー情報をログ出力
            if hasattr(e, 'response'):
                logger.error(f"Response details: {e.response}")
            if hasattr(e, 'status_code'):
                logger.error(f"Status code: {e.status_code}")
            raise

    def _extract_sources(self, result) -> List[Dict[str, str]]:
        """リサーチ結果からソース情報を抽出"""
        sources = []
        if hasattr(result, 'grounding_metadata') and result.grounding_metadata:
            for source in result.grounding_metadata.get('sources', []):
                sources.append({
                    "title": source.get("title", ""),
                    "url": source.get("uri", ""),
                    "snippet": source.get("snippet", "")
                })
        return sources

    async def search_and_generate(
        self,
        query: str,
        generation_prompt: str,
        model: str = MODEL_PRO
    ) -> GenerationResult:
        """
        Google Searchで検索してから生成する

        Args:
            query: 検索クエリ
            generation_prompt: 生成プロンプト（{search_results}プレースホルダー使用可）
            model: 使用モデル

        Returns:
            GenerationResult: 生成結果
        """
        # 検索を有効にして生成
        combined_prompt = f"""
以下のトピックについて最新情報を検索し、その情報を基に回答してください。

検索トピック: {query}

指示: {generation_prompt}
"""

        return await self.generate_content(
            prompt=combined_prompt,
            model=model,
            enable_search=True
        )

    async def generate_image(
        self,
        prompt: str,
        model: str = MODEL_IMAGE,
        num_images: int = 1
    ) -> ImageGenerationResult:
        """
        Gemini 2.5 Flash imageで画像を生成する

        Args:
            prompt: 画像生成プロンプト
            model: 使用モデル（デフォルト: gemini-2.5-flash-image）
            num_images: 生成画像数

        Returns:
            ImageGenerationResult: 生成結果（画像バイナリデータのリスト）
        """
        logger.info(f"Generating image with prompt: {prompt[:50]}...")

        try:
            # 画像生成用の設定（response_modalitiesが必須）
            config = types.GenerateContentConfig(
                response_modalities=["IMAGE"],
                temperature=1.0,
                top_p=0.95,
                top_k=40
            )

            response = await asyncio.to_thread(
                self.client.models.generate_content,
                model=model,
                contents=prompt,
                config=config
            )

            images = []
            text_response = None

            # レスポンスからの画像データ抽出
            if response.candidates and len(response.candidates) > 0:
                parts = response.candidates[0].content.parts
                for part in parts:
                    # テキストレスポンスの場合
                    if hasattr(part, 'text') and part.text:
                        text_response = part.text
                    # 画像データの場合（inlineData）
                    elif hasattr(part, 'inline_data') and part.inline_data:
                        # inline_data.dataはbytes型の場合とbase64文字列の場合がある
                        data = part.inline_data.data
                        if isinstance(data, str):
                            import base64
                            image_data = base64.b64decode(data)
                        else:
                            image_data = data

                        # 画像サイズの検証（最低1KB以上）
                        if len(image_data) > 1024:
                            images.append(image_data)
                            logger.info(f"Image extracted: {len(image_data)} bytes")
                        else:
                            logger.warning(f"Image data too small: {len(image_data)} bytes, skipping")

            if not images:
                logger.warning("No valid images generated, response may contain only text")
                if text_response:
                    logger.info(f"Text response: {text_response[:200]}...")

            logger.info(f"Generated {len(images)} valid image(s)")

            return ImageGenerationResult(
                images=images,
                model=model,
                prompt=prompt,
                text_response=text_response
            )

        except Exception as e:
            logger.error(f"Image generation failed: {e}")
            raise

    async def generate_blog_image(
        self,
        title: str,
        summary: str,
        style: str = "modern, minimalist, professional",
        image_type: str = "hero"
    ) -> ImageGenerationResult:
        """
        ブログ記事用の画像を生成する

        Args:
            title: 記事タイトル
            summary: 記事概要
            style: 画像スタイル
            image_type: 画像タイプ（hero, section, thumbnail）

        Returns:
            ImageGenerationResult: 生成結果
        """
        # ブログ用に最適化されたプロンプトを構築
        prompt = f"""Create a {image_type} image for a blog article.

Article Title: {title}
Article Summary: {summary}

Style Requirements:
- {style}
- Clean and professional design
- Suitable for blog featured image
- No text or watermarks in the image
- High quality, visually appealing
- Abstract or conceptual representation of the topic

Generate a visually stunning image that captures the essence of this article."""

        return await self.generate_image(prompt)
