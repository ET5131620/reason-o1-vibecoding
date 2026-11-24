// Sample frames for review: node stills.mjs film-en-h 0.3,0.6   (fractions of each beat)
import {bundle} from "@remotion/bundler";
import {renderStill, selectComposition} from "@remotion/renderer";
import path from "node:path";
import {mkdirSync} from "node:fs";

const id = process.argv[2] || "film-en-h";
const fr = (process.argv[3] || "0.5").split(",").map(Number);
const out = path.resolve("out", "stills", id);
mkdirSync(out, {recursive: true});
const serveUrl = await bundle({entryPoint: path.resolve("src/index.ts")});
const composition = await selectComposition({serveUrl, id});
const {beatFrames} = await import("./out/film-meta.mjs").catch(() => ({}));
const frames = process.argv[4] ? process.argv[4].split(",").map(Number) : fr.map((x) => Math.round(x * composition.durationInFrames));
for (const f of frames) {
  await renderStill({composition, serveUrl, frame: f, inputProps: composition.props, imageFormat: "jpeg", jpegQuality: 80, output: path.join(out, `${String(f).padStart(5, "0")}.jpg`)});
  console.log("frame", f);
}
void beatFrames;
