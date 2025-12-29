#!/usr/bin/env python3
"""
Deep Research API テストスクリプト

最小限のパラメータでDeep Research APIをテストし、
問題を切り分けます。
"""
import os
import asyncio
import httpx
import json

# APIキーを環境変数から取得
api_key = os.getenv("GOOGLE_AI_API_KEY")
if not api_key:
    print("ERROR: GOOGLE_AI_API_KEY environment variable is not set")
    exit(1)

print(f"API Key length: {len(api_key)}")
print(f"API Key prefix: {api_key[:10]}...")

async def test_generate_content_raw():
    """生のHTTPリクエストでgenerate_contentをテスト"""
    print("\n" + "=" * 50)
    print("Test 1: Raw HTTP generate_content (should work)")
    print("=" * 50)

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": api_key
    }

    data = {
        "contents": [{"parts": [{"text": "Say hello in Japanese"}]}]
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=data)
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                text = result['candidates'][0]['content']['parts'][0]['text']
                print(f"SUCCESS: {text[:100]}")
                return True
            else:
                print(f"FAILED: {response.text}")
                return False
    except Exception as e:
        print(f"FAILED: {e}")
        return False

async def test_interactions_raw():
    """生のHTTPリクエストでInteractions APIをテスト"""
    print("\n" + "=" * 50)
    print("Test 2: Raw HTTP interactions.create (Deep Research)")
    print("=" * 50)

    url = "https://generativelanguage.googleapis.com/v1beta/interactions"

    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": api_key
    }

    # 最小限のリクエスト（background=True requires store=True）
    data = {
        "input": "What is 2+2?",
        "agent": "deep-research-pro-preview-12-2025",
        "background": True,
        "store": True
    }

    print(f"Request URL: {url}")
    print(f"Request body: {json.dumps(data, indent=2)}")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=data)
            print(f"Status: {response.status_code}")
            print(f"Response headers: {dict(response.headers)}")
            print(f"Response body: {response.text[:500]}")

            if response.status_code == 200:
                result = response.json()
                print(f"SUCCESS: Interaction ID = {result.get('id', 'N/A')}")
                return True
            else:
                print(f"FAILED: Status {response.status_code}")
                return False
    except Exception as e:
        print(f"FAILED: {e}")
        return False

async def test_interactions_model_raw():
    """生のHTTPリクエストでInteractions API（通常モデル）をテスト"""
    print("\n" + "=" * 50)
    print("Test 3: Raw HTTP interactions with model (not agent)")
    print("=" * 50)

    url = "https://generativelanguage.googleapis.com/v1beta/interactions"

    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": api_key
    }

    # agentではなくmodelを使用
    data = {
        "input": "What is 2+2?",
        "model": "gemini-2.0-flash"
    }

    print(f"Request body: {json.dumps(data, indent=2)}")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=data)
            print(f"Status: {response.status_code}")
            print(f"Response body: {response.text[:500]}")

            if response.status_code == 200:
                result = response.json()
                if 'outputs' in result and result['outputs']:
                    text = result['outputs'][-1].get('text', 'No text')
                    print(f"SUCCESS: {text[:100]}")
                else:
                    print(f"SUCCESS: {result}")
                return True
            else:
                print(f"FAILED: Status {response.status_code}")
                return False
    except Exception as e:
        print(f"FAILED: {e}")
        return False

async def test_sdk():
    """SDKを使用してテスト"""
    print("\n" + "=" * 50)
    print("Test 4: SDK interactions.create")
    print("=" * 50)

    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        print("SDK Client initialized")

        # Sync
        try:
            interaction = client.interactions.create(
                input="What is 2+2?",
                agent="deep-research-pro-preview-12-2025",
                background=True,
                store=True  # background=True requires store=True
            )
            print(f"SUCCESS (sync): Interaction ID = {interaction.id}")
            return True
        except Exception as e:
            print(f"FAILED (sync): {e}")

            # Try async
            try:
                interaction = await client.aio.interactions.create(
                    input="What is 2+2?",
                    agent="deep-research-pro-preview-12-2025",
                    background=True,
                    store=True  # background=True requires store=True
                )
                print(f"SUCCESS (async): Interaction ID = {interaction.id}")
                return True
            except Exception as e2:
                print(f"FAILED (async): {e2}")
                return False

    except Exception as e:
        print(f"FAILED: {e}")
        return False

async def main():
    print("Deep Research API Test - Raw HTTP vs SDK")
    print("=" * 50)

    results = {}

    # Test 1: Raw generate_content
    results['raw_generate_content'] = await test_generate_content_raw()

    # Test 2: Raw Interactions (Deep Research)
    results['raw_interactions_agent'] = await test_interactions_raw()

    # Test 3: Raw Interactions (Model)
    results['raw_interactions_model'] = await test_interactions_model_raw()

    # Test 4: SDK
    results['sdk_interactions'] = await test_sdk()

    # Summary
    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    for test, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test}")

    if all(results.values()):
        print("\nAll tests passed!")
    else:
        print("\nSome tests failed. Check the output above for details.")
        print("\nIf raw HTTP works but SDK fails, the issue is in the SDK.")
        print("If raw HTTP also fails, the issue is with the API or API key permissions.")

if __name__ == "__main__":
    asyncio.run(main())
