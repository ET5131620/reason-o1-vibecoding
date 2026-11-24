import React from "react";
import {AbsoluteFill, Audio, Easing, Img, interpolate, random, Sequence, spring, staticFile, useCurrentFrame, useVideoConfig} from "remotion";
import {TransitionSeries, linearTiming} from "@remotion/transitions";
import {fade} from "@remotion/transitions/fade";
import {wipe} from "@remotion/transitions/wipe";
import {slide} from "@remotion/transitions/slide";
import {iris} from "@remotion/transitions/iris";
import {pushCut} from "@remotion/transitions/push-cut";
import {loadFont as loadGrotesk} from "@remotion/google-fonts/SpaceGrotesk";
import {loadFont as loadMono} from "@remotion/google-fonts/JetBrainsMono";
import DUR from "./durations.json";
import {CAPS, LINES, Lang} from "./script";

const {fontFamily: F} = loadGrotesk("normal", {weights: ["400", "500", "700"], subsets: ["latin", "latin-ext"]});
const {fontFamily: MONO} = loadMono("normal", {weights: ["400", "600"], subsets: ["latin", "latin-ext"]});

// "Big Bang" palette, the same as the landing page: deep-space blue, white light, cool greys, one warm core.
const K = {bg: "#02040a", txt: "#f5f8fc", mut: "#a6b0c0", dim: "#6a7486", blue: "#2f6bff", sky: "#6ea8ff", ice: "#cfe0ff", core: "#fff3e2", warm: "#ffc89a", line: "rgba(200,220,255,.22)", panel: "rgba(3,6,12,.84)"};
export const FPS = 30;
const LEAD = 5;    // frames of picture before the voice starts
const T = 14;      // transition length in frames
const E = Easing.bezier(0.45, 0, 0.2, 1);
const CL = {extrapolateLeft: "clamp", extrapolateRight: "clamp"} as const;
const fadeIn = (f: number, a: number, b: number) => interpolate(f, [a, b], [0, 1], {...CL, easing: E});

// ---------------- timeline ----------------
type Tr = "fade" | "wipe" | "slide" | "iris" | "push";
export type Beat = {id: string; pad?: number; tr?: Tr};
const durs = DUR as Record<string, Record<string, number>>;
const voiceFrames = (lang: Lang, id: string) => Math.round((durs[lang]?.[id] ?? 0) * FPS);
export const beatFrames = (lang: Lang, b: Beat) => (b.id === "end" ? 80 : voiceFrames(lang, b.id) + Math.round((b.pad ?? 0.35) * FPS) + LEAD);
export const totalFrames = (lang: Lang, beats: Beat[]) => beats.reduce((s, b) => s + beatFrames(lang, b), 0) - T * (beats.length - 1);

export const FILM: Beat[] = [
  {id: "f01", pad: 0.3}, {id: "f02", tr: "fade"}, {id: "f03", tr: "fade"}, {id: "f04", tr: "fade", pad: 0.6},
  {id: "f05", tr: "iris", pad: 2.0},
  {id: "f06", tr: "push"}, {id: "f07", tr: "wipe"}, {id: "f08", tr: "fade"}, {id: "f09", tr: "fade"}, {id: "f10", tr: "wipe"},
  {id: "f11", tr: "slide"}, {id: "f12", tr: "iris", pad: 0.6}, {id: "f13", tr: "fade", pad: 0.9}, {id: "end", tr: "fade"},
];
export const CUTS: Record<string, Beat[]> = {
  "c01-why": [{id: "f01", pad: 0.3}, {id: "f02", tr: "fade"}, {id: "f03", tr: "fade"}, {id: "f05", tr: "iris", pad: 2.0}, {id: "end", tr: "fade"}],
  "c02-map": [{id: "h02"}, {id: "f06", tr: "push"}, {id: "t02", tr: "slide"}, {id: "end", tr: "fade"}],
  "c03-kits": [{id: "h03"}, {id: "f07", tr: "push"}, {id: "f08", tr: "fade"}, {id: "end", tr: "fade"}],
  "c04-steps": [{id: "h04"}, {id: "f09", tr: "push"}, {id: "t04", tr: "slide"}, {id: "end", tr: "fade"}],
  "c05-council": [{id: "h05"}, {id: "f10", tr: "push"}, {id: "t05", tr: "slide"}, {id: "end", tr: "fade"}],
  "c06-trends": [{id: "h06"}, {id: "b06", tr: "push"}, {id: "end", tr: "fade"}],
  "c07-usage": [{id: "h07"}, {id: "b07", tr: "push"}, {id: "end", tr: "fade"}],
  "c08-free": [{id: "h08"}, {id: "f12", tr: "iris", pad: 0.6}, {id: "f13", tr: "fade", pad: 0.9}, {id: "end", tr: "fade"}],
};

const presentation = (tr: Tr | undefined, w: number, h: number) => {
  switch (tr) {
    case "wipe": return wipe({direction: "from-left"});
    case "slide": return slide({direction: "from-right"});
    case "iris": return iris({width: w, height: h});
    case "push": return pushCut({flashColor: "#ffffff", flashOpacity: 0.55});
    default: return fade();
  }
};

// ---------------- shared pieces ----------------
const Stars: React.FC<{n?: number}> = ({n = 110}) => {
  const f = useCurrentFrame(); const {width: W, height: H} = useVideoConfig();
  return <AbsoluteFill>{Array.from({length: n}, (_, i) => {
    const r = random(`r${i}`) * 1.7 + 0.3, p = random(`p${i}`) * 6;
    return <div key={i} style={{position: "absolute", left: random(`x${i}`) * W, top: ((random(`y${i}`) * H - f * 0.12 * r) % H + H) % H, width: r * 2, height: r * 2, borderRadius: "50%",
      background: r > 1.4 ? "#fff" : "#c9d8f0", opacity: 0.18 + 0.5 * Math.abs(Math.sin(f / 45 + p))}} />;
  })}</AbsoluteFill>;
};

