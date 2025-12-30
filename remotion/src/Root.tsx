import { Composition } from "remotion";
import { BlogVideo, BlogVideoProps } from "./compositions/BlogVideo";

// デフォルトのブログデータ（プレビュー用）
const defaultBlogData: BlogVideoProps = {
  title: "AIツールの最新動向2025",
  summary: "2025年のAIツールトレンドを詳しく解説します。",
  points: [
    "生成AIの進化と実用化",
    "業務効率化ツールの普及",
    "セキュリティとプライバシーの重要性"
  ],
  topic: "ai_tools",
  date: "2025年12月30日",
  authorName: "if(塾) Blog"
};

export const RemotionRoot: React.FC = () => {
  return (
    <>
      {/* メインのブログ動画 - 30秒版 */}
      <Composition
        id="BlogVideo"
        component={BlogVideo}
        durationInFrames={900}  // 30秒 @ 30fps
        fps={30}
        width={1920}
        height={1080}
        defaultProps={defaultBlogData}
      />

      {/* ショート動画 - 15秒版 */}
      <Composition
        id="BlogVideoShort"
        component={BlogVideo}
        durationInFrames={450}  // 15秒 @ 30fps
        fps={30}
        width={1080}
        height={1920}  // 縦型（Shorts/Reels用）
        defaultProps={{
          ...defaultBlogData,
          isShort: true
        }}
      />
    </>
  );
};
