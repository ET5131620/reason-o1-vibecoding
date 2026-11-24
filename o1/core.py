"""REASON O1 core: inventory of the local AI ecosystem, project passport and advice.

Read-only by design. Only names, counts and dates are collected:
no keys, no environment variables, no MCP arguments, no conversation content.
"""
from __future__ import annotations

import json
import os
import platform
import re
import shutil
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
HOME = Path.home()
APP_DIR = HOME / ".reason-o1"
CONFIG_FILE = APP_DIR / "config.json"
IS_WIN = platform.system() == "Windows"
IS_MAC = platform.system() == "Darwin"
APPDATA = Path(os.environ.get("APPDATA", HOME / "AppData/Roaming"))
LOCALAPPDATA = Path(os.environ.get("LOCALAPPDATA", HOME / "AppData/Local"))
SKIP_DIRS = {"node_modules", ".git", "__pycache__", ".venv", "venv", "dist", "build", ".next", "target", ".cache"}

FOLDERS = {
    "skills": "01_SKILLS", "mcp": "02_MCP", "cli": "03_CLI", "agentes": "04_AGENTES", "llm": "05_LLM",
    "projetos": "06_PROJETOS", "prompts": "07_PROMPTS", "relatorios": "08_RELATORIOS", "kits": "09_KITS",
}

DEFAULT_CONFIG = {
    "setup_done": False,
    "owner": {"nome": "", "email": ""},
    "base_dir": str(HOME / "REASON_O1"),
    "project_roots": [str(p) for p in (HOME / "Documents", HOME / "Projects", HOME / "dev", HOME / "source" / "repos", HOME / "Desktop") if p.exists()],
    "consent": {"ferramentas": True, "projetos": True, "conversas": True},
    "auto_update": True,
}


# ---------- config ----------

def load_json(p: Path, default=None):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return default


def load_config() -> dict:
    cfg = json.loads(json.dumps(DEFAULT_CONFIG))
    saved = load_json(CONFIG_FILE, {}) or {}
    for k, v in saved.items():
        if isinstance(v, dict) and isinstance(cfg.get(k), dict):
            cfg[k].update(v)
        else:
            cfg[k] = v
    return cfg


def save_config(patch: dict) -> dict:
    cfg = load_config()
    # "termos": data em que a pessoa aceitou o termo de responsabilidade (texto em TERMOS.md)
    allowed = {"setup_done", "owner", "base_dir", "project_roots", "consent", "auto_update", "termos"}
    for k, v in patch.items():
        if k not in allowed:
            continue
        if isinstance(v, dict) and isinstance(cfg.get(k), dict):
            cfg[k].update({kk: vv for kk, vv in v.items() if isinstance(vv, (str, bool))})
        elif k == "project_roots" and isinstance(v, list):
            cfg[k] = [str(x) for x in v if isinstance(x, str) and x.strip()][:20]
        elif isinstance(v, (str, bool)):
            cfg[k] = v
    APP_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    return cfg


def create_folders(base_dir: str) -> dict:
    base = Path(base_dir).expanduser()
    made = []
    for key, name in FOLDERS.items():
        d = base / name
        d.mkdir(parents=True, exist_ok=True)
        made.append(str(d))
    readme = base / "LEIA-ME.txt"
    if not readme.exists():
        readme.write_text("Pasta do REASON O1 / VIBECODING.\nCada tipo de ficheiro tem a sua pasta numerada.\n", encoding="utf-8")
    return {"base": str(base), "pastas": made}


def folder_for(cat: str) -> Path:
    return Path(load_config()["base_dir"]).expanduser() / FOLDERS.get(cat, FOLDERS["kits"])


# ---------- small helpers ----------

def mtime(p: Path) -> str:
    try:
        return time.strftime("%Y-%m-%d", time.localtime(p.stat().st_mtime))
    except OSError:
        return ""


def frontmatter(text: str) -> dict:
    m = re.match(r"^---\s*\n(.*?)\n---", text, re.S)
    out = {}
    if m:
        for line in m.group(1).splitlines():
            mm = re.match(r"^(name|description):\s*(.*)$", line.strip())
            if mm:
                out[mm.group(1)] = mm.group(2).strip().strip('"').strip("'")
    return out


