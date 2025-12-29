# Image Agent

## 役割
ブログ記事に適した画像をGemini 2.5 Flash imageモデルで生成する

## 使用API
- **Primary**: Gemini 2.5 Flash image (`gemini-2.5-flash-image`)

## 処理フロー
```
1. 記事情報を受け取る
2. 画像生成用プロンプトを最適化
3. Gemini 2.5 Flash imageで画像生成
4. 画像データをBase64から変換して保存
5. 生成結果を返却
```

## 入力
```json
{
  "article_title": "記事タイトル",
  "article_summary": "記事概要",
  "image_prompts": {
    "hero": "ヒーロー画像プロンプト",
    "sections": ["セクション画像プロンプト1"]
  },
  "style_guide": {
    "color_scheme": "blue_gradient",
    "style": "modern_minimalist"
  }
}
```

## 出力
```json
{
  "status": "success",
  "hero": {
    "type": "hero",
    "title": "記事タイトル",
    "prompt": "生成に使用したプロンプト",
    "model": "gemini-2.5-flash-image",
    "images": [
      {
        "file_path": "/output/images/hero_20251229_123456_0.png",
        "filename": "hero_20251229_123456_0.png",
        "size_bytes": 123456
      }
    ],
    "generated_at": "20251229_123456"
  },
  "sections": [],
  "total_images": 1
}
```

## 画像仕様
| 用途 | サイズ | アスペクト比 | 形式 |
|------|--------|--------------|------|
| ヒーロー画像 | 1200x630 | 1.91:1 | PNG |
| OGP画像 | 1200x630 | 1.91:1 | PNG |
| 本文画像 | 800x450 | 16:9 | PNG/WebP |

## API呼び出しパターン
```python
from lib.gemini_client import GeminiClient

client = GeminiClient()

# ブログ用画像生成
result = await client.generate_blog_image(
    title="AIツールの最新動向2025",
    summary="2025年のAIツールトレンドを詳しく解説",
    style="modern, minimalist, professional",
    image_type="hero"
)

# 汎用画像生成
result = await client.generate_image(
    prompt="A modern tech workspace with futuristic elements",
    model="gemini-2.5-flash-image"
)
```

## プロンプト最適化ルール
```
1. 英語で記述する
2. 具体的で明確な描写
3. スタイル指定を含める
4. 避けるべき要素を明記:
   - 人物の顔（著作権/プライバシー）
   - テキスト（読めない可能性）
   - 著作物・ブランドロゴ
5. ブログに適した構図を指定
```

## エラーハンドリング
- API エラー時はログに記録
- 画像生成失敗時は status: "error" を返却
- リトライロジックは上位レイヤーで実装
