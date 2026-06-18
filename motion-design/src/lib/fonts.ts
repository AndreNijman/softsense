import { continueRender, delayRender, staticFile } from "remotion";

type Face = { family: string; weight: string; file: string };

const FACES: Face[] = [
  { family: "Sora", weight: "400", file: "fonts/sora-400.woff2" },
  { family: "Sora", weight: "600", file: "fonts/sora-600.woff2" },
  { family: "Sora", weight: "700", file: "fonts/sora-700.woff2" },
  { family: "Sora", weight: "800", file: "fonts/sora-800.woff2" },
  { family: "JetBrains Mono", weight: "400", file: "fonts/jbmono-400.woff2" },
  { family: "JetBrains Mono", weight: "500", file: "fonts/jbmono-500.woff2" },
  { family: "JetBrains Mono", weight: "700", file: "fonts/jbmono-700.woff2" },
];

let started = false;

// Load every face from public/ and gate rendering until ready, so headless
// frames never capture an un-styled fallback.
export const ensureFonts = (): void => {
  if (started || typeof document === "undefined") return;
  started = true;
  const handle = delayRender("load-fonts");
  Promise.all(
    FACES.map(async (f) => {
      const face = new FontFace(f.family, `url(${staticFile(f.file)})`, {
        weight: f.weight,
      });
      await face.load();
      (document.fonts as FontFaceSet).add(face);
    }),
  )
    .then(() => continueRender(handle))
    .catch(() => continueRender(handle));
};
