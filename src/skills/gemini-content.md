# Gemini Content Skill

## 概要
Gemini 3 Pro Previewを使用したコンテンツ生成スキル

## モデル設定

### 高品質コンテンツ生成
```python
response = client.models.generate_content(
    model="gemini-3-pro-preview",
    contents=prompt,
    config={
        "temperature": 0.7,
        "max_output_tokens": 8192,
        "top_p": 0.9,
        "top_k": 40
    }
)
```

### 高速ドラフト生成
```python
response = client.models.generate_content(
    model="gemini-2.0-flash",
    contents=prompt,
    config={
        "temperature": 0.5,
        "max_output_tokens": 4096
    }
)
```

## プロンプトテンプレート

### ブログ記事生成
```
あなたはプロのブログライターです。以下の情報を基に、読者にとって価値のあるブログ記事を執筆してください。

【トピック】{topic}
【調査結果】{research_summary}
【ターゲット読者】{target_audience}
【文字数】{word_count}文字程度
【トーン】{tone}

執筆ガイドライン:
- 導入で読者の興味を引く
- 具体的なデータ・事例を含める
- 専門用語は初出時に解説
- 段落は3-4文で区切る
- 結論で読者に行動を促す

出力形式: Markdown
```

## 品質向上テクニック

### Chain of Thought
```
以下のステップで記事を作成してください:

Step 1: 記事の目的と読者価値を定義
Step 2: 主要なポイントを3-5つリストアップ
Step 3: 各ポイントの論拠・データを整理
Step 4: 記事構成（見出し）を決定
Step 5: 各セクションを執筆
Step 6: 導入と結論を最適化

各ステップの思考過程を示してから、最終的な記事を出力してください。
```
