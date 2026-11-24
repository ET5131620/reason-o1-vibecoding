"""Usage: how many tokens you spend, where and on what — read from the local logs of Claude Code and Codex.

Only numbers are read: token counts, model name, date and the project folder name. Never the content of a
conversation. It only runs when the person turns it on (config consent["uso"]).

Claude Code  ~/.claude/projects/**/*.jsonl   assistant lines carry message.usage; one message can appear on
                                              several lines (one per content block), so it is counted once per id.
Codex        ~/.codex/sessions/**/*.jsonl    token_count events carry the session's running total and the
                                              plan's rate limits; turn_context carries the model and folder.

Per-file results are cached in ~/.reason-o1/usage_cache.json by size and mtime, so only new logs are read again.
Also: OmniRoute status (local port) and the OpenRouter balance when OPENROUTER_API_KEY is set (the key never
leaves the server process).
"""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

from . import core

CACHE = core.APP_DIR / "usage_cache.json"
HOME = Path.home()


def _name(cwd: str | None) -> str:
    return Path(cwd).name if cwd else "—"


def _claude_file(f: Path) -> dict:
    """{ 'YYYY-MM-DD|model|project': [input, cache_write, cache_read, output, messages] }"""
    seen, out = set(), {}
    with f.open(encoding="utf-8", errors="replace") as fh:
        for line in fh:
            if '"usage"' not in line or '"assistant"' not in line:
                continue
            try:
                d = json.loads(line)
            except Exception:
                continue
            m = d.get("message")
            if d.get("type") != "assistant" or not isinstance(m, dict) or not isinstance(m.get("usage"), dict):
                continue
            mid = m.get("id") or d.get("requestId") or d.get("uuid")
            if mid in seen:
                continue
            seen.add(mid)
            u = m["usage"]
            model = m.get("model") or "?"
            if model.startswith("<"):  # synthetic lines, not a real request
                continue
            day = (d.get("timestamp") or "")[:10]
            k = f"{day}|{model}|{_name(d.get('cwd'))}"
            a = out.setdefault(k, [0, 0, 0, 0, 0])
            a[0] += u.get("input_tokens") or 0
            a[1] += u.get("cache_creation_input_tokens") or 0
            a[2] += u.get("cache_read_input_tokens") or 0
            a[3] += u.get("output_tokens") or 0
            a[4] += 1
    return out


def _codex_file(f: Path) -> dict:
    total, model, cwd, day, limits, lim_t = None, "?", None, "", None, ""
    with f.open(encoding="utf-8", errors="replace") as fh:
        for line in fh:
            if '"token_count"' not in line and '"turn_context"' not in line:
                continue
            try:
                d = json.loads(line)
            except Exception:
                continue
            p = d.get("payload") if isinstance(d.get("payload"), dict) else {}
            if d.get("type") == "turn_context":
                model, cwd = p.get("model") or model, p.get("cwd") or cwd
            elif p.get("type") == "token_count":
                info = p.get("info") or {}
                if info.get("total_token_usage"):
                    total = info["total_token_usage"]
                if (p.get("rate_limits") or {}).get("primary"):  # some events carry the plan but no numbers
                    limits, lim_t = p["rate_limits"], d.get("timestamp") or ""
                day = day or (d.get("timestamp") or "")[:10]
    if not total:
        return {"rows": {}, "limits": limits, "lim_t": lim_t}
    inp, cached = total.get("input_tokens") or 0, total.get("cached_input_tokens") or 0
    row = [max(inp - cached, 0), total.get("cache_write_input_tokens") or 0, cached, total.get("output_tokens") or 0, 1]
    return {"rows": {f"{day}|{model}|{_name(cwd)}": row}, "limits": limits, "lim_t": lim_t}


def _scan(files: list[Path], reader, cache: dict, tag: str) -> list:
    results = []
    for f in files:
        try:
            st = f.stat()
        except OSError:
            continue
        key = f"{tag}:{f}"
        hit = cache.get(key)
        if not hit or hit.get("s") != st.st_size or hit.get("m") != int(st.st_mtime):
            try:
                hit = {"s": st.st_size, "m": int(st.st_mtime), "r": reader(f)}
            except Exception:
                continue
            cache[key] = hit
        results.append(hit["r"])
    return results