const Space: React.FC<{glow?: number}> = ({glow = 0.12}) => <>
  <AbsoluteFill style={{background: `radial-gradient(60% 50% at 70% 10%, rgba(47,107,255,${glow}), transparent 70%), radial-gradient(50% 40% at 10% 90%, rgba(160,190,230,.05), transparent 70%), ${K.bg}`}} />
  <Stars />
</>;

const Brand: React.FC<{vert: boolean}> = ({vert}) => <div style={{position: "absolute", top: vert ? 80 : 56, left: vert ? 80 : 110, display: "flex", alignItems: "center", gap: 16, opacity: 0.85}}>
  <Img src={staticFile("wordmark.svg")} style={{height: vert ? 34 : 28}} />
  <span style={{fontFamily: MONO, fontSize: vert ? 20 : 17, letterSpacing: 6, color: K.mut}}>/ VIBECODING</span></div>;

// Words of the spoken line, lit as they are said (simple linear timing over the voice length).
const Karaoke: React.FC<{lang: Lang; id: string; size: number; emph?: string[]; align?: "center" | "left"; dimRest?: boolean}> = ({lang, id, size, emph = [], align = "center", dimRest}) => {
  const f = useCurrentFrame(); const vf = Math.max(voiceFrames(lang, id), 1);
  const words = (LINES[lang][id] || "").split(" ");
  const total = words.reduce((s, w) => s + w.length + 1, 0); let acc = 0;
  return <div style={{fontFamily: F, fontWeight: 700, fontSize: size, lineHeight: 1.08, letterSpacing: -size * 0.02, textAlign: align, textWrap: "balance" as any}}>
    {words.map((w, i) => {
      const at = LEAD + (acc / total) * vf * 0.92; acc += w.length + 1;
      const on = spring({frame: f - at, fps: FPS, config: {damping: 18, mass: 0.6}});
      const hot = emph.includes(w.replace(/[^\p{L}\p{N}?]/gu, "").toLowerCase());
      return <span key={i} style={{display: "inline-block", marginRight: size * 0.26, opacity: dimRest ? 0.25 + 0.75 * on : on, transform: `translateY(${(1 - on) * size * 0.35}px)`, filter: `blur(${(1 - on) * 6}px)`,
        ...(hot ? {background: `linear-gradient(100deg, #fff, ${K.ice} 40%, ${K.sky} 80%, ${K.blue})`, WebkitBackgroundClip: "text", backgroundClip: "text", color: "transparent"} : {color: K.txt})}}>{w}</span>;
    })}</div>;
};

const Subtitle: React.FC<{lang: Lang; id: string; vert: boolean}> = ({lang, id, vert}) => {
  const f = useCurrentFrame(); const vf = Math.max(voiceFrames(lang, id), 1);
  const words = (LINES[lang][id] || "").replace(/\.\.\./g, "…").split(" ");
  const p = (f - LEAD) / vf;
  const shown = fadeIn(f, LEAD - 4, LEAD + 6) * (1 - fadeIn(f, LEAD + vf + 12, LEAD + vf + 22));
  return <div style={{position: "absolute", left: vert ? 60 : 260, right: vert ? 60 : 260, bottom: vert ? 150 : 46, display: "flex", justifyContent: "center", opacity: shown}}>
    <div style={{fontFamily: F, fontWeight: 500, fontSize: vert ? 40 : 30, lineHeight: 1.35, textAlign: "center", padding: vert ? "16px 26px" : "10px 22px", borderRadius: 14, background: "rgba(2,4,10,.78)", border: `1px solid ${K.line}`}}>
      {words.map((w, i) => <span key={i} style={{color: i / words.length <= p ? K.txt : K.dim}}>{w}{i < words.length - 1 ? " " : ""}</span>)}</div></div>;
};

const Voice: React.FC<{lang: Lang; id: string}> = ({lang, id}) => voiceFrames(lang, id) ? <Sequence from={LEAD} layout="none"><Audio src={staticFile(`voice/${lang}/${id}.mp3`)} /></Sequence> : null;
const Sfx: React.FC<{name: string; at: number; vol?: number}> = ({name, at, vol = 1}) => <Sequence from={Math.max(0, Math.round(at))} layout="none"><Audio src={staticFile(`sfx/${name}.wav`)} volume={vol} /></Sequence>;

