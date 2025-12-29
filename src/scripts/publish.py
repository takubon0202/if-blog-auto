#!/usr/bin/env python3
"""
GitHub Pages (Jekyll) 公開スクリプト

ブログ記事をGitHub Pagesに投稿します。
"""
import os
import re
import asyncio
import subprocess
import shutil
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List
import unicodedata

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GitHubPagesPublisher:
    """GitHub Pages投稿クラス"""

    def __init__(self):
        self.repo_root = Path(__file__).parent.parent.parent
        self.docs_dir = self.repo_root / "docs"
        self.posts_dir = self.docs_dir / "_posts"
        self.images_dir = self.docs_dir / "assets" / "images"
        self.base_url = "https://takubon0202.github.io/if-blog-auto"

        # ディレクトリ作成
        self.posts_dir.mkdir(parents=True, exist_ok=True)
        self.images_dir.mkdir(parents=True, exist_ok=True)

    def slugify(self, text: str) -> str:
        """URLスラッグを生成"""
        # 正規化
        text = unicodedata.normalize('NFKC', text)
        # 英数字とハイフン以外を削除
        text = re.sub(r'[^\w\s-]', '', text.lower())
        # スペースをハイフンに
        text = re.sub(r'[-\s]+', '-', text).strip('-')
        # 50文字に制限
        return text[:50] or 'untitled'

    def generate_front_matter(
        self,
        title: str,
        description: str,
        categories: List[str],
        tags: Optional[List[str]] = None,
        featured_image: Optional[str] = None,
        author: str = "AI Blog Generator"
    ) -> str:
        """Jekyll用Front Matterを生成"""
        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d %H:%M:%S +0900")

        lines = [
            "---",
            "layout: post",
            f'title: "{title}"',
            f'description: "{description}"',
            f"date: {date_str}",
            f"categories: [{', '.join(categories)}]",
        ]

        if tags:
            lines.append(f"tags: [{', '.join(tags)}]")

        lines.append(f'author: "{author}"')

        if featured_image:
            lines.append(f'featured_image: "{featured_image}"')

        lines.append("---")
        lines.append("")

        return "\n".join(lines)

    def copy_images(self, article: Dict, slug: str) -> Optional[str]:
        """画像をdocs/assets/imagesにコピー"""
        images = article.get("images", {})
        hero = images.get("hero", {})
        hero_images = hero.get("images", [])

        if not hero_images:
            return None

        # 最初の画像をコピー
        first_image = hero_images[0]
        src_path = Path(first_image.get("file_path", ""))

        if not src_path.exists():
            logger.warning(f"Image not found: {src_path}")
            return None

        # コピー先
        filename = f"{slug}_{src_path.name}"
        dest_path = self.images_dir / filename

        shutil.copy(src_path, dest_path)
        logger.info(f"Copied image: {dest_path}")

        # Jekyll用の相対パス
        return f"/if-blog-auto/assets/images/{filename}"

    def create_post_file(
        self,
        title: str,
        content: str,
        description: str,
        categories: List[str],
        tags: Optional[List[str]] = None,
        featured_image: Optional[str] = None
    ) -> Path:
        """記事ファイルを作成"""
        now = datetime.now()
        slug = self.slugify(title)
        filename = f"{now.strftime('%Y-%m-%d')}-{slug}.md"
        filepath = self.posts_dir / filename

        # Front Matter生成
        front_matter = self.generate_front_matter(
            title=title,
            description=description,
            categories=categories,
            tags=tags,
            featured_image=featured_image
        )

        # ファイル書き込み
        full_content = front_matter + content
        filepath.write_text(full_content, encoding='utf-8')
        logger.info(f"Created post: {filepath}")

        return filepath

    def git_commit_and_push(self, message: str) -> bool:
        """Git操作（add, commit, push）"""
        try:
            # Git add
            subprocess.run(
                ["git", "add", "docs/"],
                cwd=self.repo_root,
                check=True,
                capture_output=True
            )

            # Git commit
            subprocess.run(
                ["git", "commit", "-m", message],
                cwd=self.repo_root,
                check=True,
                capture_output=True
            )

            # Git push
            subprocess.run(
                ["git", "push", "origin", "main"],
                cwd=self.repo_root,
                check=True,
                capture_output=True
            )

            logger.info("Successfully pushed to GitHub")
            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"Git operation failed: {e}")
            logger.error(f"Stderr: {e.stderr.decode() if e.stderr else 'N/A'}")
            return False

    def get_public_url(self, title: str) -> str:
        """公開URLを生成"""
        now = datetime.now()
        slug = self.slugify(title)
        return f"{self.base_url}/{now.strftime('%Y/%m/%d')}/{slug}/"


async def publish_to_github_pages(article: Dict) -> Dict:
    """
    記事をGitHub Pagesに投稿

    Args:
        article: 記事データ
            - title: タイトル
            - content: 本文（Markdown）
            - description: 概要
            - categories: カテゴリリスト
            - tags: タグリスト（オプション）
            - images: 画像データ（オプション）

    Returns:
        投稿結果
    """
    publisher = GitHubPagesPublisher()

    title = article.get("title", "Untitled")
    content = article.get("content", "")
    description = article.get("description", "")[:120]  # 120文字制限
    categories = article.get("categories", ["未分類"])
    tags = article.get("tags", [])

    # タイトルが長すぎる場合は切り詰め
    if len(title) > 60:
        title = title[:57] + "..."

    try:
        # 画像コピー
        slug = publisher.slugify(title)
        featured_image = publisher.copy_images(article, slug)

        # 記事ファイル作成
        post_path = publisher.create_post_file(
            title=title,
            content=content,
            description=description,
            categories=categories,
            tags=tags,
            featured_image=featured_image
        )

        # Git操作
        commit_message = f"Add blog post: {title}"
        git_success = publisher.git_commit_and_push(commit_message)

        if not git_success:
            return {
                "status": "error",
                "message": "Git push failed",
                "post_path": str(post_path)
            }

        # 公開URL
        public_url = publisher.get_public_url(title)

        return {
            "status": "success",
            "post_path": str(post_path),
            "public_url": public_url,
            "message": f"Successfully published: {title}"
        }

    except Exception as e:
        logger.error(f"Publish failed: {e}")
        return {
            "status": "error",
            "message": str(e)
        }


# 後方互換性のためWordPress関数を残す（無効化）
async def publish_to_wordpress(article: dict) -> dict:
    """WordPress投稿（非推奨）"""
    logger.warning("WordPress publishing is disabled. Use GitHub Pages instead.")
    return await publish_to_github_pages(article)


if __name__ == "__main__":
    import json

    # テスト用記事
    test_article = {
        "title": "テスト投稿",
        "content": "# テスト\n\nこれはテスト投稿です。\n\n## セクション1\n\n本文...",
        "description": "テスト投稿の説明文です。",
        "categories": ["テスト"],
        "tags": ["テスト", "GitHub Pages"]
    }

    result = asyncio.run(publish_to_github_pages(test_article))
    print(json.dumps(result, ensure_ascii=False, indent=2))
