import { AbsoluteFill } from "remotion";
import { C } from "../lib/theme";
import { Caustics } from "./Caustics";
import { GodRays } from "./GodRays";
import { Particulate } from "./Particulate";
import { Bubbles } from "./Bubbles";

// Persistent deep-water environment. `depth01` (0..1) darkens the scene as the
// film descends, so the whole piece reads as one continuous dive.
export const Underwater: React.FC<{ depth01?: number }> = ({ depth01 = 0 }) => {
  const d = Math.max(0, Math.min(1, depth01));
  return (
    <AbsoluteFill style={{ backgroundColor: C.abyss }}>
      <AbsoluteFill
        style={{
          background: `linear-gradient(178deg, ${C.mid} -14%, ${C.deep2} 30%, ${C.deep} 60%, ${C.abyss} 100%)`,
        }}
      />
      <AbsoluteFill
        style={{
          background: `linear-gradient(180deg, rgba(2,16,27,${0.12 + 0.5 * d}) 0%, rgba(1,9,16,${0.34 + 0.5 * d}) 100%)`,
        }}
      />
      <GodRays opacity={0.5 - 0.26 * d} />
      <Caustics id="bg-caustic" opacity={0.4 - 0.18 * d} speed={1} scale={1.15} />
      <Particulate count={82} opacity={0.5} />
      <Bubbles count={30} />
      <AbsoluteFill
        style={{
          pointerEvents: "none",
          boxShadow: "inset 0 0 340px 70px rgba(1,9,16,0.9)",
        }}
      />
    </AbsoluteFill>
  );
};
