import React, { useMemo } from "react";
import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
  Audio,
  Img,
  Sequence
} from "remotion";

/**
 * SlideVideoV3 - SlideMovie_WorkFlow方式のタイミングベース動画
 *
 * 特徴:
 * - フレームベースのスライド検出（固定時間ではなく音声の長さに基づく）
 * - 字幕の自動表示
 * - スライドごとの音声再生
 * - スムーズなトランジション
 */

// トピック別カラースキーム
const TOPIC_COLORS: Record<string, { primary: string; secondary: string; bg: string }> = {
  psychology: { primary: "#00b4d8", secondary: "#90e0ef", bg: "#1a1a2e" },
  education: { primary: "#10b981", secondary: "#6ee7b7", bg: "#1a1a2e" },
  startup: { primary: "#f59e0b", secondary: "#fcd34d", bg: "#1a1a2e" },
  investment: { primary: "#14b8a6", secondary: "#5eead4", bg: "#1a1a2e" },
  ai_tools: { primary: "#3b82f6", secondary: "#93c5fd", bg: "#1a1a2e" },
  inclusive_education: { primary: "#06b6d4", secondary: "#67e8f9", bg: "#1a1a2e" },
  weekly_summary: { primary: "#0ea5e9", secondary: "#7dd3fc", bg: "#1a1a2e" }
};

// 型定義
interface Subtitle {
  text: string;
  startFrame: number;
  endFrame: number;
}

interface SlideData {
  type: "title" | "content" | "ending";
  heading: string;
  subheading?: string;
  points?: string[];
  startFrame: number;
  endFrame: number;
  duration: number;
  audioBase64?: string | null;
  subtitles?: Subtitle[];
}

export interface SlideVideoV3Props {
  title: string;
  topic: string;
  fps: number;
  totalFrames: number;
  slides: SlideData[];
  slideImages: string[];
}

// 現在のスライドを見つける
function findCurrentSlide(slides: SlideData[], frame: number): SlideData | null {
  return slides.find(
    slide => frame >= slide.startFrame && frame < slide.endFrame
  ) || null;
}

// 現在の字幕を見つける
function findCurrentSubtitle(subtitles: Subtitle[] | undefined, frame: number): Subtitle | null {
  if (!subtitles) return null;
  return subtitles.find(
    sub => frame >= sub.startFrame && frame < sub.endFrame
  ) || null;
}

