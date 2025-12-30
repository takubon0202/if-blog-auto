# Video Agent

## 役割
ブログ記事の内容からRemotionを使用して動画を自動生成する。
記事タイトル、要約、ポイントを視覚的なショート動画に変換します。

## 使用技術
- **Framework**: Remotion 4.0
- **Runtime**: Node.js 20+
- **Output**: MP4 (H.264)

## 動画仕様

### 標準動画（30秒版）
| 項目 | 値 |
|------|------|
| 解像度 | 1920x1080 |
| フレームレート | 30fps |
| 長さ | 30秒（900フレーム） |
| 形式 | MP4 (H.264) |
| 用途 | YouTube、ブログ埋め込み |

### ショート動画（15秒版）
| 項目 | 値 |
|------|------|
| 解像度 | 1080x1920（縦型） |
| フレームレート | 30fps |
| 長さ | 15秒（450フレーム） |
| 形式 | MP4 (H.264) |
| 用途 | YouTube Shorts、TikTok、Instagram Reels |

## トピック別カラースキーム

画像生成と統一されたカラースキームを使用：

| トピックID | Primary | Accent | 名称 |
|-----------|---------|--------|------|
| `psychology` | #2b6cb0 | #4299e1 | 心理学 |
| `education` | #2f855a | #48bb78 | 教育 |
| `startup` | #c05621 | #ed8936 | スタートアップ |
| `investment` | #744210 | #d69e2e | 投資 |
| `ai_tools` | #1a365d | #3182ce | AIツール |
| `inclusive_education` | #285e61 | #38b2ac | インクルーシブ教育 |
| `weekly_summary` | #553c9a | #805ad5 | 週間総括 |

## シーン構成

### 標準動画（30秒）
```
Scene 1: タイトルシーン（6秒）
- トピックラベル表示（アニメーション付き）
- メインタイトル（フェードイン + スライドアップ）

Scene 2: サマリーシーン（5秒）
- 記事要約をシンプルに表示
- カラーアクセント付き

Scene 3-5: ポイントシーン（各4秒 × 3ポイント = 12秒）
- 番号アイコン（スケールアニメーション）
- ポイントテキスト（スライドイン）

Scene 6: エンディング（5秒）
- ブログ名/著者名
- 日付
- CTA「ブログで詳しく読む」
```

### ショート動画（15秒）
```
Scene 1: タイトルシーン（4秒）
Scene 2: サマリーシーン（3秒）
Scene 3-4: ポイントシーン（各2秒 × 2ポイント = 4秒）
Scene 5: エンディング（3秒）
```

## 処理フロー
```
1. ブログ記事データを受け取る
   - title: 記事タイトル
   - summary: 記事要約
   - points: 主要ポイント（配列）
   - topic: トピックID
   - date: 日付

2. Remotionプロジェクトにpropsを渡す

3. remotion renderコマンドを実行
   - 標準動画: BlogVideo コンポジション
   - ショート動画: BlogVideoShort コンポジション

4. 生成された動画を出力ディレクトリに保存

5. 結果を返却
```

## 入力
```json
{
  "title": "AIツールの最新動向2025",
  "summary": "2025年のAIツールトレンドを詳しく解説します。",
  "points": [
    "生成AIの進化と実用化",
    "業務効率化ツールの普及",
    "セキュリティとプライバシーの重要性"
  ],
  "topic": "ai_tools",
  "date": "2025年12月30日",
  "authorName": "if(塾) Blog"
}
```

## 出力
```json
{
  "status": "success",
  "videos": {
    "standard": {
      "path": "output/videos/blog_video_20251230_123456.mp4",
      "duration": 30,
      "resolution": "1920x1080"
    },
    "short": {
      "path": "output/videos/blog_video_short_20251230_123456.mp4",
      "duration": 15,
      "resolution": "1080x1920"
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

### 推奨スタイル
- クリーンでミニマルなデザイン
- スムーズなアニメーション（spring, interpolate）
- 読みやすいフォントサイズ
- 適切なコントラスト

## API呼び出しパターン

### Pythonからの呼び出し
```python
from scripts.generate_video import generate_video

result = await generate_video(
    article={
        "title": "記事タイトル",
        "summary": "記事要約",
        "points": ["ポイント1", "ポイント2", "ポイント3"],
        "topic_id": "ai_tools",
        "date": "2025年12月30日"
    },
    output_dir="output/videos",
    generate_short=True  # ショート動画も生成
)
```

### Node.jsからの呼び出し
```javascript
// render.mjs
import { bundle } from "@remotion/bundler";
import { renderMedia, selectComposition } from "@remotion/renderer";

await renderMedia({
  composition,
  serveUrl: bundled,
  codec: "h264",
  outputLocation: outputPath,
  inputProps: blogData
});
```

## 依存関係

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

## エラーハンドリング
```python
try:
    result = await generate_video(article)
except VideoGenerationError as e:
    logger.error(f"Video generation failed: {e}")
    # フォールバック: 動画なしで続行
    result = {"status": "skipped", "reason": str(e)}
```

## レート制限
- 動画レンダリングは重い処理のため、1記事につき1回のみ
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
└─────────────────┬──────────────────┘
                  │
        ┌─────────▼─────────────────┐
        │ ブログデータをJSONに変換   │
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
        └─────────┬─────────────────┘
                  │
        ┌─────────▼─────────────────┐
        │ MP4ファイル生成           │
        │ (H.264 codec)             │
        └─────────┬─────────────────┘
                  │
        ┌─────────▼─────────────────┐
        │ 出力パスを返却            │
        └───────────────────────────┘
```
