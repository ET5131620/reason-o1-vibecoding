"""REASON O1 as an MCP server (stdio, JSON-RPC 2.0, one message per line).

Connect it to Claude Code:  claude mcp add reason-o1 -- python /path/reason_o1.py mcp
Connect it to Codex:        [mcp_servers.reason-o1] command = "python" args = ["/path/reason_o1.py", "mcp"]
"""
from __future__ import annotations

import json
import sys

from . import core, studio, trends
from .about import ABOUT

TOOLS = [
    {"name": "o1_inventario", "description": "Resumo do que está instalado neste PC: apps de IA, skills, MCP, CLIs, modelos locais, agentes, projetos. Só leitura.",
     "inputSchema": {"type": "object", "properties": {"detalhe": {"type": "boolean", "description": "true devolve as listas completas"}}}},
    {"name": "o1_kits", "description": "Lista os kits necessários (conjuntos de skills, MCPs, CLIs e LLMs por objetivo).",
     "inputSchema": {"type": "object", "properties": {}}},
    {"name": "o1_kit", "description": "Detalhe de um kit: ferramentas com repositório, passo a passo e APIs grátis.",
     "inputSchema": {"type": "object", "properties": {"id": {"type": "string"}}, "required": ["id"]}},
    {"name": "o1_catalogo_pesquisar", "description": "Pesquisa no catálogo curado de skills, MCPs, CLIs e LLMs.",
     "inputSchema": {"type": "object", "properties": {"q": {"type": "string"}}, "required": ["q"]}},
    {"name": "o1_passaporte", "description": "Analisa uma pasta de projeto (só leitura) e devolve o passaporte e os kits recomendados, com o que falta.",
     "inputSchema": {"type": "object", "properties": {"caminho": {"type": "string"}}, "required": ["caminho"]}},
    {"name": "o1_guardar_relatorio", "description": "Guarda um relatório Markdown na pasta 08_RELATORIOS do REASON O1. Só escreve nessa pasta.",
     "inputSchema": {"type": "object", "properties": {"titulo": {"type": "string"}, "markdown": {"type": "string"}}, "required": ["titulo", "markdown"]}},
    {"name": "o1_tendencias", "description": "Tendências atuais (GitHub, Hacker News, Reddit): repositórios a subir, ferramentas mais faladas e as que aparecem juntas. Com 'tema', devolve também um pedido de pesquisa para fazeres na web (TikTok, Instagram, etc.).",
     "inputSchema": {"type": "object", "properties": {"atualizar": {"type": "boolean"}, "tema": {"type": "string"}}}},
    {"name": "o1_kit_criar", "description": "Sugere um kit para um objetivo em palavras simples: kits que servem, ferramentas (com o que o utilizador já tem) e as skills dele que ajudam.",
     "inputSchema": {"type": "object", "properties": {"objetivo": {"type": "string"}}, "required": ["objetivo"]}},
    {"name": "o1_kit_guardar", "description": "Guarda um kit do utilizador em 09_KITS. Usa só depois de o utilizador aprovar a lista. itens: [{n, r, t, p}].",
     "inputSchema": {"type": "object", "properties": {"nome": {"type": "string"}, "objetivo": {"type": "string"}, "itens": {"type": "array", "items": {"type": "object"}}, "notas": {"type": "string"}}, "required": ["nome", "itens"]}},
    {"name": "o1_prompt_gerar", "description": "Gera um prompt forte, passo a passo, para um objetivo e um ou mais kits (ids de o1_kits ou de kits do utilizador). nivel: essencial ou completo.",
     "inputSchema": {"type": "object", "properties": {"objetivo": {"type": "string"}, "kits": {"type": "array", "items": {"type": "string"}}, "nivel": {"type": "string", "enum": ["essencial", "completo"]}}, "required": ["objetivo"]}},
    {"name": "o1_prompts", "description": "Biblioteca de prompts do utilizador (07_PROMPTS). acao 'listar' (opcional q para filtrar) ou 'guardar' (titulo, texto, tags).",
     "inputSchema": {"type": "object", "properties": {"acao": {"type": "string", "enum": ["listar", "guardar"]}, "q": {"type": "string"}, "titulo": {"type": "string"}, "texto": {"type": "string"}, "tags": {"type": "string"}}, "required": ["acao"]}},
    {"name": "o1_skill_criar", "description": "Cria o esqueleto de uma skill (SKILL.md com name e description) em 01_SKILLS do utilizador. Não instala: devolve onde copiar para o Claude Code ou o Codex.",
     "inputSchema": {"type": "object", "properties": {"nome": {"type": "string"}, "descricao": {"type": "string"}, "quando": {"type": "string"}, "passos": {"type": "array", "items": {"type": "string"}}}, "required": ["nome", "descricao"]}},
]


