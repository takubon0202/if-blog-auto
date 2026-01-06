# Remotion Video Generator v2.0.0

ブログ記事から動画を自動生成するRemotionプロジェクト。

## 技術スタック

| 技術 | バージョン | 用途 |
|------|-----------|------|
| Remotion | 4.0.0 | 動画レンダリングフレームワーク |
| React | 18.2.0 | UIコンポーネント |
| TypeScript | 5.3.0+ | 型安全な開発 |
| Node.js | 20+ | 実行環境 |

## コンポジション一覧

| ID | 説明 | 解像度 | 長さ | 用途 |
|----|------|--------|------|------|
| `BlogVideo` | ブログ概要動画 | 1920x1080 | 30秒 | YouTube/Web埋め込み |
| `BlogVideoShort` | ショート動画 | 1080x1920 | 15秒 | Shorts/Reels/TikTok |
| `SlideVideo` | スライドベース動画 | 1920x1080 | 可変長 | 解説動画 |
| `SlideVideoShort` | スライドショート | 1080x1920 | 可変長 | ショート解説 |

## セットアップ

```bash
cd remotion
npm install
```

## 使用方法

### プレビュー（Remotion Studio）

```bash
npm start
# または
npm run preview
```

### レンダリング

```bash
# BlogVideo（デフォルト）
npm run render

# BlogVideo
npm run render:blog

# SlideVideo
npm run render:slide

# ショート動画
npm run build:short

# カスタムprops付き
node render.mjs SlideVideo output/video.mp4 props.json

# CI環境
CI=true node render.mjs SlideVideo output/video.mp4 props.json
```

### その他のコマンド

```bash
# 型チェック
npm run typecheck

# Remotionアップグレード
npm run upgrade
```

## Props形式

### BlogVideo

```json
{
  "title": "記事タイトル",
  "summary": "記事概要（2-3文）",
  "points": ["ポイント1", "ポイント2", "ポイント3"],
  "topic": "ai_tools",
  "date": "2025年1月6日",
  "authorName": "if(塾) Blog",
  "isShort": false,
  "audioUrl": "narration.wav",
  "heroImageUrl": "hero.png"
}
```

| プロパティ | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| `title` | string | Yes | 記事タイトル |
| `summary` | string | Yes | 記事概要 |
| `points` | string[] | Yes | 要点リスト（最大3つ表示） |
| `topic` | string | Yes | トピックID（カラースキーム選択） |
| `date` | string | Yes | 公開日 |
| `authorName` | string | No | 著者名（デフォルト: if(塾) Blog） |
| `isShort` | boolean | No | ショート版フラグ |
| `audioUrl` | string | No | TTS音声ファイルパス |
| `heroImageUrl` | string | No | ヒーロー画像パス |

### SlideVideo

