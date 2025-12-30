# Video Agent

## 役割
**ブログ記事全体を分析**してRemotionを使用して高品質な動画を自動生成する。
記事の全文を読み込み、主要テーマ、統計データ、専門家の見解を抽出し、
**TTS音声ナレーション**と**記事画像**を統合して、動画を見ただけでブログの本質が理解できるようにします。

## 記事全体分析機能（重要）
記事本文（10,000字以上）を完全に分析し、以下を自動抽出：
- **main_theme**: 記事の主要テーマ
- **key_message**: 最も重要なメッセージ
- **statistics**: 記事内の重要な数値データ（最大5つ）
- **expert_quotes**: 専門家の引用・研究結果（最大3つ）
- **narrative_arc**: ストーリーの流れ（導入→問題→解決→結論）
- **video_points**: 動画で強調すべきポイント（最大5つ）

## 使用技術
- **Framework**: Remotion 4.0
- **Runtime**: Node.js 20+
- **TTS**: Gemini 2.5 Flash TTS
- **Output**: MP4 (H.264) with audio

## 品質基準（97%以上合格必須）

### 必須要件
- [ ] 音声ナレーションが含まれている
- [ ] ヒーロー画像が動画内に表示される
- [ ] 記事の主要ポイントが視覚的に伝わる
- [ ] 動画だけで記事内容が理解できる
- [ ] アニメーションがスムーズ
- [ ] テキストが読みやすい
- [ ] カラースキームがトピックに適合

### 品質評価項目（各10点満点、合計70点以上で合格）
1. **音声品質** (10点): ナレーションが自然で聞き取りやすい
2. **視覚的明瞭さ** (10点): 情報が視覚的に整理されている
3. **コンテンツ伝達** (10点): 記事の本質が30秒で伝わる
4. **デザイン一貫性** (10点): トピック別カラースキームの適用
5. **アニメーション** (10点): スムーズで目に優しい動き
6. **画像活用** (10点): ヒーロー画像が効果的に使用されている
7. **技術品質** (10点): 解像度、フレームレート、圧縮品質

## 動画仕様

### 標準動画（30秒版）- メイン
| 項目 | 値 |
|------|------|
| 解像度 | 1920x1080 |
| フレームレート | 30fps |
| 長さ | 30秒（900フレーム） |
| 形式 | MP4 (H.264 + AAC) |
| 用途 | YouTube、ブログ埋め込み |
| 音声 | Gemini TTS ナレーション |

### ショート動画（15秒版）- 将来拡張用
| 項目 | 値 |
|------|------|
| 解像度 | 1080x1920（縦型） |
| フレームレート | 30fps |
| 長さ | 15秒（450フレーム） |
| 形式 | MP4 (H.264 + AAC) |
| 用途 | YouTube Shorts、TikTok、Instagram Reels |
| **状態** | **デフォルトでスキップ** |

## TTS音声生成

### Gemini TTS設定
```python
from lib.gemini_client import GeminiClient

client = GeminiClient()

# ナレーションスクリプト生成 + TTS
narration = await client.generate_video_narration(
    title="記事タイトル",
    summary="記事概要",
    points=["ポイント1", "ポイント2", "ポイント3"],
    duration_seconds=30,
    voice="default"  # Kore（落ち着いた声）
)

# 音声データ取得
audio_data = narration["audio_data"]  # bytes (WAV/MP3)
script = narration["script"]  # ナレーションテキスト
```

### 音声オプション
| 音声ID | 声の特徴 | 推奨用途 |
|--------|---------|---------|
| `default` (Kore) | 落ち着いた声 | 教育、投資、心理学 |
| `bright` (Puck) | 明るい声 | スタートアップ、AIツール |
| `calm` (Charon) | 静かな声 | インクルーシブ教育 |
| `warm` (Aoede) | 温かみのある声 | 週間総括 |

## 画像統合

### ヒーロー画像の使用
動画内で記事のヒーロー画像を効果的に表示：

```typescript
// 画像シーン（3秒間表示）
<Sequence from={180} durationInFrames={90}>
  <HeroImageScene
    imageUrl={props.heroImageUrl}
    title={props.title}
  />
</Sequence>
```

### 視覚的構成
```
0s ─────── 6s ─────── 9s ─────── 21s ─────── 25s ─────── 30s
[タイトル] [画像シーン] [ポイント説明 x3] [まとめ]  [エンディング]
    ↑           ↑            ↑              ↑           ↑
  音声開始    画像表示   各ポイント説明   締めの言葉   CTA
```

