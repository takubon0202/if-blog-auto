import React from "react";
import {
  AbsoluteFill,
  Sequence,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
  Audio,
  Img,
  staticFile,
  Easing
} from "remotion";

// トピック別カラースキーム（紫禁止）
const TOPIC_COLORS: Record<string, { primary: string; secondary: string; bg: string }> = {
  psychology: { primary: "#00b4d8", secondary: "#90e0ef", bg: "#1a1a2e" },
  education: { primary: "#10b981", secondary: "#6ee7b7", bg: "#1a1a2e" },
  startup: { primary: "#f59e0b", secondary: "#fcd34d", bg: "#1a1a2e" },
  investment: { primary: "#14b8a6", secondary: "#5eead4", bg: "#1a1a2e" },
  ai_tools: { primary: "#3b82f6", secondary: "#93c5fd", bg: "#1a1a2e" },
  inclusive_education: { primary: "#06b6d4", secondary: "#67e8f9", bg: "#1a1a2e" },
  weekly_summary: { primary: "#0ea5e9", secondary: "#7dd3fc", bg: "#1a1a2e" }
};

export interface SlideVideoProps {
  title: string;
  slides: SlideData[];
  topic: string;
  authorName?: string;
  audioUrl?: string | null;
  slideImagePrefix?: string;  // スライド画像のプレフィックス
  slideDuration?: number;     // 各スライドの表示時間（秒）
}

interface SlideData {
  heading: string;
  subheading?: string;
  points?: string[];
  type: "title" | "content" | "ending";
  imageUrl?: string;
  narrationText?: string;
}

// トランジションタイプ
type TransitionType = "fade" | "slide-left" | "slide-right" | "zoom" | "ken-burns";

// スライドシーン（Ken Burnsエフェクト付き）
const SlideScene: React.FC<{
  slide: SlideData;
  slideNumber: number;
  totalSlides: number;
  colors: { primary: string; secondary: string; bg: string };
  transition: TransitionType;
}> = ({ slide, slideNumber, totalSlides, colors, transition }) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  // トランジションのイージング
  const transitionDuration = 15; // 0.5秒

  // Ken Burns エフェクト（ズーム + パン）
  const kenBurnsScale = interpolate(
    frame,
    [0, durationInFrames],
    [1.05, 1.0],
    { extrapolateRight: "clamp" }
  );

  const kenBurnsX = interpolate(
    frame,
    [0, durationInFrames],
    [slideNumber % 2 === 0 ? -10 : 10, 0],
    { extrapolateRight: "clamp" }
  );

  // フェードイン/アウト
  const opacity = interpolate(
    frame,
    [0, transitionDuration, durationInFrames - transitionDuration, durationInFrames],
    [0, 1, 1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  // スライドイン（左から）
  const slideX = interpolate(
    frame,
    [0, transitionDuration],
    [transition === "slide-left" ? -100 : transition === "slide-right" ? 100 : 0, 0],
    { extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) }
  );

  // テキストアニメーション
  const textSpring = spring({
    frame: frame - 10,
    fps,
    config: { damping: 100, stiffness: 200, mass: 0.5 }
  });

  const headingY = interpolate(textSpring, [0, 1], [30, 0]);
  const headingOpacity = interpolate(textSpring, [0, 1], [0, 1]);

  // ポイントのスタガー表示
  const pointsDelay = 20;

  return (
    <AbsoluteFill
      style={{
        backgroundColor: colors.bg,
        opacity,
        transform: `translateX(${slideX}px)`
      }}
    >
      {/* 背景画像（Ken Burns エフェクト） */}
      {slide.imageUrl && (
        <AbsoluteFill
          style={{
            transform: `scale(${kenBurnsScale}) translateX(${kenBurnsX}px)`,
            opacity: 0.7
          }}
        >
          <Img
            src={staticFile(slide.imageUrl)}
            style={{
              width: "100%",
              height: "100%",
              objectFit: "cover"
            }}
          />
          {/* グラデーションオーバーレイ */}
          <AbsoluteFill
            style={{
              background: `linear-gradient(to right, ${colors.bg}ee 0%, ${colors.bg}99 50%, ${colors.bg}ee 100%)`
            }}
          />
        </AbsoluteFill>
      )}

      {/* コンテンツ */}
      <AbsoluteFill
        style={{
          padding: slide.type === "title" ? 100 : 80,
          justifyContent: slide.type === "title" ? "center" : "flex-start",
          alignItems: slide.type === "title" ? "center" : "flex-start"
        }}
      >
        {/* スライド番号 */}
        {slide.type !== "title" && slide.type !== "ending" && (
          <div
            style={{
              position: "absolute",
              top: 40,
              right: 60,
              fontSize: 24,
              color: colors.secondary,
              opacity: headingOpacity
            }}
          >
            {slideNumber} / {totalSlides}
          </div>
        )}

        {/* 見出し */}
        <h1
          style={{
            fontSize: slide.type === "title" ? 72 : 56,
            fontWeight: 800,
            color: colors.primary,
            textAlign: slide.type === "title" ? "center" : "left",
            marginBottom: 24,
            opacity: headingOpacity,
            transform: `translateY(${headingY}px)`,
            textShadow: "0 4px 20px rgba(0,0,0,0.5)",
            maxWidth: "90%"
          }}
        >
          {slide.heading}
        </h1>

        {/* サブ見出し */}
        {slide.subheading && (
          <h2
            style={{
              fontSize: slide.type === "title" ? 40 : 32,
              fontWeight: 600,
              color: colors.secondary,
              textAlign: slide.type === "title" ? "center" : "left",
              marginBottom: 40,
              opacity: interpolate(frame, [15, 30], [0, 1], { extrapolateRight: "clamp" })
            }}
          >
            {slide.subheading}
          </h2>
        )}

        {/* ポイント（箇条書き） */}
        {slide.points && slide.points.length > 0 && (
          <ul
            style={{
              listStyle: "none",
              padding: 0,
              marginTop: 40
            }}
          >
            {slide.points.map((point, index) => {
              const pointFrame = frame - pointsDelay - index * 8;
              const pointSpring = spring({
                frame: pointFrame,
                fps,
                config: { damping: 100, stiffness: 200, mass: 0.5 }
              });
              const pointOpacity = interpolate(pointSpring, [0, 1], [0, 1]);
              const pointX = interpolate(pointSpring, [0, 1], [50, 0]);

              return (
                <li
                  key={index}
                  style={{
                    fontSize: 32,
                    color: "white",
                    marginBottom: 20,
                    opacity: pointOpacity,
                    transform: `translateX(${pointX}px)`,
                    display: "flex",
                    alignItems: "flex-start"
                  }}
                >
                  <span
                    style={{
                      display: "inline-block",
                      width: 12,
                      height: 12,
                      backgroundColor: colors.primary,
                      borderRadius: "50%",
                      marginRight: 16,
                      marginTop: 10,
                      flexShrink: 0
                    }}
                  />
                  {point}
                </li>
              );
            })}
          </ul>
        )}

        {/* エンディング時の著者名 */}
        {slide.type === "ending" && (
          <div
            style={{
              position: "absolute",
              bottom: 100,
              left: 0,
              right: 0,
              textAlign: "center",
              opacity: interpolate(frame, [20, 40], [0, 1], { extrapolateRight: "clamp" })
            }}
          >
            <p style={{ fontSize: 28, color: "rgba(255,255,255,0.8)" }}>
              ブログで詳しく読む
            </p>
          </div>
        )}
      </AbsoluteFill>

      {/* 下部プログレスバー */}
      <div
        style={{
          position: "absolute",
          bottom: 0,
          left: 0,
          width: `${(frame / durationInFrames) * 100}%`,
          height: 4,
          backgroundColor: colors.primary
        }}
      />
    </AbsoluteFill>
  );
};