```json
{
  "title": "プレゼンタイトル",
  "slides": [
    {
      "type": "title",
      "heading": "メインタイトル",
      "subheading": "サブタイトル",
      "imageUrl": "slides/slide_01.png"
    },
    {
      "type": "content",
      "heading": "見出し",
      "points": ["ポイント1", "ポイント2", "ポイント3"],
      "imageUrl": "slides/slide_02.png",
      "narrationText": "このスライドのナレーション"
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

| プロパティ | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| `title` | string | Yes | プレゼンタイトル |
| `slides` | SlideData[] | Yes | スライドデータ配列 |
| `topic` | string | Yes | トピックID |
| `authorName` | string | No | 著者名 |
| `slideDuration` | number | No | 各スライドの表示時間（秒、デフォルト: 5） |
| `audioUrl` | string | No | TTS音声ファイルパス |
| `slideImagePrefix` | string | No | スライド画像のプレフィックス |

#### SlideData型

| プロパティ | 型 | 説明 |
|-----------|-----|------|
| `type` | "title" \| "content" \| "ending" | スライドタイプ |
| `heading` | string | 見出し |
| `subheading` | string? | サブ見出し |
| `points` | string[]? | 箇条書きポイント |
| `imageUrl` | string? | 背景画像パス |
| `narrationText` | string? | ナレーションテキスト |

### 動的な動画長（calculateMetadata）

SlideVideoは`calculateMetadata`を使用して動的に長さを計算:

```
動画長（フレーム） = スライド数 × slideDuration × fps
例: 12スライド × 5秒 × 30fps = 1800フレーム（60秒）
```

## トピック別カラースキーム

### BlogVideo カラー

| トピック | Primary | Accent | 日本語名 |
|----------|---------|--------|---------|
| psychology | #2b6cb0 | #4299e1 | 心理学 |
| education | #2f855a | #48bb78 | 教育 |
| startup | #c05621 | #ed8936 | スタートアップ |
| investment | #744210 | #d69e2e | 投資 |
| ai_tools | #1a365d | #3182ce | AIツール |
| inclusive_education | #285e61 | #38b2ac | インクルーシブ教育 |
| weekly_summary | #553c9a | #805ad5 | 週間総括 |

### SlideVideo カラー

| トピック | Primary | Secondary | Background |
|----------|---------|-----------|------------|
| psychology | #00b4d8 | #90e0ef | #1a1a2e |
| education | #10b981 | #6ee7b7 | #1a1a2e |
| startup | #f59e0b | #fcd34d | #1a1a2e |
| investment | #14b8a6 | #5eead4 | #1a1a2e |
| ai_tools | #3b82f6 | #93c5fd | #1a1a2e |
| inclusive_education | #06b6d4 | #67e8f9 | #1a1a2e |
| weekly_summary | #0ea5e9 | #7dd3fc | #1a1a2e |

## アニメーション効果

### BlogVideo

| シーン | エフェクト |
|--------|-----------|
| タイトル | Spring + Fade In |
| ヒーロー画像 | Ken Burns（ズームアウト） |
| サマリー | Fade In |
| ポイント | Slide In + Spring |
| エンディング | Scale + Fade |

### SlideVideo

| エフェクト | 説明 |
|-----------|------|
| Ken Burns | ズーム + パンの組み合わせ |
| Fade | フェードイン/アウト |
| Slide Left/Right | 左右スライドイン |
| Stagger | ポイントの順次表示 |
| Progress Bar | 下部プログレスバー |

## ファイル構造

```
remotion/
├── src/
│   ├── index.tsx              # エントリーポイント（registerRoot）
│   ├── Root.tsx               # コンポジション定義
│   └── compositions/
│       ├── BlogVideo.tsx      # ブログ動画コンポーネント
│       │   ├── TitleScene     # タイトルシーン
│       │   ├── HeroImageScene # ヒーロー画像（Ken Burns）
│       │   ├── SummaryScene   # サマリーシーン
│       │   ├── PointScene     # ポイントシーン
│       │   └── EndingScene    # エンディングシーン
│       └── SlideVideo.tsx     # スライド動画コンポーネント
│           └── SlideScene     # 各スライドのシーン
├── public/                    # 静的ファイル（音声、画像）
│   ├── narration.wav          # TTS音声ファイル
│   ├── hero.png               # ヒーロー画像
│   └── slides/                # スライド画像
│       ├── slide_01.png
│       ├── slide_02.png
│       └── ...
├── out/                       # 出力ディレクトリ
├── render.mjs                 # プログラマティックレンダリング
├── remotion.config.ts         # Remotion設定
├── package.json               # 依存関係・スクリプト
├── tsconfig.json              # TypeScript設定
└── README.md                  # このファイル
```

## render.mjs の機能

### コマンドライン引数

```bash
node render.mjs [compositionId] [outputPath] [propsFile]
```

| 引数 | デフォルト | 説明 |
|------|-----------|------|
| `compositionId` | BlogVideo | レンダリングするコンポジション |
| `outputPath` | out/video.mp4 | 出力ファイルパス |
| `propsFile` | - | propsのJSONファイル |

### 機能

- **進捗ログ**: 10%ごとに進捗を出力
- **動的長さ計算**: SlideVideoのスライド数から自動計算
- **CI環境対応**: `CI=true`でソフトウェアレンダリング使用
- **エラー解析**: エラー時に原因と解決策を提案
- **ファイルサイズ検証**: 異常に小さいファイルをエラーとして検出

### CI環境設定

```javascript
const chromiumOptions = {
  gl: isCI ? 'swangle' : 'angle',
  enableMultiProcessOnLinux: true,
  headless: true
};
```

## remotion.config.ts 設定

```typescript
Config.setVideoImageFormat("jpeg");   // フレーム画像形式
Config.setOverwriteOutput(true);      // 上書き許可
Config.setJpegQuality(90);            // JPEG品質
Config.setConcurrency(4);             // 並列処理数
Config.setLevel("verbose");           // ログレベル
```

## CI/CD対応

### GitHub Actions

```yaml
- name: Setup Node.js
  uses: actions/setup-node@v4
  with:
    node-version: '20'

- name: Install dependencies
  run: |
    cd remotion
    npm ci

- name: Render video
  run: |
    cd remotion
    node render.mjs SlideVideo output/video.mp4 props.json
  env:
    CI: true
    DISPLAY: ':99'

- name: Upload artifact
  uses: actions/upload-artifact@v4
  with:
    name: video
    path: remotion/output/video.mp4
```

### Linux環境での依存関係

```bash
sudo apt-get update
sudo apt-get install -y \
  libnss3 \
  libatk-bridge2.0-0 \
  libdrm2 \
  libxkbcommon0 \
  libgbm1 \
  libasound2
```

## トラブルシューティング

### Target closed エラー

**原因**: Chromiumがクラッシュ

**解決策**:
1. Chrome依存関係をインストール
2. `gl: 'swiftshader'`を試す
3. メモリを増やす
4. `DISPLAY`環境変数を設定

### ENOENT エラー

**原因**: ファイルが見つからない

**解決策**:
1. `npm install`を実行
2. ソースファイルの存在を確認

### GPU/GL エラー

**原因**: グラフィックス関連

**解決策**:
1. `gl: 'swiftshader'`でソフトウェアレンダリング
2. Mesa/LLVMライブラリをインストール

## 統合ワークフロー

このRemotionプロジェクトは以下のワークフローの一部として使用:

```
1. ブログ生成 (Gemini 3 Pro)
   ↓
2. スライド生成 (Gemini 3 Pro + 2.5 Flash image)
   ↓
3. PDF/画像変換 (Marp CLI + pdf2image)
   ↓
4. 動画生成 (Remotion SlideVideo)
   ↓
5. 音声追加 (Gemini 2.5 Flash TTS)
   ↓
6. 品質評価 (95%以上で合格)
```

詳細は `src/scripts/generate_slide_video.py` を参照。

## ライセンス

MIT License