// ---------------- problem beats: big words on the dark ----------------
const TOOLS = ["MCP server", "CLI", "skills ×227", "agent", "plugin", "LLM", "API key", "prompt pack", "router", "embeddings", "RAG", "vector DB", "hooks", "extension", "SDK", "fine-tune", "workflow", "CLAUDE.md", "AGENTS.md", "rules", "subagents", "context", "memory", "tokens"];
const Chaos: React.FC<{vert: boolean; dim?: boolean}> = ({vert, dim}) => {
  const f = useCurrentFrame(); const {width: W, height: H} = useVideoConfig();
  return <AbsoluteFill>{TOOLS.map((t, i) => {
    const d = 10 + i * 4, s = spring({frame: f - d, fps: FPS, config: {damping: 9, mass: 1.2}});
    const x0 = random(`cx${i}`) * W, tx = (0.08 + random(`tx${i}`) * 0.84) * W, ty = H * (vert ? 0.78 : 0.74) + random(`ty${i}`) * H * 0.2 - (i % 6) * 26;
    const x = interpolate(s, [0, 1], [x0, tx]), y = interpolate(s, [0, 1], [-80, ty]), rot = (random(`ro${i}`) - 0.5) * 34 * s;
    const flick = 0.55 + 0.45 * Math.abs(Math.sin(f / 7 + i));
    return <div key={t} style={{position: "absolute", left: x, top: y, transform: `translate(-50%,-50%) rotate(${rot}deg)`, fontFamily: MONO, fontSize: vert ? 26 : 22, padding: "8px 14px", borderRadius: 10,
      color: K.mut, border: `1px solid ${K.line}`, background: "rgba(14,18,28,.9)", opacity: (dim ? 0.45 : 0.85) * flick * Math.min(1, s * 3), whiteSpace: "nowrap"}}>{t}</div>;
  })}</AbsoluteFill>;
};
const Tokens: React.FC<{vert: boolean}> = ({vert}) => {
  const f = useCurrentFrame();
  const n = Math.floor(Math.pow(Math.max(f - 6, 0), 2.35) * 9 + 18240);
  const pts = Array.from({length: 60}, (_, i) => [i * 34 + 60, 0.5 + Math.sin(i * 0.7 + random(`w${i}`) * 3) * 0.28]);
  const shown = Math.min(60, Math.floor(f / 2.5));
  return <AbsoluteFill>
    <div style={{position: "absolute", right: vert ? 70 : 120, top: vert ? 190 : 150, textAlign: "right", fontFamily: MONO}}>
      <div style={{fontSize: vert ? 22 : 18, letterSpacing: 5, color: K.dim}}>TOKENS · THIS PROJECT</div>
      <div style={{fontSize: vert ? 64 : 56, color: K.warm, fontWeight: 600}}>{n.toLocaleString("en-US")}</div></div>
    <svg style={{position: "absolute", left: 0, top: vert ? 1300 : 700, opacity: 0.6}} width="2100" height="320">
      {pts.slice(0, shown).map(([x, y], i) => <circle key={i} cx={x} cy={y * 320} r={3} fill={K.dim} />)}</svg>
  </AbsoluteFill>;
};
const Code: React.FC<{vert: boolean}> = ({vert}) => {
  const f = useCurrentFrame(); const t = "const app = await build(idea);";
  const typed = t.slice(0, Math.floor(f / 2)), strike = fadeIn(f, 70, 90);
  return <div style={{position: "absolute", left: vert ? 80 : 120, top: vert ? 330 : 200, fontFamily: MONO, fontSize: vert ? 32 : 30, color: K.dim}}>
    <span>{typed}</span><span style={{opacity: Math.floor(f / 12) % 2 ? 0 : 1, color: K.ice}}>▍</span>
    <div style={{height: 2, background: K.warm, width: `${strike * 100}%`, marginTop: -22, opacity: 0.8}} /></div>;
};

const EMPH: Record<Lang, Record<string, string[]>> = {
  en: {f01: ["code"], f02: ["setup"], f03: ["weigh", "down"], f04: ["dark"], h02: ["see"], h03: ["need?"], h04: ["fail"], h05: ["know", "it?"], h06: ["noise"], h07: ["damage"], t02: ["before", "add", "more"], t04: ["then", "code"], t05: ["yours"]},
  pt: {f01: ["código"], f02: ["configuração"], f03: ["pesam"], f04: ["escuras"], h02: ["ver"], h03: ["mesmo?"], h04: ["falhar"], h05: ["conhecea?"], h06: ["ruído"], h07: ["estrago"], t02: ["antes", "mais"], t04: ["depois", "código"], t05: ["teu"]},
};
const PROBLEM = ["f01", "f02", "f03", "f04", "h02", "h03", "h04", "h05", "h06", "h07"];

const WordsBeat: React.FC<{lang: Lang; id: string; vert: boolean}> = ({lang, id, vert}) => {
  const positive = !PROBLEM.includes(id);
  const bg = id === "f03" || id === "h03" || id === "h06" ? <Chaos vert={vert} dim={id !== "f03"} /> : id === "f04" || id === "h07" ? <Tokens vert={vert} /> : id === "f02" ? <Code vert={vert} /> : null;
  return <AbsoluteFill>
    <Space glow={positive ? 0.2 : 0.06} />
    {positive && <AbsoluteFill style={{background: `radial-gradient(40% 22% at 50% 100%, rgba(255,243,226,.35), rgba(110,168,255,.18) 40%, transparent 75%)`}} />}
    {bg}
    <Brand vert={vert} />
    <AbsoluteFill style={{alignItems: "center", justifyContent: "center", padding: vert ? "0 80px" : "0 220px"}}>
      <Karaoke lang={lang} id={id} size={vert ? 96 : 104} emph={EMPH[lang][id]} />
    </AbsoluteFill>
  </AbsoluteFill>;
};

// ---------------- the turn: the burst ----------------
const BangBeat: React.FC<{lang: Lang; id: string; vert: boolean}> = ({lang, id, vert}) => {
  const f = useCurrentFrame(); const at = LEAD + voiceFrames(lang, id) - 4;
  const b = Math.max(0, f - at), burst = interpolate(b, [0, 10, 70], [0, 1, 0.55], CL), flash = interpolate(b, [0, 4, 22], [0, 1, 0], CL);
  const logo = spring({frame: b - 14, fps: FPS, config: {damping: 16}});
  const textOut = 1 - fadeIn(f, at - 2, at + 6);
  return <AbsoluteFill>
    <Space glow={0.05 + burst * 0.2} />
    <AbsoluteFill style={{alignItems: "center", justifyContent: "center"}}>
      <div style={{width: 40, height: 40, borderRadius: "50%", transform: `scale(${0.2 + burst * (vert ? 70 : 60)})`, opacity: burst,
        background: `radial-gradient(circle, ${K.core} 0, ${K.ice} 10%, rgba(110,168,255,.55) 24%, rgba(47,107,255,.25) 42%, transparent 70%)`}} />
    </AbsoluteFill>
    <AbsoluteFill style={{alignItems: "center", justifyContent: "center", padding: vert ? "0 80px" : "0 260px", opacity: textOut}}>
      <Karaoke lang={lang} id={id} size={vert ? 92 : 96} emph={["first?", "primeiro?", "configuração"]} /></AbsoluteFill>
    <AbsoluteFill style={{alignItems: "center", justifyContent: "center", flexDirection: "column", gap: 30, opacity: logo, transform: `scale(${0.85 + 0.15 * logo})`}}>
      <Img src={staticFile("logo.svg")} style={{width: vert ? 230 : 200, filter: "drop-shadow(0 0 40px rgba(110,168,255,.8))"}} />
      <Img src={staticFile("wordmark.svg")} style={{height: vert ? 70 : 64}} />
      <div style={{fontFamily: MONO, fontSize: vert ? 30 : 26, letterSpacing: 10, color: K.ice}}>VIBECODING</div>
    </AbsoluteFill>
    <AbsoluteFill style={{background: "#fff", opacity: flash}} />
    <Sfx name="boom" at={at} vol={0.9} />
  </AbsoluteFill>;
};