def walk(top: Path, maxdepth: int):
    top = Path(top)
    base = len(top.parts)
    for d, dirs, files in os.walk(top):
        depth = len(Path(d).parts) - base
        dirs[:] = [x for x in dirs if x not in SKIP_DIRS and not x.startswith(".") or x in {".claude", ".codex", ".cursor"}]
        if depth >= maxdepth:
            dirs[:] = []
        yield Path(d), dirs, files


def skills_under(top: Path, source: str, maxdepth: int = 6) -> list[dict]:
    out = []
    if not top.exists():
        return out
    for d, _dirs, files in walk(top, maxdepth):
        if "SKILL.md" in files:
            try:
                fm = frontmatter((d / "SKILL.md").read_text(encoding="utf-8", errors="ignore")[:4000])
            except OSError:
                fm = {}
            out.append({"nome": fm.get("name") or d.name, "desc": (fm.get("description") or "")[:240],
                        "onde": source, "caminho": str(d), "data": mtime(d / "SKILL.md")})
    return out


def which(cmd: str) -> str | None:
    return shutil.which(cmd)


# ---------- inventory ----------

def detect_apps() -> list[dict]:
    def any_path(*ps):
        for p in ps:
            if p and Path(p).exists():
                return str(p)
        return None
    pkgs = LOCALAPPDATA / "Packages"
    chatgpt_pkg = next(iter(pkgs.glob("OpenAI.ChatGPT*")), None) if pkgs.exists() else None
    apps = [
        ("Claude Code", "agente", which("claude") or any_path(HOME / ".claude")),
        ("Codex", "agente", which("codex") or any_path(HOME / ".codex")),
        ("Gemini CLI", "agente", which("gemini") or any_path(HOME / ".gemini")),
        ("Claude Desktop", "chat", any_path(APPDATA / "Claude", LOCALAPPDATA / "AnthropicClaude", "/Applications/Claude.app")),
        ("ChatGPT Desktop", "chat", any_path(chatgpt_pkg, LOCALAPPDATA / "Programs/ChatGPT", "/Applications/ChatGPT.app")),
        ("Cursor", "editor", which("cursor") or any_path(HOME / ".cursor", LOCALAPPDATA / "Programs/cursor", "/Applications/Cursor.app")),
        ("Windsurf", "editor", which("windsurf") or any_path(HOME / ".codeium/windsurf")),
        ("VS Code", "editor", which("code") or any_path(LOCALAPPDATA / "Programs/Microsoft VS Code", "/Applications/Visual Studio Code.app")),
        ("Ollama", "llm", which("ollama") or any_path(HOME / ".ollama")),
        ("LM Studio", "llm", which("lms") or any_path(HOME / ".lmstudio", HOME / ".cache/lm-studio")),
        ("Jan", "llm", any_path(APPDATA / "Jan", HOME / "jan")),
    ]
    return [{"nome": n, "tipo": t, "instalado": bool(p), "onde": p or ""} for n, t, p in apps]


def _mcp_entry(name, spec, where):
    spec = spec if isinstance(spec, dict) else {}
    if spec.get("url") or spec.get("type") in ("http", "sse"):
        kind, via = "http", re.sub(r"^https?://([^/:@]+@)?([^/]+).*$", r"\2", str(spec.get("url", "")))
    else:
        kind, via = "stdio", Path(str(spec.get("command", ""))).name
    return {"nome": name, "tipo": kind, "via": via, "onde": where}


