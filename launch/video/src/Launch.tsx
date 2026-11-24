import React from "react";
import {AbsoluteFill, Easing, Img, interpolate, random, spring, staticFile, useCurrentFrame, useVideoConfig} from "remotion";
import {loadFont as loadGrotesk} from "@remotion/google-fonts/SpaceGrotesk";
import {loadFont as loadMono} from "@remotion/google-fonts/JetBrainsMono";

const {fontFamily: F} = loadGrotesk("normal", {weights: ["500", "700"], subsets: ["latin"]});
const {fontFamily: MONO} = loadMono("normal", {weights: ["600"], subsets: ["latin"]});

// the app's palette, so the videos read as the product
const C = {bg: "#04060c", txt: "#e8f1ff", mut: "#9aabc7", dim: "#5b6b86", cyan: "#38e1ff", vio: "#8b7bff", pink: "#ff5fa2", amber: "#ffb547", green: "#3ddc97", line: "rgba(120,200,255,.28)"};

type Visual =
  | {kind: "shot"; src: string; from?: [number, number]; to?: [number, number]; zoom?: [number, number]}
  | {kind: "chips"; items: string[]; color?: string}
  | {kind: "passport"}
  | {kind: "bars"}
  | {kind: "langs"}
  | {kind: "free"};

export type Scene = {id: string; kicker: string; color: string; lines: string[]; accent: number; sub: string; visual: Visual};

// Each video: a kicker, a headline (one line is coloured), one supporting sentence, one visual. Silent: the words are the subtitles.
export const SCENES: Scene[] = [
  {id: "01-why", kicker: "Why it exists", color: C.cyan, lines: ["Vibe coding doesn't", "fail on code.", "It fails on setup."], accent: 2,
   sub: "Three questions eat your hours. REASON O1 answers them.", visual: {kind: "chips", items: ["What do I already have?", "Which tool fits this job?", "Where did my tokens go?"]}},
  {id: "02-inventory", kicker: "Your map", color: C.cyan, lines: ["Everything", "you installed.", "One live map."], accent: 2,
   sub: "Apps, skills, MCP servers, CLIs, local models and projects — scanned every time it opens.", visual: {kind: "shot", src: "shot-overview.webp", from: [0, 0], to: [-4, -3], zoom: [1.02, 1.12]}},
  {id: "03-kits", kicker: "Tool kits", color: C.vio, lines: ["18 kits.", "3 to start.", "7 to master."], accent: 2,
   sub: "Curated per goal, ranked by GitHub stars — with the why, and what pairs well.", visual: {kind: "shot", src: "shot-kits.webp", from: [0, -2], to: [-3, -10], zoom: [1.04, 1.14]}},
  {id: "04-council", kicker: "Council", color: C.pink, lines: ["Point it", "at a project.", "Get what's missing."], accent: 2,
   sub: "It reads the code (read-only), writes a passport, and lists the skills, MCPs and CLIs it needs.", visual: {kind: "passport"}},
  {id: "05-trends", kicker: "Trends", color: C.cyan, lines: ["What developers", "use this week.", "Before it's old news."], accent: 1,
   sub: "Rising GitHub repos, Hacker News and Reddit. Public sources, no keys. Preview before you leave.", visual: {kind: "shot", src: "shot-trends.webp", from: [0, 0], to: [-2, -8], zoom: [1.03, 1.12]}},
  {id: "06-usage", kicker: "Usage", color: C.green, lines: ["See your tokens", "before the bill", "does."], accent: 1,
   sub: "By day, project and model — read from your own logs. Off until you turn it on.", visual: {kind: "bars"}},
  {id: "07-learn", kicker: "Learn", color: C.amber, lines: ["Seven ideas", "behind every", "AI tool."], accent: 0,
   sub: "Animated, clickable explanations — in English, Português, Français and Español.", visual: {kind: "langs"}},
  {id: "08-free", kicker: "Free · open source", color: C.pink, lines: ["Free today.", "REASON ONE", "in mid-December."], accent: 1,
   sub: "MIT licence, runs on your PC. VibeCoding is your head start — a thank-you to open source.", visual: {kind: "free"}},
];

const ease = Easing.bezier(0.2, 0.8, 0.2, 1);
const fade = (f: number, a: number, b: number) => interpolate(f, [a, b], [0, 1], {extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: ease});

