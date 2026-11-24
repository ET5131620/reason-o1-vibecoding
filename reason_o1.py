#!/usr/bin/env python3
"""REASON O1 / VIBECODING — local dashboard of your AI ecosystem.

  python reason_o1.py          open the dashboard (http://127.0.0.1:8731)
  python reason_o1.py mcp      run as an MCP server (for Claude Code / Codex)
  python reason_o1.py scan     print the inventory as JSON

Standard library only. Binds to 127.0.0.1. Every API call needs the session token.
"""
from __future__ import annotations

import json
import os
import re
import secrets
import shutil
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from o1 import core, studio, trends, updater, usage
from o1.about import ABOUT

UI = core.ROOT / "ui"
TOKEN = secrets.token_urlsafe(24)
PORT = 8731
GH_CACHE = core.APP_DIR / "gh_cache.json"
_gh_lock = threading.Lock()
_inv_lock = threading.Lock()
REPO_RE = re.compile(r"^[A-Za-z0-9_.-]{1,100}/[A-Za-z0-9_.-]{1,100}$")
MIME = {".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8", ".css": "text/css; charset=utf-8",
        ".svg": "image/svg+xml", ".png": "image/png", ".json": "application/json; charset=utf-8", ".ico": "image/x-icon", ".webp": "image/webp", ".webmanifest": "application/manifest+json"}


