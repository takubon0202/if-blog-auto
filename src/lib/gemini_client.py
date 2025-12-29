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
    method: str = "deep_research"  # deep_research, multi_search, single_search


@dataclass
class MultiSearchResult:
    """複数回検索結果のデータクラス"""
    status: str
    content: str
    sources: List[Dict[str, str]]
    search_count: int
    combined_findings: List[str]
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

    async def multi_search_research(
        self,
        topic: str,
        topic_info: Dict[str, Any],
        date_range: Dict[str, str],
        search_count: int = 3,
        model: str = MODEL_PRO
    ) -> MultiSearchResult:
        """
        Google Searchを複数回実行してDeep Research簡易版として情報収集

        3つの異なる視点から検索を行い、情報を統合します：
        1. 最新ニュース・動向
        2. 専門家の見解・研究
        3. 具体的な事例・統計データ

        Args:
            topic: トピック名
            topic_info: トピック設定情報
            date_range: 日付範囲 {"start": "...", "end": "..."}
            search_count: 検索回数（デフォルト: 3）
            model: 使用モデル

        Returns:
            MultiSearchResult: 複数回検索の統合結果
        """
        logger.info(f"Starting Multi-Search Research ({search_count} searches): {topic}")

        # 検索クエリのバリエーションを生成
        keywords = topic_info.get('keywords', [topic])
        focus_areas = topic_info.get('research_focus', [])

        search_queries = [
            # 1回目: 最新ニュース・発表
            f"{topic} 最新ニュース {date_range['end']} 発表 動向",
            # 2回目: 専門家・研究
            f"{topic} 専門家 研究 調査結果 {' '.join(keywords[:2]) if keywords else ''}",
            # 3回目: 事例・統計・トレンド
            f"{topic} 事例 統計 トレンド {' '.join(focus_areas[:2]) if focus_areas else ''} 2025"
        ]

        all_sources = []
        all_findings = []
        errors = []

        for i, query in enumerate(search_queries[:search_count], 1):
            logger.info(f"Search {i}/{search_count}: {query[:50]}...")

            search_prompt = f"""
【重要】本日は{date_range['end']}です。
必ず過去7日以内（{date_range['start']}〜{date_range['end']}）の最新情報のみを検索してください。

【検索クエリ】{query}

【出力形式】
以下の形式で情報を整理してください：

## 発見した情報
- [日付] 情報の要約（ソースURL）

## ソース一覧
各ソースについて以下を記載：
- タイトル: [タイトル]
- URL: [完全なURL]
- 要約: [1-2文の要約]

7日より古い情報は絶対に含めないでください。
"""

            try:
                result = await self.generate_content(
                    prompt=search_prompt,
                    model=model,
                    enable_search=True,
                    temperature=0.5
                )

                if result.text:
                    all_findings.append(f"【検索{i}の結果】\n{result.text}")

                # Grounding sourcesを収集
                if result.grounding_sources:
                    if hasattr(result.grounding_sources, 'grounding_chunks'):
                        for chunk in result.grounding_sources.grounding_chunks:
                            if hasattr(chunk, 'web') and chunk.web:
                                source = {
                                    "title": getattr(chunk.web, 'title', ''),
                                    "url": getattr(chunk.web, 'uri', ''),
                                    "snippet": ""
                                }
                                # 重複チェック
                                if not any(s['url'] == source['url'] for s in all_sources):
                                    all_sources.append(source)

                logger.info(f"Search {i} completed, found {len(all_findings)} findings so far")

                # API制限を避けるため少し待機
                if i < search_count:
                    await asyncio.sleep(1)

            except Exception as e:
                logger.error(f"Search {i} failed: {e}")
                errors.append(str(e))
                continue

        if not all_findings:
            return MultiSearchResult(
                status="failed",
                content="",
                sources=[],
                search_count=0,
                combined_findings=[],
                error="; ".join(errors) if errors else "No search results"
            )

        # 収集した情報を統合
        combined_content = "\n\n".join(all_findings)

        # 統合プロンプトで情報を整理
        synthesis_prompt = f"""
以下は「{topic}」に関する複数回の検索結果です。
これらを統合して、構造化されたリサーチレポートを作成してください。

【期間】{date_range['start']}〜{date_range['end']}（7日以内の情報のみ）

【収集した情報】
{combined_content}

【出力形式】
以下の構造で出力してください：

## 調査結果サマリー
[2-3文で要約]

## 主要な発見事項
1. [発見1]（日付）
2. [発見2]（日付）
3. [発見3]（日付）
...

## 最新動向
[トレンドや動向の説明]

## 専門家の見解
[専門家の意見や研究結果]

## 統計・データ
[数値データや統計情報]

## 今後の展望
[予測や今後の見通し]

注意事項：
- 7日より古い情報は含めない
- 各情報に日付を明記
- 根拠のない推測は避ける
"""

        try:
            synthesis_result = await self.generate_content(
                prompt=synthesis_prompt,
                model=model,
                enable_search=False,  # 既に収集した情報を使用
                temperature=0.3
            )

            final_content = synthesis_result.text

        except Exception as e:
            logger.error(f"Synthesis failed: {e}")
            final_content = combined_content  # フォールバック: 生の結果を使用

        logger.info(f"Multi-Search Research completed: {len(all_sources)} sources, {search_count} searches")

        return MultiSearchResult(
            status="completed",
            content=final_content,
            sources=all_sources,
            search_count=search_count,
            combined_findings=all_findings,
            error=None
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