def scan_mcp() -> list[dict]:
    out = []
    cj = load_json(HOME / ".claude.json", {}) or {}
    for n, s in (cj.get("mcpServers") or {}).items():
        out.append(_mcp_entry(n, s, "Claude Code"))
    for proj, pdata in (cj.get("projects") or {}).items():
        for n, s in ((pdata or {}).get("mcpServers") or {}).items():
            out.append(_mcp_entry(n, s, f"Claude Code · {Path(proj).name}"))
    desk = APPDATA / "Claude/claude_desktop_config.json" if IS_WIN else HOME / "Library/Application Support/Claude/claude_desktop_config.json"
    for n, s in ((load_json(desk, {}) or {}).get("mcpServers") or {}).items():
        out.append(_mcp_entry(n, s, "Claude Desktop"))
    for n, s in ((load_json(HOME / ".cursor/mcp.json", {}) or {}).get("mcpServers") or {}).items():
        out.append(_mcp_entry(n, s, "Cursor"))
    for n, s in ((load_json(HOME / ".codeium/windsurf/mcp_config.json", {}) or {}).get("mcpServers") or {}).items():
        out.append(_mcp_entry(n, s, "Windsurf"))
    vs = (APPDATA / "Code/User/mcp.json") if IS_WIN else HOME / ".config/Code/User/mcp.json"
    for n, s in ((load_json(vs, {}) or {}).get("servers") or {}).items():
        out.append(_mcp_entry(n, s, "VS Code"))
    toml = HOME / ".codex/config.toml"
    if toml.exists():
        try:
            import tomllib
            data = tomllib.loads(toml.read_text(encoding="utf-8"))
            for n, s in (data.get("mcp_servers") or {}).items():
                out.append(_mcp_entry(n, s, "Codex"))
        except Exception:
            for n in re.findall(r"^\[mcp_servers\.([^\]]+)\]", toml.read_text(encoding="utf-8", errors="ignore"), re.M):
                out.append({"nome": n.strip('"'), "tipo": "stdio", "via": "", "onde": "Codex"})
    return out


CLI_LIST = ["git", "node", "npm", "npx", "pnpm", "bun", "python", "uv", "pip", "docker", "gh", "claude", "codex",
            "gemini", "ollama", "lms", "omniroute", "ccr", "litellm", "ffmpeg", "code", "cursor", "deno", "go", "cargo", "java"]


def _version(cmd: str) -> dict:
    p = which(cmd)
    if not p:
        return {"nome": cmd, "instalado": False}
    ver = ""
    try:
        r = subprocess.run([p, "version" if cmd == "go" else "--version"], capture_output=True, text=True, timeout=6,
                           stdin=subprocess.DEVNULL, creationflags=0x08000000 if IS_WIN else 0)
        ver = (r.stdout or r.stderr).strip().splitlines()[0][:80] if (r.stdout or r.stderr).strip() else ""
    except Exception:
        pass
    return {"nome": cmd, "instalado": True, "versao": ver, "onde": p}


def scan_clis() -> list[dict]:
    with ThreadPoolExecutor(8) as ex:
        return list(ex.map(_version, CLI_LIST))


def scan_models() -> list[dict]:
    out = []
    man = HOME / ".ollama/models/manifests"
    if man.exists():
        for f in man.rglob("*"):
            if f.is_file():
                parts = f.relative_to(man).parts
                if len(parts) >= 2:
                    out.append({"nome": f"{parts[-2]}:{parts[-1]}", "motor": "Ollama", "data": mtime(f)})
    for root in (HOME / ".lmstudio/models", HOME / ".cache/lm-studio/models"):
        if root.exists():
            for f in root.rglob("*.gguf"):
                out.append({"nome": f.stem, "motor": "LM Studio", "data": mtime(f)})
    return out


def scan_agents() -> list[dict]:
    out = []
    for base, where in ((HOME / ".claude/agents", "Claude Code"), (HOME / ".codex/agents", "Codex")):
        if base.exists():
            for f in base.glob("*.md"):
                fm = frontmatter(f.read_text(encoding="utf-8", errors="ignore")[:3000])
                out.append({"nome": fm.get("name") or f.stem, "desc": (fm.get("description") or "")[:200], "onde": where, "caminho": str(f)})
    return out


