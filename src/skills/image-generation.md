# Image Generation Skill

## 概要
Imagen 3を使用した画像生成スキル

## API設定
```python
from google.genai import types

response = client.models.generate_images(
    model="imagen-3.0-generate-002",
    prompt=optimized_prompt,
    config=types.GenerateImagesConfig(
        number_of_images=1,
        aspect_ratio="16:9",
        safety_filter_level="BLOCK_MEDIUM_AND_ABOVE",
        person_generation="DONT_ALLOW"
    )
)
```

## プロンプト最適化
```
最適化の条件:
1. 明確で具体的な描写
2. スタイル指定を含める
3. 避けるべき要素を明記（人物の顔、テキスト、著作物）
4. 英語で出力
```

## 画像仕様
| 用途 | サイズ | アスペクト比 |
|------|--------|--------------|
| ヒーロー画像 | 1200x630 | 1.91:1 |
| 本文画像 | 800x450 | 16:9 |
| サムネイル | 400x225 | 16:9 |
