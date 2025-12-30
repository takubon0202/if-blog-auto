import React from "react";
import {
  AbsoluteFill,
  Sequence,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
  Easing
} from "remotion";

// トピック別カラースキーム
const TOPIC_COLORS: Record<string, { primary: string; accent: string; name: string }> = {
  psychology: { primary: "#2b6cb0", accent: "#4299e1", name: "心理学" },
  education: { primary: "#2f855a", accent: "#48bb78", name: "教育" },
  startup: { primary: "#c05621", accent: "#ed8936", name: "スタートアップ" },
  investment: { primary: "#744210", accent: "#d69e2e", name: "投資" },
  ai_tools: { primary: "#1a365d", accent: "#3182ce", name: "AIツール" },
  inclusive_education: { primary: "#285e61", accent: "#38b2ac", name: "インクルーシブ教育" },
  weekly_summary: { primary: "#553c9a", accent: "#805ad5", name: "週間総括" }
};

export interface BlogVideoProps {
  title: string;
  summary: string;
  points: string[];
  topic: string;
  date: string;
  authorName?: string;
  isShort?: boolean;
}

// タイトルシーン
const TitleScene: React.FC<{
  title: string;
  topic: string;
  colors: { primary: string; accent: string; name: string };
}> = ({ title, topic, colors }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const titleOpacity = interpolate(frame, [0, 20], [0, 1], {
    extrapolateRight: "clamp"
  });

  const titleY = spring({
    frame,
    fps,
    config: { damping: 100, stiffness: 200, mass: 0.5 }
  });

  const labelScale = spring({
    frame: frame - 10,
    fps,
    config: { damping: 100, stiffness: 200, mass: 0.5 }
  });

  return (
    <AbsoluteFill
      style={{
        background: `linear-gradient(135deg, ${colors.primary} 0%, ${colors.accent} 100%)`,
        justifyContent: "center",
        alignItems: "center",
        padding: 80
      }}
    >
      {/* トピックラベル */}
      <div
        style={{
          position: "absolute",
          top: 60,
          left: 60,
          backgroundColor: "rgba(255,255,255,0.2)",
          padding: "12px 24px",
          borderRadius: 8,
          transform: `scale(${labelScale})`,
          color: "white",
          fontSize: 24,
          fontWeight: 600
        }}
      >
        {colors.name}
      </div>

      {/* メインタイトル */}
      <h1
        style={{
          color: "white",
          fontSize: 72,
          fontWeight: 800,
          textAlign: "center",
          opacity: titleOpacity,
          transform: `translateY(${interpolate(titleY, [0, 1], [50, 0])}px)`,
          textShadow: "0 4px 20px rgba(0,0,0,0.3)",
          lineHeight: 1.3,
          maxWidth: "90%"
        }}
      >
        {title}
      </h1>
    </AbsoluteFill>
  );
};

// ポイントシーン
const PointScene: React.FC<{
  point: string;
  index: number;
  colors: { primary: string; accent: string };
}> = ({ point, index, colors }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const slideIn = spring({
    frame,
    fps,
    config: { damping: 100, stiffness: 200, mass: 0.5 }
  });

  const numberScale = spring({
    frame: frame - 5,
    fps,
    config: { damping: 80, stiffness: 300, mass: 0.3 }
  });

  return (
    <AbsoluteFill
      style={{
        backgroundColor: "#f7fafc",
        justifyContent: "center",
        alignItems: "center",
        padding: 80
      }}
    >
      {/* 番号 */}
      <div
        style={{
          position: "absolute",
          top: 80,
          left: 80,
          width: 120,
          height: 120,
          borderRadius: "50%",
          backgroundColor: colors.primary,
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          transform: `scale(${numberScale})`,
          boxShadow: "0 8px 30px rgba(0,0,0,0.15)"
        }}
      >
        <span style={{ color: "white", fontSize: 64, fontWeight: 800 }}>
          {index + 1}
        </span>
      </div>

      {/* ポイントテキスト */}
      <div
        style={{
          transform: `translateX(${interpolate(slideIn, [0, 1], [100, 0])}px)`,
          opacity: slideIn,
          maxWidth: "80%"
        }}
      >
        <p
          style={{
            fontSize: 56,
            fontWeight: 700,
            color: "#1a202c",
            textAlign: "center",
            lineHeight: 1.5
          }}
        >
          {point}
        </p>
      </div>
    </AbsoluteFill>
  );
};

