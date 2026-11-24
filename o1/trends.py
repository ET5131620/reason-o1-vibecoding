"""Trends: what the community is using now, from public sources that need no key.

GitHub  — new repositories climbing in stars (skills, MCP, agents), last 60 days
Hacker News — most-discussed stories about Claude Code, MCP and skills, last 30 days
Reddit  — top posts of the week in r/ClaudeAI and r/LocalLLaMA (may refuse; then it is skipped)

From the titles it also counts which catalogue tools are mentioned, and which appear together ("conjuntos").
TikTok, Instagram and Facebook have no open API: for those, research_prompt() hands the search to the user's agent.
Cached for 6 hours in ~/.reason-o1/trends.json.
"""
from __future__ import annotations

import itertools
import json
import re
import time
import urllib.parse
import urllib.request
from collections import Counter

from . import core

CACHE = core.APP_DIR / "trends.json"
GH_QUERIES = [
    ("Skills para agentes", "claude skills"),
    ("Servidores MCP", "mcp server"),
    ("Agentes e harness", "coding agent"),
    ("Design e UI para agentes", "design skill agent"),
]
HN_QUERIES = ["claude code", "MCP server", "agent skills"]
REDDIT = ["ClaudeAI", "LocalLLaMA"]
SKIP = {"Claude Code"}  # it is in every search query, so counting it says nothing


