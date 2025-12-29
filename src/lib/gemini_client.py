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


class GeminiClient:
    """Gemini API統合クライアント"""

    # モデル定数
    MODEL_PRO = "gemini-3-pro-preview"
    MODEL_FLASH = "gemini-2.0-flash"
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
        logger.info("GeminiClient initialized")

    async def generate_content(
        self,
        prompt: str,
        model: str = MODEL_PRO,
        enable_search: bool = False,
        system_instruction: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 8192
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

        Returns:
            GenerationResult: 生成結果
        """
        config = {
            "temperature": temperature,
            "max_output_tokens": max_tokens,
        }

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

    async def deep_research(
        self,
        query: str,
        timeout_seconds: int = 300,
        poll_interval: int = 10
    ) -> ResearchResult:
        """
        Deep Research APIで深層調査を実行

        Args:
            query: 調査クエリ
            timeout_seconds: タイムアウト秒数
            poll_interval: ポーリング間隔秒数

        Returns:
            ResearchResult: 調査結果
        """
        logger.info(f"Starting Deep Research: {query[:50]}...")

        try:
            # リサーチ開始（非同期）
            interaction = await asyncio.to_thread(
                self.client.interactions.create,
                input=query,
                agent=self.AGENT_DEEP_RESEARCH,
                background=True
            )

            interaction_id = interaction.id
            logger.info(f"Research started: {interaction_id}")

            # ポーリングで完了を待機
            elapsed = 0
            while elapsed < timeout_seconds:
                result = await asyncio.to_thread(
                    self.client.interactions.get,
                    interaction_id
                )

                if result.status == "completed":
                    # 最新の出力を取得
                    content = result.outputs[-1].text if result.outputs else ""
                    sources = self._extract_sources(result)

                    logger.info(f"Research completed: {interaction_id}")
                    return ResearchResult(
                        interaction_id=interaction_id,
                        status="completed",
                        content=content,
                        sources=sources
                    )

                elif result.status == "failed":
                    logger.error(f"Research failed: {result.error}")
                    return ResearchResult(
                        interaction_id=interaction_id,
                        status="failed",
                        content="",
                        sources=[],
                        error=str(result.error)
                    )

                await asyncio.sleep(poll_interval)
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

        except Exception as e:
            logger.error(f"Deep Research error: {e}")
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
