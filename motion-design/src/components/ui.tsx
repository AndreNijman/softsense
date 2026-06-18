import {
  AbsoluteFill,
  Easing,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { C, F } from "../lib/theme";
import { rand } from "../lib/rand";

const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

// ---- small reveal helpers ---------------------------------------------------
export const useSpringIn = (delay = 0, damping = 200) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  return spring({ frame: frame - delay, fps, config: { damping }, durationInFrames: 28 });
};

// ---- Eyebrow / section label -----------------------------------------------
export const Eyebrow: React.FC<{
  children: React.ReactNode;
  no?: string;
  delay?: number;
}> = ({ children, no, delay = 0 }) => {
  const p = useSpringIn(delay);
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: 16,
        opacity: p,
        transform: `translateX(${interpolate(p, [0, 1], [-18, 0])}px)`,
      }}
    >
      <div style={{ width: 34, height: 3, background: C.teal }} />
      {no && (
        <span
          style={{
            fontFamily: F.mono,
            fontWeight: 500,
            fontSize: 18,
            color: C.teal,
            letterSpacing: 1,
          }}
        >
          {no}
        </span>
      )}
      <span
        style={{
          fontFamily: F.mono,
          fontWeight: 500,
          fontSize: 18,
          letterSpacing: 5.5,
          textTransform: "uppercase",
          color: C.mist,
        }}
      >
        {children}
      </span>
    </div>
  );
};

// ---- Kinetic counting number ------------------------------------------------
export const KineticNumber: React.FC<{
  from?: number;
  to: number;
  start: number;
  end: number;
  format?: (n: number) => string;
  style?: React.CSSProperties;
}> = ({ from = 0, to, start, end, format = (n) => Math.round(n).toString(), style }) => {
  const frame = useCurrentFrame();
  const p = interpolate(frame, [start, end], [0, 1], {
    ...clamp,
    easing: Easing.out(Easing.cubic),
  });
  return <span style={{ fontFamily: F.mono, ...style }}>{format(from + (to - from) * p)}</span>;
};

// ---- Stat block -------------------------------------------------------------
export const Stat: React.FC<{
  value: React.ReactNode;
  label: string;
  sub?: string;
  delay?: number;
}> = ({ value, label, sub, delay = 0 }) => {
  const p = useSpringIn(delay, 180);
  return (
    <div style={{ opacity: p, transform: `translateY(${interpolate(p, [0, 1], [22, 0])}px)` }}>
      <div
        style={{
          fontFamily: F.mono,
          fontWeight: 700,
          fontSize: 78,
          lineHeight: 1,
          color: C.tealBright,
          letterSpacing: -1,
        }}
      >
        {value}
      </div>
      <div
        style={{
          marginTop: 14,
          fontFamily: F.display,
          fontWeight: 600,
          fontSize: 21,
          color: C.ice,
        }}
      >
        {label}
      </div>
      {sub && (
        <div
          style={{
            marginTop: 6,
            fontFamily: F.mono,
            fontSize: 15,
            lineHeight: 1.45,
            color: C.faint,
            maxWidth: 280,
          }}
        >
          {sub}
        </div>
      )}
    </div>
  );
};

// ---- HUD panel with corner brackets ----------------------------------------
const Corner: React.FC<{ pos: string }> = ({ pos }) => {
  const [v, h] = pos.split("-");
  return (
    <div
      style={{
        position: "absolute",
        [v]: -1,
        [h]: -1,
        width: 22,
        height: 22,
        [`border${v[0].toUpperCase()}${v.slice(1)}`]: `2px solid ${C.teal}`,
        [`border${h[0].toUpperCase()}${h.slice(1)}`]: `2px solid ${C.teal}`,
      } as React.CSSProperties}
    />
  );
};

