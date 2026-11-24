"""Self-update from the official repository only (o1/about.py → repo).

check()   latest GitHub release vs. the running version
apply()   download that release, back up the current files, replace them, ask for a restart
sync()    pull newer kits.json / catalog.json from the default branch between releases
Every step is HTTPS to github.com. User data (~/.reason-o1) is never touched.
"""
from __future__ import annotations

import io
import json
import re
import shutil
import time
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

from . import core
from .about import ABOUT

# Only these paths are replaced by an update; anything else in the folder is left alone.
MANAGED = ["reason_o1.py", "o1", "ui", "data", "ARRANCAR.bat", "README.md", "LICENSE"]
BACKUPS = core.APP_DIR / "backups"


def _get(url: str, timeout=20, raw=False):
    req = urllib.request.Request(url, headers={"User-Agent": "reason-o1", "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data = r.read()
    return data if raw else json.loads(data.decode("utf-8"))


def _ver(s: str) -> tuple:
    return tuple(int(x) for x in re.findall(r"\d+", s or "")[:3]) or (0,)


def check(timeout=12) -> dict:
    repo = ABOUT.get("repo", "")
    base = {"atual": ABOUT["version"], "repo": repo, "verificado": time.strftime("%Y-%m-%d %H:%M"),
            "auto": core.load_config().get("auto_update", True)}
    if not repo:
        return {**base, "estado": "em_breve", "texto": "Repositório oficial em breve. O programa verifica sozinho quando existir."}
    try:
        d = _get(f"https://api.github.com/repos/{repo}/releases/latest", timeout)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return {**base, "estado": "em_breve", "texto": "Ainda não há versões publicadas no repositório oficial.", "pagina": f"https://github.com/{repo}"}
        return {**base, "estado": "erro", "texto": f"GitHub respondeu {e.code}."}
    except Exception:
        return {**base, "estado": "offline", "texto": "Sem ligação: verifico na próxima vez."}
    tag = (d.get("tag_name") or "").lstrip("v")
    already = (last_update() or {}).get("para") == tag  # never re-install the same release in a loop
    newer = _ver(tag) > _ver(ABOUT["version"]) and not already
    return {**base, "estado": "nova" if newer else "atual", "ultima": tag, "url": d.get("html_url"),
            "zip": d.get("zipball_url"), "notas": (d.get("body") or "")[:1500], "pagina": f"https://github.com/{repo}",
            "texto": f"Versão {tag} disponível." if newer else "Estás na última versão."}


def _safe_extract(zf: zipfile.ZipFile, dest: Path) -> Path:
    dest = dest.resolve()
    for m in zf.infolist():
        target = (dest / m.filename).resolve()
        if dest != target and dest not in target.parents:  # zip-slip guard
            raise ValueError(f"Caminho inválido no pacote: {m.filename}")
    zf.extractall(dest)
    tops = [p for p in dest.iterdir() if p.is_dir()]
    return tops[0] if len(tops) == 1 else dest  # GitHub zipballs wrap everything in one folder


def apply(info: dict | None = None) -> dict:
    info = info or check()
    if info.get("estado") != "nova":
        return {"ok": False, "texto": info.get("texto", "Nada para atualizar.")}
    zip_url = info.get("zip") or ""
    repo = ABOUT["repo"]
    if not zip_url.startswith(f"https://api.github.com/repos/{repo}/"):
        return {"ok": False, "texto": "Endereço do pacote fora do repositório oficial: recusado."}
    blob = _get(zip_url, timeout=120, raw=True)
    stage = core.APP_DIR / "staging" / info["ultima"]
    if stage.exists():
        shutil.rmtree(stage)
    stage.mkdir(parents=True)
    src = _safe_extract(zipfile.ZipFile(io.BytesIO(blob)), stage)
    if not (src / "reason_o1.py").exists() or not (src / "o1" / "about.py").exists():
        return {"ok": False, "texto": "O pacote não parece ser o REASON O1: nada foi alterado."}
    backup = BACKUPS / f"{ABOUT['version']}_{time.strftime('%Y%m%d-%H%M%S')}"
    backup.mkdir(parents=True)
    for name in MANAGED:
        cur = core.ROOT / name
        if cur.is_dir():
            shutil.copytree(cur, backup / name, ignore=shutil.ignore_patterns("__pycache__"))
        elif cur.exists():
            shutil.copy2(cur, backup / name)
    for name in MANAGED:
        new, cur = src / name, core.ROOT / name
        if not new.exists():
            continue
        if new.is_dir():
            # Windows will not remove a folder the running program uses, so merge in place
            shutil.copytree(new, cur, dirs_exist_ok=True)
            fresh = {f.relative_to(new) for f in new.rglob("*") if f.is_file()}
            for old in [f for f in cur.rglob("*") if f.is_file() and "__pycache__" not in f.parts]:
                if old.relative_to(cur) not in fresh:
                    try:
                        old.unlink()
                    except OSError:
                        pass
        else:
            shutil.copy2(new, cur)
    shutil.rmtree(stage, ignore_errors=True)
    (core.APP_DIR / "last_update.json").write_text(json.dumps({"de": ABOUT["version"], "para": info["ultima"], "quando": time.strftime("%Y-%m-%d %H:%M"), "copia": str(backup)}, ensure_ascii=False), encoding="utf-8")
    return {"ok": True, "de": ABOUT["version"], "para": info["ultima"], "copia": str(backup), "reiniciar": True,
            "texto": f"Atualizado de {ABOUT['version']} para {info['ultima']}. Cópia de segurança em {backup}."}


def sync() -> dict:
    """Newer kits and catalogue from the official repo, without waiting for a release."""
    repo = ABOUT.get("repo", "")
    if not repo:
        return {"ok": False}
    got = []
    core.REMOTE.mkdir(parents=True, exist_ok=True)
    for name in ("kits.json", "catalog.json", "gh_snapshot.json"):
        try:
            data = json.loads(_get(f"https://raw.githubusercontent.com/{repo}/HEAD/data/{name}", raw=True).decode("utf-8"))
        except Exception:
            continue
        (core.REMOTE / name).write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        got.append(name)
    return {"ok": bool(got), "ficheiros": got}


def last_update() -> dict | None:
    return core.load_json(core.APP_DIR / "last_update.json")
