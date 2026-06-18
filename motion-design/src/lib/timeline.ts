export const FPS = 30;
export const OVL = 16; // crossfade overlap between scenes (frames)

export type SceneDef = { id: string; dur: number };

// Scene order + durations (frames @30fps). ~45s total.
export const SCENES: SceneDef[] = [
  { id: "cold", dur: 150 },
  { id: "hero", dur: 220 },
  { id: "mech", dur: 250 },
  { id: "finger", dur: 220 },
  { id: "valid", dur: 220 },
  { id: "modular", dur: 232 },
  { id: "outro", dur: 162 },
];

export const TOTAL =
  SCENES.reduce((a, s) => a + s.dur, 0) - OVL * (SCENES.length - 1);

// Absolute start frame of each scene given the crossfade overlap.
export const starts: number[] = (() => {
  const out: number[] = [];
  let cursor = 0;
  for (const s of SCENES) {
    out.push(cursor);
    cursor += s.dur - OVL;
  }
  return out;
})();
