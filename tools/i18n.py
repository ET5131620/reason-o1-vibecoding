"""Languages: find every Portuguese text the person can see, and check EN / FR / ES have all of them.

    python tools/i18n.py            check; exits 1 and lists what is missing (run before every release)
    python tools/i18n.py keys       write ui/i18n/_keys.json (all source texts, Portuguese)
    python tools/i18n.py missing    write ui/i18n/_missing.<lang>.json for each language with gaps

How it works: the interface is written in Portuguese and translated in the browser. ui/i18n/<lang>.json maps
each Portuguese text to its translation; '{}' marks a value filled in at run time ("{} ferramentas").
The texts come from ui/index.html (HTML, JS strings and template literals), data/*.json (kits, catalog)
and the Python server's messages. Nothing here needs a network or a package outside the standard library.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
I18N = ROOT / "ui" / "i18n"
LANGS = ("en", "fr", "es")
S = "\x00"  # stands for a ${...} value inside a template literal
WORD = "\x01"  # marks a text that sat alone between two tags
# lowercase Portuguese labels that appear alone between tags (code words like "ok" or "on" are not here)
PT_WORDS = {"falta", "essencial", "completo", "por", "ou", "de", "grátis", "pago", "novo", "local", "nuvem", "aberto",
            "fechado", "ativo", "desligado", "ligado", "opcional", "recomendado", "instalado", "agora", "hoje",
            "ontem", "semana", "dias", "mês", "tokens", "pedidos", "saída", "entrada", "nível", "gráfico",
            "vídeo", "imagem", "texto", "código", "dados", "segurança", "erro", "aviso", "carregar", "copiar",
            "abrir", "fechar", "guardar", "seguinte", "voltar", "sim", "não", "tudo", "nada", "mais", "menos",
            "tuas", "teus", "juntas", "juntos", "passo", "passos"}

ATTRS = ("data-tip", "title", "placeholder", "aria-label", "alt", "data-hint")
# JSON keys whose values are identifiers, links or names — never translated
# ("kits" is not here: it is the list of kits; inside a combo it holds ids, which human() drops anyway)
JSON_SKIP = {"id", "n", "r", "t", "icon", "cor", "dl", "url", "palavras", "cookbook", "repo", "version", "note",
             "e", "x", "licenca", "lang", "stars", "avatar", "tags", "cmd", "pip", "npm", "site"}


def norm(s: str) -> str:
    """Same rule as nrm() in ui/index.html: runs of spaces become one, line breaks stay (prompts keep their shape)."""
    s = re.sub(r"[ \t\r\f\v]+", " ", s)
    s = re.sub(r" ?\n ?", "\n", s)
    return re.sub(r"\n{3,}", "\n\n", s).strip()


def human(s: str) -> bool:
    """Looks like text a person reads (not a selector, class, id, URL, CSS or code)."""
    if s.startswith(WORD):  # text between two tags: "falta", "essencial", "Vantagem:" are labels
        s = norm(s[1:])
        if re.fullmatch(r"[A-Za-zÀ-ÿ][a-zà-ÿ]+[:.]?", s) and (re.search(r"[À-ÿ]", s) or s.lower() in PT_WORDS or s[0].isupper()):
            return True
    s = norm(s.replace(S, "{}"))
    letters = re.sub(r"[^A-Za-zÀ-ÿ]", "", s.replace("{}", ""))
    if len(letters) < 2 or len(s) > 4000 or "${" in s or len(letters) < .35 * len(s.replace("{}", "")):
        return False
    if re.match(r"^(https?:|/|\.[\w-]|#[\w-]|[\w-]+:\s*[\w#-]+;?$)", s) or re.search(r"[{}=]\s*$|^[\w-]+:\s*[^;]+;$|=>|\(\)|\bvar\(|\bpx\b|\brgba?\(", s.replace("{}", "")):
        return False
    if " " not in s and not re.search(r"[À-ÿ]", s):
        # one word: keep labels ("Kits", "Uso") but not code words ("click", "on", "kit")
        return bool(re.match(r"^[A-ZÀ-Ý][a-zà-ÿ]{1,}$", s)) or s in {"Ctrl K"}
    if re.match(r"^[\w.-]+/[\w.-]+$", s):  # owner/repo
        return False
    return True


# ---------- a small JavaScript scanner: strings, template literals, comments, regex literals ----------
def js_literals(src: str):
    """Yields ('str', text) and ('tpl', [chunk, S, chunk, ...]) for every literal in a JS source."""
    i, n, prev = 0, len(src), ""
    while i < n:
        c = src[i]
        if src.startswith("//", i):
            i = src.find("\n", i); i = n if i < 0 else i; continue
        if src.startswith("/*", i):
            j = src.find("*/", i + 2); i = n if j < 0 else j + 2; continue
        if c in "\"'":
            j, buf = i + 1, []
            while j < n and src[j] != c:
                if src[j] == "\\" and j + 1 < n:
                    buf.append({"n": "\n", "t": "\t"}.get(src[j + 1], src[j + 1])); j += 2; continue
                buf.append(src[j]); j += 1
            yield ("str", "".join(buf)); i = j + 1; prev = "x"; continue
        if c == "`":
            parts, i = _template(src, i + 1)
            yield ("tpl", parts)
            for inner in parts[1::2]:  # expressions may hold literals too
                yield from js_literals(inner)
            prev = "x"; continue
        if c == "/" and (prev in "(,=:[!&|?{};+-*%<>~^" or prev == "" or re.search(r"(return|typeof|case)\s*$", src[max(0, i - 8):i])):
            j, cls = i + 1, False  # regex literal
            while j < n and (src[j] != "/" or cls) and src[j] != "\n":
                if src[j] == "\\": j += 2; continue
                cls = True if src[j] == "[" else False if src[j] == "]" else cls
                j += 1
            i = j + 1; prev = "x"; continue
        if not c.isspace():
            prev = c if c in "(,=:[!&|?{};+-*%<>~^" else "x"
        i += 1


def _template(src: str, i: int):
    """Reads a template literal from i (after the backtick). Returns ([text, expr, text, ...], next index)."""
    parts, buf, n = [], [], len(src)
    while i < n:
        c = src[i]
        if c == "\\":
            buf.append({"n": "\n", "t": "\t"}.get(src[i + 1], src[i + 1]) if i + 1 < n else ""); i += 2; continue
        if c == "`":
            parts.append("".join(buf)); return parts, i + 1
        if src.startswith("${", i):
            parts.append("".join(buf)); buf = []
            depth, j = 1, i + 2
            while j < n and depth:
                if src[j] == "`":
                    _, j = _template(src, j + 1); continue
                if src[j] in "\"'":
                    q = src[j]; j += 1
                    while j < n and src[j] != q: j += 2 if src[j] == "\\" else 1
                    j += 1; continue
                depth += {"{": 1, "}": -1}.get(src[j], 0); j += 1
            parts.append(src[i + 2:j - 1]); i = j; continue
        buf.append(c); i += 1
    parts.append("".join(buf)); return parts, n


# expressions that give plain text (so the text node is not split there)
TEXTY = re.compile(r"^\s*(esc\([^`]*\)|[\w.?\[\]\"'| ]+|fmt\w*\([^`]*\)|\w+\.length|String\([^`]*\)|T\([^`]*\))\s*$")


def html_texts(markup: str, exprs: list[str]):
    """Text runs and attribute values in a chunk of markup where S marks each value."""
    out = []
    for a in ATTRS:
        for m in re.finditer(rf'{a}="([^"]*)"', markup):
            out.append(m.group(1))
    body = re.sub(r"<!--.*?-->", "", markup, flags=re.S)
    body = re.sub(r"<(script|style)\b.*?</\1>", "", body, flags=re.S | re.I)
    for run in re.split(r"<[^>]*>", body):
        if S not in run:
            out.append(WORD + run); continue  # a whole text between tags: a single word here is a label
        out.append(run)  # whole run, values as {}
        # a value that may hold markup splits the text node: keep the pieces too
        k = 0
        for piece in run.split(S):
            out.append(piece)
            k += 1
    return out


def from_html_file(path: Path):
    text = path.read_text(encoding="utf-8")
    keys = []
    scripts = re.findall(r"<script\b[^>]*>(.*?)</script>", text, flags=re.S | re.I)
    page = re.sub(r"<script\b.*?</script>|<style\b.*?</style>", "", text, flags=re.S | re.I)
    keys += html_texts(page, [])
    for m in re.finditer(r"<title>(.*?)</title>", text, flags=re.S): keys.append(m.group(1))
    for src in scripts:
        for kind, val in js_literals(src):
            if kind == "str":
                keys += html_texts(val, []) if "<" in val and ">" in val else [val]
            else:
                chunks, exprs = val[0::2], val[1::2]
                joined = S.join(chunks)
                if "<" in joined and ">" in joined:
                    keys += html_texts(joined, exprs)
                else:
                    keys.append(joined)
                    if any(not TEXTY.match(e) for e in exprs):
                        keys += chunks
    return keys


def from_json(obj, key=None):
    if isinstance(obj, str):
        return [] if key in JSON_SKIP or obj.startswith("http") else [obj]
    if isinstance(obj, list):
        if key == "c":  # curated pairs: [tool name, why]
            return [p[1] for p in obj if isinstance(p, list) and len(p) > 1]
        return [x for v in obj for x in from_json(v, key)]
    if isinstance(obj, dict):
        out = []
        for k, v in obj.items():
            if k == "n" and key == "apis":
                out.append(v)
            elif k not in JSON_SKIP:
                out += from_json(v, k if k != "itens" else None) if k != "apis" else [x for a in v for x in from_json(a, "apis")]
        return out
    return []


PY_STR = re.compile(r'(?<![\w"])(f?)("([^"\\\n]|\\.)*"|\'([^\'\\\n]|\\.)*\')')


def from_python(path: Path):
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.lstrip().startswith("#") or '"""' in line:
            continue
        for m in PY_STR.finditer(line):
            s = m.group(2)[1:-1]
            if m.group(1):
                s = re.sub(r"\{[^{}]*\}", S, s)
            # server messages the person sees are Portuguese; English strings are code or logs
            if re.search(r"[ãõçáéíóúâêôà]|\b(não|já|está|para|uma|com|sem|isto|pasta|ficheiro|chave|instala)\b", s, re.I):
                out.append(s)
    return out


