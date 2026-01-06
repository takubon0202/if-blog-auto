/**
 * Remotion Render Script
 * ブログ動画・スライド動画をプログラマティックにレンダリング
 *
 * 対応コンポジション:
 * - BlogVideo: 30秒の概要動画
 * - BlogVideoShort: 15秒のショート動画
 * - SlideVideo: スライドベースの解説動画（可変長）
 * - SlideVideoShort: スライドベースのショート動画
 *
 * CI環境対応: 適切なChromium設定とGL設定
 */

import { bundle } from "@remotion/bundler";
import { renderMedia, selectComposition } from "@remotion/renderer";
import path from "path";
import fs from "fs";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// CI環境かどうかを判定
const isCI = process.env.CI === 'true' || process.env.GITHUB_ACTIONS === 'true';

// CI環境用のChromiumオプション (Remotion 4.0 API)
const chromiumOptions = {
  // CI環境ではソフトウェアレンダリングを使用
  gl: isCI ? 'swangle' : 'angle',
  // Linux環境ではマルチプロセスを有効化
  enableMultiProcessOnLinux: true,
  // ヘッドレスモード
  headless: true,
};

// コンポジション別のデフォルト設定
const COMPOSITION_DEFAULTS = {
  BlogVideo: { fps: 30, width: 1920, height: 1080, durationInFrames: 900 },
  BlogVideoShort: { fps: 30, width: 1080, height: 1920, durationInFrames: 450 },
  SlideVideo: { fps: 30, width: 1920, height: 1080, durationInFrames: 1800 },
  SlideVideoShort: { fps: 30, width: 1080, height: 1920, durationInFrames: 900 },
};

async function render() {
  // コマンドライン引数を取得
  const args = process.argv.slice(2);
  const compositionId = args[0] || "BlogVideo";
  const outputPath = args[1] || path.join(__dirname, "out", "video.mp4");
  const propsFile = args[2];

  console.log(`[Remotion] ========================================`);
  console.log(`[Remotion] Starting render...`);
  console.log(`[Remotion] Composition: ${compositionId}`);
  console.log(`[Remotion] Output: ${outputPath}`);
  console.log(`[Remotion] CI Environment: ${isCI}`);
  console.log(`[Remotion] GL mode: ${chromiumOptions.gl}`);
  console.log(`[Remotion] DISPLAY: ${process.env.DISPLAY || 'not set'}`);
  console.log(`[Remotion] ========================================`);

  // propsを読み込む
  let inputProps = {};
  if (propsFile && fs.existsSync(propsFile)) {
    const propsContent = fs.readFileSync(propsFile, "utf-8");
    inputProps = JSON.parse(propsContent);
    console.log(`[Remotion] Props loaded from: ${propsFile}`);
    console.log(`[Remotion] Title: ${inputProps.title || 'N/A'}`);

    // SlideVideoの場合、スライド数を表示
    if (compositionId.includes('Slide') && inputProps.slides) {
      console.log(`[Remotion] Slides: ${inputProps.slides.length}`);
      console.log(`[Remotion] Slide Duration: ${inputProps.slideDuration || 5}s each`);
      // 動画の総時間を計算
      const fps = 30;
      const slideDuration = inputProps.slideDuration || 5;
      const totalFrames = inputProps.slides.length * slideDuration * fps;
      const totalSeconds = totalFrames / fps;
      console.log(`[Remotion] Calculated Duration: ${totalSeconds}s (${totalFrames} frames)`);
    }
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

    console.log("[Remotion] Bundle complete");

    // コンポジションを選択
    console.log("[Remotion] Selecting composition...");
    const composition = await selectComposition({
      serveUrl: bundled,
      id: compositionId,
      inputProps,
      chromiumOptions,
    });

    console.log(`[Remotion] Composition: ${composition.id}`);
    console.log(`[Remotion] Duration: ${composition.durationInFrames} frames @ ${composition.fps}fps`);
    console.log(`[Remotion] Size: ${composition.width}x${composition.height}`);

    // レンダリング実行
    console.log("[Remotion] Starting render...");
    const startTime = Date.now();

    await renderMedia({
      composition,
      serveUrl: bundled,
      codec: "h264",
      outputLocation: outputPath,
      inputProps,
      chromiumOptions,
      // CRF値を調整（品質とファイルサイズのバランス）
      crf: 23,
      // ピクセルフォーマット
      pixelFormat: "yuv420p",
      onProgress: ({ progress }) => {
        const percent = Math.round(progress * 100);
        // 10%ごとにログを出力
        if (percent % 10 === 0) {
          const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
          console.log(`[Remotion] Progress: ${percent}% (${elapsed}s elapsed)`);
        }
      },
    });

    const totalTime = ((Date.now() - startTime) / 1000).toFixed(1);
    console.log(`[Remotion] Render complete in ${totalTime}s`);
    console.log(`[Remotion] Output: ${outputPath}`);

    // ファイルサイズを確認
    const stats = fs.statSync(outputPath);
    const sizeMB = (stats.size / 1024 / 1024).toFixed(2);
    console.log(`[Remotion] File size: ${sizeMB} MB (${stats.size} bytes)`);

    if (stats.size < 10000) {
      console.error(`[Remotion] ERROR: File size is too small (${stats.size} bytes)`);
      process.exit(1);
    }

    console.log("[Remotion] SUCCESS");
    process.exit(0);
  } catch (error) {
    console.error(`[Remotion] ERROR: ${error.message}`);

    // 詳細なエラー情報
    if (error.stack) {
      console.error(`[Remotion] Stack trace:\n${error.stack}`);
    }

    // エラー解析と解決策の提案
    const errorMsg = error.message.toLowerCase();
    console.error("\n[Remotion] === Error Analysis ===");

    if (errorMsg.includes('target closed')) {
      console.error("Cause: Chromium browser crashed");
      console.error("Solutions:");
      console.error("  1. Ensure all Chrome dependencies are installed");
      console.error("  2. Try using gl: 'swiftshader' instead of 'swangle'");
      console.error("  3. Increase available memory");
      console.error("  4. Check DISPLAY environment variable is set");
    } else if (errorMsg.includes('enoent')) {
      console.error("Cause: Required file or directory not found");
      console.error("Solutions:");
      console.error("  1. Run 'npm install' in the remotion directory");
      console.error("  2. Check that all source files exist");
    } else if (errorMsg.includes('timeout')) {
      console.error("Cause: Operation timed out");
      console.error("Solutions:");
      console.error("  1. Increase timeout value");
      console.error("  2. Reduce video complexity or duration");
    } else if (errorMsg.includes('gl') || errorMsg.includes('gpu') || errorMsg.includes('angle')) {
      console.error("Cause: Graphics/GPU related error");
      console.error("Solutions:");
      console.error("  1. Try gl: 'swiftshader' for software rendering");
      console.error("  2. Ensure Mesa/LLVM libraries are installed");
    } else {
      console.error("Cause: Unknown error");
      console.error("Check the full stack trace above for more details");
    }

    process.exit(1);
  }
}

render();
