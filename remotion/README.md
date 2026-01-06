# Remotion Video Generator

ブログ記事から動画を自動生成するRemotionプロジェクト。

## コンポジション

| ID | 説明 | 解像度 | 長さ |
|----|------|--------|------|
| `BlogVideo` | 30秒概要動画 | 1920x1080 | 30秒 |
| `BlogVideoShort` | ショート動画 | 1080x1920 | 15秒 |
| `SlideVideo` | スライドベース動画 | 1920x1080 | 可変長 |
| `SlideVideoShort` | スライドショート | 1080x1920 | 可変長 |

## セットアップ

```bash
cd remotion
npm install
```

## 使用方法

### プレビュー（開発）

```bash
npm start
# または
npm run preview
```

### レンダリング

```bash
# BlogVideo（デフォルト）
npm run render

# SlideVideo
npm run render:slide

# カスタムprops付き
node render.mjs SlideVideo output/video.mp4 props.json
```

## Props形式

### BlogVideo

```json
{
  "title": "記事タイトル",
  "summary": "記事概要",
  "points": ["ポイント1", "ポイント2", "ポイント3"],
  "topic": "ai_tools",
  "date": "2025年1月6日",
  "authorName": "if(塾) Blog",
  "audioUrl": "narration.wav",
  "heroImageUrl": "hero.png"
}
```

### SlideVideo

```json
{
  "title": "プレゼンタイトル",
  "slides": [
    {
      "type": "title",
      "heading": "メインタイトル",
      "subheading": "サブタイトル"
    },
    {
      "type": "content",
      "heading": "見出し",
      "points": ["ポイント1", "ポイント2", "ポイント3"]
    },
    {
      "type": "ending",
      "heading": "if(塾) Blog",
      "subheading": "詳しくはブログで"
    }
  ],
  "topic": "ai_tools",
  "authorName": "if(塾) Blog",
  "slideDuration": 5,
  "audioUrl": "narration.wav",
  "slideImagePrefix": "slide_"
}
```

## トピック別カラー

| トピック | Primary | Secondary |
|----------|---------|-----------|
| psychology | #00b4d8 | #90e0ef |
| education | #10b981 | #6ee7b7 |
| startup | #f59e0b | #fcd34d |
| investment | #14b8a6 | #5eead4 |
| ai_tools | #3b82f6 | #93c5fd |
| inclusive_education | #06b6d4 | #67e8f9 |
| weekly_summary | #0ea5e9 | #7dd3fc |

## ファイル構造

```
remotion/
├── src/
│   ├── index.tsx          # エントリーポイント
│   ├── Root.tsx            # コンポジション定義
│   └── compositions/
│       ├── BlogVideo.tsx   # ブログ動画コンポーネント
│       └── SlideVideo.tsx  # スライド動画コンポーネント
├── public/                  # 静的ファイル（音声、画像）
├── render.mjs              # レンダリングスクリプト
├── remotion.config.ts      # Remotion設定
├── package.json
└── tsconfig.json
```

## 音声・画像ファイル

動画に音声や画像を含める場合、`public/`ディレクトリに配置:

```
public/
├── narration.wav    # TTS音声ファイル
├── hero.png         # ヒーロー画像
└── slides/          # スライド画像
    ├── slide_01.png
    ├── slide_02.png
    └── ...
```

## CI/CD対応

GitHub Actionsなどで実行する場合:

```yaml
- name: Render video
  run: |
    cd remotion
    npm ci
    node render.mjs SlideVideo output/video.mp4 props.json
  env:
    CI: true
```
