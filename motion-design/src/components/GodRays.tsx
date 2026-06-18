import { AbsoluteFill, useCurrentFrame } from "remotion";
import { randRange } from "../lib/rand";

// Soft volumetric light shafts raking down from the surface, swaying slowly.
export const GodRays: React.FC<{ opacity?: number; count?: number }> = ({
  opacity = 0.42,
  count = 6,
}) => {
  const f = useCurrentFrame();
  return (
    <AbsoluteFill
      style={{
        mixBlendMode: "screen",
        opacity,
        pointerEvents: "none",
        overflow: "hidden",
      }}
    >
      {Array.from({ length: count }).map((_, i) => {
        const left = randRange(i * 31 + 1, -8, 88); // vw
        const w = randRange(i * 17 + 3, 130, 320);
        const angle = randRange(i * 23 + 5, -16, -6);
        const sway = Math.sin(f * 0.011 + i * 1.7) * 1.6;
        const breathe = 0.6 + 0.4 * (0.5 + 0.5 * Math.sin(f * 0.02 + i));
        const a = randRange(i * 13 + 7, 0.1, 0.26) * breathe;
        return (
          <div
            key={i}
            style={{
              position: "absolute",
              top: -260,
              left: `${left}vw`,
              width: w,
              height: 1900,
              transformOrigin: "top center",
              transform: `rotate(${angle + sway}deg)`,
              background: `linear-gradient(to bottom, rgba(180,248,236,${a}) 0%, rgba(120,220,210,${a * 0.4}) 38%, rgba(0,0,0,0) 74%)`,
              filter: "blur(46px)",
            }}
          />
        );
      })}
    </AbsoluteFill>
  );
};