// メインのSlideVideoコンポーネント
export const SlideVideo: React.FC<SlideVideoProps> = ({
  title,
  slides,
  topic,
  authorName = "if(塾) Blog",
  audioUrl = null,
  slideImagePrefix = "slide_",
  slideDuration = 5
}) => {
  const { fps } = useVideoConfig();
  const colors = TOPIC_COLORS[topic] || TOPIC_COLORS.ai_tools;

  // 各スライドの長さ（フレーム単位）
  const slideFrames = slideDuration * fps;

  // トランジションパターン
  const transitions: TransitionType[] = ["fade", "slide-left", "ken-burns", "slide-right", "zoom"];

  const sequences: JSX.Element[] = [];

  // オーディオトラック
  if (audioUrl) {
    sequences.push(
      <Audio
        key="audio"
        src={staticFile(audioUrl)}
        volume={1}
      />
    );
  }

  // 各スライドのシーケンス
  let currentFrame = 0;
  slides.forEach((slide, index) => {
    const transition = transitions[index % transitions.length];

    // スライド用の画像URL設定
    const slideWithImage: SlideData = {
      ...slide,
      imageUrl: slide.imageUrl || `slides/${slideImagePrefix}${String(index + 1).padStart(2, "0")}.png`
    };

    sequences.push(
      <Sequence
        key={`slide-${index}`}
        from={currentFrame}
        durationInFrames={slideFrames}
      >
        <SlideScene
          slide={slideWithImage}
          slideNumber={index + 1}
          totalSlides={slides.length}
          colors={colors}
          transition={transition}
        />
      </Sequence>
    );

    currentFrame += slideFrames;
  });

  return (
    <AbsoluteFill style={{ backgroundColor: colors.bg }}>
      {sequences}
    </AbsoluteFill>
  );
};

// デフォルトエクスポート
export default SlideVideo;