// ---------------- the demo: real screens, a camera, a cursor ----------------
type Key = {t: number; src?: string; cam: [number, number, number]; cur: [number, number]; click?: boolean};
type Ov = {src: string; from: number; to: number; kind: "ring" | "mask" | "scan" | "type" | "steps"; rect: [number, number, number, number]; text?: string};
const SIZE: Record<string, [number, number]> = {"app/05-trends.webp": [1440, 900], "app/07-learn.webp": [1440, 900]};
const size = (src: string) => SIZE[src] || [1600, 1000];

const TRACKS: Record<string, {keys: Key[]; ov?: Ov[]}> = {
  f06: {keys: [
    {t: 0, src: "app/01-overview.png", cam: [800, 500, 1], cur: [1050, 760]}, {t: 0.2, cam: [800, 500, 1], cur: [1050, 760]},
    {t: 0.36, cam: [1150, 300, 1.25], cur: [1420, 241], click: true}, {t: 0.52, cam: [1150, 300, 1.25], cur: [1430, 250]},
    {t: 0.78, cam: [700, 470, 1.15], cur: [1240, 560]}, {t: 1.2, cam: [800, 500, 1.02], cur: [1240, 560]}],
    ov: [{src: "app/01-overview.png", kind: "scan", from: 0.38, to: 0.72, rect: [110, 280, 1450, 436]},
      {src: "app/01-overview.png", kind: "ring", from: 0.62, to: 1.2, rect: [920, 280, 640, 436], text: "found on this PC"},
      {src: "app/01-overview.png", kind: "ring", from: 0.7, to: 1.2, rect: [110, 280, 796, 436], text: "one live map"}]},
  f07: {keys: [
    {t: 0, src: "app/01-overview.png", cam: [800, 500, 1], cur: [700, 600]}, {t: 0.12, cam: [800, 500, 1], cur: [700, 600]},
    {t: 0.3, cam: [420, 320, 1.3], cur: [42, 169], click: true},
    {t: 0.36, src: "app/02-kits.png", cam: [600, 460, 1.08], cur: [42, 169]}, {t: 0.62, cam: [600, 460, 1.08], cur: [468, 440]},
    {t: 0.78, cam: [470, 440, 1.4], cur: [468, 440], click: true},
    {t: 0.84, src: "app/03a-kit-top.png", cam: [1100, 300, 1.2], cur: [620, 640]}, {t: 1.2, cam: [1100, 320, 1.22], cur: [620, 640]}],
    ov: [{src: "app/02-kits.png", kind: "ring", from: 0.6, to: 0.84, rect: [354, 310, 228, 257], text: "goal: a web page"}]},
  f08: {keys: [
    {t: 0, src: "app/03a-kit-top.png", cam: [1100, 320, 1.22], cur: [1000, 700]}, {t: 0.14, cam: [1150, 580, 1.38], cur: [1250, 520]},
    {t: 0.48, cam: [1150, 580, 1.38], cur: [1390, 725]},
    {t: 0.54, src: "app/03b-kit-rows.png", cam: [1150, 420, 1.22], cur: [1390, 725]}, {t: 0.86, cam: [1100, 620, 1.28], cur: [1390, 537]},
    {t: 1.2, cam: [1100, 620, 1.28], cur: [1390, 540]}],
    ov: [{src: "app/03a-kit-top.png", kind: "ring", from: 0.14, to: 0.54, rect: [1340, 436, 95, 26], text: "you have it"},
      {src: "app/03a-kit-top.png", kind: "ring", from: 0.2, to: 0.54, rect: [1340, 579, 95, 26]},
      {src: "app/03a-kit-top.png", kind: "ring", from: 0.27, to: 0.54, rect: [1340, 712, 72, 26], text: "missing"},
      {src: "app/03a-kit-top.png", kind: "ring", from: 0.36, to: 0.54, rect: [772, 726, 186, 50], text: "the why"},
      {src: "app/03b-kit-rows.png", kind: "ring", from: 0.58, to: 1.2, rect: [1340, 204, 72, 26], text: "missing"},
      {src: "app/03b-kit-rows.png", kind: "ring", from: 0.66, to: 1.2, rect: [1340, 524, 72, 26]},
      {src: "app/03b-kit-rows.png", kind: "ring", from: 0.74, to: 1.2, rect: [1340, 781, 72, 26]}]},
  f09: {keys: [
    {t: 0, src: "app/03a-kit-top.png", cam: [1000, 300, 1.2], cur: [1100, 620]}, {t: 0.24, cam: [1000, 300, 1.2], cur: [968, 294], click: true},
    {t: 0.3, src: "app/03c-kit-steps.png", cam: [1110, 460, 1.28], cur: [968, 294]}, {t: 1.2, cam: [1110, 470, 1.3], cur: [1300, 640]}],
    ov: [{src: "app/03c-kit-steps.png", kind: "steps", from: 0.34, to: 0.98, rect: [655, 333, 912, 272]}]},
  f10: {keys: [
    {t: 0, src: "app/01-overview.png", cam: [1100, 300, 1.15], cur: [1100, 520]}, {t: 0.13, cam: [1200, 260, 1.2], cur: [1516, 34], click: true},
    {t: 0.18, src: "app/04-council.png", cam: [800, 330, 1.05], cur: [1516, 34]}, {t: 0.3, cam: [800, 330, 1.05], cur: [700, 291]},
    {t: 0.42, cam: [1100, 330, 1.12], cur: [1455, 291], click: true}, {t: 0.62, cam: [820, 500, 1.04], cur: [1455, 300]},
    {t: 0.8, cam: [1190, 580, 1.42], cur: [1200, 650]}, {t: 1.2, cam: [1190, 580, 1.42], cur: [1200, 650]}],
    ov: [{src: "app/04-council.png", kind: "type", from: 0.2, to: 0.36, rect: [130, 270, 1225, 42], text: "~/projects/my-landing-page"},
      {src: "app/04-council.png", kind: "mask", from: 0.18, to: 0.53, rect: [126, 328, 1418, 370]},
      {src: "app/04-council.png", kind: "ring", from: 0.56, to: 0.74, rect: [130, 332, 694, 360], text: "passport"},
      {src: "app/04-council.png", kind: "ring", from: 0.72, to: 1.2, rect: [846, 566, 690, 112], text: "what it needs"}]},
  b06: {keys: [
    {t: 0, src: "app/05-trends.webp", cam: [720, 450, 1], cur: [900, 720]}, {t: 0.35, cam: [520, 420, 1.3], cur: [420, 430]},
    {t: 0.7, cam: [1000, 430, 1.3], cur: [1100, 440], click: true}, {t: 1.2, cam: [720, 450, 1.05], cur: [1100, 440]}]},
  h08: {keys: [
    {t: 0, src: "app/07-learn.webp", cam: [720, 450, 1], cur: [900, 620]}, {t: 0.4, cam: [430, 500, 1.35], cur: [300, 560], click: true},
    {t: 1.2, cam: [1100, 420, 1.25], cur: [1150, 360]}]},
};

