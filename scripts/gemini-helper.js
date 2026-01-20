#!/usr/bin/env node
/**
 * Gemini Helper - Google Gemini CLI連携スクリプト
 * if-blog-auto プロジェクト用
 *
 * Geminiサブスクリプションに含まれるGemini CLIを使用します。
 * Claude Code / Codex CLIと同じ仕組みです。
 *
 * モデル優先順位:
 *   1. gemini-3-pro-preview（推奨・デフォルト）
 *   2. gemini-3-flash-preview（高速処理用）
 *   3. gemini-2.5-pro（フォールバック）
 *   4. gemini-2.5-flash（フォールバック）
 *
 * 使用方法:
 *   node scripts/gemini-helper.js "タスク内容"
 *   node scripts/gemini-helper.js --fast "簡単な質問"
 *   node scripts/gemini-helper.js --error "エラーメッセージ"
 *   node scripts/gemini-helper.js --file path/to/file.js "修正内容"
 *   node scripts/gemini-helper.js --interactive
 *   node scripts/gemini-helper.js --yolo "タスク"
 */

const fs = require('fs');
const path = require('path');
const { spawn, execSync } = require('child_process');

// モデル設定（Gemini 3系を優先）
const MODELS = {
  // メイン（常にこちらを使用）
  PRO: 'gemini-3-pro-preview',      // 推奨・デフォルト
  FLASH: 'gemini-3-flash-preview',  // 高速処理用

  // フォールバック（エラー時のみ）
  PRO_FALLBACK: 'gemini-2.5-pro',
  FLASH_FALLBACK: 'gemini-2.5-flash'
};

// デフォルト設定
const CONFIG = {
  model: MODELS.PRO,  // デフォルトはGemini 3 Pro
  yolo: true  // デフォルトで自動承認モード
};

// if-blog-auto プロジェクト情報
const PROJECT_CONTEXT = `# if-blog-auto プロジェクト情報

Gemini APIを活用した最新トレンド情報自動収集・画像/動画付きブログ記事生成・GitHub Pages自動投稿システム

## 技術スタック
- Python 3.11+ (メインスクリプト)
- TypeScript/JavaScript (Remotion動画生成)
- Gemini API (gemini-3-pro-preview, gemini-3-flash-preview, gemini-2.5-flash-image)
- Remotion 4.0 (動画生成 - SlideVideoV3)
- Marp CLI (スライド生成)
- Jekyll (GitHub Pages)
- GitHub Actions (CI/CD)

## ディレクトリ構成
- src/scripts/ - Pythonスクリプト (main.py, generate_video_v3.py等)
- remotion/ - Remotion動画生成 (render.mjs, SlideVideoV3.tsx等)
- docs/ - GitHub Pagesサイト
- .github/workflows/ - GitHub Actions

## 要件
- コメントは日本語
- PEP8準拠 (Python)
- ESLint準拠 (TypeScript/JavaScript)
- 絵文字使用禁止
- 紫色系デザイン禁止`;

function checkGeminiInstalled() {
  try {
    execSync('gemini --version', { stdio: 'pipe' });
    return true;
  } catch { return false; }
}

function readFile(filePath) {
  try {
    const absolutePath = path.isAbsolute(filePath)
      ? filePath : path.join(process.cwd(), filePath);
    return fs.readFileSync(absolutePath, 'utf8');
  } catch (e) {
    console.error(`ファイル読み込みエラー: ${filePath}`);
    return null;
  }
}

function generatePrompt(task, mode = 'general', fileInfo = null) {
  let prompt = '';
  switch (mode) {
    case 'error':
      prompt = `以下のエラーを解決してください。原因を分析し、修正コードを提示してください。\n\nエラー:\n${task}`;
      break;
    case 'file':
      prompt = `以下のファイルを修正してください。\n\nファイル: ${fileInfo.name}\nタスク: ${task}\n\n現在のコード:\n\`\`\`javascript\n${fileInfo.content}\n\`\`\``;
      break;
    default:
      prompt = task;
  }
  return prompt;
}

/**
 * フォールバックモデルを取得
 */
function getFallbackModel(currentModel) {
  if (currentModel === MODELS.PRO) {
    return MODELS.PRO_FALLBACK;
  }
  if (currentModel === MODELS.FLASH) {
    return MODELS.FLASH_FALLBACK;
  }
  return null;
}

function runGeminiInteractive(model) {
  console.log('Gemini CLI を対話モードで起動します...');
  console.log(`モデル: ${model}`);
  console.log('終了するには Ctrl+C または /exit を入力\n');

  const args = ['-m', model];
  const gemini = spawn('gemini', args, {
    stdio: 'inherit',
    shell: true,
    cwd: process.cwd()
  });

  gemini.on('close', (code) => {
    console.log(`\nGemini CLI 終了 (code: ${code})`);
  });
}

/**
 * Gemini CLIを実行（プロンプト指定、フォールバック対応）
 */
