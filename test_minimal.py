#!/usr/bin/env python3
"""
Deep Research API 最小テスト
公式ドキュメント完全準拠
https://ai.google.dev/gemini-api/docs/deep-research
"""
import os
import time
from google import genai

# APIキー設定
api_key = os.getenv("GOOGLE_AI_API_KEY")
if not api_key:
    print("ERROR: GOOGLE_AI_API_KEY not set")
    exit(1)

print(f"API Key: {api_key[:10]}...")

# クライアント作成（公式コード準拠）
client = genai.Client(api_key=api_key)

# テスト1: シンプルな英語クエリ（公式例と同じ）
print("\n" + "=" * 50)
print("Test 1: Simple English query (official example)")
print("=" * 50)

try:
    interaction = client.interactions.create(
        input="Research the history of Google TPUs.",
        agent='deep-research-pro-preview-12-2025',
        background=True
    )
    print(f"SUCCESS: Research started: {interaction.id}")

    # 30秒だけポーリング（テスト用）
    for i in range(3):
        time.sleep(10)
        result = client.interactions.get(interaction.id)
        print(f"Status: {result.status}")
        if result.status in ["completed", "failed"]:
            break

except Exception as e:
    print(f"FAILED: {e}")

# テスト2: 日本語クエリ（シンプル）
print("\n" + "=" * 50)
print("Test 2: Simple Japanese query")
print("=" * 50)

try:
    interaction = client.interactions.create(
        input="心理学の最新トレンドについて調査してください。",
        agent='deep-research-pro-preview-12-2025',
        background=True
    )
    print(f"SUCCESS: Research started: {interaction.id}")

except Exception as e:
    print(f"FAILED: {e}")

# テスト3: 現在使用中のクエリ形式
print("\n" + "=" * 50)
print("Test 3: Current query format")
print("=" * 50)

current_query = """【重要】本日は2025年12月29日です。必ず過去7日以内の最新情報のみを調査してください。

【調査トピック】心理学・メンタルヘルス

【調査要件】
1. 期間制限: 7日以内の情報のみ
2. 言語: 日本語優先
"""

try:
    interaction = client.interactions.create(
        input=current_query,
        agent='deep-research-pro-preview-12-2025',
        background=True
    )
    print(f"SUCCESS: Research started: {interaction.id}")

except Exception as e:
    print(f"FAILED: {e}")

print("\n" + "=" * 50)
print("Tests completed")
print("=" * 50)
