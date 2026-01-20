# if-blog-auto プロジェクト情報 (Codex用)

Gemini APIを活用した最新トレンド情報自動収集・画像/動画付きブログ記事生成・GitHub Pages自動投稿システム

## 技術スタック

- **Python 3.11+**: メインスクリプト
- **TypeScript/JavaScript**: Remotion動画生成
- **Gemini API**:
  - `gemini-3-pro-preview` (記事生成、リサーチ)
  - `gemini-3-flash-preview` (SEO、レビュー - 思考オフ)
  - `gemini-2.5-flash-image` (画像生成)
  - `deep-research-pro-preview-12-2025` (週間総括)
- **Remotion 4.0**: 動画生成 (SlideVideoV3)
- **Marp CLI**: スライド生成 (Markdown → PDF → PNG)
- **Jekyll**: GitHub Pagesサイト
- **GitHub Actions**: CI/CD

## ディレクトリ構成

```
if-blog-auto/
├── src/
│   ├── scripts/          # Pythonスクリプト
│   │   ├── main.py       # メインエントリーポイント
│   │   ├── generate_video_v3.py  # 動画生成V3
│   │   ├── generate_content.py   # 記事生成
│   │   └── ...
│   ├── lib/              # ライブラリ
│   │   ├── gemini_client.py      # Gemini APIクライアント
│   │   └── ...
│   └── config/           # 設定
├── remotion/             # Remotion動画生成
│   ├── src/
│   │   ├── Root.tsx      # Composition定義
│   │   └── compositions/
│   │       ├── SlideVideoV3.tsx  # メインコンポジション
│   │       └── ...
│   └── render.mjs        # レンダリングスクリプト
├── docs/                 # GitHub Pagesサイト
└── .github/workflows/    # GitHub Actions
```

## コーディング規約

- **言語**: 日本語コメント
- **Python**: PEP8準拠、型ヒント必須
- **TypeScript**: ESLint準拠
- **デザイン禁止事項**:
  - 絵文字の使用
  - 紫色系の配色
  - AIっぽい表現（「革新的」「画期的」等）

## 主要機能

1. **情報収集**: Multi-Search 3回検索 / Deep Research API
2. **記事生成**: 20,000文字以上の高品質記事
3. **画像生成**: アニメスタイルアイキャッチ (16:9)
4. **動画生成**: Marpスライド + TTS音声 → Remotion動画
5. **SEO最適化**: メタデータ自動生成
6. **品質評価**: 97%合格ライン
7. **自動投稿**: GitHub Pages

## CLI設定

### 使用モデル
- Codex: `gpt-5.2-codex`
- Gemini: `gemini-3-pro-preview`（推奨）/ `gemini-3-flash-preview`（高速）

### コマンド例

```bash
# Codex
codex "generate_video_v3.pyのエラーハンドリングを改善"

# ヘルパースクリプト
node scripts/codex-helper.js --error "エラーメッセージ"
node scripts/codex-helper.js --file src/scripts/main.py "リファクタリング"
```

## 注意事項

- 動画生成時は必ず `SlideVideoV3` コンポジションを使用
- render.mjs の引数順序: `compositionId, outputPath, propsPath`
- Gemini 2.5系はフォールバックのみ使用