def scan_conversations() -> list[dict]:
    out = []
    cp = HOME / ".claude/projects"
    if cp.exists():
        for d in cp.iterdir():
            if d.is_dir():
                n = len(list(d.glob("*.jsonl")))
                if n:
                    label = d.name.replace("--", "/").split("-")[-1] or d.name
                    out.append({"app": "Claude Code", "projeto": label, "sessoes": n, "data": mtime(d)})
    cs = HOME / ".codex/sessions"
    if cs.exists():
        n = sum(1 for _ in cs.rglob("*.jsonl"))
        if n:
            out.append({"app": "Codex", "projeto": "(todas)", "sessoes": n, "data": mtime(cs)})
    ws = (APPDATA / "Cursor/User/workspaceStorage") if IS_WIN else HOME / "Library/Application Support/Cursor/User/workspaceStorage"
    if ws.exists():
        n = sum(1 for d in ws.iterdir() if d.is_dir())
        if n:
            out.append({"app": "Cursor", "projeto": "(áreas de trabalho)", "sessoes": n, "data": mtime(ws)})
    return out


def git_remote(repo: Path) -> str:
    cfg = repo / ".git" / "config"
    try:
        m = re.search(r'\[remote "origin"\][^\[]*?url\s*=\s*(\S+)', cfg.read_text(encoding="utf-8", errors="ignore"))
    except OSError:
        return ""
    if not m:
        return ""
    url = re.sub(r"//[^/@]+@", "//", m.group(1))  # never keep credentials
    return url


def scan_projects(roots: list[str]) -> list[dict]:
    out, seen = [], set()
    for r in roots:
        rp = Path(r).expanduser()
        if not rp.exists():
            continue
        for d, dirs, files in os.walk(rp):
            depth = len(Path(d).parts) - len(rp.parts)
            if ".git" in dirs or ".git" in files:
                p = Path(d)
                if str(p) not in seen:
                    seen.add(str(p))
                    marks = [m for m in ("CLAUDE.md", "AGENTS.md", ".cursorrules", ".mcp.json") if (p / m).exists()]
                    out.append({"nome": p.name, "caminho": str(p), "remote": git_remote(p), "agente": marks, "data": mtime(p / ".git")})
                dirs[:] = []
                continue
            dirs[:] = [x for x in dirs if x not in SKIP_DIRS and not x.startswith(".")]
            if depth >= 3 or len(out) >= 300:
                dirs[:] = []
    return out


def inventory() -> dict:
    cfg = load_config()
    consent = cfg.get("consent", {})
    t0 = time.time()
    skills = []
    if consent.get("ferramentas", True):
        skills += skills_under(HOME / ".claude/skills", "Claude Code", 3)
        skills += skills_under(HOME / ".claude/plugins", "Claude Code · plugin", 8)
        skills += skills_under(HOME / ".codex/skills", "Codex", 3)
        skills += skills_under(HOME / ".agents/skills", "Agentes (partilhado)", 3)
    inv = {
        "gerado": time.strftime("%Y-%m-%d %H:%M"),
        "sistema": f"{platform.system()} {platform.release()}",
        "apps": detect_apps() if consent.get("ferramentas", True) else [],
        "skills": skills,
        "mcp": scan_mcp() if consent.get("ferramentas", True) else [],
        "clis": scan_clis() if consent.get("ferramentas", True) else [],
        "modelos": scan_models() if consent.get("ferramentas", True) else [],
        "agentes": scan_agents() if consent.get("ferramentas", True) else [],
        "conversas": scan_conversations() if consent.get("conversas", True) else [],
        "projetos": scan_projects(cfg.get("project_roots", [])) if consent.get("projetos", True) else [],
    }
    inv["segundos"] = round(time.time() - t0, 1)
    APP_DIR.mkdir(parents=True, exist_ok=True)
    (APP_DIR / "inventory.json").write_text(json.dumps(inv, ensure_ascii=False), encoding="utf-8")
    return inv


def cached_inventory() -> dict | None:
    return load_json(APP_DIR / "inventory.json")