// スライドシーン
const SlideScene: React.FC<{
  slide: SlideData;
  slideIndex: number;
  totalSlides: number;
  colors: { primary: string; secondary: string; bg: string };
  backgroundImage?: string;
  globalFrame: number;
}> = ({ slide, slideIndex, totalSlides, colors, backgroundImage, globalFrame }) => {
  const { fps } = useVideoConfig();

  // スライド内のローカルフレーム
  const localFrame = globalFrame - slide.startFrame;
  const slideDuration = slide.endFrame - slide.startFrame;

  // トランジション設定
  const transitionFrames = Math.min(15, slideDuration / 4);

  // フェードイン
  const fadeIn = interpolate(
    localFrame,
    [0, transitionFrames],
    [0, 1],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  // フェードアウト（最後のスライドは完全にフェードしない）
  const isLast = slideIndex === totalSlides - 1;
  const fadeOut = isLast ? 1 : interpolate(
    localFrame,
    [slideDuration - transitionFrames, slideDuration],
    [1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  const opacity = Math.min(fadeIn, fadeOut);

  // Ken Burns エフェクト
  const kenBurnsScale = interpolate(
    localFrame,
    [0, slideDuration],
    [1.05, 1.0],
    { extrapolateRight: "clamp" }
  );

  const kenBurnsX = interpolate(
    localFrame,
    [0, slideDuration],
    [slideIndex % 2 === 0 ? -15 : 15, 0],
    { extrapolateRight: "clamp" }
  );

  // テキストアニメーション
  const textSpring = spring({
    frame: localFrame - 5,
    fps,
    config: { damping: 100, stiffness: 200, mass: 0.5 }
  });

  const headingY = interpolate(textSpring, [0, 1], [30, 0]);
  const headingOpacity = interpolate(textSpring, [0, 1], [0, 1]);

  // 現在の字幕
  const currentSubtitle = findCurrentSubtitle(slide.subtitles, globalFrame);

  return (
    <AbsoluteFill style={{ backgroundColor: colors.bg, opacity }}>
      {/* 背景画像 */}
      {backgroundImage && (
        <AbsoluteFill
          style={{
            transform: `scale(${kenBurnsScale}) translateX(${kenBurnsX}px)`,
          }}
        >
          <Img
            src={backgroundImage}
            style={{
              width: "100%",
              height: "100%",
              objectFit: "cover",
              opacity: 0.5
            }}
          />
          <AbsoluteFill
            style={{
              background: `linear-gradient(to bottom, ${colors.bg}ee 0%, ${colors.bg}88 40%, ${colors.bg}ee 100%)`
            }}
          />
        </AbsoluteFill>
      )}

      {/* コンテンツ */}
      <AbsoluteFill
        style={{
          padding: slide.type === "title" ? 100 : 80,
          justifyContent: slide.type === "title" ? "center" : "flex-start",
          alignItems: slide.type === "title" ? "center" : "flex-start",
          display: "flex",
          flexDirection: "column"
        }}
      >
        {/* スライド番号 */}
        {slide.type === "content" && (
          <div
            style={{
              position: "absolute",
              top: 40,
              right: 60,
              fontSize: 24,
              color: colors.secondary,
              opacity: headingOpacity,
              fontFamily: "sans-serif"
            }}
          >
            {slideIndex + 1} / {totalSlides}
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
            maxWidth: "90%",
            fontFamily: "sans-serif",
            lineHeight: 1.3
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
              opacity: interpolate(localFrame, [10, 25], [0, 1], { extrapolateRight: "clamp" }),
              fontFamily: "sans-serif"
            }}
          >
            {slide.subheading}
          </h2>
        )}

        {/* ポイント */}
        {slide.points && slide.points.length > 0 && (
          <ul style={{ listStyle: "none", padding: 0, marginTop: 40 }}>
            {slide.points.map((point, index) => {
              const pointDelay = 15 + index * 8;
              const pointSpring = spring({
                frame: localFrame - pointDelay,
                fps,
                config: { damping: 100, stiffness: 200, mass: 0.5 }
              });
              const pointOpacity = interpolate(pointSpring, [0, 1], [0, 1]);
              const pointX = interpolate(pointSpring, [0, 1], [40, 0]);

              return (
                <li
                  key={index}
                  style={{
                    fontSize: 32,
                    color: "white",
                    marginBottom: 24,
                    opacity: pointOpacity,
                    transform: `translateX(${pointX}px)`,
                    display: "flex",
                    alignItems: "flex-start",
                    fontFamily: "sans-serif",
                    lineHeight: 1.4
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

        {/* エンディングCTA */}
        {slide.type === "ending" && (
          <div
            style={{
              position: "absolute",
              bottom: 120,
              left: 0,
              right: 0,
              textAlign: "center",
              opacity: interpolate(localFrame, [20, 40], [0, 1], { extrapolateRight: "clamp" })
            }}
          >
            <p style={{ fontSize: 28, color: "rgba(255,255,255,0.8)", fontFamily: "sans-serif" }}>
              ブログで詳しく読む
            </p>
          </div>
        )}
      </AbsoluteFill>

      {/* 字幕 */}
      {currentSubtitle && (
        <div
          style={{
            position: "absolute",
            bottom: 80,
            left: "10%",
            right: "10%",
            textAlign: "center",
            fontSize: 28,
            color: "white",
            fontFamily: "sans-serif",
            fontWeight: 600,
            textShadow: "2px 2px 4px rgba(0,0,0,0.8)",
            lineHeight: 1.5,
            backgroundColor: "rgba(0,0,0,0.5)",
            padding: "12px 24px",
            borderRadius: 8,
            opacity: interpolate(
              globalFrame,
              [currentSubtitle.startFrame, currentSubtitle.startFrame + 5, currentSubtitle.endFrame - 5, currentSubtitle.endFrame],
              [0, 1, 1, 0],
              { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
            )
          }}
        >
          {currentSubtitle.text}
        </div>
      )}

      {/* プログレスバー */}
      <div
        style={{
          position: "absolute",
          bottom: 0,
          left: 0,
          width: `${(localFrame / slideDuration) * 100}%`,
          height: 6,
          backgroundColor: colors.primary
        }}
      />
    </AbsoluteFill>
  );
};

// メインコンポーネント
export const SlideVideoV3: React.FC<SlideVideoV3Props> = ({
  title,
  topic,
  fps,
  totalFrames,
  slides,
  slideImages
}) => {
  const frame = useCurrentFrame();
  const colors = TOPIC_COLORS[topic] || TOPIC_COLORS.ai_tools;

  // デバッグログ
  console.log('[SlideVideoV3] Rendering:', {
    title,
    topic,
    fps,
    totalFrames,
    slidesCount: slides?.length,
    imagesCount: slideImages?.length,
    currentFrame: frame
  });

  // 現在のスライドを見つける
  const currentSlide = useMemo(() => {
    return findCurrentSlide(slides || [], frame);
  }, [slides, frame]);

  const currentSlideIndex = useMemo(() => {
    if (!currentSlide || !slides) return 0;
    return slides.findIndex(s => s.startFrame === currentSlide.startFrame);
  }, [currentSlide, slides]);

  // スライドがない場合
  if (!slides || slides.length === 0) {
    console.error('[SlideVideoV3] No slides provided');
    return (
      <AbsoluteFill style={{ backgroundColor: colors.bg }}>
        <div style={{ color: 'white', textAlign: 'center', marginTop: 200, fontSize: 32 }}>
          No slides to display
        </div>
      </AbsoluteFill>
    );
  }

  // 現在のスライドがない場合（フレーム範囲外）
  if (!currentSlide) {
    // 最後のスライドを表示
    const lastSlide = slides[slides.length - 1];
    return (
      <AbsoluteFill style={{ backgroundColor: colors.bg }}>
        <SlideScene
          slide={lastSlide}
          slideIndex={slides.length - 1}
          totalSlides={slides.length}
          colors={colors}
          backgroundImage={slideImages[slides.length - 1]}
          globalFrame={frame}
        />
      </AbsoluteFill>
    );
  }

  // 背景画像
  const backgroundImage = slideImages && slideImages[currentSlideIndex]
    ? slideImages[currentSlideIndex]
    : undefined;

  return (
    <AbsoluteFill style={{ backgroundColor: colors.bg }}>
      {/* 現在のスライドシーン */}
      <SlideScene
        slide={currentSlide}
        slideIndex={currentSlideIndex}
        totalSlides={slides.length}
        colors={colors}
        backgroundImage={backgroundImage}
        globalFrame={frame}
      />

      {/* スライドごとの音声 */}
      {slides.map((slide, index) => {
        if (!slide.audioBase64) return null;

        return (
          <Sequence
            key={`audio-${index}`}
            from={slide.startFrame}
            durationInFrames={slide.endFrame - slide.startFrame}
          >
            <Audio
              src={slide.audioBase64}
              volume={1}
            />
          </Sequence>
        );
      })}
    </AbsoluteFill>
  );
};

export default SlideVideoV3;
