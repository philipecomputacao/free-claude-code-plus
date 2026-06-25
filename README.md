# free-claude-code-plus

> **A community fork of [Alishahryar1/free-claude-code][upstream] that adds first-class
> support for the [MiniMax Token Plan][minimax-docs] as an LLM provider.**
> Route Claude Code (CLI + VS Code) through MiniMax-M3 / M2.7 / M2.5 / M2.1 / M2,
> or mix MiniMax with NVIDIA NIM, OpenCode Zen, OpenRouter, and 14 other providers
> in the same project.

[upstream]: https://github.com/Alishahryar1/free-claude-code
[minimax-docs]: https://platform.minimax.io/docs/guides/quickstart

[![license](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
![status](https://img.shields.io/badge/status-stable-brightgreen.svg)
![python](https://img.shields.io/badge/python-3.14%2B-blueviolet.svg)
![providers](https://img.shields.io/badge/providers-18-orange.svg)
![fork](https://img.shields.io/badge/fork-Alishahryar1%2Ffree--claude--code-blue.svg)
[![Maintained by @lpdigital.me](https://img.shields.io/badge/maintained%20by-%40lpdigital.me-E4405F.svg)](https://www.instagram.com/lpdigital.me/)

---

<table>
<tr>
<td width="120" align="center" valign="top">
<a href="https://www.instagram.com/lpdigital.me/"><img src="https://raw.githubusercontent.com/philipecomputacao/inventario-apis-gratuitas/main/assets/perfil-300.jpg" width="100" height="100" alt="@lpdigital.me" style="border-radius: 50%;" /></a>
</td>
<td valign="top">

**Fork mantido por [@lpdigital.me](https://www.instagram.com/lpdigital.me/)** — Philipe compartilha plugins, automações e IA toda semana no Instagram. Manda um follow se o proxy te ajudou.

</td>
</tr>
</table>

---

## What is this?

`free-claude-code` (FCC) is a **proxy server** that sits between the Claude Code
CLI / VS Code extension and a backend LLM provider. By default, FCC points at
NVIDIA NIM (free tier) — but you can configure it to talk to **18+ providers**,
including OpenCode Zen, OpenRouter, Groq, Cerebras, Fireworks, Z.AI, Kimi,
DeepSeek, Mistral, Codestral, Gemini, and now **MiniMax**.

This fork exists because the upstream didn't yet have a MiniMax provider, and
adding it correctly required more than a config line — it required a new
`AnthropicMessagesTransport` subclass because MiniMax speaks Anthropic's wire
format on a non-standard path.

```
┌────────────┐  Anthropic API  ┌──────────────────┐  Anthropic-compat    ┌────────────┐
│ Claude Code│ ──────────────► │  fcc-server      │ ───────────────────► │  MiniMax   │
│ (CLI/VSX)  │ ◄────────────── │  (this fork)     │ ◄─────────────────── │  Token Plan│
└────────────┘  SSE streaming  └──────────────────┘  x-api-key header     └────────────┘
                                            │
                                            │  same proxy can fan out to
                                            ▼
                                    ┌──────────────────┐
                                    │  NVIDIA NIM      │
                                    │  OpenCode Zen    │
                                    │  OpenRouter      │
                                    │  14+ more…       │
                                    └──────────────────┘
```

---

## Why this fork exists

The upstream `free-claude-code` is excellent but moves slowly. MiniMax's
Token Plan is one of the best value-for-money LLM subscriptions in the
Brazilian market (R$120/month for M3 + M2.7 + M2.5 + M2.1 + M2 with 5h
rolling windows), but adding it as a first-class provider required:

1. A new `providers/minimax/` module (subclass of `AnthropicMessagesTransport`)
2. A new `MINIMAX_DEFAULT_BASE` constant (with the right `/v1` suffix)
3. Wiring into the `PROVIDER_CATALOG` so it shows in the Admin UI
4. Env-var plumbing (`MINIMAX_API_KEY`) and Admin UI fields
5. A critical bug fix: the base URL **must** include `/v1` or `/messages`
   resolves to a 404

All of that is in this fork. The bug fix alone is non-trivial to discover
(see [§ Bug fix: missing /v1 suffix](#bug-fix-missing-v1-suffix) below).

---

## Table of contents

- [What you get](#what-you-get)
- [Quick start](#quick-start)
  - [0. Install with an AI assistant](#0-install-with-an-ai-assistant-recommended-if-youre-not-technical)
- [Supported providers](#supported-providers)
- [Model visibility control](#model-visibility-control)
- [MiniMax provider in depth](#minimax-provider-in-depth)
- [Bug fix: missing /v1 suffix](#bug-fix-missing-v1-suffix)
- [Architecture](#architecture)
- [Development](#development)
- [Syncing with upstream](#syncing-with-upstream)
- [Contributing back to upstream](#contributing-back-to-upstream)
- [Related projects](#related-projects)
- [License](#license)

---

## What you get

### With MiniMax enabled

```bash
# Set the API key
export MINIMAX_API_KEY=sk-cp-...

# Use any MiniMax model as if it were a native Claude model
claude --model minimax/MiniMax-M3 "explana o teorema de Bayes em PT-BR"
claude --model minimax/MiniMax-M2.5 "write a python web server"
claude --model minimax/MiniMax-M2 "summarize this diff"
```

The MiniMax-M3 is the flagship 1M-context model; the `-highspeed` variants trade
some quality for latency.

### With multi-provider routing

Configure the proxy to fan out across providers based on the request:

```jsonc
// ~/.claude/settings.json
{
  "env": {
    "ANTHROPIC_BASE_URL": "http://127.0.0.1:8082",
    "ANTHROPIC_AUTH_TOKEN": "dummy"
  }
}
```

Then the model id routes through fcc-server:

| Model id | Provider |
|---|---|
| `minimax/MiniMax-M3` | MiniMax Token Plan |
| `nvidia_nim/meta/llama-3.3-70b-instruct` | NVIDIA NIM |
| `opencode/big-pickle` | OpenCode Zen |
| `open_router/anthropic/claude-sonnet-4` | OpenRouter |
| `groq/llama-3.3-70b-versatile` | Groq |
| `cerebras/llama-3.3-70b` | Cerebras |
| `deepseek/deepseek-chat` | DeepSeek |
| `gemini/gemini-2.5-pro` | Gemini |
| `mistral/mistral-large-latest` | Mistral |
| `kimi/kimi-k2-0711-preview` | Kimi (Moonshot) |
| `fireworks/accounts/fireworks/models/llama-v3p3-70b-instruct` | Fireworks |
| `zai/glm-4.5` | Z.AI |
| `codestral/codestral-2508` | Mistral Codestral |
| `ollama/llama3.2` | Ollama (local) |
| `llamacpp/...` | llama.cpp (local) |
| `lmstudio/...` | LM Studio (local) |
| `wafer/...` | Wafer (experimental) |

Mix and match per conversation or per project. Use `DISABLED_PROVIDERS` and
`HIDDEN_MODELS` (or the Admin UI's model visibility panel) to control which
models appear in the `/model` picker.

---

## Quick start

### 0. Install with an AI assistant (recommended if you're not technical)

Copy the prompt below and paste it into any AI chat (ChatGPT, Claude,
Gemini, etc.). The assistant will install this wrapper end-to-end on
your machine — no programming knowledge required on your side.

<details>
<summary><strong>Click to reveal the install prompt — copy everything inside the box</strong></summary>

```plaintext
You are helping me install "free-claude-code-plus", a Python wrapper
around the Claude Code CLI that adds support for MiniMax, OpenRouter,
OpenAI, DeepSeek, Mistral, and 13+ other LLM providers as first-class
backends (Claude Code natively only supports Anthropic). It runs
locally as `fcc-claude` / `fcc` and is normally installed via uv.

Your job: install it on my machine end-to-end and verify it works.
Do not ask me coding questions — make sensible decisions and tell me
what you did. If you hit a step that needs my input (e.g. choosing
a provider key), ask exactly one focused question and continue.

=========================================================
STEP 1 — Detect my environment
=========================================================
Run these commands and remember the output:

  uname -a                          # OS family (Darwin / Linux / Windows-bash)
  python3 --version                 # need 3.10+ (3.14+ recommended)
  command -v uv                     # need uv 0.11+ for `uv tool install`
  command -v claude                 # is Claude Code already installed?
  command -v fcc-claude             # is this wrapper already installed?
  echo "KEYS=${MINIMAX_API_KEY:-unset} ${OPENROUTER_API_KEY:-unset}"  # which keys exist?

If `uv` is missing, install it:
  curl -LsSf https://astral.sh/uv/install.sh | sh
  # restart the shell afterwards

If `python3` is missing, tell me to install Python 3 from
https://python.org and stop.

=========================================================
STEP 2 — Install the wrapper
=========================================================
Run:

  git clone https://github.com/philipecomputacao/free-claude-code-plus.git
  cd free-claude-code-plus
  uv tool install .

If `uv tool install .` fails with "no module named X", that's a
missing dev dep — install it with `uv tool install . --with X` and
retry. If it fails with "permission denied" on macOS, ensure
~/.local/bin is on PATH (`echo $PATH | grep -q "$HOME/.local/bin"`
should return true; if not, add `export PATH="$HOME/.local/bin:$PATH"`
to ~/.zshrc and restart the shell).

After install, verify the binaries exist:

  command -v fcc-server             # must print a path
  command -v fcc                    # must print a path

If either is missing, your PATH doesn't include ~/.local/bin — fix
the PATH and retry before continuing.

=========================================================
STEP 3 — Configure provider keys
=========================================================
Ask me ONE question: "Which provider do you want to use as backend?"
Options: MiniMax, OpenRouter, OpenAI, DeepSeek, Mistral, Groq,
Cerebras, Fireworks, ZAI, Kimi, NVIDIA NIM, Ollama (local), or
"skip for now" (you can add keys later).

After I answer, run:

  mkdir -p ~/.fcc
  cp .env.example ~/.fcc/.env
  # Now edit ~/.fcc/.env and set the matching env var to the key I paste.
  # NEVER invent a key — wait for me to paste it.

After I paste the key, restart my shell (or `source ~/.zshrc` /
`source ~/.bashrc`) so the new env var is visible to fcc-server.

=========================================================
STEP 4 — Start the local proxy
=========================================================
The wrapper runs a local HTTP proxy (fcc-server) that Claude Code
talks to. fcc-server has no subcommands — invoking it starts the
proxy directly in foreground. To run it in the background:

  # macOS / Linux — background
  nohup fcc-server > ~/.fcc/logs/server.out 2>&1 &

  # or, foreground (Ctrl+C to stop)
  fcc-server

Verify it's up:

  curl -s -o /dev/null -w "%{http_code}\n" -m 2 http://localhost:8082/
  # expect 404, 405, or 204 (any HTTP response means the proxy is up)

If curl times out, fcc-server didn't start — check the logs (the
proxy writes to ~/.fcc/logs/server.log via loguru; the uvicorn
stdout/stderr goes wherever you redirected it, e.g. server.out) and
tell me what they say.

=========================================================
STEP 5 — Run Claude Code through the wrapper
=========================================================
Now run Claude Code via the wrapper instead of the bare `claude`
binary. This makes Claude Code talk to the fcc-server proxy you
just started, which in turn talks to your chosen provider:

  fcc-claude                        # replaces `claude`
  # or with a specific session:
  fcc-claude --resume <session-id>

If you see "API key not set" or "provider not configured", go back
to STEP 3 — the env var didn't reach fcc-server (shell not reloaded,
or wrong env file).

=========================================================
STEP 6 — Verify end-to-end
=========================================================
In a fresh fcc-claude session, send a short prompt like "say hi".
Then exit the session. Run:

  cat ~/.cache/claude-llm-quota-bar/provider-quota.json 2>/dev/null \
      || echo "quota bar not installed yet — skip this check"

If the quota bar file exists, the wrapper is talking to the
provider correctly. If the file doesn't exist or is older than
5 minutes, something is off — paste me the most recent error from
~/.fcc/logs/server.log.

=========================================================
DONE — Tell me what you did
=========================================================
Summarise in 3-5 bullet points:
- which provider I picked and the matching env var you set
- the install path (output of `command -v fcc-server`)
- whether STEP 4 verification passed (curl status code)
- whether STEP 6 verification passed (quota cache fresh?)
- any caveats or things I should know

If anything failed, give me the exact error message and the command
that produced it. Don't try to fix it silently — surface it.
```

</details>

### Prerequisites

- Python 3.14+ (uv-managed)
- [uv][uv] 0.11+
- An active subscription / API key for at least one provider

[uv]: https://docs.astral.sh/uv/

### Install

```bash
git clone https://github.com/philipecomputacao/free-claude-code-plus.git
cd free-claude-code-plus

# Install as a uv tool (creates `fcc-server`, `free-claude-code`,
# `fcc-init`, `fcc-claude`, and `fcc-codex` commands)
uv tool install .
```

### Configure

```bash
# Copy the example env and edit
cp .env.example ~/.fcc/.env
$EDITOR ~/.fcc/.env
```

Add the API keys for the providers you want to enable:

```bash
# ~/.fcc/.env

# Required for the server itself
# Defaults are HOST=127.0.0.1, PORT=8082 (localhost-only; safe default).
# Set HOST=0.0.0.0 ONLY if you need the proxy reachable from your LAN.
PORT=8082
# HOST=127.0.0.1

# MiniMax (this fork adds support)
MINIMAX_API_KEY=sk-cp-...

# Other providers (any subset)
NVIDIA_NIM_API_KEY=nvapi-...
OPENROUTER_API_KEY=sk-or-...
DEEPSEEK_API_KEY=sk-...
MISTRAL_API_KEY=ms-...
GROQ_API_KEY=gsk_...
# ...etc

# Model visibility (optional — see "Model visibility control")
# DISABLED_PROVIDERS=open_router,ollama
# HIDDEN_MODELS=deepseek/deepseek-reasoner,minimax/MiniMax-M2
```

### Run

```bash
# Start the server in the background
nohup fcc-server > ~/.fcc/logs/server.out 2>&1 &

# Or, foreground (Ctrl+C to stop):
fcc-server

# Check health
curl http://127.0.0.1:8082/health
```

### Wire into Claude Code

Edit `~/.claude/settings.json`:

```json
{
  "env": {
    "ANTHROPIC_BASE_URL": "http://127.0.0.1:8082",
    "ANTHROPIC_AUTH_TOKEN": "dummy"
  }
}
```

Now every Claude Code request goes through fcc-server, which fans out to the
provider configured for the model id.

### Verify MiniMax works

```bash
# 1. List models
curl -s http://127.0.0.1:8082/v1/models | jq '.data[].id' | grep minimax

# 2. Send a test message
curl -s -X POST http://127.0.0.1:8082/v1/messages \
  -H "Content-Type: application/json" \
  -H "x-api-key: $MINIMAX_API_KEY" \
  -d '{
    "model": "minimax/MiniMax-M3",
    "max_tokens": 100,
    "messages": [{"role": "user", "content": "diz oi em 1 linha"}]
  }' | jq '.content[0].text'
```

Expected output: `"Oi!"` (or similar, in Portuguese).

### Admin UI

Open <http://127.0.0.1:8082/admin> in your browser. You'll see the provider
catalogue, a button to test each provider, env-var fields, and a
**model visibility selector** to toggle individual LLMs on/off per provider
(see [Model visibility control](#model-visibility-control)). The MiniMax
entry was added in this fork.

---

## Supported providers

| Provider | Cost | Models | Notes |
|---|---|---|---|
| `minimax` (Token Plan) | Subscription | 8 | **Added in this fork** — see below |
| `nvidia_nim` | Free tier / paid | 30+ | Upstream default |
| `opencode` (Zen) | Free / paid | 15+ | OpenCode's curated catalogue |
| `opencode_go` | Free / paid | 10+ | OpenCode Go (faster routing) |
| `open_router` | Pay-as-you-go | 200+ | Gateway to every LLM |
| `deepseek` | Pay-as-you-go | 2 | Cheapest frontier model |
| `gemini` | Free tier / paid | 3 | Google |
| `groq` | Free tier / paid | 4 | Ultra-fast inference |
| `cerebras` | Free tier / paid | 3 | Wafer-scale silicon |
| `fireworks` | Pay-as-you-go | 5+ | Fast open models |
| `mistral` | Pay-as-you-go | 5+ | Mistral AI direct |
| `codestral` | Free for individual | 1 | Mistral code-specialised |
| `kimi` (Moonshot) | Pay-as-you-go | 3 | Chinese frontier |
| `zai` | Pay-as-you-go | 5+ | Z.AI / GLM family |
| `ollama` | Free (local) | 100+ | Local inference |
| `llamacpp` | Free (local) | ∞ | Local via llama.cpp server |
| `lmstudio` | Free (local) | 100+ | LM Studio local server |
| `wafer` | Per-chip | 5+ | Experimental Cerebras-like |

`free / paid` means the provider has a free tier with rate limits and a paid
tier. The Admin UI shows the current balance for paid providers that expose
a balance API.

---

## Model visibility control

By default, every model discovered by a configured provider is listed in
`/v1/models` (and therefore visible in Claude Code's `/model` selector).
Two env vars let you filter the list without removing provider keys:

### `DISABLED_PROVIDERS`

Comma-separated list of provider IDs to hide entirely from the model listing.
The provider remains functional for routing — if another tool or config
references a model from a disabled provider, requests still go through.
Only the **listing** is affected.

```bash
# Hide all OpenRouter and Ollama models from the model picker
DISABLED_PROVIDERS=open_router,ollama
```

### `HIDDEN_MODELS`

Comma-separated denylist of individual model refs (`provider_id/model_name`)
to hide from the listing. Everything not listed stays visible. Empty = show all.

```bash
# Hide specific models you don't use
HIDDEN_MODELS=deepseek/deepseek-reasoner,minimax/MiniMax-M2,minimax/MiniMax-M2.1
```

### Admin UI: model visibility selector

The Admin UI (`/admin`) includes a **Modelos visíveis** panel in the Model
Config view. It shows all discovered models grouped by provider, with
checkboxes to toggle individual models on/off. Features:

- **Search**: filter models by name across all providers
- **Per-provider toggle**: "Marcar todos" / "Desmarcar todos" buttons
- **Global controls**: mark all / clear all / refresh the discovered model list
- **Provider filter**: only configured providers (with valid API keys) show the toggle
- **Newly configured providers** show all models active by default

Changes are saved via the Apply button and take effect immediately on the
server. Claude Code clients need to open a **new window** to pick up the
updated model list (the client caches models at
`~/.claude/cache/gateway-models.json`).

---

## MiniMax provider in depth

### Models supported

| Model | Context | Notes |
|---|---|---|
| `MiniMax-M3` | 1M tokens | Flagship, best quality |
| `MiniMax-M2.7` | 128K | Previous-gen, fast |
| `MiniMax-M2.5` | 128K | Stable, well-tested |
| `MiniMax-M2.1` | 128K | Older |
| `MiniMax-M2` | 128K | Original |
| `MiniMax-M2.1-highspeed` | 128K | Lower latency, slightly lower quality |
| `MiniMax-M2.5-highspeed` | 128K | Same |
| `MiniMax-M2.7-highspeed` | 128K | Same |

### Endpoint

```
POST https://api.minimax.io/anthropic/v1/messages
```

- **Wire format**: Anthropic Messages API (system + messages + tools)
- **Auth header**: `x-api-key: ${MINIMAX_API_KEY}` (not `Authorization: Bearer`)
- **SSE streaming**: native, same as Anthropic
- **Model listing**: `GET https://api.minimax.io/v1/models` (OpenAI-compat root)

### Token Plan (subscription)

Unlike most providers that charge per-token, MiniMax sells a **monthly
subscription** with **5-hour rolling windows** of included usage. The plan
includes all 8 models above. When you hit the limit, the API returns 429
until the window resets.

To see your current quota in the statusline, see
[claude-code-statusline][csl] — this fork's sister project adds a `minimax`
quota adapter that calls the Token Plan API.

[csl]: https://github.com/philipecomputacao/claude-code-statusline

### How the provider is implemented

The provider is a thin subclass of `AnthropicMessagesTransport`:

```python
# providers/minimax/client.py (excerpt)
from core.transports.anthropic_messages import AnthropicMessagesTransport

class MiniMaxProvider(AnthropicMessagesTransport):
    DEFAULT_BASE = "https://api.minimax.io/anthropic/v1"

    def _auth_headers(self) -> dict[str, str]:
        return {"x-api-key": self._api_key}

    async def list_models(self) -> list[dict]:
        # OpenAI-compat root, not the Anthropic-compat one
        async with httpx.AsyncClient() as client:
            r = await client.get(
                "https://api.minimax.io/v1/models",
                headers={"Authorization": f"Bearer {self._api_key}"},
            )
            r.raise_for_status()
            return r.json()["data"]
```

Total new code: ~120 LOC (client + `__init__.py` + registry factory).

---

## Bug fix: missing /v1 suffix

The `AnthropicMessagesTransport` base class appends `/messages` to the
provider's base URL. If the base is `https://api.minimax.io/anthropic`,
the request goes to `https://api.minimax.io/anthropic/messages` — which
returns **HTTP 404 page not found**.

The correct path is `https://api.minimax.io/anthropic/v1/messages`.
The fix is one character — change `MINIMAX_DEFAULT_BASE` from
`https://api.minimax.io/anthropic` to `https://api.minimax.io/anthropic/v1`.

This is **not** documented in the MiniMax API docs. We discovered it
by trial-and-error:

```bash
# Wrong (404):
$ curl -i -X POST https://api.minimax.io/anthropic/messages \
    -H "x-api-key: sk-dummy" -d '{}'
HTTP/2 404
not found

# Right (401 = path is valid, just auth failed):
$ curl -i -X POST https://api.minimax.io/anthropic/v1/messages \
    -H "x-api-key: sk-dummy" -d '{}'
HTTP/2 401
missing or invalid x-api-key
```

If you're integrating a new provider, always probe the path first.
Many "Anthropic-compat" providers serve on a non-standard path
(Kimi, Z.AI, MiniMax all need `/v1`).

This fix is in commit `a2218a8` of this repo and is **already upstreamed** —
see [Contributing back](#contributing-back-to-upstream).

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│  fcc-server (FastAPI)                                            │
│                                                                  │
│  ┌─────────────────┐  ┌──────────────────┐  ┌────────────────┐  │
│  │  /v1/messages   │  │  /admin/api/*    │  │  /v1/models    │  │
│  │  (Anthropic-    │  │  (Admin UI       │  │  (OpenAI-      │  │
│  │   compat proxy) │  │   JSON API)      │  │   compat list) │  │
│  └────────┬────────┘  └────────┬─────────┘  └────────┬───────┘  │
│           │                    │                     │          │
│           └────────┬───────────┴─────────────────────┘          │
│                    ▼                                             │
│           ┌─────────────────┐                                    │
│           │  ModelRouter    │ parses model id ("minimax/...")   │
│           │                 │ and dispatches to the right        │
│           │                 │ provider factory                   │
│           └────────┬────────┘                                    │
│                    │                                             │
│       ┌────────────┴────────────┐                                │
│       ▼            ▼            ▼                                │
│  ┌─────────┐ ┌──────────┐ ┌──────────┐                           │
│  │ minimax │ │  open_   │ │  nvidia  │  18 providers total        │
│  │ (NEW)   │ │  router  │ │   _nim   │                           │
│  └────┬────┘ └─────┬────┘ └────┬─────┘                           │
│       │            │           │                                 │
│       └────────────┴───────────┘                                 │
│                    ▼                                             │
│           ┌─────────────────┐                                    │
│           │  ProviderClient │ retry, rate-limit, stream-SSE      │
│           │  + QuotaTracker │ optional live quota check          │
│           └────────┬────────┘                                    │
└────────────────────┼─────────────────────────────────────────────┘
                     ▼
              Upstream LLM provider
```

### Code layout

```
.
├── api/                    # FastAPI routes, Admin UI
│   ├── admin_routes.py     # /admin/api/* JSON endpoints
│   ├── admin_static/       # HTML/JS for the Admin UI
│   ├── routes.py           # /v1/messages, /v1/models
│   ├── model_router.py     # model id → provider dispatch
│   ├── model_catalog.py    # /v1/models response (applies denylist + disabled filters)
│   └── gateway_model_ids.py # gateway ID rewriting
├── cli/                    # `fcc` command, `fcc-server` launcher
├── config/                 # provider_catalog.py, settings
├── core/                   # cross-cutting (transports, retry, rate-limit)
├── providers/              # 18 provider implementations
│   └── minimax/            # ← this fork adds this
│       ├── __init__.py
│       └── client.py
├── messaging/              # Telegram + Discord bots (optional)
├── server.py               # FastAPI app factory
├── pyproject.toml          # 2.5.0 (model visibility + denylist)
└── smoke/                  # integration tests
```

---

## Development

```bash
# Clone
git clone https://github.com/philipecomputacao/free-claude-code-plus.git
cd free-claude-code-plus

# Install in editable mode
uv tool install --editable .

# Run the server in dev mode (auto-reload)
fcc-server --reload

# Run smoke tests
pytest smoke/

# Type-check
basedpyright providers/ api/ core/
```

### Adding a new provider

1. **Create `providers/<name>/{__init__.py,client.py}`** with a subclass of
   `AnthropicMessagesTransport` (for Anthropic-compat) or `OpenAIChatCompletionsTransport`
   (for OpenAI-compat).
2. **Add a factory** in `providers/registry.py`:
   ```python
   def _create_your_provider(settings: Settings) -> BaseProvider:
       return YourProvider(
           api_key=settings.your_provider_api_key,
           base_url=YOUR_PROVIDER_DEFAULT_BASE,
       )
   PROVIDER_FACTORIES["your_provider"] = _create_your_provider
   ```
3. **Add the constant** in `config/provider_catalog.py`:
   ```python
   YOUR_PROVIDER_DEFAULT_BASE = "https://api.your-provider.com/v1"
   PROVIDER_CATALOG["your_provider"] = {
       "default_base": YOUR_PROVIDER_DEFAULT_BASE,
       "auth_header": "Authorization",
       "auth_prefix": "Bearer ",
       "env_key": "YOUR_PROVIDER_API_KEY",
       "display_name": "Your Provider",
       "tier": "qwen-medium",
   }
   ```
4. **Add the env-var** to `Settings` and `.env.example`.
5. **Write a smoke test** in `smoke/prereq/test_provider_prereq_live.py` following
   the existing pattern for `cerebras` or `groq`.
6. **(Optional) Add a quota adapter** in
   [claude-code-statusline][csl] so the statusline shows live quota.

### Running the Admin UI in dev

```bash
cd api/admin_static
python3 -m http.server 5173   # serves the static files
# Then point fcc-server's static mount at it
```

---

## Syncing with upstream

This fork tracks `Alishahryar1/free-claude-code:main` and rebases the
`feat/provider-minimax` branch on top. A weekly GitHub Action
([`.github/workflows/upstream-sync.yml`](.github/workflows/upstream-sync.yml))
detects divergence and opens a tracking issue; **nothing is auto-merged**.

To sync manually:

```bash
cd ~/free-claude-code-plus

# Fetch upstream
git fetch upstream

# Update main from upstream
git checkout main
git merge upstream/main --ff-only  # or use a merge commit
git push origin main

# Rebase the feature branch on the new main
git checkout feat/provider-minimax
git rebase main
git push origin feat/provider-minimax --force-with-lease

# Run CI to verify
./scripts/ci.sh
```

Conflict hot-spots when rebasing:
- `providers/registry.py` (new provider factories)
- `config/provider_catalog.py` (PROVIDER_CATALOG dict)
- `pyproject.toml` (version bumps)
- `uv.lock` (regenerate with `uv lock`)

---

## Contributing back to upstream

The MiniMax provider and the `/v1` base-URL bug fix are intended to be
upstreamed. To prepare a PR:

1. **Squash the fork-specific commits** into a single feature commit:
   ```bash
   git checkout feat/provider-minimax
   git rebase -i main
   # Squash: 8890e7a (provider) + a2218a8 (bug fix) into one
   ```
2. **Add a smoke test** in `smoke/prereq/test_provider_prereq_live.py` —
   the upstream maintainer will require this.
3. **Update `pyproject.toml`** — keep the version bump, but the upstream
   might prefer a different version scheme.
4. **Open a PR** against `Alishahryar1/free-claude-code:main` with:
   - Title: `feat(minimax): add native MiniMax Token Plan provider`
   - Description: link to this fork's `feat/provider-minimax` branch for
     the full diff history
5. **Update the upstream CLAUDE.md / AGENTS.md** with MiniMax's specific
   gotchas (the `/v1` bug is the most important).

---

## Related projects

- **[Alishahryar1/free-claude-code][upstream]** — the original FCC project
  that this fork builds on. Most provider code comes from here.
- **[claude-code-statusline][csl]** — the multi-provider statusline bar
  used with this fork. The `minimax` quota adapter was added in this
  fork's sister project.
- **[opencode-llm-statusline][oc-plugin]** — same statusline bar, but
  usable from [OpenCode][oc] (not just Claude Code).

[csl]: https://github.com/philipecomputacao/claude-code-statusline
[oc-plugin]: https://github.com/philipecomputacao/opencode-llm-statusline
[oc]: https://opencode.ai

---

## License

MIT — same as upstream. See [LICENSE](LICENSE).

Fork mantido por **[@lpdigital.me](https://www.instagram.com/lpdigital.me/)**.
