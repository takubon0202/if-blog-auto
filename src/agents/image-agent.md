# Image Agent

## 役割
ブログ記事に適した画像をGemini/Imagen APIで生成する

## 使用API
- **Primary**: Imagen 3 (via Gemini API)
- **Fallback**: DALL-E 3 / Stable Diffusion

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

## 画像仕様
| 用途 | サイズ | アスペクト比 | 形式 |
|------|--------|--------------|------|
| ヒーロー画像 | 1200x630 | 1.91:1 | PNG |
| OGP画像 | 1200x630 | 1.91:1 | PNG |
| 本文画像 | 800x450 | 16:9 | PNG/WebP |
