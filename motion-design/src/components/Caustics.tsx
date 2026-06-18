import { AbsoluteFill, useCurrentFrame } from "remotion";
import { C } from "../lib/theme";

// Animated underwater light caustics via SVG feTurbulence. Seed is FIXED
// (changing it per frame would flicker); motion comes from translating the
// filtered layer and gently breathing baseFrequency. Renders reliably headless.
export const Caustics: React.FC<{
  id: string;
  opacity?: number;
  tint?: string;
  speed?: number;
  scale?: number;
}> = ({ id, opacity = 0.5, tint = C.tealBright, speed = 1, scale = 1 }) => {
  const f = useCurrentFrame();
  const bf = (0.0095 + 0.0015 * Math.sin(f * 0.018)) / scale;
  const tx = (f * 0.22 * speed) % 480;
  const ty = (f * 0.12 * speed) % 480;
  return (
    <AbsoluteFill
      style={{ mixBlendMode: "screen", opacity, pointerEvents: "none" }}
    >
      <svg
        width="100%"
        height="100%"
        viewBox="0 0 1920 1080"
        preserveAspectRatio="xMidYMid slice"
      >
        <defs>
          <filter
            id={id}
            x="-25%"
            y="-25%"
            width="150%"
            height="150%"
            colorInterpolationFilters="sRGB"
          >
            <feTurbulence
              type="fractalNoise"
              baseFrequency={bf}
              numOctaves={2}
              seed={11}
              stitchTiles="stitch"
              result="t"
            />
            {/* keep only the bright ridges of the noise -> alpha */}
            <feColorMatrix
              in="t"
              type="matrix"
              values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0.95 0.95 0.95 0 -1.18"
              result="a"
            />
            <feComponentTransfer in="a" result="b">
              <feFuncA type="gamma" amplitude="1" exponent="2.6" offset="0" />
            </feComponentTransfer>
            <feFlood floodColor={tint} result="col" />
            <feComposite in="col" in2="b" operator="in" result="caustic" />
            <feGaussianBlur in="caustic" stdDeviation="1.1" />
          </filter>
        </defs>
        <g transform={`translate(${-240 + tx} ${-240 + ty})`}>
          <rect x="-480" y="-480" width="2880" height="2040" filter={`url(#${id})`} />
        </g>
      </svg>
    </AbsoluteFill>
  );
};
