"""The workshop: what you already have per kit, your own kits, a prompt library, skill scaffolds and the Claude Cookbook.

Everything the user creates goes to their own REASON O1 folder (09_KITS, 07_PROMPTS, 01_SKILLS). Nothing is installed by itself.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import time
import unicodedata
from pathlib import Path

from . import core

SLUG = re.compile(r"[^a-z0-9-]+")


def slug(s: str, n=50) -> str:
    plain = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode()  # relatório → relatorio
    return SLUG.sub("-", plain.lower().replace(" ", "-")).strip("-")[:n] or "sem-nome"


# ---------- "Já tens": the user's skills grouped by kit (what the old Aplicabilidade map showed) ----------

def _rx(words: list[str]):
    # short words (ui, ux, qa, 3d, api…) must match as whole words, the rest as part of a word
    parts = [rf"\b{re.escape(w)}\b" if len(w) <= 3 else re.escape(w) for w in words]
    return re.compile("|".join(parts), re.I) if parts else None


def mine(inv: dict | None = None) -> dict:
    inv = inv or core.cached_inventory() or {}
    seen, skills = set(), []
    for s in inv.get("skills", []):  # the same skill installed in two apps counts once
        if s["nome"] not in seen:
            seen.add(s["nome"])
            skills.append(s)
    out = {}
    for kit in core.kits()["kits"]:
        rx = _rx(kit.get("palavras", []))
        hits = [s for s in skills if rx and rx.search(s["nome"] + " " + s.get("desc", ""))] if rx else []
        out[kit["id"]] = {"n": len(hits), "skills": [{"nome": s["nome"], "desc": s.get("desc", "")[:140], "onde": s["onde"]} for s in hits[:60]],
                          "tens_itens": sum(1 for it in kit["itens"] if core._have(it["n"], inv))}
    return {"total": len(skills), "kits": out}


# ---------- kit creator ----------

def suggest(goal: str, inv: dict | None = None) -> dict:
    """From a goal in plain words: the kits that fit, their items (with what you have) and your own skills that serve it."""
    inv = inv or core.cached_inventory() or {}
    text = (goal or "").lower()
    my = mine(inv)["kits"]
    scored = []
    for kit in core.kits()["kits"]:
        words = set(kit.get("palavras", [])) | set(core.SIGNALS.get(kit["id"], []))
        hits = [w for w in words if w in text]
        if kit["nome"].lower() in text:
            hits.append(kit["nome"])
        if hits:
            scored.append((len(hits), kit, hits))
    scored.sort(key=lambda x: -x[0])
    if not scored:  # nothing matched: start from the beginner combo
        scored = [(0, k, []) for k in core.kits()["kits"] if k["id"] in ("agente", "codigo", "escrita")]
    kits = []
    for pts, kit, hits in scored[:4]:
        kits.append({"id": kit["id"], "nome": kit["nome"], "cor": kit["cor"], "sinais": hits[:6],
                     "itens": [{**i, "tens": core._have(i["n"], inv)} for i in kit["itens"]],
                     "minhas": [s["nome"] for s in my.get(kit["id"], {}).get("skills", [])[:12]]})
    return {"objetivo": goal, "kits": kits}


def user_kits() -> list[dict]:
    d = core.folder_for("kits")
    out = []
    if d.exists():
        for f in sorted(d.glob("*.json")):
            k = core.load_json(f)
            if isinstance(k, dict) and k.get("nome"):
                out.append({**k, "ficheiro": str(f), "meu": True})
    return out


def save_kit(kit: dict) -> dict:
    nome = str(kit.get("nome", "")).strip()[:80]
    if not nome:
        raise ValueError("O kit precisa de um nome.")
    itens = [{k: str(v)[:300] for k, v in it.items() if k in ("t", "n", "r", "p", "v")} for it in kit.get("itens", [])[:30] if isinstance(it, dict) and it.get("n")]
    if not itens:
        raise ValueError("Escolhe pelo menos uma ferramenta.")
    out = {"id": "meu-" + slug(nome), "nome": nome, "objetivo": str(kit.get("objetivo", ""))[:600], "icon": "kit",
           "cor": kit.get("cor") if re.match(r"^#[0-9a-fA-F]{6}$", str(kit.get("cor", ""))) else "#38e1ff",
           "itens": itens, "minhas": [str(x)[:80] for x in kit.get("minhas", [])[:40]],
           "notas": str(kit.get("notas", ""))[:2000], "criado": time.strftime("%Y-%m-%d %H:%M")}
    d = core.folder_for("kits")
    d.mkdir(parents=True, exist_ok=True)
    f = d / f"{slug(nome)}.json"
    f.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    return {**out, "ficheiro": str(f)}


# ---------- prompts ----------

def kit_prompt(goal: str, kit_ids: list[str], nivel: str = "completo", inv: dict | None = None) -> str:
    inv = inv or core.cached_inventory() or {}
    allk = {k["id"]: k for k in core.kits()["kits"]} | {k["id"]: k for k in user_kits()}
    my = mine(inv)["kits"]
    blocks = []
    for kid in kit_ids or []:
        k = allk.get(kid)
        if not k:
            continue
        itens = [i for i in k["itens"] if nivel != "essencial" or i.get("e")]
        lines = [f"  - {i['n']} ({i.get('t', '')}) — {i.get('p', '')}. {'JÁ TENHO' if core._have(i['n'], inv) else 'FALTA'}"
                 + (f" · https://github.com/{i['r']}" if "/" in i.get("r", "") and not i["r"].startswith("http") else "") for i in itens]
        mine_names = [s["nome"] for s in my.get(kid, {}).get("skills", [])[:10]] or k.get("minhas", [])
        blocks.append(f"KIT {k['nome']}:\n" + "\n".join(lines) + (f"\n  Skills que já tenho para isto: {', '.join(mine_names)}" if mine_names else ""))
    cb = core.kits().get("cookbook", {})
    return f"""Objetivo: {goal or '(descreve aqui o que queres fazer)'}