def summary(inv: dict) -> dict:
    return {
        "apps": [a["nome"] for a in inv.get("apps", []) if a.get("instalado")],
        "skills": len(inv.get("skills", [])), "mcp": len(inv.get("mcp", [])),
        "clis": [c["nome"] for c in inv.get("clis", []) if c.get("instalado")],
        "modelos_locais": [m["nome"] for m in inv.get("modelos", [])],
        "agentes": len(inv.get("agentes", [])), "projetos": len(inv.get("projetos", [])),
        "conversas": sum(c.get("sessoes", 0) for c in inv.get("conversas", [])),
    }


# ---------- kits and catalogue ----------

REMOTE = APP_DIR / "remote"


def _newest(name: str, default):
    """Local data file, or the copy synced from the official repository when it carries a higher version."""
    local = load_json(DATA / name, default)
    remote = load_json(REMOTE / name, None)
    if isinstance(remote, dict) and remote.get("version", 0) > (local or {}).get("version", 0):
        return remote
    return local


def kits() -> dict:
    return _newest("kits.json", {"kits": [], "combos": []})


def catalog() -> dict:
    return _newest("catalog.json", {})


def search_catalog(q: str) -> list[dict]:
    q = q.lower().strip()
    hits = []
    for kit in kits()["kits"]:
        for it in kit["itens"]:
            if not q or q in (it["n"] + " " + it.get("p", "") + " " + it.get("r", "")).lower():
                hits.append({**it, "kit": kit["nome"]})
    for group, items in catalog().items():
        if isinstance(items, list):
            for it in items:
                if not q or q in json.dumps(it, ensure_ascii=False).lower():
                    hits.append({**it, "grupo": group})
    return hits[:60]


# ---------- passport and advice ----------

SIGNALS = {
    "agente": ["agent", "llm", "openai", "anthropic", "langchain", "langgraph", "crewai", "mcp", "prompt", "claude", "ollama", "chatbot", "assistant", "agente"],
    "video": ["video", "vídeo", "remotion", "ffmpeg", "whisper", ".mp4", "subtitle", "legenda", "motion-canvas", ".mov"],
    "design": ["design", "figma", "poster", "flyer", "canvas", ".svg", "brand", "logo", "comfyui", "stable-diffusion", ".psd", "cartaz"],
    "frontend": ["react", "vue", "svelte", "next", "vite", "tailwind", ".tsx", ".jsx", ".css", "shadcn", "frontend"],
    "backend": ["fastapi", "express", "hono", "django", "flask", "prisma", "drizzle", "postgres", "supabase", ".sql", "database", "api", "backend"],
    "web": ["website", "astro", "seo", "landing", ".html", "blog", "wordpress", "site"],
    "seguranca": ["auth", "login", "password", "jwt", "oauth", ".env", "token", "payment", "secret"],
    "codigo": ["test", "pytest", "jest", "vitest", "eslint", "ruff", "bug", "refactor"],
    "escrita": ["docs", ".md", "prompt", "token", "cost", "memory", "memória", "claude.md", "agents.md", "context", "llm"],
    "monetizar": ["stripe", "polar", "payment", "checkout", "subscription", "pricing", "billing", "paypal", "monet"],
    "cad3d": ["blender", "cad", "ifc", ".dwg", ".dxf", "sketchup", "three", "freecad", "revit", ".blend", ".skp", "arquitet"],
    "pesquisa": ["rag", "embedding", "vector", "chroma", "qdrant", "llamaindex", "crawl", "scrape", ".pdf", "search", "pesquisa"],
    "automacao": ["n8n", "zapier", "webhook", "cron", "workflow", "automation", "schedule", "automa"],
    "imagem": ["image", "imagem", "render", "photo", "foto", "upscale", "comfyui", "background", ".png", ".jpg"],
    "aiapps": ["anthropic", "@anthropic-ai", "claude", "electron", "tauri", "openai", "ai app", "chat", "streaming"],
    "docs": ["docs", "obsidian", ".md", "pdf", "docx", "notes", "notas", "vault", "wiki", "memória"],
    "marketing": ["marketing", "seo", "social", "post", "newsletter", "campanha", "campaign", "analytics", "landing"],
    "dados": ["csv", "xlsx", "pandas", "dashboard", "duckdb", "sql", "chart", "gráfico", "dados", "analytics", "parquet"],
}
BASE_KITS = {"seguranca": 2, "codigo": 2, "escrita": 1}
MANIFESTS = ["package.json", "requirements.txt", "pyproject.toml", "Cargo.toml", "go.mod", "composer.json", "Gemfile", "pom.xml"]


