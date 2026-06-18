// Deep-ocean "in the field" palette. Carries the repo's teal accent
// (the assembly-render design language) into an underwater setting.
export const C = {
  abyss: "#02101b",
  deep: "#06243a",
  deep2: "#093350",
  mid: "#0d4a64",
  steel: "#9fb3bd", // CAD-grey of the gripper renders
  teal: "#16b9a6",
  tealBright: "#5fe9d2",
  tealDim: "#0e7c7b",
  ice: "#eaf7f4",
  mist: "rgba(220,242,238,0.66)",
  faint: "rgba(176,212,221,0.34)",
  hair: "rgba(120,224,206,0.32)",
  amber: "#ffce5c",
  ink: "#010c14",
} as const;

export const F = {
  display: '"Sora", system-ui, sans-serif',
  mono: '"JetBrains Mono", ui-monospace, monospace',
} as const;

// shared layout
export const PAD = 132;
export const W = 1920;
export const H = 1080;