export const Panel: React.FC<{
  children?: React.ReactNode;
  header?: string;
  style?: React.CSSProperties;
  reveal?: number; // 0..1 wipe-in
}> = ({ children, header, style, reveal = 1 }) => {
  return (
    <div
      style={{
        position: "relative",
        border: `1px solid ${C.hair}`,
        background: "rgba(6,28,44,0.42)",
        backdropFilter: "blur(2px)",
        boxShadow: "0 30px 80px rgba(0,0,0,0.45)",
        clipPath: `inset(0 ${(1 - reveal) * 100}% 0 0)`,
        ...style,
      }}
    >
      <Corner pos="top-left" />
      <Corner pos="top-right" />
      <Corner pos="bottom-left" />
      <Corner pos="bottom-right" />
      {header && (
        <div
          style={{
            position: "absolute",
            top: -12,
            left: 18,
            padding: "2px 10px",
            background: C.deep,
            border: `1px solid ${C.hair}`,
            fontFamily: F.mono,
            fontSize: 13,
            letterSpacing: 3,
            textTransform: "uppercase",
            color: C.teal,
          }}
        >
          {header}
        </div>
      )}
      {children}
    </div>
  );
};

// ---- Callout: dot + connector + label --------------------------------------
export const Callout: React.FC<{
  title: string;
  body?: string;
  align?: "left" | "right";
  delay?: number;
  width?: number;
}> = ({ title, body, align = "left", delay = 0, width = 320 }) => {
  const p = useSpringIn(delay, 160);
  const right = align === "right";
  return (
    <div
      style={{
        display: "flex",
        flexDirection: right ? "row-reverse" : "row",
        alignItems: "flex-start",
        gap: 12,
        width,
        opacity: p,
        transform: `translateX(${interpolate(p, [0, 1], [right ? 16 : -16, 0])}px)`,
        textAlign: right ? "right" : "left",
      }}
    >
      <div style={{ marginTop: 6, display: "flex", alignItems: "center", flexDirection: right ? "row-reverse" : "row" }}>
        <div style={{ width: 8, height: 8, borderRadius: "50%", background: C.teal, boxShadow: `0 0 10px ${C.teal}` }} />
        <div style={{ width: 26, height: 1, background: C.hair }} />
      </div>
      <div>
        <div style={{ fontFamily: F.display, fontWeight: 700, fontSize: 21, color: C.ice }}>{title}</div>
        {body && (
          <div style={{ marginTop: 4, fontFamily: F.mono, fontSize: 14.5, lineHeight: 1.5, color: C.faint }}>
            {body}
          </div>
        )}
      </div>
    </div>
  );
};

// ---- Chip -------------------------------------------------------------------
export const Chip: React.FC<{ label: string; delay?: number }> = ({ label, delay = 0 }) => {
  const p = useSpringIn(delay, 160);
  return (
    <div
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 9,
        padding: "9px 16px",
        border: `1px solid ${C.hair}`,
        borderRadius: 999,
        background: "rgba(8,34,52,0.4)",
        opacity: p,
        transform: `translateY(${interpolate(p, [0, 1], [12, 0])}px)`,
      }}
    >
      <div style={{ width: 7, height: 7, borderRadius: "50%", background: C.teal }} />
      <span style={{ fontFamily: F.mono, fontSize: 16, color: C.ice, letterSpacing: 0.4 }}>{label}</span>
    </div>
  );
};

// ---- readability scrim ------------------------------------------------------
export const Scrim: React.FC<{ from?: string; opacity?: number; dir?: number }> = ({
  from = "left",
  opacity = 0.7,
  dir,
}) => {
  const angle = dir ?? (from === "left" ? 90 : from === "right" ? 270 : from === "bottom" ? 0 : 180);
  return (
    <AbsoluteFill
      style={{
        pointerEvents: "none",
        background: `linear-gradient(${angle}deg, rgba(2,14,23,${opacity}) 0%, rgba(2,14,23,${opacity * 0.5}) 32%, rgba(2,14,23,0) 62%)`,
      }}
    />
  );
};

