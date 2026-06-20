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
- [Supported providers](#supported-providers)
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

Mix and match per conversation or per project.

---

## Quick start

### Prerequisites

- Python 3.14+ (uv-managed)
- [uv][uv] 0.11+
- An active subscription / API key for at least one provider

[uv]: https://docs.astral.sh/uv/

### Install

```bash
git clone https://github.com/philipecomputacao/free-claude-code-plus.git \
    ~/Projetos/projetos/free-claude-code-plus
cd ~/Projetos/projetos/free-claude-code-plus

# Install as a uv tool (creates `fcc-server` and `fcc` commands)
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
APP_PORT=8082
APP_HOST=127.0.0.1

# MiniMax (this fork adds support)
MINIMAX_API_KEY=sk-cp-...

# Other providers (any subset)
NVIDIA_NIM_API_KEY=nvapi-...
OPENROUTER_API_KEY=sk-or-...
DEEPSEEK_API_KEY=sk-...
MISTRAL_API_KEY=ms-...
GROQ_API_KEY=gsk_...
# ...etc
```

### Run

```bash
# Start the server in the background
nohup fcc-server > ~/.fcc/server.log 2>&1 &

# Or use the launcher
fcc run

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
catalogue, a button to test each provider, and env-var fields. The MiniMax
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
├── pyproject.toml          # 2.4.1 (PATCH bump from upstream 2.3.13)
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
cd ~/Projetos/projetos/free-claude-code-plus

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
