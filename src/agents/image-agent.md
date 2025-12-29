# Image Agent

## 役割
ブログ記事に適した画像をGemini 2.5 Flash imageモデルで生成する

## 使用API
- **Primary**: Gemini 2.5 Flash image (`gemini-2.5-flash-image`)

## 重要な設定（必須遵守）

### response_modalities の指定
画像を生成するには、必ず `response_modalities=["IMAGE"]` を設定する必要があります。
この設定がないと、テキストのみが返され画像が生成されません。

```python
from google.genai import types

config = types.GenerateContentConfig(
    response_modalities=["IMAGE"],  # 必須
    temperature=1.0,
    top_p=0.95,
    top_k=40
)
```

### 画像検証ルール
- 最低サイズ: 10KB以上（10KB未満は破損と判断）
- PNGヘッダー検証: `\x89PNG\r\n\x1a\n`

## 処理フロー
```
1. 記事情報を受け取る
2. デザインガイドラインに基づきプロンプトを最適化
3. response_modalities=["IMAGE"] を設定
4. Gemini 2.5 Flash imageで画像生成
5. 画像データを検証（サイズ・ヘッダー）
6. 有効な画像のみを保存
7. 生成結果を返却
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
    "color_scheme": "professional_blue",
    "style": "clean_minimal"
  }
}
```

## デザインガイドライン（必須遵守）

### 禁止カラー
- **紫色系の禁止**: purple, violet, lavender, magenta は使用しない
- **派手な色の禁止**: ネオンカラー、蛍光色は避ける

### 推奨カラー
```
Primary: Deep Navy (#1a1a2e) - 信頼性・知性
Accent: Professional Blue (#0f3460) - 落ち着き
Background: White/Light Gray (#f7fafc) - クリーンさ
Text: Dark Gray (#2d3748) - 読みやすさ
```

### カテゴリ別推奨カラー
- 心理学: Blue (#2b6cb0)
- 教育: Green (#2f855a)
- 起業: Orange (#c05621)
- 投資: Brown (#744210)
- AI: Navy (#1a365d)
- 不登校: Teal (#285e61)
- 発達障害: Indigo (#2c5282)

### 画像スタイル
- **クリーンでミニマル**: 余計な装飾を避ける
- **プロフェッショナル**: ビジネスに適した雰囲気
- **抽象的・概念的**: 具体的な人物は避ける
- **明るく読みやすい**: テキストが映える背景

### 避けるべき要素
1. 派手なグラデーション背景
2. 紫系の配色
3. 過度な装飾やアイコン
4. 人物の顔（著作権/プライバシー）
5. テキストを含む画像
6. 著作物・ブランドロゴ

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

## プロンプトテンプレート

### ヒーロー画像
```
A clean, professional illustration for a blog article about [TOPIC].
Style: minimal, modern, professional
Colors: deep navy blue (#1a1a2e), light gray background (#f7fafc), accent blue (#0f3460)
Mood: trustworthy, intelligent, calm
Composition: centered subject, clean background, suitable for text overlay
Avoid: purple colors, neon colors, text, human faces, cluttered design
```

### セクション画像
```
A simple, abstract illustration representing [CONCEPT].
Style: flat design, minimal, clean lines
Colors: [CATEGORY_COLOR], white background
Mood: educational, approachable
Avoid: purple colors, complex patterns, text, faces
```

## API呼び出しパターン
```python
from lib.gemini_client import GeminiClient

client = GeminiClient()

# ブログ用画像生成
result = await client.generate_blog_image(
    title="AIツールの最新動向2025",
    summary="2025年のAIツールトレンドを詳しく解説",
    style="clean, minimal, professional, navy blue accent",
    image_type="hero"
)
```

## 品質チェックリスト
- [ ] 紫色系が含まれていないか
- [ ] 派手すぎないか
- [ ] プロフェッショナルな雰囲気か
- [ ] テキストが映える背景か
- [ ] 記事内容と関連しているか
