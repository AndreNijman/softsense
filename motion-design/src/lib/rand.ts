// Deterministic pseudo-random in [0,1) from an integer seed.
// Remotion re-renders every frame fresh, so all particle/noise state MUST be
// derived from a stable seed (index), never Math.random() — else it flickers.
export const rand = (seed: number): number => {
  let t = (Math.floor(seed) + 0x6d2b79f5) >>> 0;
  t = Math.imul(t ^ (t >>> 15), t | 1);
  t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
  return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
};

// random in [a,b) for seed
export const randRange = (seed: number, a: number, b: number): number =>
  a + (b - a) * rand(seed);
