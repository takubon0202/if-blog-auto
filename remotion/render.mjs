/**
 * Remotion Render Script
 * ブログ動画をプログラマティックにレンダリング
 */

import { bundle } from "@remotion/bundler";
import { renderMedia, selectComposition } from "@remotion/renderer";
import path from "path";
import fs from "fs";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

async function render() {
  // コマンドライン引数を取得
  const args = process.argv.slice(2);
  const compositionId = args[0] || "BlogVideo";
  const outputPath = args[1] || path.join(__dirname, "out", "video.mp4");
  const propsFile = args[2];

  console.log(`[Remotion] Starting render...`);
  console.log(`[Remotion] Composition: ${compositionId}`);
  console.log(`[Remotion] Output: ${outputPath}`);

  // propsを読み込む
  let inputProps = {};
  if (propsFile && fs.existsSync(propsFile)) {
    const propsContent = fs.readFileSync(propsFile, "utf-8");
    inputProps = JSON.parse(propsContent);
    console.log(`[Remotion] Props loaded from: ${propsFile}`);
  }

  // 出力ディレクトリを作成
  const outputDir = path.dirname(outputPath);
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }

  try {
    // Webpackでバンドル
    console.log("[Remotion] Bundling...");
    const bundled = await bundle({
      entryPoint: path.join(__dirname, "src", "index.tsx"),
      webpackOverride: (config) => config,
    });

    // コンポジションを選択
    console.log("[Remotion] Selecting composition...");
    const composition = await selectComposition({
      serveUrl: bundled,
      id: compositionId,
      inputProps,
    });

    // レンダリング実行
    console.log("[Remotion] Rendering...");
    await renderMedia({
      composition,
      serveUrl: bundled,
      codec: "h264",
      outputLocation: outputPath,
      inputProps,
      onProgress: ({ progress }) => {
        const percent = Math.round(progress * 100);
        process.stdout.write(`\r[Remotion] Progress: ${percent}%`);
      },
    });

    console.log(`\n[Remotion] Render complete: ${outputPath}`);

    // ファイルサイズを確認
    const stats = fs.statSync(outputPath);
    console.log(`[Remotion] File size: ${(stats.size / 1024 / 1024).toFixed(2)} MB`);

    process.exit(0);
  } catch (error) {
    console.error(`\n[Remotion] Error: ${error.message}`);
    if (error.stack) {
      console.error(`[Remotion] Stack trace:\n${error.stack}`);
    }
    process.exit(1);
  }
}

render();