def http_json(url: str, timeout=12):
    req = urllib.request.Request(url, headers={"User-Agent": "reason-o1", "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def gh_repo(repo: str) -> dict:
    """Live repo facts (stars, licence, owner avatar), cached for a day. Falls back to ungh.cc when the API rate-limits."""
    with _gh_lock:
        cache = core.load_json(GH_CACHE, {}) or {}
        hit = cache.get(repo)
        if hit and time.time() - hit.get("_t", 0) < 86400:
            return hit
    try:
        d = http_json(f"https://api.github.com/repos/{repo}")
        out = {"stars": d.get("stargazers_count"), "licenca": (d.get("license") or {}).get("spdx_id"), "desc": d.get("description"),
               "autor": (d.get("owner") or {}).get("login"), "avatar": (d.get("owner") or {}).get("avatar_url"),
               "pushed": (d.get("pushed_at") or "")[:10], "arquivado": d.get("archived"), "nome": d.get("full_name")}
    except Exception:
        try:
            d = http_json(f"https://ungh.cc/repos/{repo}")["repo"]
            owner = (d.get("repo") or repo).split("/")[0]
            out = {"stars": d.get("stars"), "licenca": None, "desc": d.get("description"), "autor": owner,
                   "avatar": f"https://github.com/{owner}.png?size=64", "pushed": (d.get("pushedAt") or "")[:10], "nome": d.get("repo")}
        except Exception as e:
            return {"erro": str(e)[:120]}
    out["_t"] = time.time()
    with _gh_lock:
        cache = core.load_json(GH_CACHE, {}) or {}
        cache[repo] = out
        core.APP_DIR.mkdir(parents=True, exist_ok=True)
        GH_CACHE.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
    return out


def gh_readme(repo: str) -> dict:
    """The first part of a repository's README as plain text, for a preview before opening GitHub."""
    import re
    try:
        req = urllib.request.Request(f"https://api.github.com/repos/{repo}/readme",
                                     headers={"User-Agent": "reason-o1", "Accept": "application/vnd.github.raw"})
        with urllib.request.urlopen(req, timeout=12) as r:
            txt = r.read(60000).decode("utf-8", "replace")
    except Exception as e:
        return {"erro": str(e)[:120]}
    txt = re.sub(r"<!--.*?-->", "", txt, flags=re.S)
    txt = re.sub(r"<[^>]+>", "", txt)                    # html (badges, centred blocks)
    txt = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", txt)       # images and badges
    txt = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", txt)   # links -> their text
    out, blank = [], 0
    for line in txt.splitlines():
        blank = blank + 1 if not line.strip() else 0
        if blank < 2:
            out.append(line.rstrip())
    return {"texto": "\n".join(out).strip()[:2600]}


def check_update() -> dict:
    return updater.check()


def engines() -> dict:
    return {"claude": bool(shutil.which("claude")), "codex": bool(shutil.which("codex"))}


def ask(engine: str, prompt: str, cwd: str | None) -> dict:
    """Runs the user's own Claude Code / Codex in read-only mode. The prompt goes through stdin, never through the command line."""
    exe = shutil.which(engine)
    if engine not in ("claude", "codex") or not exe:
        return {"erro": f"{engine} não está instalado neste PC."}
    if engine == "claude":
        cmd = [exe, "-p", "--output-format", "text", "--disallowedTools", "Bash,Edit,Write,NotebookEdit,MultiEdit"]
    else:
        cmd = [exe, "exec", "--sandbox", "read-only", "--skip-git-repo-check", "-"]
    work = cwd if cwd and Path(cwd).is_dir() else str(core.HOME)
    try:
        r = subprocess.run(cmd, input=prompt, capture_output=True, text=True, encoding="utf-8", errors="replace",
                           timeout=600, cwd=work, creationflags=0x08000000 if core.IS_WIN else 0)
    except subprocess.TimeoutExpired:
        return {"erro": "Demorou mais de 10 minutos. Experimenta no terminal."}
    out = (r.stdout or "").strip()
    return {"resposta": out[:200000] or (r.stderr or "").strip()[:4000], "codigo": r.returncode}


def _short(p: Path) -> str:
    """Path shown on screen: the home folder becomes ~ and only the last two folders show, so a screenshot
    doesn't carry the account name or a synced-drive folder named after an email. The full path is on hover."""
    p = Path(p).resolve()
    try:
        parts = p.relative_to(Path.home().resolve()).parts
        head = "~"
    except ValueError:
        parts, head = p.parts[1:], p.anchor.rstrip("\\/")
    return os.sep.join([head, *(["…"] if len(parts) > 2 else []), *parts[-2:]])


def state() -> dict:
    cfg = core.load_config()
    return {"about": ABOUT, "config": cfg, "engines": engines(), "pastas": core.FOLDERS,
            "mcp_cmd": f'python "{core.ROOT / "reason_o1.py"}" mcp', "raiz": str(core.ROOT),
            "raiz_curta": _short(core.ROOT), "ultima_atualizacao": updater.last_update()}


class Handler(BaseHTTPRequestHandler):
    server_version = "ReasonO1"

    def log_message(self, *a):
        pass

    def _send(self, code: int, body: bytes, ctype="application/json; charset=utf-8"):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, obj, code=200):
        self._send(code, json.dumps(obj, ensure_ascii=False).encode("utf-8"))

    def _host_ok(self) -> bool:  # blocks DNS-rebinding: only our own address may talk to us
        return self.headers.get("Host", "") in (f"127.0.0.1:{PORT}", f"localhost:{PORT}")

    def _auth(self) -> bool:
        return self._host_ok() and secrets.compare_digest(self.headers.get("X-O1-Token", ""), TOKEN)

    def _body(self) -> dict:
        n = min(int(self.headers.get("Content-Length") or 0), 2_000_000)
        try:
            return json.loads(self.rfile.read(n).decode("utf-8") or "{}")
        except Exception:
            return {}

    def do_GET(self):
        if not self._host_ok():
            return self._send(403, b"forbidden", "text/plain")
        u = urlparse(self.path)
        q = {k: v[0] for k, v in parse_qs(u.query).items()}
        if u.path in ("/", "/index.html"):
            html = (UI / "index.html").read_text(encoding="utf-8").replace("__O1_TOKEN__", TOKEN)
            return self._send(200, html.encode("utf-8"), MIME[".html"])
        if u.path == "/sw.js":  # na raiz, para o service worker abranger a app toda
            return self._send(200, (UI / "sw.js").read_bytes(), MIME[".js"])
        if u.path.startswith("/ui/"):
            f = (UI / u.path[4:]).resolve()
            if UI.resolve() in f.parents and f.is_file():
                return self._send(200, f.read_bytes(), MIME.get(f.suffix.lower(), "application/octet-stream"))
            return self._send(404, b"not found", "text/plain")
        if not u.path.startswith("/api/"):
            return self._send(404, b"not found", "text/plain")
        if not self._auth():
            return self._json({"erro": "sem autorização"}, 401)
        try:
            if u.path == "/api/state":
                return self._json(state())
            if u.path == "/api/inventory":
                inv = None if q.get("refresh") else core.cached_inventory()
                if not inv:
                    with _inv_lock:
                        inv = core.inventory()
                return self._json(inv)
            if u.path == "/api/kits":
                return self._json(core.kits())
            if u.path == "/api/catalog":
                return self._json(core.catalog())
            if u.path == "/api/snapshot":
                return self._json(core.load_json(core.DATA / "gh_snapshot.json", {}))
            if u.path == "/api/readme":
                r = q.get("r", "")
                return self._json(gh_readme(r) if REPO_RE.match(r) else {"erro": "repo inválido"})
            if u.path == "/api/gh":
                r = q.get("r", "")
                return self._json(gh_repo(r) if REPO_RE.match(r) else {"erro": "repo inválido"})
            if u.path == "/api/update":
                return self._json(check_update())
            if u.path == "/api/search":
                return self._json(core.search_catalog(q.get("q", "")))
            if u.path == "/api/mine":
                return self._json(studio.mine())
            if u.path == "/api/trends":
                return self._json(trends.trends(bool(q.get("refresh"))))
            if u.path == "/api/usage":
                return self._json(usage.usage(bool(q.get("refresh"))))
            if u.path == "/api/providers":
                return self._json(usage.providers())
            if u.path == "/api/mykits":
                return self._json(studio.user_kits())
            if u.path == "/api/prompts":
                return self._json(studio.prompts_list())
            if u.path == "/api/cookbook":
                return self._json(studio.cookbook_status())
        except Exception as e:
            return self._json({"erro": str(e)}, 500)
        return self._json({"erro": "rota desconhecida"}, 404)

    def do_POST(self):
        if not self._auth():
            return self._json({"erro": "sem autorização"}, 401)
        u = urlparse(self.path)
        b = self._body()
        try:
            if u.path == "/api/config":
                return self._json(core.save_config(b))
            if u.path == "/api/setup":
                cfg = core.save_config(b)
                made = core.create_folders(cfg["base_dir"])
                core.save_config({"setup_done": True})
                return self._json({"ok": True, **made})
            if u.path == "/api/passport":
                adv = core.advise(str(b.get("caminho", "")))
                return self._json({**adv, "prompt": core.advice_prompt(str(b.get("caminho", "")), adv)})
            if u.path == "/api/ask":
                return self._json(ask(str(b.get("motor", "")), str(b.get("prompt", ""))[:60000], b.get("cwd")))
            if u.path == "/api/update/apply":
                return self._json(updater.apply())
            if u.path == "/api/restart":
                threading.Thread(target=restart, args=(self.server,), daemon=True).start()
                return self._json({"ok": True})
            if u.path == "/api/kit/suggest":
                return self._json(studio.suggest(str(b.get("objetivo", ""))[:2000]))
            if u.path == "/api/kit/save":
                return self._json(studio.save_kit(b))
            if u.path == "/api/prompt/generate":
                return self._json({"prompt": studio.kit_prompt(str(b.get("objetivo", ""))[:2000], [str(x) for x in b.get("kits", [])][:8], str(b.get("nivel", "completo")))})
            if u.path == "/api/prompt/save":
                return self._json(studio.prompt_save(str(b.get("titulo", "")), str(b.get("texto", ""))[:60000], str(b.get("tags", ""))))
            if u.path == "/api/skill/create":
                return self._json(studio.skill_create(str(b.get("nome", "")), str(b.get("descricao", "")), [str(x) for x in b.get("passos", [])], str(b.get("quando", ""))))
            if u.path == "/api/cookbook/clone":
                return self._json(studio.cookbook_clone())
            if u.path == "/api/trends/prompt":
                return self._json({"prompt": trends.research_prompt(str(b.get("tema", "")))})
            if u.path == "/api/report":
                return self._json({"guardado": core.save_report(str(b.get("titulo", "relatorio")), str(b.get("markdown", "")))})
        except ValueError as e:
            return self._json({"erro": str(e)}, 400)
        except Exception as e:
            return self._json({"erro": str(e)}, 500)
        return self._json({"erro": "rota desconhecida"}, 404)


def restart(httpd):
    """Start a fresh copy of the (possibly updated) program, then let this one go."""
    time.sleep(0.4)
    subprocess.Popen([sys.executable, str(core.ROOT / "reason_o1.py"), "--no-browser", f"--port={PORT}"], cwd=str(core.ROOT),
                     creationflags=0x00000008 if core.IS_WIN else 0)  # DETACHED_PROCESS
    httpd.shutdown()


def startup_update():
    """On every launch: if the official repo has a newer release and auto-update is on, install it and relaunch."""
    if not ABOUT.get("repo") or not core.load_config().get("auto_update", True):
        return False
    info = updater.check(timeout=6)
    if info.get("estado") != "nova":
        return False
    res = updater.apply(info)
    print(res.get("texto", ""))
    if res.get("ok"):
        args = [a for a in sys.argv[1:]]
        subprocess.Popen([sys.executable, str(core.ROOT / "reason_o1.py"), *args], cwd=str(core.ROOT))
        return True
    return False


def serve(open_browser=True, want_port=8731):
    global PORT
    httpd = None
    deadline = time.time() + (6 if want_port != 8731 else 0)
    while not httpd:  # after a restart, wait for the old process to free its port
        for port in [want_port] + [p for p in range(8731, 8741) if p != want_port]:
            try:
                httpd = ThreadingHTTPServer(("127.0.0.1", port), Handler)
                PORT = port
                break
            except OSError:
                if time.time() < deadline:
                    break
                continue
        if not httpd and time.time() < deadline:
            time.sleep(0.3)
        elif not httpd:
            break
    if not httpd:
        sys.exit("Não encontrei uma porta livre entre 8731 e 8740.")
    threading.Thread(target=updater.sync, daemon=True).start()
    url = f"http://127.0.0.1:{PORT}/"
    try:  # sem consola UTF-8 (atalho, pipe), o print com "→" rebentava o arranque
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    print(f"REASON O1 / VIBECODING {ABOUT['version']} → {url}  (Ctrl+C para fechar)")
    if open_browser:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nFechado.")


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else "serve"
    if arg == "mcp":
        from o1 import mcp_server
        mcp_server.serve()
    elif arg == "scan":
        sys.stdout.reconfigure(encoding="utf-8")
        print(json.dumps(core.inventory(), ensure_ascii=False, indent=1))
    else:
        if "--skip-update" not in sys.argv and startup_update():
            sys.exit(0)
        port = next((int(a.split("=", 1)[1]) for a in sys.argv if a.startswith("--port=")), 8731)
        serve(open_browser="--no-browser" not in sys.argv, want_port=port)