Tenho o REASON O1 ligado (MCP reason-o1). Usa as ferramentas o1_inventario, o1_kit e o1_tendencias se precisares de mais contexto.

{chr(10).join(blocks) or '(sem kit escolhido: usa o1_kit_criar para me sugerir um)'}

O que quero que faças:
1. Confirma o objetivo numa frase e diz-me o que vais entregar no fim.
2. Usa primeiro o que JÁ TENHO. Para o que FALTA, mostra a ficha (licença, último commit, estrelas, riscos) e espera o meu sim antes de instalar.
3. Instala no Claude Code ou no Codex, um item de cada vez, e testa cada um.
4. Se servir, segue o exemplo mais próximo no Claude Cookbook ({cb.get('url', 'https://github.com/anthropics/claude-cookbooks')}).
5. Faz o trabalho por passos curtos, com um plano visível e testes.
6. No fim: tabela item | para quê | estado, e o que ficou por fazer.
Regras: nada pago sem me perguntar; chaves só em variáveis de ambiente; não apagues nada sem confirmar.
"""


def prompts_list() -> list[dict]:
    d = core.folder_for("prompts")
    out = []
    if d.exists():
        for f in sorted(d.glob("*.md"), key=lambda p: -p.stat().st_mtime)[:200]:
            txt = f.read_text(encoding="utf-8", errors="ignore")
            fm = re.match(r"^---\n(.*?)\n---\n?(.*)$", txt, re.S)
            meta = dict(re.findall(r"^(\w+):\s*(.*)$", fm.group(1), re.M)) if fm else {}
            out.append({"titulo": meta.get("title", f.stem), "tags": meta.get("tags", ""), "data": meta.get("created", core.mtime(f)),
                        "texto": (fm.group(2) if fm else txt)[:20000], "ficheiro": str(f)})
    return out


def prompt_save(titulo: str, texto: str, tags: str = "") -> dict:
    titulo = (titulo or "prompt").strip()[:100]
    if not texto.strip():
        raise ValueError("O prompt está vazio.")
    d = core.folder_for("prompts")
    d.mkdir(parents=True, exist_ok=True)
    f = d / f"{time.strftime('%Y-%m-%d')}_{slug(titulo)}.md"
    safe_tags = re.sub(r"[\r\n]", " ", tags)[:200]
    f.write_text(f"---\ntitle: {titulo.replace(chr(10), ' ')}\ntags: {safe_tags}\ncreated: {time.strftime('%Y-%m-%d')}\n---\n{texto.strip()}\n", encoding="utf-8")
    return {"guardado": str(f)}


# ---------- skill scaffold ----------

def skill_create(nome: str, descricao: str, passos: list[str] | None = None, quando: str = "") -> dict:
    name = slug(nome, 60)
    if len(name) < 3:
        raise ValueError("Nome curto demais: usa pelo menos 3 letras.")
    desc = re.sub(r"\s+", " ", descricao or "").strip()[:900]
    if not desc:
        raise ValueError("A descrição diz ao agente quando usar a skill: é obrigatória.")
    d = core.folder_for("skills") / name
    if (d / "SKILL.md").exists():
        raise ValueError(f"Já existe uma skill com esse nome em {d}.")
    d.mkdir(parents=True, exist_ok=True)
    steps = "\n".join(f"{i}. {p.strip()}" for i, p in enumerate([p for p in (passos or []) if p.strip()][:15], 1)) or "1. (escreve aqui o primeiro passo)"
    body = f"""---
name: {name}
description: {desc.replace(chr(34), "'")}
---

# {nome.strip()}

## Quando usar
{quando.strip() or desc}

## Passos
{steps}

## Verificação
- O resultado foi testado (não basta parecer certo).
- O que não foi verificado está dito claramente.
"""
    (d / "SKILL.md").write_text(body, encoding="utf-8")
    return {"pasta": str(d), "ficheiro": str(d / "SKILL.md"), "nome": name,
            "instalar_claude": f'copia a pasta para ~/.claude/skills/{name}/', "instalar_codex": f'copia a pasta para ~/.codex/skills/{name}/'}


# ---------- Claude Cookbook ----------

def cookbook_dir() -> Path:
    return core.folder_for("skills") / "claude-cookbooks"


def cookbook_status() -> dict:
    d = cookbook_dir()
    cb = core.kits().get("cookbook", {})
    return {"instalado": (d / "README.md").exists(), "pasta": str(d), "git": bool(shutil.which("git")), **cb}


def cookbook_clone() -> dict:
    st = cookbook_status()
    if st["instalado"]:
        return {**st, "texto": "O Cookbook já está na tua pasta."}
    if not st["git"]:
        return {**st, "erro": "O git não está instalado. Instala-o (git-scm.com) ou descarrega o zip do GitHub."}
    d = cookbook_dir()
    d.parent.mkdir(parents=True, exist_ok=True)
    r = subprocess.run(["git", "clone", "--depth", "1", "https://github.com/anthropics/claude-cookbooks.git", str(d)],
                       capture_output=True, text=True, timeout=600, creationflags=0x08000000 if core.IS_WIN else 0)
    if r.returncode != 0:
        return {**st, "erro": (r.stderr or "falhou")[-400:]}
    return {**cookbook_status(), "texto": "Cookbook descarregado."}