const Stars: React.FC = () => {
  const f = useCurrentFrame(); const {width: W, height: H} = useVideoConfig();
  return <AbsoluteFill>{Array.from({length: 90}, (_, i) => {
    const x = random(`x${i}`) * W, y = random(`y${i}`) * H, r = random(`r${i}`) * 1.8 + 0.4, p = random(`p${i}`) * 6;
    return <div key={i} style={{position: "absolute", left: x, top: y - f * 0.15 * r, width: r * 2, height: r * 2, borderRadius: "50%", background: "#bfe8ff", opacity: 0.2 + 0.5 * Math.abs(Math.sin(f / 40 + p))}} />;
  })}</AbsoluteFill>;
};

const Chip: React.FC<{text: string; color: string; delay: number; big?: boolean}> = ({text, color, delay, big}) => {
  const f = useCurrentFrame(); const {fps} = useVideoConfig();
  const s = spring({frame: f - delay, fps, config: {damping: 16, mass: 0.7}});
  return <div style={{transform: `translateY(${(1 - s) * 30}px)`, opacity: s, display: "inline-flex", alignItems: "center", gap: 14, padding: big ? "22px 30px" : "16px 24px",
    borderRadius: 18, border: `1.5px solid ${color}66`, background: "rgba(10,16,30,.78)", boxShadow: `0 0 40px ${color}22`, fontFamily: F, fontWeight: 500, fontSize: big ? 40 : 32, color: C.txt}}>
    <span style={{width: 12, height: 12, borderRadius: 6, background: color, boxShadow: `0 0 14px ${color}`}} />{text}</div>;
};