def call(name: str, args: dict):
    if name == "o1_inventario":
        inv = core.cached_inventory() or core.inventory()
        return inv if args.get("detalhe") else core.summary(inv)
    if name == "o1_kits":
        k = core.kits()
        return {"kits": [{"id": x["id"], "nome": x["nome"], "resumo": x["resumo"]} for x in k["kits"]], "combos": k.get("combos", [])}
    if name == "o1_kit":
        kit = next((x for x in core.kits()["kits"] if x["id"] == args.get("id")), None)
        if not kit:
            raise ValueError("Kit não encontrado. Usa o1_kits para ver os ids.")
        inv = core.cached_inventory() or {}
        return {**kit, "itens": [{**i, "tens": core._have(i["n"], inv), "url": f"https://github.com/{i['r']}" if "/" in i.get("r", "") and not i["r"].startswith("http") else i.get("r", "")} for i in kit["itens"]]}
    if name == "o1_catalogo_pesquisar":
        return core.search_catalog(str(args.get("q", "")))
    if name == "o1_passaporte":
        return core.advise(str(args.get("caminho", "")))
    if name == "o1_guardar_relatorio":
        return {"guardado": core.save_report(str(args.get("titulo", "relatorio")), str(args.get("markdown", "")))}
    if name == "o1_tendencias":
        t = trends.trends(bool(args.get("atualizar")))
        out = {k: t.get(k) for k in ("gerado", "falados", "conjuntos", "github", "discussao", "listas", "erro") if t.get(k) is not None}
        if args.get("tema"):
            out["pedido_de_pesquisa"] = trends.research_prompt(str(args["tema"]))
        return out
    if name == "o1_kit_criar":
        return studio.suggest(str(args.get("objetivo", "")))
    if name == "o1_kit_guardar":
        return studio.save_kit(args)
    if name == "o1_prompt_gerar":
        return {"prompt": studio.kit_prompt(str(args.get("objetivo", "")), [str(x) for x in args.get("kits", [])], str(args.get("nivel", "completo")))}
    if name == "o1_prompts":
        if args.get("acao") == "guardar":
            return studio.prompt_save(str(args.get("titulo", "")), str(args.get("texto", "")), str(args.get("tags", "")))
        q = str(args.get("q", "")).lower()
        return [p for p in studio.prompts_list() if not q or q in (p["titulo"] + p["tags"] + p["texto"]).lower()][:30]
    if name == "o1_skill_criar":
        return studio.skill_create(str(args.get("nome", "")), str(args.get("descricao", "")), [str(x) for x in args.get("passos", [])], str(args.get("quando", "")))
    raise ValueError(f"Ferramenta desconhecida: {name}")


def _send(msg: dict):
    sys.stdout.write(json.dumps(msg, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def serve():
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stdin.reconfigure(encoding="utf-8")
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            _send({"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "Parse error"}})
            continue
        rid, method = req.get("id"), req.get("method", "")
        if rid is None:  # notification
            continue
        try:
            if method == "initialize":
                ver = (req.get("params") or {}).get("protocolVersion") or "2025-06-18"
                result = {"protocolVersion": ver, "capabilities": {"tools": {}},
                          "serverInfo": {"name": "reason-o1", "version": ABOUT["version"]},
                          "instructions": "REASON O1 / VIBECODING: inventário local de IA, kits e conselho por projeto. Só lê, exceto o1_guardar_relatorio, o1_kit_guardar, o1_prompts (guardar) e o1_skill_criar, que escrevem só nas pastas do REASON O1. Ajuda a escolher kits, gerar e guardar prompts e criar skills."}
            elif method == "tools/list":
                result = {"tools": TOOLS}
            elif method == "tools/call":
                p = req.get("params") or {}
                try:
                    out = call(p.get("name", ""), p.get("arguments") or {})
                    result = {"content": [{"type": "text", "text": json.dumps(out, ensure_ascii=False, indent=1)}]}
                except Exception as e:  # tool errors go back to the model, not as protocol errors
                    result = {"content": [{"type": "text", "text": f"Erro: {e}"}], "isError": True}
            elif method == "ping":
                result = {}
            else:
                _send({"jsonrpc": "2.0", "id": rid, "error": {"code": -32601, "message": f"Método não suportado: {method}"}})
                continue
            _send({"jsonrpc": "2.0", "id": rid, "result": result})
        except Exception as e:
            _send({"jsonrpc": "2.0", "id": rid, "error": {"code": -32603, "message": str(e)}})
