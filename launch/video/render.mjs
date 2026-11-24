// Renders the narrated launch videos with the sound kept apart from the picture.
//   node render.mjs en            film + 8 cuts, 16:9 and 9:16, English
//   node render.mjs pt c03-kits   one cut, both shapes, Portuguese
//   node render.mjs en --mix      only re-mix sound onto the existing picture (seconds, no re-render)
//   node render.mjs v1            the old silent 9-second cards
//
// Stems, in out/<lang>/stems/:
//   <name>-h.video.mp4 / <name>-v.video.mp4   picture only (muted)
//   <name>.fx.wav                             voice + clicks, whooshes, burst (the same for both shapes)
// Music: public/sfx/music.wav (made by `python voice.py sfx`), ducked under the voice at mix time.
// Final: out/<lang>/<name>-h.mp4, <name>-v.mp4 and <name>.jpg (poster)
// Change the music, its level or the ducking -> `--mix` only. Change the voice speed -> re-render (timing follows the voice).
import {bundle} from "@remotion/bundler";
import {renderMedia, renderStill, selectComposition} from "@remotion/renderer";
import path from "node:path";
import {existsSync, mkdirSync} from "node:fs";
import {spawnSync} from "node:child_process";

const lang = process.argv[2] || "en";
const only = process.argv.slice(3).find((a) => !a.startsWith("--"));
const mixOnly = process.argv.includes("--mix");
const MUSIC = path.resolve("public/sfx/music.wav");
const MUSIC_DB = -9;      // music level before ducking

const mix = (video, fx, out) => {
  // music ducks (sidechain) whenever the voice/fx stem is loud, then both are summed
  const f = `[1:a]aformat=sample_rates=48000:channel_layouts=stereo,asplit=2[fx][key];` +
    `[2:a]volume=${MUSIC_DB}dB,aformat=sample_rates=48000:channel_layouts=stereo[mus];` +
    `[mus][key]sidechaincompress=threshold=0.03:ratio=8:attack=15:release=350[duck];` +
    `[fx][duck]amix=inputs=2:normalize=0:duration=first[a]`;
  const r = spawnSync("ffmpeg", ["-v", "error", "-y", "-i", video, "-i", fx, "-stream_loop", "-1", "-i", MUSIC, "-filter_complex", f,
    "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", out], {stdio: "inherit"});
  if (r.status !== 0) throw new Error("ffmpeg mix failed: " + out);
};

if (lang === "v1") {
  const serveUrl = await bundle({entryPoint: path.resolve("src/index.ts")});
  for (const id of ["01-why", "02-inventory", "03-kits", "04-council", "05-trends", "06-usage", "07-learn", "08-free"]) for (const s of ["h", "v"]) {
    const composition = await selectComposition({serveUrl, id: `${id}-${s}`, inputProps: {id}});
    await renderMedia({composition, serveUrl, codec: "h264", crf: 20, inputProps: {id}, outputLocation: path.resolve("out", `${id}-${s}.mp4`)});
  }
  process.exit(0);
}

const out = path.resolve("out", lang), stems = path.join(out, "stems");
mkdirSync(stems, {recursive: true});
const names = ["film", "c01-why", "c02-map", "c03-kits", "c04-steps", "c05-council", "c06-trends", "c07-usage", "c08-free"].filter((n) => !only || n === only);
const serveUrl = mixOnly ? null : await bundle({entryPoint: path.resolve("src/index.ts")});

for (const name of names) {
  const fx = path.join(stems, `${name}.fx.wav`);
  for (const shape of ["h", "v"]) {
    const video = path.join(stems, `${name}-${shape}.video.mp4`);
    if (!mixOnly) {
      const composition = await selectComposition({serveUrl, id: `${name}-${lang}-${shape}`});
      const t = Date.now();
      if (shape === "h") await renderMedia({composition, serveUrl, codec: "wav", inputProps: composition.props, outputLocation: fx});   // sound only: fast
      await renderMedia({composition, serveUrl, codec: "h264", crf: 21, muted: true, inputProps: composition.props, outputLocation: video});
      console.log(`${lang}/${name}-${shape}  ${(composition.durationInFrames / 30).toFixed(1)}s video  ${((Date.now() - t) / 1000).toFixed(0)}s render`);
      if (shape === "h") await renderStill({composition, serveUrl, frame: Math.min(composition.durationInFrames - 1, name === "film" ? 900 : Math.round(composition.durationInFrames * 0.45)), inputProps: composition.props, imageFormat: "jpeg", jpegQuality: 82, output: path.join(out, `${name}.jpg`)});
    }
    if (existsSync(video) && existsSync(fx)) { mix(video, fx, path.join(out, `${name}-${shape}.mp4`)); console.log(`  mixed ${name}-${shape}.mp4`); }
  }
}
console.log("done");