const lerp = (a: number, b: number, p: number) => a + (b - a) * p;

const Overlay: React.FC<{o: Ov; tf: (t: number) => number}> = ({o, tf}) => {
  const f = useCurrentFrame(); const [x, y, w, h] = o.rect; const a = tf(o.from), b = tf(o.to);
  if (o.kind === "ring") {
    const on = fadeIn(f, a, a + 10) * (1 - fadeIn(f, b - 6, b)), s = spring({frame: f - a, fps: FPS, config: {damping: 14}});
    return <div style={{position: "absolute", left: x - 6, top: y - 6, width: w + 12, height: h + 12, borderRadius: 12, border: `2.5px solid ${K.ice}`, opacity: on,
      boxShadow: `0 0 0 4px rgba(110,168,255,.25), 0 0 34px rgba(110,168,255,.7)`, transform: `scale(${1.15 - 0.15 * s})`}}>
      {o.text && <div style={{position: "absolute", left: 0, bottom: "100%", marginBottom: 8, whiteSpace: "nowrap", fontFamily: MONO, fontWeight: 600, fontSize: 15, letterSpacing: 1.5, textTransform: "uppercase",
        padding: "5px 10px", borderRadius: 8, background: K.ice, color: K.bg}}>{o.text}</div>}</div>;
  }
  if (o.kind === "mask") {
    const wipeP = fadeIn(f, b, b + 16), load = f >= tf(0.43) && f < b;
    return <div style={{position: "absolute", left: x + w * wipeP, top: y, width: w * (1 - wipeP), height: h, background: "#060a14", borderRadius: 14, overflow: "hidden"}}>
      {load && <div style={{position: "absolute", top: 0, bottom: 0, width: 260, left: ((f * 26) % (w + 260)) - 260, background: "linear-gradient(90deg, transparent, rgba(110,168,255,.25), transparent)"}} />}
      {load && <div style={{position: "absolute", left: 30, top: 30, fontFamily: MONO, fontSize: 16, letterSpacing: 3, color: K.sky}}>READING THE PROJECT…</div>}</div>;
  }
  if (o.kind === "scan") {
    const p = interpolate(f, [a, b], [0, 1], CL), on = p > 0 && p < 1 ? 1 : 0;
    return <div style={{position: "absolute", left: x + p * w - 60, top: y, width: 120, height: h, opacity: on,
      background: "linear-gradient(90deg, transparent, rgba(207,224,255,.55), transparent)", mixBlendMode: "screen"}} />;
  }
  if (o.kind === "type") {
    const t = o.text || "", n = Math.floor(interpolate(f, [a, b], [0, t.length], CL)), on = f >= a - 4;
    return on ? <div style={{position: "absolute", left: x, top: y, width: w, height: h, background: "#050913", borderRadius: 8, display: "flex", alignItems: "center", paddingLeft: 12, fontFamily: F, fontSize: 16, color: K.txt}}>
      {t.slice(0, n)}<span style={{opacity: Math.floor(f / 10) % 2, color: K.sky}}>|</span></div> : null;
  }
  // steps: the rows appear one by one, each with a tick
  const rows = 5, rh = h / rows;
  return <>{Array.from({length: rows}, (_, i) => {
    const at = lerp(a, b, i / rows), p = fadeIn(f, at, at + 10);
    return <React.Fragment key={i}>
      <div style={{position: "absolute", left: x + w * p, top: y + i * rh, width: w * (1 - p), height: rh, background: "#070b15"}} />
      <div style={{position: "absolute", left: x + w - 40, top: y + i * rh + rh / 2 - 13, width: 26, height: 26, borderRadius: 13, background: K.ice, color: K.bg, fontWeight: 700, fontSize: 17,
        display: "flex", alignItems: "center", justifyContent: "center", opacity: fadeIn(f, at + 8, at + 14), transform: `scale(${spring({frame: f - at - 8, fps: FPS, config: {damping: 10}})})`}}>✓</div>
      {p > 0 && p < 1 && <Sfx name="click" at={at} vol={0.25} />}
    </React.Fragment>;
  })}</>;
};

