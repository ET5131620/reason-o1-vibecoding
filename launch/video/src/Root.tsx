import React from "react";
import {Composition} from "remotion";
import {Launch, SCENES} from "./Launch";
import {CUTS, FILM, FPS, totalFrames, Video} from "./Film";
import type {Lang} from "./script";

// v2 (narrated): the film (problem -> turn -> demo -> result) and 8 short cuts, per language,
// in 16:9 (GitHub, YouTube, LinkedIn) and 9:16 (Reels, TikTok, Shorts). Length follows the voice.
const LANGS: Lang[] = ["en", "pt"];
const SHAPES = [["h", 1920, 1080], ["v", 1080, 1920]] as const;

export const Root: React.FC = () => (
  <>
    {LANGS.map((lang) => [["film", FILM] as const, ...Object.entries(CUTS)].map(([name, beats]) => SHAPES.map(([s, w, h]) => {
      const d = totalFrames(lang, beats);
      return d > 60 ? <Composition key={`${name}-${lang}-${s}`} id={`${name}-${lang}-${s}`} component={Video} durationInFrames={d} fps={FPS} width={w} height={h} defaultProps={{lang, beats}} /> : null;
    })))}
    {/* v1: the 8 silent 9-second cards, kept as they were */}
    {SCENES.map((s) => (
      <React.Fragment key={s.id}>
        <Composition id={`${s.id}-h`} component={Launch} durationInFrames={9 * 30} fps={30} width={1920} height={1080} defaultProps={{id: s.id}} />
        <Composition id={`${s.id}-v`} component={Launch} durationInFrames={9 * 30} fps={30} width={1080} height={1920} defaultProps={{id: s.id}} />
      </React.Fragment>
    ))}
  </>
);
