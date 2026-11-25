# REASON O1 / VibeCoding: guia de visibilidade

Verificado a 2026-11-25. As fontes que não consegui abrir estão marcadas com ⚠️ (o Reddit, o Product Hunt e o Glama bloqueiam leitores automáticos).
Repositório: https://github.com/ET5131620/reason-o1-vibecoding · Site: https://et5131620.github.io/reason-o1-vibecoding/

## 0. Já feito no repositório (2026-11-25)

- README em EN e PT com banner, emblemas, botão de download direto, porque foi criado, vantagens, 5 GIFs do fluxo e galeria de capturas.
- 16 topics: `vibe-coding`, `claude-code`, `mcp`, `mcp-server`, `model-context-protocol`, `codex`, `ai-tools`, `ai-agents`, `llm`, `ollama`, `developer-tools`, `local-first`, `python`, `claude`, `cursor`, `open-source`.
- Homepage apontada para o site (GitHub Pages).
- Release v1.0.0 publicada.
- Site com GIFs e cartão social (`og:image` 1280×640).

## 1. Fica contigo (5 minutos)

| Passo | Onde |
|---|---|
| **Cartão social**: carregar `docs/assets/readme/banner.png` (1280×640, 280 KB) | Settings → General → *Social preview* → Edit → Upload |
| **Fixar o repositório no perfil** | github.com/ET5131620 → *Customize your pins* |
| **Ativar as Discussions** (Q&A e Show and tell) | Settings → General → Features → Discussions |
| Topics extra que valem a pena (o limite é 20): `agent-skills`, `claude-skills`, `local-llm`, `ai-coding` | Engrenagem do *About* |

## 2. Listas "awesome" no GitHub (por ordem de impacto)

