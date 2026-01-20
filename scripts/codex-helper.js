#!/usr/bin/env node
/**
 * Codex Helper - OpenAI Codex CLI連携スクリプト
 * if-blog-auto プロジェクト用
 *
 * 使用方法:
 *   node scripts/codex-helper.js "タスク内容"
 *   node scripts/codex-helper.js --error "エラーメッセージ"
 *   node scripts/codex-helper.js --file path/to/file.js "修正内容"
 *   node scripts/codex-helper.js --interactive
 */

const fs = require('fs');
const path = require('path');
const { spawn, execSync } = require('child_process');

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

function checkCodexInstalled() {
  try {
    execSync('codex --version', { stdio: 'pipe' });
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
      prompt = `以下のファイルを修正してください。\n\nファイル: ${fileInfo.name}\nタスク: ${task}\n\n現在のコード:\n\`\`\`\n${fileInfo.content}\n\`\`\``;
      break;
    default:
      prompt = task;
  }
  return prompt;
}

function runCodexInteractive() {
  console.log('Codex CLI を対話モードで起動します...\n');
  const codex = spawn('codex', [], { stdio: 'inherit', shell: true, cwd: process.cwd() });
  codex.on('close', (code) => console.log(`\nCodex CLI 終了 (code: ${code})`));
}

function runCodexWithPrompt(prompt, interactive = false) {
  if (interactive) {
    // 対話モード（ターミナルが必要）
    console.log('Codex CLI を実行中（対話モード）...\n');
    const codex = spawn('codex', [prompt], { stdio: 'inherit', shell: true, cwd: process.cwd() });
    codex.on('close', (code) => {
      if (code !== 0) console.error(`\nCodex CLI がエラーで終了しました (code: ${code})`);
    });
  } else {
    // 非対話モード（codex exec使用）
    console.log('Codex CLI を実行中（非対話モード）...\n');
    const codex = spawn('codex', ['exec', prompt], { stdio: 'inherit', shell: true, cwd: process.cwd() });
    codex.on('close', (code) => {
      if (code !== 0) console.error(`\nCodex CLI がエラーで終了しました (code: ${code})`);
    });
  }
}

function writeProjectContext() {
  const codexMdPath = path.join(process.cwd(), 'CODEX.md');
  if (fs.existsSync(codexMdPath)) return;
  try {
    fs.writeFileSync(codexMdPath, PROJECT_CONTEXT, 'utf8');
    console.log('CODEX.md を作成しました');
  } catch (e) {}
}

async function main() {
  const args = process.argv.slice(2);

  if (args.length === 0 || args[0] === '--help' || args[0] === '-h') {
    console.log('Codex Helper - OpenAI Codex CLI連携 (if-blog-auto)\n');
    console.log('使用方法:');
    console.log('  node scripts/codex-helper.js "タスク内容"          # 非対話モード (codex exec)');
    console.log('  node scripts/codex-helper.js --error "エラー"      # エラー解決');
    console.log('  node scripts/codex-helper.js --file X.js "修正"    # ファイル修正');
    console.log('  node scripts/codex-helper.js --interactive         # 対話モード\n');
    console.log('または直接:');
    console.log('  codex exec "タスク内容"   # 非対話モード');
    console.log('  codex "タスク内容"        # 対話モード（ターミナル必要）');
    process.exit(0);
  }

  if (!checkCodexInstalled()) {
    console.error('エラー: Codex CLIがインストールされていません。');
    console.log('\nインストール: npm install -g @openai/codex');
    console.log('ログイン: codex --login');
    process.exit(1);
  }

  writeProjectContext();

  if (args[0] === '--interactive' || args[0] === '-i') {
    runCodexInteractive();
    return;
  }

  let prompt = '', mode = 'general', fileInfo = null;

  if (args[0] === '--error' || args[0] === '-e') {
    mode = 'error';
    prompt = generatePrompt(args.slice(1).join(' '), mode);
  } else if (args[0] === '--file' || args[0] === '-f') {
    mode = 'file';
    const filePath = args[1];
    const content = readFile(filePath);
    if (!content) process.exit(1);
    fileInfo = { name: path.basename(filePath), content };
    const task = args.slice(2).join(' ') || '改善してください';
    prompt = generatePrompt(task, mode, fileInfo);
  } else {
    prompt = generatePrompt(args.join(' '), mode);
  }

  runCodexWithPrompt(prompt);
}

main();
