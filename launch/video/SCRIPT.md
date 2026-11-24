# Launch film — script (v2, narrated)

Voice: `en-US-ChristopherNeural` (edge-tts, free), rate −8 %, pitch −4 Hz — senior, calm.
Structure: **problem → turn → demo in the real app → result → thanks**. About 105 s.
Every line lives in `src/script.ts`; `python voice.py en` regenerates the audio and the timing.

| # | Narration | On screen |
|---|---|---|
| f01 | Most AI projects don't fail because of the code. | Dark space, the words light up as they're spoken. A low drone. |
| f02 | They fail long before the first line... in the setup. | A line of code is typed, then struck through. |
| f03 | Too many tools. The wrong ones. Settings that quietly weigh the whole system down. | Tool chips (MCP, CLI, skills, plugins…) rain down and pile up. |
| f04 | And if you don't know exactly where you're going... you burn days, and tokens, building in the dark. | A token counter racing; a dotted path that goes nowhere. |
| f05 | So... what if the setup came first? | **Burst**: white core, blue halo, the REASON O1 logo. |
| f06 | REASON O1 reads your machine. Every model, agent, skill, MCP server and CLI... on one living map. | Real Overview screen. Cursor clicks **Scan again**; a scan sweeps the map; "found on this PC". |
| f07 | Say you want to build a web page. Open Kits... and choose the goal. | Cursor → **Kits** → the kits grid → clicks **UI/UX web design**. |
| f08 | It shows what you already have, what's missing, and why each tool is there. Nothing extra. Nothing that weighs you down. | The kit: rings on "you have it", "missing" and "the why". |
| f09 | Then the step by step. In the right order. | Cursor clicks **Step by step**; five steps appear with ticks. |
| f10 | Now point the Council at your project. It reads it, writes its passport, and tells you exactly what it needs. | **Council** → types the project folder → **Analyse project** → "Reading the project…" → passport and gaps. |
| f11 | Fewer errors. Less waste. And a faster road to the result you actually want. | Three cards. |
| f12 | REASON O1. VibeCoding. Free, open source, and running on your own PC. | Logo, chips, repository address. |
| f13 | A thank-you to the open source community... and your head start before REASON ONE, arriving in mid-December. | REASON ONE card. |

## The 8 cuts (~18–25 s each, for social)

| Cut | Beats |
|---|---|
| c01-why | f01 · f02 · f03 · f05 |
| c02-map | "You can't build well with tools you can't even see." · f06 · "Know what you have. Before you add more." |
| c03-kits | "Thousands of tools out there. Which ones does your project really need?" · f07 · f08 |
| c04-steps | "The right tools, in the wrong order... still fail." · f09 · "Setup first. Then code." |
| c05-council | "Every project has a mission. Does your setup know it?" · f10 · "Read-only. Local. Yours." |
| c06-trends | "New tools every week. Most of them are noise." · Trends screen with the cursor |
| c07-usage | "The bill always arrives after the damage." · token chart |
| c08-free | "Seven ideas sit behind every AI tool. Learn them, in four languages." · f12 · f13 |

Each ends on the logo card with `github.com/ET5131620/reason-o1-vibecoding`.

## Sound
Voice + synthesised effects only (`voice.py sfx`): click, whoosh on transitions, a low boom on the burst, a quiet drone under the problem part. No music, nothing to license.

## Privacy in the captures
Screens recorded in English from the running app. The Council runs on a demo folder (`my-landing-page`); the real folder path and the MCP command paths were masked before capture. The Usage view (real token numbers) is not used — the chart is abstract.
