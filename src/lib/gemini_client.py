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

    def _generate_topic_specific_queries(
        self,
        topic_id: str,
        topic_name: str,
        topic_info: Dict[str, Any],
        date_range: Dict[str, str]
    ) -> List[str]:
        """
        トピック別に最適化された検索クエリを生成

        各トピックの特性に合わせた具体的で効果的な検索クエリを生成します。
        """
        keywords = topic_info.get('keywords', [])
        focus_areas = topic_info.get('research_focus', [])
        year = "2025"

        # トピック別の専門的な検索クエリパターン
        topic_query_patterns = {
            "psychology": [
                f"心理学 メンタルヘルス 最新研究 論文発表 {date_range['end']}",
                f"認知行動療法 マインドフルネス 効果 エビデンス 学会 {year}",
                f"ストレス対策 うつ病予防 カウンセリング 新手法 臨床心理"
            ],
            "education": [
                f"教育改革 学習指導要領 文部科学省 発表 {date_range['end']}",
                f"EdTech オンライン学習 AI教育 導入事例 効果測定 {year}",
                f"学習科学 アクティブラーニング 教育効果 研究 実証実験"
            ],
            "startup": [
                f"スタートアップ 資金調達 IPO M&A ニュース {date_range['end']}",
                f"起業家 成功事例 ユニコーン企業 ビジネスモデル {year} 日本",
                f"ベンチャーキャピタル 投資動向 注目スタートアップ テック企業"
            ],
            "investment": [
                f"新NISA iDeCo 制度変更 金融庁 発表 {date_range['end']}",
                f"投資信託 資産形成 ポートフォリオ 運用戦略 {year}",
                f"株式市場 経済動向 金融リテラシー 投資教育 初心者向け"
            ],
            "ai_tools": [
                f"生成AI ChatGPT Claude Gemini 新機能 アップデート {date_range['end']}",
                f"AIツール 業務効率化 活用事例 企業導入 {year}",
                f"機械学習 大規模言語モデル LLM 技術動向 開発者向け"
            ],
            "inclusive_education": [
                f"不登校 支援制度 フリースクール 教育機会確保法 {date_range['end']}",
                f"発達障害 ADHD ASD 合理的配慮 学校支援 {year}",
                f"ニューロダイバーシティ インクルーシブ教育 成功事例 専門家"
            ],
            "weekly_summary": [
                f"週間ニュース 注目トピック AI 教育 経済 {date_range['end']}",
                f"心理学 スタートアップ 投資 トレンド まとめ {year}",
                f"インクルーシブ教育 メンタルヘルス テクノロジー 最新動向"
            ]
        }

        # トピック別クエリがあればそれを使用、なければ汎用クエリを生成
        if topic_id in topic_query_patterns:
            return topic_query_patterns[topic_id]

        # フォールバック: 汎用的だが詳細なクエリを生成
        keyword_str = ' '.join(keywords[:3]) if keywords else topic_name
        focus_str = ' '.join(focus_areas[:2]) if focus_areas else ""

        return [
            f"{keyword_str} 最新ニュース 公式発表 {date_range['end']}",
            f"{topic_name} 専門家 研究 調査報告 論文 {year}",
            f"{topic_name} {focus_str} 事例 統計データ 分析レポート"
        ]

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
        1. 最新ニュース・動向（公式発表、重要ニュース）
        2. 専門家の見解・研究（学術的知見、エビデンス）
        3. 具体的な事例・統計データ（実践例、数値データ）

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

        # トピックIDを取得（topic_infoまたはtopicから）
        topic_id = topic_info.get('id', '')
        topic_name = topic_info.get('name', topic)

        # トピック別に最適化された検索クエリを生成
        search_queries = self._generate_topic_specific_queries(
            topic_id=topic_id,
            topic_name=topic_name,
            topic_info=topic_info,
            date_range=date_range
        )

        all_sources = []
        all_findings = []
        errors = []

        # 検索視点のラベル
        search_perspectives = [
            "最新ニュース・公式発表",
            "専門家の見解・研究データ",
            "実践事例・統計情報"
        ]

        for i, query in enumerate(search_queries[:search_count], 1):
            perspective = search_perspectives[i-1] if i <= len(search_perspectives) else f"視点{i}"
            logger.info(f"Search {i}/{search_count} ({perspective}): {query[:50]}...")

            search_prompt = f"""
【重要な前提条件】
- 本日は{date_range['end']}です
- 必ず過去7日以内（{date_range['start']}〜{date_range['end']}）の最新情報のみを検索・報告してください
- 7日より古い情報は絶対に含めないでください

【検索視点】{perspective}
【検索クエリ】{query}

【詳細な出力要件】

あなたはプロのリサーチャーです。以下の形式で、**読者に価値を提供できる具体的で詳細な情報**を収集してください。

## 発見した重要情報（最低3件、できれば5件以上）

各情報について以下を必ず記載：
- **日付**: YYYY年MM月DD日形式
- **情報の種類**: ニュース/研究発表/政策発表/企業発表/調査結果
- **要約**: 50-100字で具体的に（数値データがあれば必ず含める）
- **重要度**: 高/中（なぜ重要かを一言で）
- **ソースURL**: 完全なURLを記載

## 具体的な数値・データ（見つかった場合）

- 統計データ、調査結果の数値
- 前年比、増減率などの変化
- 市場規模、利用者数などの具体値

## 専門家の意見・分析（見つかった場合）

- 専門家名（または機関名）
- 発言・分析の要約
- 出典

## ソース一覧

各ソースについて：
- タイトル: [記事タイトル]
- URL: [https://で始まる完全URL]
- 信頼度: 高/中（公的機関、大手メディア、専門誌は「高」）
- 公開日: [日付]

【品質基準】
- 曖昧な情報より具体的なデータを優先
- 「〜らしい」「〜と思われる」などの推測は含めない
- 一次ソース（政府発表、研究機関、企業公式）を優先
- 読者がすぐに活用できる実践的な情報を重視
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

        # 統合プロンプトで情報を整理（高品質版）
        target_audience = topic_info.get('target_audience', '一般読者')

        synthesis_prompt = f"""
