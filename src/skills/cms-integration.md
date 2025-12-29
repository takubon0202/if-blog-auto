# CMS Integration Skill

## 概要
WordPress/Notion APIを使用したコンテンツ公開スキル

## WordPress REST API

### 認証設定
```python
import base64

credentials = f"{username}:{app_password}"
token = base64.b64encode(credentials.encode()).decode()
headers = {
    "Authorization": f"Basic {token}",
    "Content-Type": "application/json"
}
```

### 記事投稿
```python
import httpx

async def publish_to_wordpress(article: dict) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{wp_url}/wp-json/wp/v2/posts",
            headers=headers,
            json={
                "title": article["title"],
                "content": article["content"],
                "status": "draft",
                "categories": article.get("categories", []),
                "tags": article.get("tags", [])
            }
        )
        return response.json()
```

## Notion API

### ページ作成
```python
from notion_client import Client

notion = Client(auth=os.environ["NOTION_TOKEN"])

notion.pages.create(
    parent={"database_id": database_id},
    properties={
        "Title": {"title": [{"text": {"content": title}}]},
        "Status": {"select": {"name": "Draft"}}
    },
    children=blocks
)
```