def _get(url: str, timeout=12):
    req = urllib.request.Request(url, headers={"User-Agent": "reason-o1/0.2 (trends; +local app)", "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def _github(days=60) -> list[dict]:
    since = time.strftime("%Y-%m-%d", time.gmtime(time.time() - days * 86400))
    out = []
    for grupo, q in GH_QUERIES:
        url = "https://api.github.com/search/repositories?" + urllib.parse.urlencode(
            {"q": f"{q} created:>{since}", "sort": "stars", "order": "desc", "per_page": 8})
        try:
            for it in _get(url).get("items", []):
                out.append({"grupo": grupo, "nome": it["full_name"], "url": it["html_url"], "estrelas": it["stargazers_count"],
                            "desc": (it.get("description") or "")[:200], "criado": it["created_at"][:10], "fonte": "GitHub"})
        except Exception:
            continue
    seen, uniq = set(), []
    for r in sorted(out, key=lambda x: -x["estrelas"]):
        if r["nome"] not in seen:
            seen.add(r["nome"])
            uniq.append(r)
    return uniq[:24]


def _hn(days=30) -> list[dict]:
    since = int(time.time() - days * 86400)
    out = []
    for q in HN_QUERIES:
        url = "https://hn.algolia.com/api/v1/search?" + urllib.parse.urlencode(
            {"query": q, "tags": "story", "numericFilters": f"created_at_i>{since},points>40", "hitsPerPage": 10})
        try:
            for h in _get(url).get("hits", []):
                out.append({"titulo": h.get("title") or "", "url": h.get("url") or f"https://news.ycombinator.com/item?id={h['objectID']}",
                            "pontos": h.get("points", 0), "comentarios": h.get("num_comments", 0),
                            "data": time.strftime("%Y-%m-%d", time.gmtime(h.get("created_at_i", 0))), "fonte": "Hacker News"})
        except Exception:
            continue
    seen, uniq = set(), []
    for r in sorted(out, key=lambda x: -x["pontos"]):
        if r["url"] not in seen:
            seen.add(r["url"])
            uniq.append(r)
    return uniq[:15]


def _reddit() -> list[dict]:
    out = []
    for sub in REDDIT:
        try:
            for c in _get(f"https://www.reddit.com/r/{sub}/top.json?t=week&limit=12")["data"]["children"]:
                d = c["data"]
                out.append({"titulo": d.get("title", ""), "url": "https://www.reddit.com" + d.get("permalink", ""), "pontos": d.get("score", 0),
                            "comentarios": d.get("num_comments", 0), "data": time.strftime("%Y-%m-%d", time.gmtime(d.get("created_utc", 0))),
                            "fonte": f"r/{sub}"})
        except Exception:
            continue
    return sorted(out, key=lambda x: -x["pontos"])[:15]


def _tool_names() -> dict:
    """Catalogue tools and the short keys we look for in titles (e.g. 'Playwright MCP' → 'playwright')."""
    names = {}
    for kit in core.kits()["kits"]:
        for it in kit["itens"]:
            key = re.sub(r"\(.*?\)", "", it["n"]).strip().lower()
            key = re.sub(r"\b(mcp|skills?|sdk|cli|ui|css|orm)\b", "", key).strip(" /-") or key
            if len(key) >= 4:
                names[key] = it["n"]
    return names


def _mentions(texts: list[tuple[str, dict]]) -> tuple[list, list]:
    """texts: (text, source) pairs. Returns the most-mentioned tools and pairs, each with where it was seen."""
    names = _tool_names()
    count, pairs, where = Counter(), Counter(), {}
    for t, src in texts:
        low = t.lower()
        found = sorted({full for key, full in names.items() if full not in SKIP and re.search(rf"\b{re.escape(key)}\b", low)})
        count.update(found)
        for f in found:
            where.setdefault(f, []).append(src)
        for pr in itertools.combinations(found, 2):
            pairs[pr] += 1
            where.setdefault(pr, []).append(src)
    return ([{"nome": n, "vezes": c, "onde": where[n][:6]} for n, c in count.most_common(15)],
            [{"juntos": list(p), "vezes": c, "onde": where[p][:6]} for p, c in pairs.most_common(10)])


def trends(refresh=False) -> dict:
    cached = core.load_json(CACHE)
    if cached and not refresh and cached.get("v") == 2 and time.time() - cached.get("_t", 0) < 6 * 3600:
        return cached
    gh, hn, rd = _github(), _hn(), _reddit()
    texts = [(f"{r['nome']} {r['desc']}", {"titulo": r["nome"], "url": r["url"], "fonte": "GitHub"}) for r in gh] + \
            [(r["titulo"], {"titulo": r["titulo"], "url": r["url"], "fonte": r["fonte"]}) for r in hn + rd]
    falados, conjuntos = _mentions(texts)
    out = {"v": 2, "gerado": time.strftime("%Y-%m-%d %H:%M"), "_t": time.time(), "github": gh, "discussao": sorted(hn + rd, key=lambda x: -x["pontos"])[:20],
           "falados": falados, "conjuntos": conjuntos,
           "fontes": {"GitHub": len(gh), "Hacker News": len(hn), "Reddit": len(rd)},
           "listas": [{"nome": "awesome-claude-code", "r": "hesreallyhim/awesome-claude-code"},
                      {"nome": "awesome-mcp-servers", "r": "punkpeye/awesome-mcp-servers"},
                      {"nome": "awesome-claude-skills", "r": "ComposioHQ/awesome-claude-skills"}]}
    if not (gh or hn or rd):
        out["erro"] = "Sem ligação às fontes públicas. Tenta mais tarde."
        return cached or out
    core.APP_DIR.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
    return out


def research_prompt(tema: str) -> str:
    tema = (tema or "skills, MCPs e conjuntos de ferramentas para agentes de IA").strip()[:300]
    return f"""Pesquisa as tendências atuais sobre: {tema}

Procura em: GitHub (repositórios a subir em estrelas), listas awesome, Reddit, Hacker News, X/Twitter, YouTube, TikTok, Instagram e Facebook (só páginas públicas; não inicies sessão em lado nenhum).

Quero:
1. As 10 ferramentas (skills, MCPs, CLIs, modelos) mais faladas agora, com o link oficial no GitHub.
2. Os CONJUNTOS: que ferramentas as pessoas usam juntas para este tipo de trabalho, e porquê.
3. Para cada uma: estrelas, último commit, licença e uma frase de vantagem.
4. O que é moda passageira e o que tem sinais de durar.
5. Uma proposta de kit em dois níveis: Essencial (3) e Completo (7).
Distingue o que verificaste do que é só opinião das redes. Se o MCP reason-o1 estiver ligado, compara com o1_kits e guarda o kit com o1_kit_guardar quando eu aprovar.
"""