def passport(path: str) -> dict:
    p = Path(path).expanduser()
    if not p.is_dir():
        raise ValueError("Essa pasta não existe neste PC.")
    exts, nfiles, folders = {}, 0, set()
    for d, dirs, files in walk(p, 5):
        dirs[:] = [x for x in dirs if not x.startswith(".")]
        if d != p:
            folders.add(d.name.lower())
        for f in files:
            nfiles += 1
            e = Path(f).suffix.lower()
            if e:
                exts[e] = exts.get(e, 0) + 1
        if nfiles > 6000:
            break
    readme_txt = ""
    for name in ("README.md", "readme.md", "README.txt", "README"):
        if (p / name).exists():
            readme_txt = (p / name).read_text(encoding="utf-8-sig", errors="ignore")[:6000]  # -sig: a BOM would hide the "#" title
            break
    lines = [l.strip() for l in readme_txt.splitlines() if l.strip()]
    title = next((l.lstrip("# ").strip() for l in lines if l.startswith("#")), p.name)
    mission = next((l for l in lines if not l.startswith(("#", "!", "[", "<", "|", "```", "-", "*"))), "")[:400]
    deps = []
    pj = load_json(p / "package.json", None)
    if isinstance(pj, dict):
        for k in ("dependencies", "devDependencies"):
            deps += list((pj.get(k) or {}).keys())
        mission = mission or pj.get("description", "")
    for f in ("requirements.txt",):
        if (p / f).exists():
            deps += [re.split(r"[<>=\[ ;]", l.strip())[0] for l in (p / f).read_text(encoding="utf-8", errors="ignore").splitlines() if l.strip() and not l.startswith("#")]
    if (p / "pyproject.toml").exists():
        deps += re.findall(r'^\s*"([A-Za-z0-9_.\-]+)', (p / "pyproject.toml").read_text(encoding="utf-8", errors="ignore"), re.M)
    agent_files = [m for m in ("CLAUDE.md", "AGENTS.md", ".cursorrules", ".mcp.json", ".claude", ".codex") if (p / m).exists()]
    mcp_names = list(((load_json(p / ".mcp.json", {}) or {}).get("mcpServers") or {}).keys())
    top_ext = sorted(exts.items(), key=lambda x: -x[1])[:10]
    return {
        "nome": title, "caminho": str(p), "missao": mission,
        "ficheiros": nfiles, "extensoes": top_ext, "pastas": sorted(folders)[:40],
        "dependencias": sorted(set(deps))[:80], "manifestos": [m for m in MANIFESTS if (p / m).exists()],
        "agente": agent_files, "mcp_do_projeto": mcp_names, "remote": git_remote(p) if (p / ".git").exists() else "",
        "docker": (p / "Dockerfile").exists() or (p / "docker-compose.yml").exists(),
        "ci": (p / ".github/workflows").exists(), "readme": bool(readme_txt),
        "_texto": (readme_txt[:3000] + " " + " ".join(deps) + " " + " ".join(folders) + " " + " ".join(e for e, _ in top_ext)).lower(),
    }


def _have(name: str, inv: dict) -> bool:
    n = name.lower()
    # "Anthropic Skills (frontend-design, canvas-design)" counts as had when any of the named skills is installed
    inner = re.search(r"\((.*?)\)", n)
    if inner and any(_have(part.strip(), inv) for part in inner.group(1).split(",") if len(part.strip()) >= 3):
        return True
    key = re.sub(r"[^a-z0-9]", "", n.split("(")[0])
    pool = [s["nome"] for s in inv.get("skills", [])] + [m["nome"] for m in inv.get("mcp", [])] + \
           [c["nome"] for c in inv.get("clis", []) if c.get("instalado")] + [a["nome"] for a in inv.get("apps", []) if a.get("instalado")]
    def match(x: str) -> bool:
        k2 = re.sub(r"[^a-z0-9]", "", x.lower())
        # the tool's name inside an installed name (et-dev-gitleaks ⊃ gitleaks), or an installed name that covers almost all of it
        return bool(key and k2 and (key in k2 or (k2 in key and len(k2) >= 0.8 * len(key))))
    return any(match(x) for x in pool)