const AppBeat: React.FC<{lang: Lang; id: string; vert: boolean}> = ({lang, id, vert}) => {
  const f = useCurrentFrame(); const {width: W, height: H} = useVideoConfig();
  const tr = TRACKS[id]; const vf = Math.max(voiceFrames(lang, id), 1);
  const tf = (t: number) => LEAD + t * vf;
  const ks = tr.keys;
  // where are we between keys
  let i = 0; while (i < ks.length - 1 && f >= tf(ks[i + 1].t)) i++;
  const k0 = ks[i], k1 = ks[Math.min(i + 1, ks.length - 1)];
  const p = k1 === k0 ? 1 : E(interpolate(f, [tf(k0.t), tf(k1.t)], [0, 1], CL));
  const cam = [0, 1, 2].map((j) => lerp(k0.cam[j], k1.cam[j], p));
  const cur = [0, 1].map((j) => lerp(k0.cur[j], k1.cur[j], p));
  // which screen is showing, and the one before it (for the cross-fade)
  const srcAt = (t: number) => { let s = ks[0].src!; for (const k of ks) if (k.t <= t && k.src) s = k.src; return s; };
  const changes = ks.filter((k) => k.src).map((k) => ({at: tf(k.t), src: k.src!}));
  let ci = 0; while (ci < changes.length - 1 && f >= changes[ci + 1].at) ci++;
  const cur_src = changes[ci].src, prev_src = ci > 0 ? changes[ci - 1].src : null, xf = ci > 0 ? fadeIn(f, changes[ci].at, changes[ci].at + 9) : 1;
  void srcAt;
  // viewport for the screen
  const VP = vert ? {x: 0, y: 360, w: W, h: 1230} : {x: 160, y: 40, w: 1600, h: 1000};
  const place = (src: string) => {
    const [SW, SH] = size(src);
    const base = VP.w / SW, cover = Math.max(1, VP.h / (SH * base));
    let z = vert ? Math.max(cam[2] * 1.9, cover) : Math.max(cam[2], cover);
    const s = base * z;
    let [cx, cy] = [cam[0], cam[1]];
    if (vert) { cx = lerp(cx, cur[0], 0.6); cy = lerp(cy, cur[1], 0.5); }
    const tx = Math.min(0, Math.max(VP.w - SW * s, VP.w / 2 - cx * s)), ty = Math.min(0, Math.max(VP.h - SH * s, VP.h / 2 - cy * s));
    return {s, tx, ty};
  };
  const layer = (src: string, op: number) => { const {s, tx, ty} = place(src); const [SW, SH] = size(src);
    return <div key={src + op} style={{position: "absolute", left: 0, top: 0, width: SW, height: SH, transform: `translate(${tx}px, ${ty}px) scale(${s})`, transformOrigin: "0 0", opacity: op}}>
      <Img src={staticFile(src)} style={{width: SW, height: SH, display: "block"}} />
      {(tr.ov || []).filter((o) => o.src === src).map((o, j) => <Overlay key={j} o={o} tf={tf} />)}
    </div>; };
  const pl = place(cur_src);
  const cx = VP.x + cur[0] * pl.s + pl.tx, cy = VP.y + cur[1] * pl.s + pl.ty;
  // clicks: ripple + sound
  const clicks = ks.filter((k) => k.click).map((k) => tf(k.t));
  const lastClick = clicks.filter((c) => c <= f).pop();
  const rp = lastClick === undefined ? 1 : interpolate(f - lastClick, [0, 14], [0, 1], CL);
  const press = lastClick === undefined ? 1 : interpolate(f - lastClick, [0, 3, 8], [1, 0.82, 1], CL);
  const enter = spring({frame: f, fps: FPS, config: {damping: 20}});
  return <AbsoluteFill>
    <Space glow={0.16} />
    <div style={{position: "absolute", left: VP.x, top: VP.y, width: VP.w, height: VP.h, overflow: "hidden", borderRadius: vert ? 0 : 22, border: vert ? "none" : `1.5px solid ${K.line}`,
      boxShadow: "0 -30px 120px rgba(47,107,255,.22), 0 40px 120px rgba(0,0,0,.7)", transform: `scale(${0.96 + 0.04 * enter})`}}>
      {prev_src && xf < 1 && layer(prev_src, 1)}
      {layer(cur_src, xf)}
    </div>
    {/* cursor */}
    <div style={{position: "absolute", left: cx, top: cy, pointerEvents: "none"}}>
      <div style={{position: "absolute", left: -30, top: -30, width: 60, height: 60, borderRadius: 30, border: `3px solid ${K.ice}`, opacity: 1 - rp, transform: `scale(${0.3 + rp * 1.4})`}} />
      <svg width={vert ? 46 : 38} height={vert ? 46 : 38} viewBox="0 0 24 24" style={{transform: `scale(${press})`, transformOrigin: "0 0", filter: "drop-shadow(0 4px 10px rgba(0,0,0,.6))"}}>
        <path d="M3 2l7.5 19 2.6-7.9L21 10.5z" fill="#fff" stroke="#02040a" strokeWidth="1.4" strokeLinejoin="round" /></svg>
    </div>
    {clicks.map((c, j) => <Sfx key={j} name="click" at={c} vol={0.7} />)}
    {/* caption: short, on a dark panel over the screen */}
    <Caption lang={lang} id={id} vert={vert} />
    <Subtitle lang={lang} id={id} vert={vert} />
  </AbsoluteFill>;
};