// ---- film grain (very subtle, static-seeded) -------------------------------
export const Grain: React.FC<{ opacity?: number }> = ({ opacity = 0.05 }) => {
  const frame = useCurrentFrame();
  const seed = (frame % 6) + 1;
  return (
    <AbsoluteFill style={{ pointerEvents: "none", opacity, mixBlendMode: "overlay" }}>
      <svg width="100%" height="100%">
        <filter id={`grain-${seed}`}>
          <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" seed={seed} stitchTiles="stitch" />
          <feColorMatrix type="saturate" values="0" />
        </filter>
        <rect width="100%" height="100%" filter={`url(#grain-${seed})`} />
      </svg>
    </AbsoluteFill>
  );
};

// ---- fade in/out wrapper by local frame ------------------------------------
export const FadeWrap: React.FC<{ dur: number; children: React.ReactNode; inDur?: number; outDur?: number }> = ({
  dur,
  children,
  inDur = 18,
  outDur = 18,
}) => {
  const frame = useCurrentFrame();
  const o = interpolate(frame, [0, inDur, dur - outDur, dur], [0, 1, 1, 0], clamp);
  return <AbsoluteFill style={{ opacity: o }}>{children}</AbsoluteFill>;
};

// ---- persistent dive HUD (driven by ABSOLUTE frame) ------------------------
export const DepthHUD: React.FC<{ absFrame: number; total: number }> = ({ absFrame, total }) => {
  const depth = interpolate(absFrame, [0, total], [1.5, 54], clamp);
  const tcSec = absFrame / 30;
  const mm = String(Math.floor(tcSec / 60)).padStart(2, "0");
  const ss = String(Math.floor(tcSec % 60)).padStart(2, "0");
  const ff = String(absFrame % 30).padStart(2, "0");
  const pulse = 0.5 + 0.5 * Math.sin(absFrame * 0.18);
  const lbl = { fontFamily: F.mono, fontSize: 14, letterSpacing: 2, color: C.faint } as React.CSSProperties;
  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      {/* top bar */}
      <div style={{ position: "absolute", top: 46, left: 56, display: "flex", alignItems: "center", gap: 12 }}>
        <div style={{ width: 10, height: 10, borderRadius: "50%", background: C.teal, opacity: 0.5 + 0.5 * pulse, boxShadow: `0 0 10px ${C.teal}` }} />
        <span style={{ ...lbl, color: C.ice, fontWeight: 500 }}>SOFTSENSE</span>
        <span style={{ ...lbl }}>· FIELD FILM</span>
      </div>
      <div style={{ position: "absolute", top: 46, right: 56, textAlign: "right" }}>
        <div style={{ ...lbl, color: C.teal }}>
          DEPTH {depth.toFixed(1)} m
        </div>
      </div>
      {/* bottom timecode + ticks */}
      <div style={{ position: "absolute", bottom: 44, left: 56, display: "flex", alignItems: "center", gap: 14 }}>
        <span style={{ ...lbl }}>REC</span>
        <div style={{ width: 8, height: 8, borderRadius: "50%", background: "#ff5d5d", opacity: 0.4 + 0.6 * pulse }} />
        <span style={{ ...lbl, color: C.mist }}>{mm}:{ss}:{ff}</span>
      </div>
      <div style={{ position: "absolute", bottom: 46, right: 56, display: "flex", gap: 5, alignItems: "flex-end" }}>
        {Array.from({ length: 26 }).map((_, i) => {
          const on = i / 26 < absFrame / total;
          const h = 6 + (rand(i * 5) * 12 + (i % 4 === 0 ? 10 : 0));
          return <div key={i} style={{ width: 2, height: h, background: on ? C.teal : C.hair, opacity: on ? 0.9 : 0.4 }} />;
        })}
      </div>
    </AbsoluteFill>
  );
};
