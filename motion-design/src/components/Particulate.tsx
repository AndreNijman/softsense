import { AbsoluteFill, useCurrentFrame } from "remotion";
import { rand, randRange } from "../lib/rand";

// Suspended marine snow drifting slowly — depth atmosphere. Deterministic.
export const Particulate: React.FC<{ count?: number; opacity?: number }> = ({
  count = 90,
  opacity = 0.5,
}) => {
  const f = useCurrentFrame();
  return (
    <AbsoluteFill style={{ pointerEvents: "none", opacity }}>
      {Array.from({ length: count }).map((_, i) => {
        const depth = randRange(i * 3 + 1, 0.3, 1); // parallax factor
        const size = randRange(i * 5 + 2, 1, 3.2) * (0.6 + depth);
        const x0 = rand(i * 17 + 3) * 1980;
        const y0 = rand(i * 29 + 7) * 1140;
        const driftX = Math.sin(f * 0.01 * depth + i) * 22 * depth;
        const driftY = ((f * 0.18 * depth) % 1180);
        const x = (x0 + driftX) % 1980;
        const y = (y0 + driftY) % 1180;
        const op = randRange(i * 11 + 6, 0.1, 0.5) * depth;
        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: x - 30,
              top: y - 30,
              width: size,
              height: size,
              borderRadius: "50%",
              background: "rgba(196,232,228,1)",
              opacity: op,
              filter: depth < 0.55 ? "blur(1.2px)" : "none",
            }}
          />
        );
      })}
    </AbsoluteFill>
  );
};
