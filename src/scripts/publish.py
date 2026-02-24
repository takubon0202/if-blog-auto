#!/usr/bin/env python3
"""
GitHub Pages (Jekyll) 公開スクリプト

ブログ記事をGitHub Pagesに投稿します。
動画の生成・埋め込みは行いません。
"""
import os
import re
import asyncio
import subprocess
import shutil
import logging
import sys
from pathlib import Path
from typing import Optional, Dict, List
import unicodedata

# タイムゾーンユーティリティをインポート
sys.path.insert(0, str(Path(__file__).parent.parent))
from lib.timezone import now_jst, format_datetime_jst, format_date, get_timestamp_jst

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def sanitize_video_content(content: str) -> str:
    """Remove video sections, tags, and references from markdown content.

    Strips the following patterns so that even if upstream LLM text includes
    video-related blocks they never reach the published post:

    - ``## 動画で見る`` heading (and everything until the next ``##`` or EOF)
    - ``<video>...</video>`` HTML elements (any attributes)
    - ``<source ... /assets/videos/ ...>`` lines
    - ``<div class="video-container">...</div>`` wrappers
    - ``<p class="video-caption">...</p>`` captions
    - Liquid ``{{ ... /assets/videos/ ... }}`` references
    - Standalone lines containing only "ショート動画" (with optional markup)
    - Front-matter ``tags:`` entries referencing video keywords
    """
    # 1. Remove '## 動画で見る' heading and everything until the next '## ' or EOF
    content = re.sub(
        r'\n*##\s*動画で見る[^\n]*\n.*?(?=\n## |\Z)',
        '',
        content,
        flags=re.DOTALL,
    )
    # 2. Remove <div class="video-container...">...</div> blocks
    content = re.sub(
        r'<div\s+class="video-container[^"]*">.*?</div>',
        '',
        content,
        flags=re.DOTALL,
    )
    # 3. Remove <video ...>...</video> tags (any attributes, multiline)
    content = re.sub(
        r'<video[^>]*>.*?</video>',
        '',
        content,
        flags=re.DOTALL,
    )
    # 4. Remove standalone <video ... /> self-closing tags
    content = re.sub(
        r'<video[^>]*/\s*>',
        '',
        content,
    )
    # 5. Remove <source> tags referencing /assets/videos/
    content = re.sub(
        r'<source\s+[^>]*/assets/videos/[^>]*/?>\s*',
        '',
        content,
    )
    # 6. Remove <source> tags with video MIME types
    content = re.sub(
        r'<source\s+[^>]*type="video/[^"]*"[^>]*/?>',
        '',
        content,
    )
    # 7. Remove Liquid/Jekyll references to assets/videos/
    content = re.sub(
        r"\{\{.*?/assets/videos/.*?\}\}",
        '',
        content,
        flags=re.DOTALL,
    )
    # 8. Remove <p class="video-caption">...</p> captions
    content = re.sub(
        r'<p\s+class="video-caption">[^<]*</p>',
        '',
        content,
    )
    # 9. Remove standalone lines that are just "ショート動画" (with optional tags)
    content = re.sub(
        r'^[*_]*ショート動画[*_]*\s*$',
        '',
        content,
        flags=re.MULTILINE,
    )
    # 10. Strip video-related keywords from front-matter tags line
    content = re.sub(
        r'(tags:\s*\[)([^\]]*)\]',
        lambda m: m.group(1) + ', '.join(
            t.strip() for t in m.group(2).split(',')
            if t.strip() and 'ショート動画' not in t and '動画' not in t.split('/')[-1:]
        ) + ']',
        content,
    )
    # Collapse runs of 3+ blank lines into 2
    content = re.sub(r'\n{3,}', '\n\n', content)
    return content