const Caption: React.FC<{lang: Lang; id: string; vert: boolean}> = ({lang, id, vert}) => {
  const f = useCurrentFrame(); const s = spring({frame: f - 6, fps: FPS, config: {damping: 16}});
  const text = CAPS[lang][id] || "";
  return <div style={{position: "absolute", ...(vert ? {left: 60, right: 60, top: 120} : {left: 200, top: 84}), maxWidth: vert ? undefined : 760, opacity: s, transform: `translateY(${(1 - s) * 24}px)`,
    padding: vert ? "28px 34px" : "22px 30px", borderRadius: 20, background: K.panel, border: `1px solid ${K.line}`, backdropFilter: "blur(14px)", boxShadow: "0 24px 70px rgba(0,0,0,.6)"}}>
    <div style={{fontFamily: MONO, fontSize: vert ? 22 : 17, letterSpacing: 5, color: K.sky, marginBottom: 8}}>REASON O1</div>
    <div style={{fontFamily: F, fontWeight: 700, fontSize: vert ? 56 : 46, lineHeight: 1.05, textTransform: "uppercase", letterSpacing: -0.5, color: K.txt}}>{text}</div></div>;
};

// ---------------- result, usage, ending ----------------
const ResultBeat: React.FC<{lang: Lang; id: string; vert: boolean}> = ({lang, id, vert}) => {
  const f = useCurrentFrame();
  const items = lang === "pt" ? ["Menos erros", "Menos desperdício", "Resultado mais rápido"] : ["Fewer errors", "Less waste", "Faster results"];
  const icons = ["M5 12l5 5 9-10", "M4 7h16M7 7v12h10V7M10 4h4", "M13 3L5 14h6l-1 7 8-11h-6z"];
  const vf = voiceFrames(lang, id);
  return <AbsoluteFill>
    <Space glow={0.22} />
    <AbsoluteFill style={{background: `radial-gradient(45% 25% at 50% 100%, rgba(255,243,226,.3), rgba(110,168,255,.16) 40%, transparent 75%)`}} />
    <Brand vert={vert} />
    <AbsoluteFill style={{flexDirection: vert ? "column" : "row", alignItems: "center", justifyContent: "center", gap: vert ? 34 : 40, padding: vert ? "0 80px" : 0}}>
      {items.map((t, i) => { const at = LEAD + (vf * i) / 3.2, s = spring({frame: f - at, fps: FPS, config: {damping: 14}});
        const bar = interpolate(f, [at + 8, at + 40], [1, 0.28], {...CL, easing: E});
        return <div key={t} style={{width: vert ? "100%" : 470, padding: 40, borderRadius: 26, background: K.panel, border: `1px solid ${K.line}`, opacity: s, transform: `translateY(${(1 - s) * 40}px)`, boxShadow: "0 30px 90px rgba(0,0,0,.6)"}}>
          <svg width="54" height="54" viewBox="0 0 24 24" fill="none" stroke={K.ice} strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d={icons[i]} /></svg>
          <div style={{fontFamily: F, fontWeight: 700, fontSize: vert ? 60 : 48, textTransform: "uppercase", marginTop: 18, lineHeight: 1.05}}>{t}</div>
          <div style={{height: 10, borderRadius: 5, background: "rgba(200,220,255,.1)", marginTop: 26}}>
            <div style={{height: 10, borderRadius: 5, width: `${(i === 2 ? 1 - bar + 0.28 : bar) * 100}%`, background: `linear-gradient(90deg, ${K.blue}, ${K.ice})`}} /></div>
        </div>; })}
    </AbsoluteFill>
    <Subtitle lang={lang} id={id} vert={vert} />
  </AbsoluteFill>;
};

const BarsBeat: React.FC<{lang: Lang; id: string; vert: boolean}> = ({lang, id, vert}) => {
  const f = useCurrentFrame(); const hs = [0.35, 0.5, 0.42, 0.7, 0.55, 0.9, 0.62, 0.78, 0.48, 0.66, 0.84, 0.58, 0.4, 0.72];
  const hover = Math.min(hs.length - 1, Math.max(0, Math.floor(interpolate(f, [LEAD + 60, LEAD + voiceFrames(lang, id)], [3, 12], CL))));
  return <AbsoluteFill>
    <Space glow={0.16} />
    <div style={{position: "absolute", ...(vert ? {left: 60, right: 60, top: 420, height: 1000} : {left: 260, right: 260, top: 230, height: 640}), borderRadius: 26, background: K.panel, border: `1px solid ${K.line}`, padding: 44, display: "flex", flexDirection: "column"}}>
      <div style={{fontFamily: MONO, fontSize: vert ? 24 : 20, letterSpacing: 5, color: K.sky}}>{lang === "pt" ? "TOKENS · ÚLTIMOS 30 DIAS" : "TOKENS · LAST 30 DAYS"}</div>
      <div style={{flex: 1, display: "flex", alignItems: "flex-end", gap: 12, marginTop: 30}}>
        {hs.map((h, i) => { const g = fadeIn(f, LEAD + i * 4, LEAD + 30 + i * 4), on = i === hover;
          return <div key={i} style={{flex: 1, display: "flex", flexDirection: "column", justifyContent: "flex-end", height: "100%", gap: 4, opacity: on ? 1 : 0.75}}>
            <div style={{height: `${h * 40 * g}%`, background: K.mut, borderRadius: "8px 8px 2px 2px", opacity: 0.6}} />
            <div style={{height: `${h * 52 * g}%`, background: on ? K.ice : K.sky, borderRadius: "2px 2px 8px 8px", boxShadow: on ? `0 0 30px ${K.sky}` : "none"}} /></div>; })}
      </div>
      <div style={{display: "flex", gap: 30, marginTop: 22, fontFamily: F, fontSize: vert ? 30 : 24, color: K.mut}}><span><b style={{color: K.sky}}>■</b> Claude Code</span><span><b style={{color: K.mut}}>■</b> Codex</span></div>
    </div>
    <Caption lang={lang} id={id} vert={vert} />
    <Subtitle lang={lang} id={id} vert={vert} />
  </AbsoluteFill>;
};

