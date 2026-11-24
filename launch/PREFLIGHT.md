# Pre-publish check · v1.0.0 · 2026-11-23

Scanned: the exact set of files that goes to GitHub (84 files, 24 MB — everything except `node_modules/`, `launch/video/out/`, `__pycache__/` and the translation work files `ui/i18n/_*.json`).

| Check | Tool | Result |
|---|---|---|
| Secrets (keys, tokens, passwords) | gitleaks 8.30.1 `dir` | **No leaks found** |
| Personal data (author's e-mail, Windows user, private folder names, private `ET_` projects) | text search | **None** in text files. Five hits inside MP4 files were random video bytes (`Et_`, `eT_`), not data. |
| Screenshots used on the site and in the videos | manual review | Only Overview, Kits, Trends and Learn, in English. Usage (real token numbers) was left out on purpose. |
| Four languages | `python tools/i18n.py` | 1863/1863 texts in EN, FR and ES |
| User data in the repo | `.gitignore` | `config.json`, `inventory.json`, `gh_cache.json` and `.env*` are ignored; settings live in `~/.reason-o1/` |
| Licence | `LICENSE` | MIT, © 2026 531620ET · Godmode. Fonts on the site and in the videos: Space Grotesk and JetBrains Mono (SIL OFL), loaded from Google Fonts. Videos have no music. |

Before each future release: run `gitleaks dir` on the publish set and `python tools/i18n.py`.
