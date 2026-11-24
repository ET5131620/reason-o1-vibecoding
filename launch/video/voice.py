"""Makes the narration and the sound effects for the launch videos.

    python voice.py en        # all English lines
    python voice.py pt f05    # one Portuguese line

Reads the lines from src/script.ts, speaks them with edge-tts (free Microsoft voices),
and writes each clip's length to src/durations.json so the video timing follows the voice.
Sound effects are synthesised with ffmpeg, so there is nothing to license.
"""
import json, re, subprocess, sys
from pathlib import Path

HERE = Path(__file__).parent
# v2.1: a little faster and brighter (more energy), same voices
VOICE = {"en": ("en-US-ChristopherNeural", "+6%", "-1Hz"), "pt": ("pt-PT-DuarteNeural", "+6%", "+0Hz")}


def lines(lang):
    src = (HERE / "src" / "script.ts").read_text(encoding="utf-8")
    block = re.search(r"export const LINES.*?\n  %s: \{(.*?)\n  \}," % lang, src, re.S).group(1)
    return dict(re.findall(r'^\s+(\w+): "(.*)",\s*$', block, re.M))


def seconds(f):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(f)], capture_output=True, text=True).stdout
    return round(float(out.strip()), 3)


def speak(lang, only=None):
    voice, rate, pitch = VOICE[lang]
    out = HERE / "public" / "voice" / lang
    out.mkdir(parents=True, exist_ok=True)
    durs_file = HERE / "src" / "durations.json"
    durs = json.loads(durs_file.read_text(encoding="utf-8")) if durs_file.exists() else {}
    durs.setdefault(lang, {})
    for key, text in lines(lang).items():
        if only and key != only:
            continue
        f = out / f"{key}.mp3"
        raw = out / f"{key}.raw.mp3"
        subprocess.run([sys.executable, "-m", "edge_tts", "--voice", voice, f"--rate={rate}", f"--pitch={pitch}", "--text", text, "--write-media", str(raw)], check=True, capture_output=True)
        # trim the dead air the TTS leaves at both ends, keeping a tiny tail so words don't clip
        trim = "silenceremove=start_periods=1:start_threshold=-45dB,areverse,silenceremove=start_periods=1:start_threshold=-45dB,areverse,apad=pad_dur=0.08"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(raw), "-af", trim, "-b:a", "128k", str(f)], check=True)
        raw.unlink()
        durs[lang][key] = seconds(f)
        print(f"{lang}/{key}  {durs[lang][key]:5.2f}s  {text[:60]}")
    durs_file.write_text(json.dumps(durs, indent=1), encoding="utf-8")


def sfx():
    out = HERE / "public" / "sfx"
    out.mkdir(parents=True, exist_ok=True)
    recipes = {
        # a soft mouse click: a very short filtered tick
        "click.wav": "anoisesrc=d=0.04:c=white:a=0.6,highpass=f=1800,lowpass=f=6000,afade=t=out:st=0.005:d=0.035",
        # a whoosh for transitions: pink noise swept through a band-pass
        "whoosh.wav": "anoisesrc=d=0.7:c=pink:a=0.5,bandpass=f=900:w=1.2,afade=t=in:d=0.35,afade=t=out:st=0.35:d=0.35",
        # the burst: a deep sine drop with a long tail
        "boom.wav": "sine=f=55:d=2.4,volume=1.4,afade=t=in:d=0.02,afade=t=out:st=0.3:d=2.1",
        # a quiet bed tone under the problem part, so the silence feels deliberate
        "drone.wav": "sine=f=82.4:d=12,volume=0.18,tremolo=f=0.25:d=0.5,afade=t=in:d=2,afade=t=out:st=9:d=3",
    }
    # background music, made here so there is nothing to license: a warm minor pad that breathes,
    # a soft pulse at 112 bpm and a little air. It is mixed in at the end (render.mjs) and ducks under the voice.
    beat = "0.5357"
    pad = "+".join(f"{a}*sin(2*PI*{f}*t)*(0.55+0.45*sin(2*PI*{l}*t+{p}))" for a, f, l, p in
                   [(0.10, 110, 0.05, 0), (0.07, 164.81, 0.07, 1), (0.06, 220, 0.09, 2), (0.045, 261.63, 0.06, 3), (0.04, 329.63, 0.11, 4), (0.025, 493.88, 0.13, 5)])
    kick = f"0.55*sin(2*PI*(45+90*exp(-mod(t,{beat})*28))*mod(t,{beat}))*exp(-mod(t,{beat})*8)*min(1,t/6)"
    recipes["music.wav"] = (f"aevalsrc='{pad}+{kick}':s=48000:d=140,aecho=0.8:0.6:90|180:0.25|0.15,"
                            "lowpass=f=4200,highpass=f=35,afade=t=in:d=1.5,afade=t=out:st=136:d=4,volume=1.6")
    for name, chain in recipes.items():
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", chain, "-ac", "2", "-ar", "48000", str(out / name)], check=True)
        print("sfx", name)


if __name__ == "__main__":
    if sys.argv[1] == "sfx":
        sfx()
    else:
        speak(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