あなたは{topic_name}分野の専門ライターです。
以下の検索結果を統合して、**読者が価値を感じる高品質なリサーチレポート**を作成してください。

【対象読者】{target_audience}
【調査期間】{date_range['start']}〜{date_range['end']}（7日以内の情報のみ）

【収集した情報（3つの視点から検索）】
{combined_content}

【レポート作成ガイドライン】

## 1. エグゼクティブサマリー（重要度: 最高）
- この1週間で最も重要な3つのポイントを箇条書きで
- 読者が「これだけは知っておくべき」という情報
- 具体的な数値やファクトを含める

## 2. 今週の重要ニュース
各ニュースについて：
- **[日付] タイトル**
- 内容の要約（50-100字）
- なぜ重要か（読者への影響）
- ソース情報

## 3. 注目トレンド・動向分析
- 今週見られた傾向や変化
- 前週や前年との比較（データがあれば）
- 業界・分野への影響予測

## 4. 専門家の見解・研究知見
- 専門家の発言や分析を引用
- 研究機関からの新しい知見
- エビデンスに基づいた洞察

## 5. 実践的な数値・データ
- 具体的な統計データ
- 調査結果の数値
- 市場データ、利用状況など

## 6. 読者へのアクションポイント
- この情報を踏まえて読者が取るべき行動
- 注意すべき点、チェックすべきこと
- 次のステップとして推奨すること

## 7. 来週の注目ポイント（予告）
- 来週発表予定の情報や動向
- フォローすべきトピック

【品質チェックリスト】
- [ ] すべての情報に日付を明記したか
- [ ] 具体的な数値・データを含めたか
- [ ] 読者にとっての価値を明確にしたか
- [ ] 根拠のない推測を排除したか
- [ ] 7日より古い情報を除外したか
- [ ] ソース情報を記載したか

