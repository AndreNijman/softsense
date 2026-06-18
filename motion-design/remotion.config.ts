import { Config } from "@remotion/cli/config";

// Render with the system Chromium (Void Linux; Remotion's downloaded Chrome
// Headless Shell is not glibc-compatible here). Headless smoke-tested OK.
Config.setBrowserExecutable("/usr/bin/chromium");

// JPEG frames render markedly faster than PNG and the film has no alpha output.
Config.setVideoImageFormat("jpeg");
Config.setOverwriteOutput(true);

// SVG/CSS-only effects — no WebGL — so the default software GL path is fine.
// Keep concurrency modest: the underwater scenes use per-frame SVG filters.
Config.setConcurrency(6);