const VisualView: React.FC<{v: Visual; color: string; vert: boolean}> = ({v, color, vert}) => {
  const f = useCurrentFrame(); const {fps} = useVideoConfig();
  const t = interpolate(f, [70, 260], [0, 1], {extrapolateLeft: "clamp", extrapolateRight: "clamp"});
  const enter = spring({frame: f - 60, fps, config: {damping: 18}});
  const box: React.CSSProperties = {width: "100%", height: "100%", display: "flex", alignItems: "center", justifyContent: "center", opacity: enter, transform: `translateY(${(1 - enter) * 40}px)`};
  if (v.kind === "shot") {
    const [z0, z1] = v.zoom || [1, 1.1], [x0, y0] = v.from || [0, 0], [x1, y1] = v.to || [0, 0];
    return <div style={box}><div style={{width: "100%", aspectRatio: "16 / 10", borderRadius: 26, overflow: "hidden", border: `1.5px solid ${color}88`, boxShadow: `0 40px 120px ${color}30`}}>
      <Img src={staticFile(v.src)} style={{width: "100%", height: "100%", objectFit: "cover", objectPosition: "left top",
        transform: `scale(${interpolate(t, [0, 1], [z0, z1])}) translate(${interpolate(t, [0, 1], [x0, x1])}%, ${interpolate(t, [0, 1], [y0, y1])}%)`, transformOrigin: "left top"}} /></div></div>;
  }
  if (v.kind === "chips") return <div style={{...box, flexDirection: "column", alignItems: vert ? "center" : "flex-start", gap: 22}}>
    {v.items.map((c, i) => <Chip key={c} text={c} color={[C.cyan, C.vio, C.pink][i % 3]} delay={70 + i * 18} big />)}</div>;
  if (v.kind === "passport") {
    const rows: [string, string, string][] = [["MISSION", "Booking API with login and email", C.txt], ["STACK", "Python · FastAPI · Postgres", C.txt], ["HAVE", "Supabase · FastAPI", C.green], ["MISSING", "Auth MCP · test runner · secret scan", C.pink]];
    return <div style={box}><div style={{width: vert ? 860 : 760, borderRadius: 26, border: `1.5px solid ${color}88`, background: "rgba(10,16,30,.85)", padding: 40, boxShadow: `0 40px 120px ${color}26`}}>
      <div style={{fontFamily: MONO, fontSize: 22, letterSpacing: 4, color}}>PROJECT PASSPORT</div>
      {rows.map(([k, val, col], i) => { const s = fade(f, 80 + i * 16, 100 + i * 16);
        return <div key={k} style={{opacity: s, transform: `translateX(${(1 - s) * 30}px)`, marginTop: 26, paddingTop: 22, borderTop: `1px dashed ${C.line}`}}>
          <div style={{fontFamily: MONO, fontSize: 18, letterSpacing: 3, color: C.dim}}>{k}</div>
          <div style={{fontFamily: F, fontSize: 34, fontWeight: 500, color: col, marginTop: 6}}>{val}</div></div>; })}
    </div></div>;
  }
  if (v.kind === "bars") {
    // an abstract chart: shapes only, no numbers — the real ones are the person's own
    const hs = [0.35, 0.5, 0.42, 0.7, 0.55, 0.9, 0.62, 0.78, 0.48, 0.66, 0.84, 0.58];
    return <div style={box}><div style={{width: "100%", height: vert ? 620 : 560, borderRadius: 26, border: `1.5px solid ${color}88`, background: "rgba(10,16,30,.85)", padding: 40, display: "flex", flexDirection: "column"}}>
      <div style={{fontFamily: MONO, fontSize: 22, letterSpacing: 4, color}}>TOKENS · LAST 30 DAYS</div>
      <div style={{flex: 1, display: "flex", alignItems: "flex-end", gap: 14, marginTop: 30}}>
        {hs.map((h, i) => { const g = fade(f, 80 + i * 6, 120 + i * 6); return <div key={i} style={{flex: 1, display: "flex", flexDirection: "column", justifyContent: "flex-end", height: "100%", gap: 4}}>
          <div style={{height: `${h * 45 * g}%`, background: C.vio, borderRadius: "8px 8px 2px 2px"}} />
          <div style={{height: `${h * 50 * g}%`, background: color, borderRadius: "2px 2px 8px 8px", boxShadow: `0 0 20px ${color}55`}} /></div>; })}
      </div>
      <div style={{display: "flex", gap: 30, marginTop: 24, fontFamily: F, fontSize: 26, color: C.mut}}><span><b style={{color}}>■</b> Claude Code</span><span><b style={{color: C.vio}}>■</b> Codex</span></div>
    </div></div>;
  }
  if (v.kind === "langs") {
    const ideas = ["LLM", "MCP", "CLI", "Skill", "Agent", "API", "RAG"], langs = ["English", "Português", "Français", "Español"];
    return <div style={{...box, flexDirection: "column", gap: 40}}>
      <div style={{display: "flex", flexWrap: "wrap", gap: 16, justifyContent: "center", maxWidth: 820}}>{ideas.map((x, i) => <Chip key={x} text={x} color={[C.amber, C.cyan, C.green, C.vio, C.pink][i % 5]} delay={70 + i * 9} />)}</div>
      <div style={{display: "flex", gap: 14, flexWrap: "wrap", justifyContent: "center"}}>{langs.map((l, i) => { const s = fade(f, 150 + i * 10, 170 + i * 10);
        return <div key={l} style={{opacity: s, fontFamily: MONO, fontSize: 28, padding: "12px 20px", borderRadius: 99, border: `1.5px solid ${C.line}`, color: i === Math.floor((f / 18) % 4) ? C.txt : C.mut, background: i === Math.floor((f / 18) % 4) ? "rgba(56,225,255,.16)" : "transparent"}}>{l}</div>; })}</div>
    </div>;
  }
  // free: the badge row and the REASON ONE date
  return <div style={{...box, flexDirection: "column", gap: 34}}>
    <div style={{display: "flex", gap: 16, flexWrap: "wrap", justifyContent: "center"}}>{["Free forever", "MIT", "Runs on your PC", "4 languages"].map((x, i) => <Chip key={x} text={x} color={[C.green, C.cyan, C.vio, C.amber][i]} delay={70 + i * 12} />)}</div>
    <div style={{opacity: fade(f, 140, 170), textAlign: "center", border: `1.5px solid ${C.pink}77`, borderRadius: 26, padding: "34px 50px", background: "radial-gradient(60% 80% at 50% 0,rgba(255,95,162,.18),transparent 70%), rgba(10,16,30,.85)"}}>
      <div style={{fontFamily: MONO, fontSize: 22, letterSpacing: 5, color: C.pink}}>COMING MID-DECEMBER</div>
      <div style={{fontFamily: F, fontWeight: 700, fontSize: 64, color: C.txt, marginTop: 10}}>REASON ONE</div>
      <div style={{fontFamily: F, fontSize: 28, color: C.mut, marginTop: 6}}>the studio · closed source</div>
    </div>
  </div>;
};

