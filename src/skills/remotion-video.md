# Remotion Video Skill

## 概要
Remotionフレームワークを使用したブログ動画生成スキル。
記事の内容を視覚的な動画に自動変換します。

## 使用技術
- **Framework**: Remotion 4.0
- **Language**: TypeScript/React
- **Output**: MP4 (H.264)

## Remotion概要
Remotionは、Reactコンポーネントを使ってプログラマティックに動画を作成できるフレームワークです。

### 主要概念
- **Composition**: 動画の定義（サイズ、長さ、fps）
- **Sequence**: タイムライン上のシーン配置
- **useCurrentFrame**: 現在のフレーム番号を取得
- **interpolate**: 値をアニメーション
- **spring**: 物理ベースのアニメーション

## コンポジション設定

### BlogVideo（標準版）
```typescript
<Composition
  id="BlogVideo"
  component={BlogVideo}
  durationInFrames={900}  // 30秒 @ 30fps
  fps={30}
  width={1920}
  height={1080}
  defaultProps={blogData}
/>
```

### BlogVideoShort（ショート版）
```typescript
<Composition
  id="BlogVideoShort"
  component={BlogVideo}
  durationInFrames={450}  // 15秒 @ 30fps
  fps={30}
  width={1080}
  height={1920}  // 縦型
  defaultProps={{...blogData, isShort: true}}
/>
```

## Props インターフェース
```typescript
interface BlogVideoProps {
  title: string;        // 記事タイトル
  summary: string;      // 記事要約
  points: string[];     // 主要ポイント（配列）
  topic: string;        // トピックID
  date: string;         // 日付
  authorName?: string;  // 著者名（デフォルト: "if(塾) Blog"）
  isShort?: boolean;    // ショート動画フラグ
}
```

## トピック別カラースキーム
```typescript
const TOPIC_COLORS = {
  psychology: { primary: "#2b6cb0", accent: "#4299e1", name: "心理学" },
  education: { primary: "#2f855a", accent: "#48bb78", name: "教育" },
  startup: { primary: "#c05621", accent: "#ed8936", name: "スタートアップ" },
  investment: { primary: "#744210", accent: "#d69e2e", name: "投資" },
  ai_tools: { primary: "#1a365d", accent: "#3182ce", name: "AIツール" },
  inclusive_education: { primary: "#285e61", accent: "#38b2ac", name: "インクルーシブ教育" },
  weekly_summary: { primary: "#553c9a", accent: "#805ad5", name: "週間総括" }
};
```

## アニメーション技法

### Spring アニメーション
```typescript
const slideIn = spring({
  frame,
  fps,
  config: { damping: 100, stiffness: 200, mass: 0.5 }
});
```

### Interpolate
```typescript
const opacity = interpolate(frame, [0, 20], [0, 1], {
  extrapolateRight: "clamp"
});

const translateY = interpolate(slideIn, [0, 1], [50, 0]);
```

## シーン構成

### TitleScene
- グラデーション背景（トピックカラー）
- トピックラベル（スケールアニメーション）
- メインタイトル（フェードイン + スライドアップ）

### SummaryScene
- ダークグレー背景
- カラーアクセントバー
- 要約テキスト（フェードイン）

### PointScene
- ライトグレー背景
- 番号バッジ（スケールアニメーション）
- ポイントテキスト（スライドイン）

### EndingScene
- グラデーション背景（トピックカラー）
- 著者名/ブログ名（スケールアニメーション）
- 日付（フェードイン）
- CTA「ブログで詳しく読む」

## レンダリング

### CLIでのレンダリング
```bash
# 標準動画
npx remotion render BlogVideo out/video.mp4

# ショート動画
npx remotion render BlogVideoShort out/video_short.mp4

# カスタムprops
npx remotion render BlogVideo out/video.mp4 --props='{"title":"カスタムタイトル"}'
```

### プログラマティックレンダリング
```javascript
import { bundle } from "@remotion/bundler";
import { renderMedia, selectComposition } from "@remotion/renderer";

const bundled = await bundle({
  entryPoint: "./src/index.tsx",
  webpackOverride: (config) => config,
});

const composition = await selectComposition({
  serveUrl: bundled,
  id: "BlogVideo",
  inputProps: blogData,
});

await renderMedia({
  composition,
  serveUrl: bundled,
  codec: "h264",
  outputLocation: "out/video.mp4",
  inputProps: blogData,
});
```

## Pythonからの呼び出し
```python
import subprocess
import json
import os

def render_video(blog_data: dict, output_path: str, is_short: bool = False):
    """Remotion動画をレンダリング"""

    remotion_dir = os.path.join(os.path.dirname(__file__), "..", "remotion")

    # propsをJSONファイルに保存
    props_file = os.path.join(remotion_dir, "props.json")
    with open(props_file, "w", encoding="utf-8") as f:
        json.dump(blog_data, f, ensure_ascii=False)

    composition = "BlogVideoShort" if is_short else "BlogVideo"

    # Remotionレンダリング実行
    result = subprocess.run(
        ["node", "render.mjs", composition, output_path, props_file],
        cwd=remotion_dir,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        raise Exception(f"Render failed: {result.stderr}")

    return output_path
```

## プロジェクト構成
```
remotion/
├── package.json
├── remotion.config.ts
├── render.mjs              # レンダリングスクリプト
├── tsconfig.json
└── src/
    ├── index.tsx           # エントリーポイント
    ├── Root.tsx            # コンポジション定義
    └── compositions/
        └── BlogVideo.tsx   # メイン動画コンポーネント
```

## 依存関係インストール
```bash
cd remotion
npm install
```

## 開発プレビュー
```bash
npm start
# ブラウザで http://localhost:3000 を開く
```

## エラーハンドリング
```python
class VideoRenderError(Exception):
    """動画レンダリングエラー"""
    pass

try:
    output = render_video(blog_data, "out/video.mp4")
except subprocess.CalledProcessError as e:
    raise VideoRenderError(f"Remotion render failed: {e.stderr}")
except FileNotFoundError:
    raise VideoRenderError("Node.js or Remotion not found")
```

## 出力ディレクトリ
```
output/
└── videos/
    ├── blog_video_20251230_ai_tools.mp4       # 標準版
    └── blog_video_short_20251230_ai_tools.mp4 # ショート版
```

## 注意事項
- Node.js 20+ が必要
- 初回実行時は依存関係のインストールが必要
- レンダリングは重い処理のため、CI/CDでのタイムアウトに注意
- 日本語フォントが必要な場合は、システムフォントを使用
