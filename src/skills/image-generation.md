# Image Generation Skill

## 概要
Gemini 2.5 Flash imageを使用した画像生成スキル。
**スマートプロンプト機能**により、記事タイトルを分析して内容に合った具体的で多様な画像を生成します。

## 使用モデル
- **画像生成**: `gemini-2.5-flash-image`
- **記事分析**: `gemini-2.0-flash`（スマートプロンプト用）
- **API**: Google Generative AI (genai)

## 重要な設定（必須）

### response_modalities の指定
画像を生成するには、必ず `response_modalities=["IMAGE"]` を設定する必要があります。
この設定がないと、テキストのみが返され画像が生成されません。

## API設定
```python
from google import genai
from google.genai import types
import base64

client = genai.Client(api_key=api_key)

# 画像生成（response_modalities が必須）
config = types.GenerateContentConfig(
    response_modalities=["IMAGE"],  # 必須：画像出力を有効化
    temperature=1.0,
    top_p=0.95,
    top_k=40
)

response = client.models.generate_content(
    model="gemini-2.5-flash-image",
    contents=prompt,
    config=config
)

# レスポンス処理
for part in response.candidates[0].content.parts:
    if hasattr(part, 'text') and part.text:
        # テキストレスポンス
        print(part.text)
    elif hasattr(part, 'inline_data') and part.inline_data:
        # 画像データ（bytesまたはBase64）
        data = part.inline_data.data
        if isinstance(data, str):
            image_data = base64.b64decode(data)
        else:
            image_data = data

        # 画像サイズを検証（最低1KB以上）
        if len(image_data) > 1024:
            with open("output.png", "wb") as f:
                f.write(image_data)
            print(f"Image saved: {len(image_data)} bytes")
        else:
            print(f"Warning: Image too small ({len(image_data)} bytes)")
```

## GeminiClientでの使用
```python
from lib.gemini_client import GeminiClient

client = GeminiClient()

# スマートプロンプトでブログ用画像生成（推奨）
result = await client.generate_blog_image(
    title="AIの未来",
    summary="人工知能が変える私たちの生活",
    style="modern, minimalist, professional",
    image_type="hero",
    topic_id="ai_tools",  # トピック別カラースキーム自動適用
    use_smart_prompt=True  # 記事分析を有効化（デフォルト）
)

# シンプルプロンプトで画像生成（従来方式）
result = await client.generate_blog_image(
    title="記事タイトル",
    summary="記事概要",
    use_smart_prompt=False  # 分析をスキップ
)

# 汎用画像生成（カスタムプロンプト）
result = await client.generate_image(
    prompt="A futuristic cityscape with flying cars",
    model="gemini-2.5-flash-image"
)

# 結果
for image_bytes in result.images:
    # 画像バイナリデータを処理
    pass
```

## スマートプロンプト機能

### 記事分析
Gemini 2.0 Flashで記事タイトルを分析し、以下を自動生成：
- **main_subject**: メインの視覚的対象（例: "a glowing neural network"）
- **visual_metaphor**: 視覚的メタファー（例: "interconnected nodes"）
- **mood**: 感情的トーン（例: "hopeful and bright"）
- **key_elements**: 具体的な視覚要素リスト
- **background_style**: 背景スタイル
- **lighting**: ライティングスタイル

### トピック別カラースキーム
```python
TOPIC_COLORS = {
    "psychology": {"primary": "#2b6cb0", "name": "calming blue"},
    "education": {"primary": "#2f855a", "name": "growth green"},
    "startup": {"primary": "#c05621", "name": "energetic orange"},
    "investment": {"primary": "#744210", "name": "trustworthy gold-brown"},
    "ai_tools": {"primary": "#1a365d", "name": "tech navy blue"},
    "inclusive_education": {"primary": "#285e61", "name": "supportive teal"},
    "weekly_summary": {"primary": "#553c9a", "name": "insightful indigo"}
}
```

### 構図バリエーション（ランダム選択）
- centered focal point / dynamic diagonal
- layered depth / radial arrangement
- asymmetric balance / grid-based
- organic flowing / geometric abstract

## プロンプト最適化
```
最適化の条件:
1. 明確で具体的な描写（英語推奨）
2. スタイル指定を含める
3. 避けるべき要素を明記:
   - 人物の顔（著作権/プライバシー問題）
   - テキスト（生成されたテキストは読めない可能性）
   - 著作物・ブランドロゴ
4. 出力形式: 英語
5. ブログに適した構図を指定
6. トピック別カラースキームを適用
```

## プロンプトテンプレート
```
Create a {image_type} image for a blog article.

Article Title: {title}
Article Summary: {summary}

Style Requirements:
- {style}
- Clean and professional design
- Suitable for blog featured image
- No text or watermarks in the image
- High quality, visually appealing
- Abstract or conceptual representation of the topic

Generate a visually stunning image that captures the essence of this article.
```

## 画像仕様
| 用途 | サイズ | アスペクト比 | 推奨スタイル |
|------|--------|--------------|--------------|
| ヒーロー画像 | 1200x630 | 1.91:1 | modern, impactful |
| 本文画像 | 800x450 | 16:9 | clean, illustrative |
| サムネイル | 400x225 | 16:9 | bold, eye-catching |

## 出力形式
```python
@dataclass
class ImageGenerationResult:
    images: List[bytes]      # 画像バイナリデータのリスト
    model: str               # 使用モデル名
    prompt: str              # 使用プロンプト
    text_response: str       # テキストレスポンス（あれば）
```

## エラーハンドリング
```python
try:
    result = await client.generate_image(prompt)
except Exception as e:
    logger.error(f"Image generation failed: {e}")
    # フォールバック処理またはエラー返却
```

## レート制限
- 1分あたり60リクエスト以内を推奨
- 画像生成は負荷が高いため間隔を空ける
