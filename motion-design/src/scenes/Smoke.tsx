import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";

// Trivial 30-frame composition to smoke-test the full render pipeline
// (Node 24 + system Chromium 148) before any real content exists.
export const Smoke: React.FC = () => {
  const frame = useCurrentFrame();
  const x = interpolate(frame, [0, 29], [-200, 200]);
  return (
    <AbsoluteFill
      style={{
        background: "linear-gradient(180deg, #0a2540 0%, #0e7c7b 100%)",
        justifyContent: "center",
        alignItems: "center",
      }}
    >
      <div
        style={{
          transform: `translateX(${x}px)`,
          width: 160,
          height: 160,
          borderRadius: 24,
          background: "#5fe3c0",
        }}
      />
    </AbsoluteFill>
  );
};