def source_keys() -> list[str]:
    raw = from_html_file(ROOT / "ui" / "index.html")  # offline.html carries its own four languages
    for f in sorted((ROOT / "data").glob("*.json")):
        if f.name.startswith("gh_"):
            continue  # live GitHub snapshot: descriptions come from the authors
        raw += from_json(json.loads(f.read_text(encoding="utf-8")))
    for f in [ROOT / "reason_o1.py", *sorted((ROOT / "o1").glob("*.py"))]:
        raw += from_python(f)
    own_names = {"Português", "English", "Français", "Español"}  # each language is named in itself
    keys = {norm(k.replace(S, "{}").replace(WORD, "")) for k in raw if human(k)} - own_names
    keys = {k for k in keys if not re.fullmatch(r"[\W\d{}]*", k)}
    return sorted(keys)


def load(lang: str) -> dict:
    f = I18N / f"{lang}.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}


def main(argv: list[str]) -> int:
    keys = source_keys()
    cmd = argv[0] if argv else "check"
    I18N.mkdir(parents=True, exist_ok=True)
    if cmd == "keys":
        (I18N / "_keys.json").write_text(json.dumps(keys, ensure_ascii=False, indent=0), encoding="utf-8")
        print(f"{len(keys)} textos -> ui/i18n/_keys.json"); return 0
    if cmd == "merge":
        # translators return {"<index in the list they were given>": "translation"}; the list is _keys.json
        # or, when it exists, _missing.<lang>.json
        for lang in LANGS:
            parts = sorted(I18N.glob(f"_tr.{lang}*.json"))
            if not parts:
                continue
            src_f = I18N / f"_missing.{lang}.json"
            src = json.loads((src_f if src_f.exists() else I18N / "_keys.json").read_text(encoding="utf-8"))
            d = load(lang)
            for p in parts:
                for i, tr in json.loads(p.read_text(encoding="utf-8")).items():
                    d[src[int(i)]] = tr
            d = {k: d[k] for k in sorted(d)}
            (I18N / f"{lang}.json").write_text(json.dumps(d, ensure_ascii=False, indent=0), encoding="utf-8")
            print(f"{lang}: {len(d)} entradas")
        return 0
    bad = 0
    for lang in LANGS:
        d = load(lang)
        miss = [k for k in keys if not str(d.get(k, "")).strip()]
        holes = [k for k in keys if k in d and k.count("{}") != str(d[k]).count("{}")]
        if cmd == "missing" and miss:
            (I18N / f"_missing.{lang}.json").write_text(json.dumps(miss, ensure_ascii=False, indent=0), encoding="utf-8")
        print(f"{lang}: {len(keys) - len(miss)}/{len(keys)} traduzidos" + (f", faltam {len(miss)}" if miss else "") +
              (f", {len(holes)} com '{{}}' trocado" if holes else ""))
        for k in (miss + holes)[:8]:
            print("   -", k[:110])
        bad += len(miss) + len(holes)
    if bad:
        print("FALHOU: há textos sem tradução. Corre 'python tools/i18n.py missing' e traduz os ficheiros _missing.")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