export const Launch: React.FC<{id: string}> = ({id}) => {
  const s = SCENES.find((x) => x.id === id)!;
  const f = useCurrentFrame(); const {fps, width, height, durationInFrames: D} = useVideoConfig();
  const vert = height > width;
  const outro = fade(f, D - 50, D - 32);            // the end card takes over in the last ~1.5 s
  const main = 1 - outro;
  const pad = vert ? 90 : 120;
  const head = vert ? 104 : 86;
  return (
    <AbsoluteFill style={{background: C.bg, fontFamily: F, color: C.txt, overflow: "hidden"}}>
      <AbsoluteFill style={{background: `radial-gradient(50% 45% at ${vert ? "50% 80%" : "78% 50%"}, ${s.color}26, transparent 70%), radial-gradient(40% 40% at 10% 0%, ${C.vio}22, transparent 70%)`}} />
      <Stars />
      {/* top bar: the brand, always visible */}
      <div style={{position: "absolute", top: vert ? 80 : 56, left: pad, right: pad, display: "flex", alignItems: "center", gap: 16, opacity: fade(f, 0, 14) * main}}>
        <Img src={staticFile("wordmark.svg")} style={{height: vert ? 40 : 34}} />
        <span style={{fontFamily: MONO, fontSize: vert ? 22 : 20, letterSpacing: 6, color: C.mut}}>/ VIBECODING</span>
        <span style={{marginLeft: "auto", fontFamily: MONO, fontSize: vert ? 22 : 20, letterSpacing: 3, color: s.color}}>{SCENES.indexOf(s) + 1} / 8</span>
      </div>
      {/* text block */}
      <div style={{position: "absolute", left: pad, top: vert ? 250 : 0, bottom: vert ? undefined : 0, width: vert ? width - pad * 2 : width * 0.47, display: "flex", flexDirection: "column", justifyContent: "center", opacity: main}}>
        <div style={{fontFamily: MONO, fontSize: vert ? 30 : 26, letterSpacing: 6, textTransform: "uppercase", color: s.color, opacity: fade(f, 6, 20)}}>{s.kicker}</div>
        <div style={{marginTop: 22}}>{s.lines.map((l, i) => { const sp = spring({frame: f - 12 - i * 10, fps, config: {damping: 15, mass: 0.8}});
          return <div key={i} style={{fontSize: head, fontWeight: 700, lineHeight: 1.04, letterSpacing: -2, transform: `translateY(${(1 - sp) * 50}px)`, opacity: sp,
            ...(i === s.accent ? {background: `linear-gradient(110deg, ${s.color}, ${C.vio} 70%, ${C.pink})`, WebkitBackgroundClip: "text", backgroundClip: "text", color: "transparent"} : {})}}>{l}</div>; })}</div>
        <div style={{marginTop: 34, fontSize: vert ? 36 : 32, lineHeight: 1.4, color: C.mut, maxWidth: vert ? undefined : 720, opacity: fade(f, 48, 66), transform: `translateY(${(1 - fade(f, 48, 66)) * 20}px)`}}>{s.sub}</div>
      </div>
      {/* visual */}
      <div style={{position: "absolute", opacity: main, ...(vert ? {left: pad, right: pad, top: 980, bottom: 160} : {left: width * 0.55, right: pad, top: 170, bottom: 150})}}>
        <VisualView v={s.visual} color={s.color} vert={vert} />
      </div>
      {/* end card */}
      <AbsoluteFill style={{opacity: outro, alignItems: "center", justifyContent: "center", flexDirection: "column", gap: 28}}>
        <Img src={staticFile("logo.svg")} style={{width: vert ? 200 : 170, transform: `scale(${0.9 + 0.1 * outro})`}} />
        <Img src={staticFile("wordmark.svg")} style={{height: vert ? 64 : 58}} />
        <div style={{fontFamily: MONO, fontSize: vert ? 30 : 28, letterSpacing: 8, color: C.mut}}>VIBECODING</div>
        <div style={{display: "flex", gap: 14, marginTop: 10}}>{["FREE", "OPEN SOURCE", "MIT"].map((x) => <span key={x} style={{fontFamily: MONO, fontSize: vert ? 24 : 22, letterSpacing: 3, padding: "10px 18px", borderRadius: 99, border: `1.5px solid ${C.line}`, color: C.txt}}>{x}</span>)}</div>
        <div style={{fontFamily: F, fontSize: vert ? 34 : 32, color: s.color, marginTop: 6}}>github · reason-o1-vibecoding</div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