def usage(refresh: bool = False) -> dict:
    cfg = core.load_config()
    if not (cfg.get("consent") or {}).get("uso"):
        return {"consentimento": False}
    cache = core.load_json(CACHE, {}) or {}
    if refresh:
        cache = {}
    cc_files = list((HOME / ".claude" / "projects").rglob("*.jsonl")) if (HOME / ".claude" / "projects").exists() else []
    cx_files = list((HOME / ".codex" / "sessions").rglob("*.jsonl")) if (HOME / ".codex" / "sessions").exists() else []
    cc = _scan(cc_files, _claude_file, cache, "cc")
    cx = _scan(cx_files, _codex_file, cache, "cx")
    alive = {f"cc:{f}" for f in cc_files} | {f"cx:{f}" for f in cx_files}
    cache = {k: v for k, v in cache.items() if k in alive}
    core.APP_DIR.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(cache), encoding="utf-8")

    rows = []  # (engine, day, model, project, [in, cw, cr, out, n])
    for r in cc:
        rows += [("claude", *k.split("|", 2), v) for k, v in r.items()]
    limits, lim_t = None, ""
    for r in cx:
        rows += [("codex", *k.split("|", 2), v) for k, v in r["rows"].items()]
        if r.get("limits") and r.get("lim_t", "") >= lim_t:
            limits, lim_t = r["limits"], r["lim_t"]

    today = datetime.now(timezone.utc).date()
    days = [(today - timedelta(days=i)).isoformat() for i in range(29, -1, -1)]
    since7, since30 = days[-7], days[0]
    tot = lambda v: v[0] + v[1] + v[2] + v[3]

    def agg(pred):
        s = {"entrada": 0, "cache_escrita": 0, "cache_lida": 0, "saida": 0, "pedidos": 0}
        for e, d, m, p, v in rows:
            if pred(e, d):
                s["entrada"] += v[0]; s["cache_escrita"] += v[1]; s["cache_lida"] += v[2]; s["saida"] += v[3]; s["pedidos"] += v[4]
        s["total"] = s["entrada"] + s["cache_escrita"] + s["cache_lida"] + s["saida"]
        return s

    by_day = {d: {"claude": 0, "codex": 0} for d in days}
    by_model, by_proj = {}, {}
    for e, d, m, p, v in rows:
        if d in by_day:
            by_day[d][e] += tot(v)
        if d >= since30:
            by_model[(e, m)] = by_model.get((e, m), 0) + tot(v)
            by_proj[p] = by_proj.get(p, 0) + tot(v)

    lim = None
    if limits:
        prim = limits.get("primary") or {}
        lim = {"plano": limits.get("plan_type"), "usado": prim.get("used_percent"), "janela_min": prim.get("window_minutes"),
               "renova": datetime.fromtimestamp(prim["resets_at"]).strftime("%Y-%m-%d %H:%M") if prim.get("resets_at") else None,
               "visto": lim_t[:16].replace("T", " ")}
    return {
        "consentimento": True, "gerado": time.strftime("%Y-%m-%d %H:%M"),
        "ficheiros": {"claude": len(cc_files), "codex": len(cx_files)},
        "hoje": agg(lambda e, d: d == days[-1]), "dias7": agg(lambda e, d: d >= since7), "dias30": agg(lambda e, d: d >= since30),
        "motor30": {e: agg(lambda ee, d, e=e: ee == e and d >= since30) for e in ("claude", "codex")},
        "por_dia": [{"dia": d, **by_day[d]} for d in days],
        "por_modelo": [{"motor": e, "modelo": m, "tokens": t} for (e, m), t in sorted(by_model.items(), key=lambda x: -x[1])[:10]],
        "por_projeto": [{"projeto": p, "tokens": t} for p, t in sorted(by_proj.items(), key=lambda x: -x[1])[:10]],
        "codex_limite": lim,
    }


def _get(url: str, headers: dict | None = None, timeout: float = 4):
    req = urllib.request.Request(url, headers={"User-Agent": "reason-o1", **(headers or {})})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, json.loads(r.read().decode("utf-8") or "{}")


def providers() -> dict:
    out = {}
    # OmniRoute: is the local gateway running? 401 also means "running, needs its key".
    try:
        st, d = _get("http://127.0.0.1:20128/v1/models", timeout=1.5)
        out["omniroute"] = {"a_correr": True, "modelos": len(d.get("data") or [])}
    except urllib.error.HTTPError as e:
        out["omniroute"] = {"a_correr": e.code in (401, 403), "modelos": None}
    except Exception:
        out["omniroute"] = {"a_correr": False}
    # OpenRouter: balance from its key endpoint, only when the person set the key in the environment.
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        out["openrouter"] = {"configurada": False}
    else:
        try:
            _, d = _get("https://openrouter.ai/api/v1/key", {"Authorization": f"Bearer {key}"}, timeout=8)
            d = d.get("data") or {}
            out["openrouter"] = {"configurada": True, "usado": d.get("usage"), "limite": d.get("limit"),
                                 "restante": d.get("limit_remaining"), "gratis": d.get("is_free_tier")}
            try:  # credit bought vs spent; some keys cannot read it, then only usage is shown
                _, c = _get("https://openrouter.ai/api/v1/credits", {"Authorization": f"Bearer {key}"}, timeout=8)
                c = c.get("data") or {}
                if c.get("total_credits") is not None:
                    out["openrouter"]["creditos"] = c["total_credits"]
                    out["openrouter"]["saldo"] = round(c["total_credits"] - (c.get("total_usage") or 0), 4)
            except Exception:
                pass
        except Exception as e:
            out["openrouter"] = {"configurada": True, "erro": str(e)[:100]}
    out["chaves"] = {k: bool(os.environ.get(k)) for k in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "OPENROUTER_API_KEY", "GEMINI_API_KEY", "GROQ_API_KEY")}
    return out