## トピック別カラースキーム

画像生成と統一されたカラースキームを使用：

| トピックID | Primary | Accent | 名称 | 推奨音声 |
|-----------|---------|--------|------|---------|
| `psychology` | #2b6cb0 | #4299e1 | 心理学 | default |
| `education` | #2f855a | #48bb78 | 教育 | default |
| `startup` | #c05621 | #ed8936 | スタートアップ | bright |
| `investment` | #744210 | #d69e2e | 投資 | default |
| `ai_tools` | #1a365d | #3182ce | AIツール | bright |
| `inclusive_education` | #285e61 | #38b2ac | インクルーシブ教育 | calm |
| `weekly_summary` | #553c9a | #805ad5 | 週間総括 | warm |

## シーン構成（音声付き30秒版）

```
Scene 1: タイトルシーン（6秒）
- トピックラベル表示（アニメーション付き）
- メインタイトル（フェードイン + スライドアップ）
- 音声: 「今日は〇〇についてお話しします」

Scene 2: 画像シーン（3秒）- NEW
- ヒーロー画像を全画面表示
- オーバーレイでタイトル再表示
- 音声: 「〇〇の最新動向を見ていきましょう」

Scene 3: サマリーシーン（2秒）
- 記事要約をシンプルに表示
- 音声: 要約の読み上げ

Scene 4-6: ポイントシーン（各4秒 × 3ポイント = 12秒）
- 番号アイコン（スケールアニメーション）
- ポイントテキスト（スライドイン）
- 音声: 各ポイントの説明

Scene 7: まとめシーン（2秒）- NEW
- 3つのポイントを小さく再表示
- 音声: 「以上3つのポイントをお伝えしました」

Scene 8: エンディング（5秒）
- ブログ名/著者名
- 日付
- CTA「ブログで詳しく読む」
- 音声: 「詳しくはブログをご覧ください」
```

## 処理フロー
```
1. ブログ記事データを受け取る
   - title: 記事タイトル
   - summary: 記事要約
   - content: 記事全文（10,000字以上）★重要
   - points: 主要ポイント（配列）
   - topic: トピックID
   - date: 日付
   - hero_image_path: ヒーロー画像パス

2. 記事全体分析（NEW - analyze_article_for_video）
   - 記事全文をGemini Flashで分析
   - 主要テーマ、統計データ、専門家見解を抽出
   - ストーリーアーク（導入→問題→解決→結論）を特定
   - 動画用ポイントを自動生成（最大5つ）

3. Gemini TTSでナレーション音声を生成
   - 記事分析結果を活用したスクリプト生成
   - 統計・専門家見解を含む充実したナレーション
   - TTS変換（WAV）

4. Remotionプロジェクトにprops + 音声を渡す
   - 分析から得た拡張ポイントを使用

5. remotion renderコマンドを実行
   - 標準動画のみ（ショートはスキップ）

6. 生成された動画を出力ディレクトリに保存

7. 結果を返却（記事分析結果含む）
```

## 入力
```json
{
  "title": "AIツールの最新動向2025",
  "summary": "2025年のAIツールトレンドを詳しく解説します。",
  "content": "（記事全文 10,000字以上）★重要: 動画生成品質に直結",
  "points": [
    "生成AIの進化と実用化",
    "業務効率化ツールの普及",
    "セキュリティとプライバシーの重要性"
  ],
  "topic": "ai_tools",
  "date": "2025年12月30日",
  "authorName": "if(塾) Blog",
  "heroImagePath": "output/images/hero_20251230_ai_tools.png",
  "generateShort": false
}
```

## 出力
```json
{
  "status": "success",
  "videos": {
    "standard": {
      "path": "output/videos/blog_video_20251230_ai_tools.mp4",
      "duration": 30,
      "resolution": "1920x1080",
      "has_audio": true,
      "audio_voice": "bright"
    }
  },
  "narration": {
    "script": "今日はAIツールの最新動向2025についてお話しします...",
    "audio_size_bytes": 245760,
    "article_analysis": {
      "main_theme": "2025年のAI革命と業務効率化",
      "statistics": ["生成AI市場は前年比150%成長", "企業の78%がAI導入を検討"],
      "video_points": ["生成AIの民主化", "業務自動化の加速", "セキュリティの重要性"]
    }
  },
  "generated_at": "2025-12-30T12:34:56+09:00"
}
```

## デザインガイドライン（必須遵守）