def strip_video_from_file(filepath: str) -> bool:
    """Read a markdown file, strip video content, write back if changed.

    Returns True if the file was modified, False otherwise.
    """
    path = Path(filepath)
    if not path.exists():
        logger.warning(f"File not found: {filepath}")
        return False
    original = path.read_text(encoding='utf-8')
    cleaned = sanitize_video_content(original)
    if cleaned != original:
        path.write_text(cleaned, encoding='utf-8')
        logger.info(f"Cleaned video content from: {filepath}")
        return True
    return False


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
        """Jekyll用Front Matterを生成（日本時間）"""
        date_str = format_datetime_jst()  # JST timezone-aware

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
        """画像をdocs/assets/imagesにコピー（検証付き）"""
        images = article.get("images", {})
        hero = images.get("hero", {})
        hero_images = hero.get("images", [])

        if not hero_images:
            logger.info("No hero images available")
            return None

        # 最初の画像をコピー
        first_image = hero_images[0]
        src_path = Path(first_image.get("file_path", ""))

        if not src_path.exists():
            logger.warning(f"Image not found: {src_path}")
            return None

        # 画像サイズを検証（最低10KB以上で正常な画像と判断）
        MIN_IMAGE_SIZE = 10 * 1024  # 10KB
        file_size = src_path.stat().st_size
        if file_size < MIN_IMAGE_SIZE:
            logger.warning(f"Image too small ({file_size} bytes), likely corrupted: {src_path}")
            return None

        # PNGヘッダーの検証
        with open(src_path, 'rb') as f:
            header = f.read(8)
            png_signature = b'\x89PNG\r\n\x1a\n'
            if header != png_signature:
                logger.warning(f"Invalid PNG file (wrong header): {src_path}")
                return None

        # コピー先
        filename = f"{slug}_{src_path.name}"
        dest_path = self.images_dir / filename

        shutil.copy(src_path, dest_path)
        logger.info(f"Copied valid image ({file_size} bytes): {dest_path}")

        # Jekyll用の相対パス（relative_urlフィルタで変換されるためbaseurl不要）
        return f"/assets/images/{filename}"

    def create_post_file(
        self,
        title: str,
        content: str,
        description: str,
        categories: List[str],
        tags: Optional[List[str]] = None,
        featured_image: Optional[str] = None,
    ) -> Path:
        """記事ファイルを作成（日本時間）"""
        slug = self.slugify(title)
        filename = f"{format_date()}-{slug}.md"  # JST date
        filepath = self.posts_dir / filename

        # Front Matter生成
        front_matter = self.generate_front_matter(
            title=title,
            description=description,
            categories=categories,
            tags=tags,
            featured_image=featured_image
        )

        # 動画セクション除去（LLMが生成してしまった場合の安全策）
        content = sanitize_video_content(content)

        # ファイル書き込み
        full_content = front_matter + content
        filepath.write_text(full_content, encoding='utf-8')
        logger.info(f"Created post: {filepath}")

        return filepath

    def is_ci_environment(self) -> bool:
        """CI環境かどうかを判定"""
        # GitHub Actions, GitLab CI, CircleCI など
        ci_vars = ['GITHUB_ACTIONS', 'CI', 'GITLAB_CI', 'CIRCLECI', 'JENKINS_URL']
        return any(os.environ.get(var) for var in ci_vars)

    def git_commit_and_push(self, message: str) -> bool:
        """Git操作（add, commit, push）"""
        # CI環境ではワークフローがgit操作を行うためスキップ
        if self.is_ci_environment():
            logger.info("CI environment detected - skipping git operations (handled by workflow)")
            return True

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
        """公開URLを生成（日本時間）"""
        slug = self.slugify(title)
        date_path = format_date(fmt="%Y/%m/%d")  # JST date
        return f"{self.base_url}/{date_path}/{slug}/"


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
            featured_image=featured_image,
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
    import glob as globmod

    # --- sanitize_video_content sanity tests ---
    def _run_tests():
        passed = 0
        failed = 0

        def check(name, inp, must_not_contain, must_contain=None):
            nonlocal passed, failed
            out = sanitize_video_content(inp)
            ok = True
            for bad in must_not_contain:
                if bad in out:
                    print(f"  FAIL [{name}]: '{bad}' still present")
                    ok = False
            if must_contain:
                for good in must_contain:
                    if good not in out:
                        print(f"  FAIL [{name}]: '{good}' missing")
                        ok = False
            if ok:
                passed += 1
            else:
                failed += 1
                print(f"  OUTPUT: {out!r}")

        # Test 1: ## 動画で見る section removed
        check(
            "heading_section",
            "## 前のセクション\n本文\n\n## 動画で見る\n<video src='x'></video>\nキャプション\n\n## 次のセクション\n続き",
            ["## 動画で見る", "<video"],
            ["## 前のセクション", "## 次のセクション"],
        )

        # Test 2: <video> tags removed
        check(
            "video_tag",
            'テスト\n<video controls width="100%"><source src="/assets/videos/a.mp4" type="video/mp4"></video>\n続き',
            ["<video", "</video>", "/assets/videos/"],
            ["テスト", "続き"],
        )

        # Test 3: <source> referencing /assets/videos/
        check(
            "source_assets_videos",
            '<source src="/assets/videos/demo.webm" type="video/webm">',
            ["/assets/videos/"],
        )

        # Test 4: video-container div
        check(
            "video_container",
            '<div class="video-container">\n<video src="x"></video>\n</div>\n本文',
            ["video-container", "<video"],
            ["本文"],
        )

        # Test 5: video-caption paragraph
        check(
            "video_caption",
            '<p class="video-caption">ショート動画で概要を確認</p>\nテキスト',
            ["video-caption"],
            ["テキスト"],
        )

        # Test 6: ショート動画 standalone line
        check(
            "short_video_line",
            "概要\n\nショート動画\n\n続き",
            ["\nショート動画\n"],
            ["概要", "続き"],
        )

        # Test 7: Liquid template
        check(
            "liquid_ref",
            '{{ "/assets/videos/post.mp4" | relative_url }}',
            ["/assets/videos/"],
        )

        # Test 8: front-matter tags cleaning
        check(
            "tags_cleanup",
            'tags: [AI, ショート動画, 教育]\n本文',
            ["ショート動画"],
            ["AI", "教育", "本文"],
        )

        # Test 9: innocuous content preserved
        innocent = "# タイトル\n\n本文です。動画や音声を含むマルチモーダルな回答を生成します。\n\n## まとめ\n完了"
        out = sanitize_video_content(innocent)
        if out.strip() == innocent.strip():
            passed += 1
        else:
            failed += 1
            print(f"  FAIL [innocent]: content was altered")

        print(f"\nsanitize_video_content tests: {passed} passed, {failed} failed")
        return failed == 0

    # --- Main logic ---
    if len(sys.argv) > 1 and sys.argv[1] == "--clean-posts":
        # Bulk clean mode: strip video blocks from all docs/_posts/*.md
        posts_dir = Path(__file__).parent.parent.parent / "docs" / "_posts"
        md_files = sorted(posts_dir.glob("*.md"))
        modified = 0
        for f in md_files:
            if strip_video_from_file(str(f)):
                modified += 1
        print(f"Cleaned {modified}/{len(md_files)} post files")
    elif len(sys.argv) > 1 and sys.argv[1] == "--test":
        success = _run_tests()
        sys.exit(0 if success else 1)
    else:
        # Default: run tests then publish test article
        _run_tests()
        test_article = {
            "title": "テスト投稿",
            "content": "# テスト\n\nこれはテスト投稿です。\n\n## セクション1\n\n本文...",
            "description": "テスト投稿の説明文です。",
            "categories": ["テスト"],
            "tags": ["テスト", "GitHub Pages"]
        }
        result = asyncio.run(publish_to_github_pages(test_article))
        print(json.dumps(result, ensure_ascii=False, indent=2))