const REPO = "github.com/ET5131620/reason-o1-vibecoding";
const EndBeat: React.FC<{lang: Lang; id: string; vert: boolean}> = ({lang, id, vert}) => {
  const f = useCurrentFrame(); const s = spring({frame: f - 4, fps: FPS, config: {damping: 16}});
  const chips = lang === "pt" ? ["GRÁTIS", "OPEN SOURCE", "NO TEU PC"] : ["FREE", "OPEN SOURCE", "ON YOUR PC"];
  const one = id === "f13";
  return <AbsoluteFill>
    <Space glow={0.2} />
    <AbsoluteFill style={{background: `radial-gradient(50% 28% at 50% 100%, rgba(255,243,226,.55), rgba(110,168,255,.25) 40%, transparent 75%)`}} />
    <AbsoluteFill style={{alignItems: "center", justifyContent: "center", flexDirection: "column", gap: 26, opacity: s, transform: `scale(${0.94 + 0.06 * s})`, padding: "0 70px"}}>
      {one ? <>
        <div style={{fontFamily: MONO, fontSize: vert ? 26 : 22, letterSpacing: 6, padding: "10px 20px", borderRadius: 99, border: `1.5px solid ${K.line}`, color: K.txt}}>{lang === "pt" ? "CHEGA EM MEADOS DE DEZEMBRO" : "COMING MID-DECEMBER"}</div>
        <div style={{fontFamily: F, fontWeight: 700, fontSize: vert ? 120 : 132, letterSpacing: -3, lineHeight: 1}}>REASON ONE</div>
        <div style={{fontFamily: F, fontSize: vert ? 38 : 34, color: K.mut}}>{lang === "pt" ? "o estúdio · código fechado" : "the studio · closed source"}</div>
        <div style={{fontFamily: F, fontSize: vert ? 34 : 30, color: K.ice, marginTop: 10, textAlign: "center"}}>{lang === "pt" ? "Obrigado à comunidade open source." : "Thank you, open source community."}</div>
      </> : <>
        <Img src={staticFile("logo.svg")} style={{width: vert ? 190 : 160, filter: "drop-shadow(0 0 30px rgba(110,168,255,.7))"}} />
        <Img src={staticFile("wordmark.svg")} style={{height: vert ? 64 : 58}} />
        <div style={{fontFamily: MONO, fontSize: vert ? 28 : 24, letterSpacing: 10, color: K.ice}}>VIBECODING</div>
        <div style={{display: "flex", gap: 14, marginTop: 8, flexWrap: "wrap", justifyContent: "center"}}>{chips.map((x, i) => <span key={x} style={{fontFamily: MONO, fontSize: vert ? 24 : 21, letterSpacing: 3, padding: "10px 18px", borderRadius: 99,
          border: `1.5px solid ${K.line}`, color: K.txt, opacity: fadeIn(f, 12 + i * 6, 22 + i * 6)}}>{x}</span>)}</div>
        <div style={{fontFamily: MONO, fontSize: vert ? 30 : 28, color: K.sky, marginTop: 14, opacity: fadeIn(f, 30, 44)}}>{REPO}</div>
      </>}
    </AbsoluteFill>
    {id !== "end" && <Subtitle lang={lang} id={id} vert={vert} />}
  </AbsoluteFill>;
};

const BeatView: React.FC<{lang: Lang; b: Beat; first: boolean}> = ({lang, b, first}) => {
  const {height, width} = useVideoConfig(); const vert = height > width; const id = b.id;
  const view = TRACKS[id] ? <AppBeat lang={lang} id={id} vert={vert} />
    : id === "f05" ? <BangBeat lang={lang} id={id} vert={vert} />
    : id === "f11" ? <ResultBeat lang={lang} id={id} vert={vert} />
    : id === "b07" ? <BarsBeat lang={lang} id={id} vert={vert} />
    : id === "f12" || id === "f13" || id === "end" ? <EndBeat lang={lang} id={id} vert={vert} />
    : <WordsBeat lang={lang} id={id} vert={vert} />;
  return <AbsoluteFill style={{fontFamily: F, color: K.txt, background: K.bg, overflow: "hidden"}}>
    {view}
    {id !== "end" && <Voice lang={lang} id={id} />}
    {!first && <Sfx name="whoosh" at={0} vol={0.35} />}
  </AbsoluteFill>;
};

export const Video: React.FC<{lang: Lang; beats: Beat[]}> = ({lang, beats}) => {
  const {width, height} = useVideoConfig();
  // a low bed under the opening problem beats, so the silence between lines feels deliberate
  const problemLen = beats.findIndex((b) => !PROBLEM.includes(b.id));
  const bed = beats.slice(0, Math.max(problemLen, 0)).reduce((s, b) => s + beatFrames(lang, b), 0);
  return <AbsoluteFill style={{background: K.bg}}>
    <TransitionSeries>
      {beats.flatMap((b, i) => {
        const seq = <TransitionSeries.Sequence key={`s${i}`} durationInFrames={beatFrames(lang, b)}><BeatView lang={lang} b={b} first={i === 0} /></TransitionSeries.Sequence>;
        return i === 0 ? [seq] : [<TransitionSeries.Transition key={`t${i}`} presentation={presentation(b.tr, width, height) as any} timing={linearTiming({durationInFrames: T})} />, seq];
      })}
    </TransitionSeries>
    {/* music is mixed in afterwards (render.mjs), on its own stem, so it can change without re-rendering */}
    {bed > 0 && <Sequence durationInFrames={bed} layout="none"><Audio src={staticFile("sfx/drone.wav")} loop volume={(fr) => interpolate(fr, [0, 30, bed - 30, bed], [0, 0.3, 0.3, 0], CL)} /></Sequence>}
  </AbsoluteFill>;
};