| Lista | Como se submete | Regras | Quando |
|---|---|---|---|
| [hesreallyhim/awesome-claude-code](https://github.com/hesreallyhim/awesome-claude-code) (58,8k★) | **Só pelo formulário de issue** ("recommend-resource"), no site e feito por ti. Nada de PR nem de `gh`. | O repositório precisa de **14 dias** desde o primeiro commit **ou** de 100★. Uma linha, sem emojis nem linguagem de venda. | **A partir de 8 dez 2026** |
| [punkpeye/awesome-mcp-servers](https://github.com/punkpeye/awesome-mcp-servers) (98,5k★) | Fork, uma linha no README, PR | Ordem alfabética dentro da categoria. **Obriga a ter a ficha no Glama** e o emblema no README. | Depois do Glama |
| [jqueryscript/awesome-claude-code](https://github.com/jqueryscript/awesome-claude-code) | PR ou issue | Formato `[**nome**](url) - (estrelas ⭐) - descrição`; secção *Usage & Observability* | Já |
| [roboco-io/awesome-vibecoding](https://github.com/roboco-io/awesome-vibecoding) | Issue | Declarar que és o autor; secção *Agent Workspaces & Usage* | Já |
| [filipecalegario/awesome-vibe-coding](https://github.com/filipecalegario/awesome-vibe-coding) (5,5k★) | PR segundo o CONTRIBUTING | Uma linha: nome – descrição (pouco ativa) | Já |
| [ai-for-developers/awesome-ai-coding-tools](https://github.com/ai-for-developers/awesome-ai-coding-tools) | PR | — | Já |
| [RoggeOhta/awesome-codex-cli](https://github.com/RoggeOhta/awesome-codex-cli) | PR | Pelo lado da integração MCP com o Codex | Já |
| [vince-lam/awesome-local-llms](https://github.com/vince-lam/awesome-local-llms) | PR | Pelo lado do Ollama e dos modelos locais | Já |

Evitar: appcypher/awesome-mcp-servers (arquivado) e janhq/awesome-local-ai (parado desde 2024).

**Linha pronta (sem emojis):**
> [REASON O1 / VibeCoding](https://github.com/ET5131620/reason-o1-vibecoding) - Local, read-only dashboard that inventories your AI setup (Claude Code, Codex, skills, MCP servers, CLIs, local models), suggests curated tool kits per project and doubles as an MCP server. Python stdlib, MIT.

## 3. Registos de servidores MCP

| Registo | Como | Nota |
|---|---|---|
| [Registo oficial MCP](https://github.com/modelcontextprotocol/registry) | CLI `mcp-publisher`: `init`, `login github`, `publish` | **Exige primeiro um pacote no PyPI** (ou um bundle MCPB). Outros diretórios copiam daqui. |
| Glama ⚠️ | https://glama.ai/mcp/servers → *Add server* | Necessário para a lista punkpeye |
| mcp.so | https://mcp.so/submit (formulário) | Pode pedir login |
| mcpservers.org (wong2) | https://mcpservers.org/submit | A revisão grátis demora cerca de 2 semanas. Existe uma via paga de $39, mas não é preciso. |
| Smithery | `smithery mcp publish` | Servidores locais vão como bundle MCPB |
| MCP Market · mcp.directory | formulário em /submit | Impacto baixo |
| PulseMCP | fechado de momento | Recolhe automaticamente do registo oficial |

➡️ **O passo que abre mais portas:** publicar o pacote `reason-o1` no PyPI, com `pip install reason-o1` e a linha `mcp-name: io.github.ET5131620/reason-o1` no README. Depois disso entra no registo oficial e, por arrasto, no PulseMCP e noutros diretórios.

## 4. Comunidades de lançamento

| Canal | Regras | Encaixe |
|---|---|---|
| [Show HN](https://news.ycombinator.com/showhn.html) | O título começa por "Show HN:". Tem de ser algo que se experimenta **sem registo**, e o REASON O1 cumpre. Não pedir votos. Ficar na conversa a responder. Publicar numa terça a quinta, às 14–16h de Lisboa. | Alto |
| [Anthropic, "Submit your build"](https://support.claude.com/en/articles/15485501-submit-your-build-how-it-works-and-what-you-re-agreeing-to) | Formulário (nome, email, país, link). Lê os termos: a autorização para ser destacado não se pode retirar. | Alto |
| r/ClaudeAI ⚠️ | Usar a flair "Built with Claude" | Alto |
| r/LocalLLaMA ⚠️ | No máximo cerca de 10% da tua atividade pode ser autopromoção. Declarar que és o autor. | Médio |
| r/ChatGPTCoding · r/vibecoding · r/ClaudeCode · r/mcp · r/SideProject ⚠️ | Ler a barra lateral antes; publicar em dias diferentes | Médio |
| r/opensource ⚠️ | Segundo relatos, remove projetos de autor único feitos com muito LLM | **Evitar** |
| dev.to · Hashnode | Artigo "How I…", tags `#ai #opensource #python #claude #mcp` | Médio |
| [Console.dev](https://console.dev/submit) | Newsletter de ferramentas para programadores | Médio |
| Product Hunt ⚠️ | Conta própria; o lançamento abre às 00:01 PT (08:01 em Lisboa) | Médio |
| Lobsters | Só por convite, com 70 dias de espera para autopromoção | Baixo, por agora |

## 5. Ordem sugerida

1. Hoje: as tarefas da secção 1 (cartão social, fixar o repositório, Discussions).
2. Esta semana: Show HN, r/ClaudeAI e um artigo no dev.to. Depois as listas jqueryscript e roboco, e o mcp.so.
3. Próximo passo técnico: pacote no PyPI, depois o registo oficial MCP, o Glama e o PR na punkpeye.
4. Em paralelo: carrossel no Instagram e LinkedIn e os cortes de vídeo no TikTok (secção 6).
5. **8 dez 2026**: formulário da hesreallyhim/awesome-claude-code.
6. Meados de dezembro: o lançamento do REASON ONE remete para o O1 e volta a dar-lhe tráfego.

## 6. Textos prontos

### Show HN
**Título:** `Show HN: REASON O1 – see every AI tool on your PC and what each project is missing`

> I kept losing afternoons not to code but to setup: skills in one folder, MCP servers in three configs, models I'd pulled months ago, and no idea which of them a given project actually needed.
>
> REASON O1 is a small local dashboard (Python standard library only, MIT) that scans your machine read-only — Claude Code, Codex, Cursor, Ollama, skills, MCP servers, CLIs, local models, git projects — and draws one map. Then it gives you 18 curated tool kits (3 essentials / 7 complete, ranked by GitHub stars, each with "why it's here"), marks what you already have vs. what's missing, and a "Council" that reads a project folder and lists what it needs.
>
> It never installs or runs anything by itself: it hands you the commands or a prompt for your own agent. It's also an MCP server, so Claude Code/Codex can query your inventory with your existing account, no API key.
>
> Download: https://github.com/ET5131620/reason-o1-vibecoding — feedback very welcome, especially on the kits.

### Reddit (r/ClaudeAI, flair "Built with Claude")
**Título:** `I built a free local dashboard that maps your whole AI setup and tells you what each project is missing (MCP server included)`
> Corpo: o texto do Show HN + "Disclosure: I'm the author. Free, MIT, no account." + o GIF `03-kit-steps.gif`.

### LinkedIn (PT)
> **Não é o código. É a configuração.**
>
> A maioria dos projetos com IA não falha por causa do código. Falha antes: ferramentas a mais, nenhum mapa, tokens gastos sem dar por isso.
>
> Lancei o **REASON O1 / VibeCoding**, grátis e open source (MIT):
> 🔍 vê tudo o que tens instalado: Claude Code, Codex, Cursor, Ollama, skills, MCPs, CLIs;
> 🧰 18 kits por tipo de trabalho, com o que já tens e o que falta;
> 🧭 um "Conselho" que lê o teu projeto e diz o que lhe falta;
> 🔒 corre no teu PC e nunca instala nada sozinho.
>
> ⬇ Download direto: https://github.com/ET5131620/reason-o1-vibecoding
> É um obrigado à comunidade open source e uma antevisão do REASON ONE, em meados de dezembro.
>
> #VibeCoding #ClaudeCode #MCP #OpenSource #IA #DevTools

### Instagram (carrossel de `launch/social/carrossel/pt/1–6.png`)
> Não é o código. É a configuração. 🌌
> O REASON O1 mapeia todas as ferramentas de IA do teu PC e diz o que falta a cada projeto. Grátis, open source, corre no teu computador.
> 🔗 Link na bio · 💾 Guarda para o próximo projeto
>
> #vibecoding #inteligenciaartificial #ia #programacao #developer #claudecode #opensource #aitools #coding #devtools #python #tecnologia

### X / Threads (EN)
> It's not the code. It's the setup.
> REASON O1 maps every AI tool on your PC (Claude Code, Codex, skills, MCP, Ollama…) and tells you what each project is missing. Free, MIT, local, also an MCP server.
> ⬇ https://github.com/ET5131620/reason-o1-vibecoding
> #ClaudeCode #MCP #VibeCoding #OpenSource

### TikTok / Reels
Usa os verticais de `launch/video/out/social/<lang>/*-v.mp4` (17–21 s). Legenda: a do Instagram. Hashtags: `#vibecoding #aitools #coding #programming #claudecode #opensource`.

## 7. Onde estão as peças

| Peça | Caminho |
|---|---|
| Banner e cartão social (1280×640) | `docs/assets/readme/banner.png` (fonte: `launch/banner/banner.html`) |
| GIFs do fluxo | `docs/assets/readme/01…05-*.gif` |
| Capturas | `docs/assets/readme/shot-*.webp` |
| Carrossel 1080×1350, EN e PT | `launch/social/carrossel/<lang>/1–6.png` (fonte: `launch/banner/carousel.html?lang=pt&n=1`) |
| Vídeos para as redes | `launch/video/out/social/<lang>/` |
