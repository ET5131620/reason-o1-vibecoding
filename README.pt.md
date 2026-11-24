# REASON O1 / VIBECODING

**Um mapa vivo do teu ecossistema de IA.** Vê o que tens instalado — Claude Code, Codex, Cursor, ChatGPT, Ollama, skills, MCPs, CLIs, modelos — e descobre o que falta a cada projeto.

Grátis e de código aberto. Um obrigado à comunidade e uma antevisão do **REASON ONE** *(coming soon)*.

## O que faz

| | |
|---|---|
| **Inventário automático** | Sempre que abre, varre o PC: apps de IA, skills, servidores MCP, CLIs, modelos locais, agentes, projetos git e conversas guardadas. Lê só nomes, contagens e datas. |
| **Kit de conjuntos** | 18 kits: agentes e MCP, web design UI/UX, front-end, back-end, design gráfico e canvas, vídeo, imagem, segurança, código, **reduzir erros e tokens**, apps com IA, pesquisa e RAG, automação, CAD/3D, monetizar, docs e memória, marketing, dados. Cada um tem o conjunto **Essencial** (3, para principiante) e o **Completo** (7, para expert), ordenados pelas estrelas no GitHub, com o que faz e a vantagem de cada ferramenta. Mostra também as skills que **já tens** para essa área. Dois botões: **instalar o necessário** e **gerar prompt passo a passo**. |
| **Tendências** | O que se está a usar agora, de fontes públicas e sem chave: repositórios a subir no GitHub, discussões do Hacker News e do Reddit, as ferramentas mais faladas e as que aparecem juntas. Para o TikTok, o Instagram e o Facebook gera o pedido de pesquisa para o teu agente. |
| **Criador** | Monta o teu kit a partir de um objetivo e guarda-o em `09_KITS`. Tem uma biblioteca de prompts em `07_PROMPTS` e cria o esqueleto de skills novas em `01_SKILLS`. |
| **Claude Cookbook** | As receitas oficiais da Anthropic como base de exemplos: sugeridas no primeiro arranque e ligadas a cada kit. |
| **Conselho** | Lê um projeto (só leitura), faz-lhe um passaporte — missão, stack, ligações — e diz que kits, skills, MCPs e CLIs ele precisa, com o que já tens e o que falta. |
| **Liga-se ao teu agente** | É também um servidor MCP: o teu Claude Code ou Codex passa a conhecer o teu inventário e os kits, com a conta que já tens. Sem chave de API. |
| **Aprender** | O que é um LLM, MCP, CLI, skill, agente, API e RAG — e um assistente para criar a tua primeira skill. |
| **APIs e router** | O que é um router de APIs, APIs grátis e o passo a passo com o OmniRoute: um só endereço local para muitos modelos, ligado ao Claude Code e ao Codex. |
| **Sempre atualizado** | Ao abrir (e a cada 6 h) procura a versão nova no repositório oficial, instala-a com cópia de segurança da anterior e reinicia. Os kits sincronizam mesmo entre versões. Pode ser desligado nas Definições. |

## Começar

Precisas do Python 3.10 ou mais recente. Não há nada para instalar: só a biblioteca padrão.

```bash
python reason_o1.py
```

No Windows também podes dar duplo clique em `ARRANCAR.bat`. O painel abre em `http://127.0.0.1:8731`.

### Ligar ao Claude Code

```bash
claude mcp add reason-o1 --scope user -- python /caminho/para/reason_o1.py mcp
```

### Ligar ao Codex (`~/.codex/config.toml`)

```toml
[mcp_servers.reason-o1]
command = "python"
args = ["/caminho/para/reason_o1.py", "mcp"]
```

Ferramentas MCP (12):

- **Ler:** `o1_inventario`, `o1_kits`, `o1_kit`, `o1_catalogo_pesquisar`, `o1_passaporte`, `o1_tendencias`, `o1_kit_criar`.
- **Gerar:** `o1_prompt_gerar` devolve o prompt e não grava nada.
- **Escrever** (só nas pastas do REASON O1): `o1_guardar_relatorio`, `o1_kit_guardar`, `o1_prompts` (listar e guardar), `o1_skill_criar`.

Com o MCP ligado, o Claude Code ou o Codex pedem ajuda ao programa para escolher o melhor conjunto, gerar e guardar prompts e criar skills.

## Privacidade e segurança

- Corre só em `127.0.0.1`. Cada pedido à API leva um token de sessão novo e o cabeçalho `Host` é verificado.
- Nunca lê chaves, variáveis de ambiente, argumentos de MCP nem o conteúdo das conversas. Os URLs git perdem as credenciais antes de serem mostrados.
- "Pedir ao Claude/Codex" usa o teu próprio CLI em modo só leitura e pede confirmação antes, porque conta para os teus limites.
- O programa nunca executa código descarregado. "Instalar o necessário" dá-te os comandos e um pedido para o teu agente, que pede o teu sim.
- As tuas definições ficam em `~/.reason-o1/`.

## Estrutura

```
reason_o1.py        servidor local + entrada MCP + scan
o1/core.py          inventário, passaporte, conselho
o1/mcp_server.py    servidor MCP (stdio)
o1/studio.py        o que já tens por kit, criador de kits, prompts, skills, Cookbook
o1/trends.py        tendências (GitHub, Hacker News, Reddit)
o1/updater.py       atualização a partir do repositório oficial (cópia de segurança, proteção zip-slip)
o1/about.py         versão, créditos, repositório oficial
data/kits.json      os 18 kits (3 + 7), as combinações e o Cookbook
data/catalog.json   LLMs, motores, agentes, fontes de skills e MCP
data/gh_snapshot.json  estrelas e datas para funcionar offline
ui/index.html       o painel
ui/i18n/            traduções EN / FR / ES (o português é a fonte)
tools/i18n.py       verificação das quatro línguas
```

## Línguas

O painel fala português, inglês, francês e espanhol (botão de idioma no topo). O texto é escrito em português no código e traduzido no browser a partir de `ui/i18n/<língua>.json`.

Quem mudar ou acrescentar texto à interface, aos kits ou às mensagens do servidor corre antes de publicar:

```
python tools/i18n.py            # falha e lista o que falta traduzir
python tools/i18n.py missing    # escreve ui/i18n/_missing.<língua>.json para traduzir
```

Uma versão só sai com as quatro línguas completas.

## Criado por

**531620ET · Godmode** — GitHub: *link por confirmar*

Os kits apontam para projetos de terceiros, cada um com a sua licença. Lê sempre o README e a licença antes de instalar.