def advise(path: str, inv: dict | None = None) -> dict:
    pp = passport(path)
    inv = inv or cached_inventory() or {}
    text = pp.pop("_texto")
    scores = []
    for kit in kits()["kits"]:
        hits = [s for s in SIGNALS.get(kit["id"], []) if s in text]
        score = len(hits) + BASE_KITS.get(kit["id"], 0)
        if score:
            itens = [{**it, "tens": _have(it["n"], inv)} for it in kit["itens"]]
            scores.append({"kit": kit["id"], "nome": kit["nome"], "pontos": score, "sinais": hits[:8], "itens": itens})
    scores.sort(key=lambda x: -x["pontos"])
    top = scores[:5]
    gaps = []
    if not pp["agente"]:
        gaps.append("O projeto não tem CLAUDE.md nem AGENTS.md: o agente começa sem contexto. Cria um com a missão e as regras.")
    if not pp["readme"]:
        gaps.append("Sem README: escreve a missão do projeto em 3 linhas.")
    if not pp["remote"]:
        gaps.append("Sem repositório remoto: liga ao GitHub (ou outro) para teres histórico e cópia de segurança.")
    if not pp["ci"]:
        gaps.append("Sem verificações automáticas (CI): os testes e o scan de segurança só correm se te lembrares.")
    return {"passaporte": pp, "kits": top, "lacunas": gaps}


def advice_prompt(path: str, adv: dict | None = None) -> str:
    adv = adv or advise(path)
    pp = adv["passaporte"]
    kits_txt = "\n".join(f"- {k['nome']} (sinais: {', '.join(k['sinais']) or 'base'}) — falta: " +
                         (", ".join(i["n"] for i in k["itens"] if not i["tens"]) or "nada") for k in adv["kits"])
    return f"""És o Conselho do REASON O1. Analisa este projeto e diz-me o que ele precisa para cumprir a sua missão.

PROJETO: {pp['nome']}
PASTA: {pp['caminho']}
MISSÃO (do README): {pp['missao'] or '(não encontrada — pergunta-me)'}
STACK: {', '.join(pp['manifestos']) or '—'} · extensões: {', '.join(e for e, _ in pp['extensoes'][:6])}
JÁ TEM PARA AGENTES: {', '.join(pp['agente']) or 'nada'}

PRÉ-ANÁLISE DO REASON O1 (kits prováveis):
{kits_txt}

O QUE QUERO:
1. Lê o projeto (README, manifestos, estrutura). Não alteres nada: só leitura.
2. Escreve o passaporte: missão, para quem, como funciona, ligações externas, riscos.
3. Recomenda as melhores skills, MCPs, CLIs e LLM para este projeto. Para cada um: para quê, link, se já tenho, e como instalar no Claude Code ou no Codex.
   Se o MCP reason-o1 estiver ligado, usa as ferramentas o1_inventario e o1_kit para saber o que já tenho.
4. Diz como orquestrar: que agente faz o quê, por que ordem, e onde preciso de aprovar.
5. Passo a passo para começar hoje (máx. 7 passos).
6. Termina com uma tabela: item | tipo | tenho? | prioridade | link.
Se o MCP reason-o1 estiver ligado, guarda o relatório com o1_guardar_relatorio.
"""


def save_report(title: str, markdown: str) -> str:
    d = folder_for("relatorios")
    d.mkdir(parents=True, exist_ok=True)
    slug = re.sub(r"[^A-Za-z0-9_-]+", "-", title)[:60].strip("-") or "relatorio"
    f = d / f"{time.strftime('%Y-%m-%d_%H%M')}_{slug}.md"
    f.write_text(markdown, encoding="utf-8")
    return str(f)
