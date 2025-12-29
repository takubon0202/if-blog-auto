#!/usr/bin/env python3
"""公開スクリプト"""
import os
import asyncio
import base64
import httpx
from pathlib import Path

async def publish_to_wordpress(article: dict) -> dict:
    """WordPressに記事を公開"""
    wp_url = os.getenv("WORDPRESS_URL")
    wp_user = os.getenv("WORDPRESS_USER")
    wp_password = os.getenv("WORDPRESS_APP_PASSWORD")

    if not all([wp_url, wp_user, wp_password]):
        return {"status": "error", "message": "WordPress credentials not configured"}

    credentials = f"{wp_user}:{wp_password}"
    token = base64.b64encode(credentials.encode()).decode()

    headers = {
        "Authorization": f"Basic {token}",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{wp_url}/wp-json/wp/v2/posts",
            headers=headers,
            json={
                "title": article.get("title", "Untitled"),
                "content": article.get("content", ""),
                "status": "draft"
            }
        )

        if response.status_code == 201:
            return {"status": "success", "post_id": response.json().get("id")}
        else:
            return {"status": "error", "message": response.text}

if __name__ == "__main__":
    import json
    result = asyncio.run(publish_to_wordpress({"title": "Test", "content": "Test content"}))
    print(json.dumps(result, ensure_ascii=False, indent=2))
