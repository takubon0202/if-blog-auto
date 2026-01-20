---
name: blog-automation
description: if-blog-auto ブログ自動生成システム支援スキル
---

# Blog Automation スキル

このスキルはif-blog-autoプロジェクトのブログ自動生成を支援します。

## 機能

1. **記事生成支援**: Gemini 3 Proを使用した高品質記事生成
2. **動画生成支援**: Remotion SlideVideoV3の設定・デバッグ
3. **画像生成支援**: Gemini 2.5 Flash imageのプロンプト最適化
4. **SEO最適化**: メタデータ生成とキーワード分析

## 使用例

```bash
# 記事生成プロンプトの改善
gemini "investment トピックの記事生成プロンプトを最適化して"

# 動画生成のデバッグ
gemini "SlideVideoV3でスライド画像が表示されない原因を調査"

# 画像生成プロンプト
gemini "教育トピック用のアイキャッチ画像プロンプトを生成"

# SEO分析
gemini "このブログ記事のSEOスコアを改善するための提案をして"
```

## チェックポイント

### 記事生成
- [ ] 20,000文字以上
- [ ] 12セクション以上
- [ ] 情報ソース10個以上
- [ ] 絵文字なし
- [ ] 紫色系デザインなし

### 動画生成
- [ ] SlideVideoV3コンポジション使用
- [ ] 引数順序: compositionId, outputPath, propsPath
- [ ] slideImages配列にBase64画像
- [ ] startFrame/endFrame設定

### 画像生成
- [ ] 16:9アスペクト比
- [ ] response_modalities=["IMAGE"]設定
- [ ] トピック別カラースキーム適用

## トピック別設定

| トピック | 曜日 | カラー |
|---------|------|--------|
| psychology | 月曜 | #2b6cb0 (Blue) |
| education | 火曜 | #2f855a (Green) |
| startup | 水曜 | #c05621 (Orange) |
| investment | 木曜 | #744210 (Gold) |
| ai_tools | 金曜 | #1a365d (Navy) |
| inclusive_education | 土曜 | #285e61 (Teal) |
| weekly_summary | 日曜 | Deep Research使用 |
