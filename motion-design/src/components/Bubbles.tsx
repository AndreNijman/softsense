import { AbsoluteFill, useCurrentFrame } from "remotion";
import { rand, randRange } from "../lib/rand";

// Rising bubbles — all state derived from the bubble index (+ frame for motion)
// so nothing flickers across the per-frame re-render.
export const Bubbles: React.FC<{ count?: number; opacity?: number }> = ({
  count = 34,
  opacity = 1,
}) => {
  const f = useCurrentFrame();
  const range = 1320;
  return (
    <AbsoluteFill style={{ pointerEvents: "none", opacity }}>
      {Array.from({ length: count }).map((_, i) => {
        const big = rand(i * 91 + 2) > 0.85;
        const size = big
          ? randRange(i * 7 + 1, 11, 20)
          : randRange(i * 7 + 1, 3, 9);
        const x0 = rand(i * 13 + 4) * 1920;
        const speed = randRange(i * 5 + 6, 16, 44); // px/s
        const phase = rand(i * 3 + 9) * range;
        const y =
          1140 - (((f * speed) / 30 + phase) % range);
        const wob =
          Math.sin(f * 0.035 + i * 2.1) * randRange(i * 9 + 8, 4, 16);
        const op = randRange(i * 11 + 5, 0.12, 0.4);
        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: x0 + wob,
              top: y,
              width: size,
              height: size,
              borderRadius: "50%",
              opacity: op,
              background:
                "radial-gradient(circle at 32% 28%, rgba(235,255,251,0.95), rgba(150,225,214,0.18) 55%, rgba(120,200,200,0) 72%)",
              border: "1px solid rgba(210,250,244,0.28)",
              boxShadow: "0 0 6px rgba(150,235,222,0.25)",
            }}
          />
        );
      })}
    </AbsoluteFill>
  );
};