### 禁止事項
- **紫色系の禁止**: 紫、バイオレット、ラベンダー系は使用しない（weekly_summaryのみ例外）
- **派手なエフェクトの禁止**: ネオン、グリッチなど過度なエフェクト
- **テキスト詰め込み禁止**: 1シーンに長文を入れない
- **無音動画の禁止**: 必ずナレーション音声を含める

### 推奨スタイル
- クリーンでミニマルなデザイン
- スムーズなアニメーション（spring, interpolate）
- 読みやすいフォントサイズ
- 適切なコントラスト
- 音声と視覚の同期

## API呼び出しパターン

### Pythonからの呼び出し
```python
from scripts.generate_video import generate_video

result = await generate_video(
    article={
        "title": "記事タイトル",
        "summary": "記事要約",
        "content": article_full_text,  # ★重要: 記事全文（10,000字以上）
        "points": ["ポイント1", "ポイント2", "ポイント3"],
        "topic_id": "ai_tools",
        "date": "2025年12月30日",
        "hero_image_path": "output/images/hero.png"
    },
    output_dir="output/videos",
    generate_short=False,  # ショートはスキップ
    generate_audio=True    # 音声生成を有効化（記事分析を実行）
)

# 記事分析結果を確認
if result.get("narration", {}).get("article_analysis"):
    analysis = result["narration"]["article_analysis"]
    print(f"Main theme: {analysis.get('main_theme')}")
    print(f"Statistics: {analysis.get('statistics')}")
```

## 依存関係

### Python
```
google-genai>=1.56.0  # TTS対応
```

### remotion/package.json
```json
{
  "dependencies": {
    "@remotion/cli": "4.0.0",
    "@remotion/player": "4.0.0",
    "remotion": "4.0.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0"
  }
}
```

### システム要件
- Node.js 20+
- ffmpeg（Remotionに同梱）
- Chrome依存ライブラリ（CI環境）

## エラーハンドリング
```python
try:
    result = await generate_video(article, generate_audio=True)
except VideoGenerationError as e:
    logger.error(f"Video generation failed: {e}")
    # フォールバック: 動画なしで続行
    result = {"status": "skipped", "reason": str(e)}
except AudioGenerationError as e:
    logger.warning(f"Audio generation failed: {e}")
    # フォールバック: 音声なしで動画生成
    result = await generate_video(article, generate_audio=False)
```

## レート制限
- 動画レンダリングは重い処理のため、1記事につき1回のみ
- TTS生成はRPM制限あり（適切な間隔を空ける）
- 並列レンダリングは避ける

## ドキュメント更新義務（必須遵守）

このエージェントで機能追加・修正・エラー対応を行った場合、**必ずREADME.mdを最新仕様に更新すること**。

### 更新すべき内容
1. **最新アップデート**: 変更内容を記載
2. **トラブルシューティング**: 動画生成エラーと解決策を追加
3. **内部動作フロー**: 動画生成処理の説明

### 内部動作フロー図
```
┌────────────────────────────────────┐
│ generate_video(article)            │
│ ※article.contentに記事全文を含む   │
└─────────────────┬──────────────────┘
                  │
        ┌─────────▼─────────────────┐
        │ analyze_article_for_video  │
        │ ・記事全文を分析           │
        │ ・統計/専門家見解を抽出    │
        │ ・video_pointsを生成       │
        └─────────┬─────────────────┘
                  │
        ┌─────────▼─────────────────┐
        │ Gemini TTS: ナレーション   │
        │ ・分析結果を活用           │
        │ ・スクリプト生成 + 音声変換│
        └─────────┬─────────────────┘
                  │
        ┌─────────▼─────────────────┐
        │ enhanced_pointsを使用      │
        │ ブログデータ + 音声を      │
        │ JSONに変換                │
        └─────────┬─────────────────┘
                  │
        ┌─────────▼─────────────────┐
        │ Node.js render.mjs 呼び出し│
        │ (subprocess)              │
        └─────────┬─────────────────┘
                  │
        ┌─────────▼─────────────────┐
        │ Remotion bundle & render  │
        │ (BlogVideo composition)   │
        │ 音声 + 画像を統合         │
        └─────────┬─────────────────┘
                  │
        ┌─────────▼─────────────────┐
        │ MP4ファイル生成           │
        │ (H.264 + AAC codec)       │
        └─────────┬─────────────────┘
                  │
        ┌─────────▼─────────────────┐
        │ 出力パスを返却            │
        │ ・article_analysis含む    │
        └───────────────────────────┘
```