// サマリーシーン
const SummaryScene: React.FC<{
  summary: string;
  colors: { primary: string; accent: string };
}> = ({ summary, colors }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const fadeIn = interpolate(frame, [0, 20], [0, 1], {
    extrapolateRight: "clamp"
  });

  return (
    <AbsoluteFill
      style={{
        backgroundColor: "#1a202c",
        justifyContent: "center",
        alignItems: "center",
        padding: 100
      }}
    >
      {/* 装飾 */}
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          width: "100%",
          height: 8,
          background: `linear-gradient(90deg, ${colors.primary}, ${colors.accent})`
        }}
      />

      <p
        style={{
          fontSize: 48,
          color: "white",
          textAlign: "center",
          lineHeight: 1.8,
          opacity: fadeIn,
          maxWidth: "85%"
        }}
      >
        {summary}
      </p>
    </AbsoluteFill>
  );
};

// エンディングシーン
const EndingScene: React.FC<{
  authorName: string;
  date: string;
  colors: { primary: string; accent: string };
}> = ({ authorName, date, colors }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const logoScale = spring({
    frame,
    fps,
    config: { damping: 80, stiffness: 200, mass: 0.5 }
  });

  const textOpacity = interpolate(frame, [15, 35], [0, 1], {
    extrapolateRight: "clamp"
  });

  return (
    <AbsoluteFill
      style={{
        background: `linear-gradient(135deg, ${colors.primary} 0%, ${colors.accent} 100%)`,
        justifyContent: "center",
        alignItems: "center"
      }}
    >
      {/* ロゴ/著者名 */}
      <div
        style={{
          transform: `scale(${logoScale})`,
          marginBottom: 40
        }}
      >
        <h2
          style={{
            fontSize: 72,
            fontWeight: 800,
            color: "white",
            textShadow: "0 4px 20px rgba(0,0,0,0.3)"
          }}
        >
          {authorName}
        </h2>
      </div>

      {/* 日付 */}
      <p
        style={{
          fontSize: 32,
          color: "rgba(255,255,255,0.8)",
          opacity: textOpacity
        }}
      >
        {date}
      </p>

      {/* CTA */}
      <div
        style={{
          position: "absolute",
          bottom: 80,
          opacity: textOpacity
        }}
      >
        <p style={{ fontSize: 28, color: "rgba(255,255,255,0.9)" }}>
          ブログで詳しく読む
        </p>
      </div>
    </AbsoluteFill>
  );
};

// メインのBlogVideoコンポーネント
export const BlogVideo: React.FC<BlogVideoProps> = ({
  title,
  summary,
  points,
  topic,
  date,
  authorName = "if(塾) Blog",
  isShort = false
}) => {
  const { durationInFrames, fps } = useVideoConfig();
  const colors = TOPIC_COLORS[topic] || TOPIC_COLORS.ai_tools;

  // シーンの長さを計算（フレーム単位）
  const titleDuration = isShort ? 120 : 180;  // 4秒 or 6秒
  const summaryDuration = isShort ? 90 : 150;  // 3秒 or 5秒
  const pointDuration = isShort ? 60 : 120;    // 2秒 or 4秒
  const endingDuration = isShort ? 90 : 150;   // 3秒 or 5秒

  // 使用するポイント数を制限
  const displayPoints = isShort ? points.slice(0, 2) : points.slice(0, 3);

  let currentFrame = 0;

  return (
    <AbsoluteFill style={{ backgroundColor: "#1a202c" }}>
      {/* タイトルシーン */}
      <Sequence from={currentFrame} durationInFrames={titleDuration}>
        <TitleScene title={title} topic={topic} colors={colors} />
      </Sequence>

      {currentFrame += titleDuration}

      {/* サマリーシーン */}
      <Sequence from={currentFrame} durationInFrames={summaryDuration}>
        <SummaryScene summary={summary} colors={colors} />
      </Sequence>

      {currentFrame += summaryDuration}

      {/* ポイントシーン */}
      {displayPoints.map((point, index) => {
        const startFrame = currentFrame + index * pointDuration;
        return (
          <Sequence
            key={index}
            from={startFrame}
            durationInFrames={pointDuration}
          >
            <PointScene point={point} index={index} colors={colors} />
          </Sequence>
        );
      })}

      {currentFrame += displayPoints.length * pointDuration}

      {/* エンディングシーン */}
      <Sequence from={currentFrame} durationInFrames={endingDuration}>
        <EndingScene authorName={authorName} date={date} colors={colors} />
      </Sequence>
    </AbsoluteFill>
  );
};
