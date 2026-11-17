// Builds the desktop UI with esbuild for a quick preview, without Vite or npm install.
// Used by AI sessions that cannot install packages, and for visual checks.
//
//   node scripts/ui-preview/build.mjs <outdir> <engineUrl> <token>
//
// Needs esbuild, react and react-dom available somewhere on NODE_PATH.
import { createRequire } from "node:module";
import { mkdirSync, writeFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const require = createRequire(import.meta.url);
const here = dirname(fileURLToPath(import.meta.url));
const appDir = resolve(here, "../../apps/desktop");
const [outdir = "/tmp/arca-ui", engineUrl = "http://127.0.0.1:8765", token = "dev"] = process.argv.slice(2);
const nodePaths = (process.env.NODE_PATH || "").split(":").filter(Boolean);

let esbuild;
for (const candidate of ["esbuild", ...nodePaths.map((p) => join(p, "esbuild"))]) {
  try {
    esbuild = require(candidate);
    break;
  } catch {
    /* try next */
  }
}
if (!esbuild) throw new Error("esbuild não encontrado (defina NODE_PATH).");

mkdirSync(outdir, { recursive: true });
await esbuild.build({
  entryPoints: [join(appDir, "src/main.tsx")],
  bundle: true,
  outdir,
  entryNames: "app",
  format: "esm",
  jsx: "automatic",
  target: "es2022",
  nodePaths,
  external: ["@tauri-apps/api/*"],
  define: {
    "import.meta.env.VITE_ARCA_ENGINE_URL": JSON.stringify(engineUrl),
    "import.meta.env.VITE_ARCA_TOKEN": JSON.stringify(token),
    "process.env.NODE_ENV": '"production"',
  },
  logLevel: "info",
});
writeFileSync(
  join(outdir, "index.html"),
  `<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>ARCA</title><link rel="stylesheet" href="app.css"></head><body><div id="root"></div><script type="module" src="app.js"></script></body></html>`,
);
console.log(`UI de pré-visualização em ${outdir}`);