function runGeminiWithPrompt(prompt, model, yolo = false, isRetry = false) {
  if (!isRetry) {
    console.log('Gemini CLI を実行中...');
  } else {
    console.log('\nフォールバックモデルで再試行...');
  }
  console.log(`モデル: ${model}`);
  if (yolo) console.log('モード: YOLO（自動承認）');
  console.log('');

  const args = ['-m', model];
  if (yolo) args.push('-y');
  args.push(prompt);

  const gemini = spawn('gemini', args, {
    stdio: 'inherit',
    shell: true,
    cwd: process.cwd()
  });

  gemini.on('close', (code) => {
    if (code !== 0) {
      // エラー時にフォールバックを試行
      const fallbackModel = getFallbackModel(model);
      if (fallbackModel && !isRetry) {
        console.error(`\n${model} でエラーが発生しました (code: ${code})`);
        console.log(`フォールバック: ${fallbackModel} を使用します...`);
        runGeminiWithPrompt(prompt, fallbackModel, yolo, true);
      } else {
        console.error(`\nGemini CLI がエラーで終了しました (code: ${code})`);
      }
    }
  });
}

function writeProjectContext() {
  const geminiMdPath = path.join(process.cwd(), 'GEMINI.md');
  if (fs.existsSync(geminiMdPath)) return;
  try {
    fs.writeFileSync(geminiMdPath, PROJECT_CONTEXT, 'utf8');
    console.log('GEMINI.md を作成しました（プロジェクト情報）');
  } catch (e) {}
}

async function main() {
  const args = process.argv.slice(2);

  // ヘルプ表示
  if (args.length === 0 || args[0] === '--help' || args[0] === '-h') {
    console.log('Gemini Helper - Google Gemini CLI連携 (if-blog-auto)');
    console.log('');
    console.log('Geminiサブスクリプションに含まれるGemini CLIを使用します。');
    console.log('');
    console.log('モデル優先順位:');
    console.log(`  1. ${MODELS.PRO} (推奨・デフォルト)`);
    console.log(`  2. ${MODELS.FLASH} (高速処理用)`);
    console.log(`  3. ${MODELS.PRO_FALLBACK} (フォールバック)`);
    console.log(`  4. ${MODELS.FLASH_FALLBACK} (フォールバック)`);
    console.log('');
    console.log('使用方法:');
    console.log('  node scripts/gemini-helper.js "タスク内容"        # Gemini 3 Pro');
    console.log('  node scripts/gemini-helper.js --fast "質問"       # Gemini 3 Flash');
    console.log('  node scripts/gemini-helper.js --error "エラー"    # エラー解決');
    console.log('  node scripts/gemini-helper.js --file X.js "修正"  # ファイル修正');
    console.log('  node scripts/gemini-helper.js --interactive       # 対話モード');
    console.log('  node scripts/gemini-helper.js --yolo "タスク"     # 自動承認');
    console.log('');
    console.log('または直接Gemini CLIを使用:');
    console.log(`  gemini -m ${MODELS.PRO} "タスク"`);
    console.log(`  gemini -m ${MODELS.FLASH} "簡単な質問"`);
    console.log('  gemini                          # 対話モード');
    console.log('');
    console.log('セットアップ:');
    console.log('  npm install -g @google/gemini-cli');
    console.log('  gemini  # 初回起動時にGoogleログイン');
    process.exit(0);
  }

  // Gemini CLIの存在確認
  if (!checkGeminiInstalled()) {
    console.error('エラー: Gemini CLIがインストールされていません。');
    console.log('');
    console.log('インストール方法:');
    console.log('  npm install -g @google/gemini-cli');
    console.log('');
    console.log('ログイン:');
    console.log('  gemini  # 初回起動時にブラウザでGoogleログイン');
    process.exit(1);
  }

  // GEMINI.md を作成
  writeProjectContext();

  let model = CONFIG.model;  // デフォルト: gemini-3-pro-preview
  let yolo = CONFIG.yolo;

  // 引数解析
  let prompt = '';
  let mode = 'general';
  let fileInfo = null;
  let i = 0;

  while (i < args.length) {
    const arg = args[i];

    // モデル指定
    if (arg === '--model' || arg === '-m') {
      model = args[i + 1];
      i += 2;
      continue;
    }

    // 高速モード（Gemini 3 Flash）
    if (arg === '--fast' || arg === '-f') {
      model = MODELS.FLASH;
      i++;
      continue;
    }

    // YOLOモード
    if (arg === '--yolo' || arg === '-y') {
      yolo = true;
      i++;
      continue;
    }

    // 対話モード
    if (arg === '--interactive' || arg === '-i') {
      runGeminiInteractive(model);
      return;
    }

    // エラー解決モード
    if (arg === '--error' || arg === '-e') {
      mode = 'error';
      prompt = args.slice(i + 1).join(' ');
      break;
    }

    // ファイル修正モード
    if (arg === '--file') {
      mode = 'file';
      const filePath = args[i + 1];
      const content = readFile(filePath);
      if (!content) {
        process.exit(1);
      }
      fileInfo = { name: path.basename(filePath), content };
      const task = args.slice(i + 2).join(' ') || '改善してください';
      prompt = generatePrompt(task, mode, fileInfo);
      break;
    }

    // 通常のプロンプト
    prompt = args.slice(i).join(' ');
    break;
  }

  if (!prompt) {
    console.error('プロンプトが指定されていません。');
    process.exit(1);
  }

  // プロンプト生成（エラーモードの場合）
  if (mode === 'error') {
    prompt = generatePrompt(prompt, mode);
  }

  // Gemini実行（フォールバック対応）
  runGeminiWithPrompt(prompt, model, yolo);
}

main();