【文体・トーン】
- 専門的だが親しみやすい
- 押し付けがましくない
- 絵文字は使用しない
- 「革新的」「画期的」などの陳腐な表現を避ける
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

    # トピック別カラースキーム
    TOPIC_COLORS = {
        "psychology": {"primary": "#2b6cb0", "accent": "#4299e1", "name": "calming blue"},
        "education": {"primary": "#2f855a", "accent": "#48bb78", "name": "growth green"},
        "startup": {"primary": "#c05621", "accent": "#ed8936", "name": "energetic orange"},
        "investment": {"primary": "#744210", "accent": "#d69e2e", "name": "trustworthy gold-brown"},
        "ai_tools": {"primary": "#1a365d", "accent": "#3182ce", "name": "tech navy blue"},
        "inclusive_education": {"primary": "#285e61", "accent": "#38b2ac", "name": "supportive teal"},
        "weekly_summary": {"primary": "#553c9a", "accent": "#805ad5", "name": "insightful indigo"},
        "default": {"primary": "#1a1a2e", "accent": "#0f3460", "name": "professional navy"}
    }

    # 視覚的構図バリエーション
    COMPOSITION_STYLES = [
        "centered focal point with clean negative space",
        "dynamic diagonal composition with flowing elements",
        "layered depth with foreground and background elements",
        "radial arrangement emanating from center",
        "asymmetric balance with visual tension",
        "grid-based structured layout",
        "organic flowing shapes and curves",
        "geometric abstract pattern"
    ]

    async def analyze_for_image_prompt(
        self,
        title: str,
        summary: str,
        topic_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        記事タイトルと概要を分析して、最適な画像プロンプト要素を生成

        Args:
            title: 記事タイトル
            summary: 記事概要
            topic_id: トピックID（カラースキーム決定用）

        Returns:
            画像生成用の要素を含む辞書
        """
        analysis_prompt = f"""Analyze this blog article title and summary, then suggest specific visual elements for an illustration.

Title: {title}
Summary: {summary}

Provide a JSON response with:
1. "main_subject": The primary visual subject/object to depict (be specific, e.g., "a glowing neural network", "hands exchanging a lightbulb")
2. "visual_metaphor": A creative visual metaphor that represents the article's core message
3. "mood": The emotional tone (e.g., "hopeful and bright", "calm and reflective", "dynamic and energetic")
4. "key_elements": List of 3-4 specific visual elements to include (be concrete, not abstract)
5. "background_style": Describe the background (e.g., "soft gradient from light blue to white", "abstract geometric shapes")
6. "lighting": Describe the lighting style (e.g., "warm sunrise glow", "cool ambient light", "dramatic spotlight")

Important:
- Be specific and visual, not abstract
- Suggest concrete objects, not vague concepts
- Each image should be unique based on the article content
- Avoid generic descriptions like "professional" or "modern"

Respond ONLY with valid JSON, no other text."""

        try:
            result = await self.generate_content(
                prompt=analysis_prompt,
                model=self.MODEL_FLASH,
                temperature=0.8  # 多様性を高めるため
            )

            # JSONをパース
            import json
            import re

            # JSONブロックを抽出
            text = result.text.strip()
            json_match = re.search(r'\{[\s\S]*\}', text)
            if json_match:
                analysis = json.loads(json_match.group())
            else:
                raise ValueError("No valid JSON found in response")

            # トピック別カラーを追加
            colors = self.TOPIC_COLORS.get(topic_id, self.TOPIC_COLORS["default"])
            analysis["color_scheme"] = colors

            # ランダムな構図スタイルを追加
            import random
            analysis["composition"] = random.choice(self.COMPOSITION_STYLES)

            return analysis

        except Exception as e:
            logger.warning(f"Image analysis failed, using fallback: {e}")
            # フォールバック: 基本的な分析結果を返す
            colors = self.TOPIC_COLORS.get(topic_id, self.TOPIC_COLORS["default"])
            return {
                "main_subject": f"abstract representation of {title[:50]}",
                "visual_metaphor": "interconnected nodes and pathways",
                "mood": "professional and thoughtful",
                "key_elements": ["geometric shapes", "flowing lines", "soft gradients"],
                "background_style": "clean gradient from light to white",
                "lighting": "soft ambient light",
                "color_scheme": colors,
                "composition": "centered focal point with clean negative space"
            }

    async def generate_blog_image(
        self,
        title: str,
        summary: str,
        style: str = "modern, minimalist, professional",
        image_type: str = "hero",
        topic_id: Optional[str] = None,
        use_smart_prompt: bool = True
    ) -> ImageGenerationResult:
        """
        ブログ記事用の画像を生成する（スマートプロンプト対応）

        Args:
            title: 記事タイトル
            summary: 記事概要
            style: 画像スタイル
            image_type: 画像タイプ（hero, section, thumbnail）
            topic_id: トピックID（カラースキーム決定用）
            use_smart_prompt: スマートプロンプト生成を使用するか

        Returns:
            ImageGenerationResult: 生成結果
        """
        if use_smart_prompt:
            # 記事を分析してスマートプロンプトを生成
            analysis = await self.analyze_for_image_prompt(title, summary, topic_id)

            colors = analysis.get("color_scheme", self.TOPIC_COLORS["default"])

            prompt = f"""Create a {image_type} illustration for a blog article.

VISUAL CONCEPT:
Main Subject: {analysis.get('main_subject', 'abstract concept')}
Visual Metaphor: {analysis.get('visual_metaphor', 'flowing connections')}

SPECIFIC ELEMENTS TO INCLUDE:
{chr(10).join([f"- {elem}" for elem in analysis.get('key_elements', ['geometric shapes'])])}

STYLE & MOOD:
- Mood: {analysis.get('mood', 'professional')}
- Composition: {analysis.get('composition', 'centered layout')}
- Background: {analysis.get('background_style', 'clean gradient')}
- Lighting: {analysis.get('lighting', 'soft ambient')}

COLOR PALETTE:
- Primary color: {colors['primary']} ({colors['name']})
- Accent color: {colors['accent']}
- Use white and light gray for balance

TECHNICAL REQUIREMENTS:
- High resolution, crisp details
- No text, words, or letters in the image
- No human faces
- Clean, uncluttered composition
- Suitable as blog featured image with text overlay space

Create a unique, visually striking illustration that specifically represents: "{title[:100]}" """

        else:
            # 従来のシンプルなプロンプト
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

        logger.info(f"Generating image with {'smart' if use_smart_prompt else 'simple'} prompt for: {title[:50]}...")

        return await self.generate_image(prompt)
