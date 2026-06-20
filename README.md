# free-claude-code-minimax

Fork privado do [free-claude-code](https://github.com/Alishahryar1/free-claude-code)
com **provider nativo MiniMax (Token Plan)** adicionado.

Permite usar o Claude Code (CLI e VS Code) roteando para qualquer modelo do
Token Plan MiniMax (MiniMax-M3, M2.7, M2.5, M2.1, M2 e variantes `-highspeed`)
ou misturando com outros providers (NVIDIA NIM, OpenCode Zen, etc.).

## Por que este fork existe

O `free-claude-code` upstream ainda não tem provider MiniMax nativo. Este fork
adiciona suporte oficial baseado na [documentação MiniMax](https://platform.minimax.io/docs/guides/quickstart),
usando o endpoint Anthropic-compat (`https://api.minimax.io/anthropic`).

## Mudanças em relação ao upstream

- `providers/minimax/` — subclasse de `AnthropicMessagesTransport` com header `x-api-key` e listagem via OpenAI-compat root
- `config/provider_catalog.py` — entrada `minimax` no `PROVIDER_CATALOG` + `MINIMAX_DEFAULT_BASE`
- `providers/defaults.py` — re-exporta `MINIMAX_DEFAULT_BASE`
- `providers/registry.py` — factory `_create_minimax`
- `config/settings.py` — campos `minimax_api_key` e `minimax_proxy`
- `api/admin_config.py` — `ConfigFieldSpec` para API key (providers) + proxy (advanced)
- `api/admin_static/admin.js` — label `minimax: "MiniMax"`
- `.env.example` — bloco MiniMax + smoke + comentários sobre Token Plan
- `pyproject.toml` — bump version 2.3.13 → 2.4.0 (MINOR: nova capability)

Total: **9 arquivos editados + 2 novos** (`providers/minimax/{__init__,client}.py`).
Diff resumido: `+67 / -3` linhas (sem contar `providers/minimax/`).

## Instalação

### 1. Pré-requisitos

- macOS ou Linux
- Python 3.14 (instalado via `uv`)
- Claude Code (CLI Anthropic)

### 2. Instalar uv + dependências

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"
```

### 3. Instalar a tool a partir deste fork

```bash
git clone https://github.com/philipecomputacao/free-claude-code-minimax.git ~/Projetos/projetos/free-claude-code-minimax
cd ~/Projetos/projetos/free-claude-code-minimax
uv tool install .
```

### 4. Iniciar o servidor

```bash
mkdir -p ~/.fcc
nohup fcc-server > ~/.fcc/server.log 2>&1 &
sleep 5
# Abre a Admin UI em http://127.0.0.1:8082/admin
```

## Configuração MiniMax

### Opção A — Pela Admin UI (recomendado)

1. Abra `http://127.0.0.1:8082/admin` no navegador.
2. Recarregue com `Cmd+Shift+R` (o JS pode estar em cache).
3. Aba **Providers → MiniMax API Key**: cole sua Subscription Key do Token Plan.
   - Obtenha em [platform.minimax.io/user-center/payment/token-plan](https://platform.minimax.io/user-center/payment/token-plan).
4. Clique **Validate** → **Apply**.
5. Aba **Settings → Default Model**: troque `MODEL` para `minimax/MiniMax-M3`.
6. **Apply** novamente (o server reinicia automaticamente).

### Opção B — Direto no `~/.fcc/.env`

```bash
pkill -f fcc-server; sleep 2

cat >> ~/.fcc/.env <<'EOF'
MINIMAX_API_KEY=eyJhbGciOi...sua-key-aqui
MINIMAX_PROXY=
MODEL=minimax/MiniMax-M3
EOF

nohup fcc-server > ~/.fcc/server.log 2>&1 &
```

## Uso

```bash
fcc-claude
# dentro do TUI:
/status    # mostra MODEL ativo
/model     # picker com todos os modelos disponíveis
```

Para rotear por tier (Opus/Sonnet/Haiku) veja a seção "Roteamento por tier".

## Modelos disponíveis

Todos via `/v1/models` quando o provider está configurado:

| Modelo | Context | Notas |
|---|---|---|
| `minimax/MiniMax-M3` | 1M | multimodal (imagem/vídeo), thinking adaptativo |
| `minimax/MiniMax-M2.7` | 204k | raciocínio (60 tps) |
| `minimax/MiniMax-M2.7-highspeed` | 204k | mesmo modelo, 100 tps |
| `minimax/MiniMax-M2.5` | 204k | "Peak Performance" |
| `minimax/MiniMax-M2.5-highspeed` | 204k | 100 tps |
| `minimax/MiniMax-M2.1` | 204k | — |
| `minimax/MiniMax-M2.1-highspeed` | 204k | 100 tps |
| `minimax/MiniMax-M2` | 204k | legado |

Slug final no `MODEL`: `minimax/MiniMax-M3` (formato `provider/model_id`).

## Roteamento por tier (opcional)

Por padrão todos os tiers usam `MODEL`. Para misturar providers:

```text
# ~/.fcc/.env

# Tier Opus (tarefas pesadas) → M3
MODEL_OPUS=minimax/MiniMax-M3

# Tier Sonnet (coding do dia) → M3 ou NIM (free)
MODEL_SONNET=minimax/MiniMax-M3

# Tier Haiku (probes, compressão) → NIM (free tier)
MODEL_HAIKU=nvidia_nim/nvidia/nemotron-3-super-120b-a12b

# Fallback
MODEL=minimax/MiniMax-M3
```

Isso economiza ~70% da quota do Token Plan em tarefas triviais.

## Troubleshooting

### `MiniMax API Key` não aparece na Admin UI

Recarregue com `Cmd+Shift+R`. O JS cacheia a lista antiga de fields.

### `/v1/models` retorna lista vazia

1. Verifique se a key foi salva: `grep MINIMAX ~/.fcc/.env`.
2. Restart manual: `pkill -f fcc-server && nohup fcc-server > ~/.fcc/server.log 2>&1 &`.
3. Verifique o log: `tail -30 ~/.fcc/server.log`.

### Erro 401 da MiniMax

- Subscription Key inválida ou sem Token Plan ativo. Confirme em [platform.minimax.io/user-center/payment/token-plan](https://platform.minimax.io/user-center/payment/token-plan).
- Subscription Key e pay-as-you-go API Key não são intercambiáveis. Para pay-as-you-go, gere uma nova API Key em [platform.minimax.io/user-center/basic-information/interface-key](https://platform.minimax.io/user-center/basic-information/interface-key).

### `MiniMax-M3` não aparece no picker

Force o slug direto: `MODEL=minimax/MiniMax-M3` no `.env`. Mesmo se a listagem
estiver atrasada, o slug exato funciona se o provider estiver autenticado.

## Segurança

- **Nunca** commite a Subscription Key. O `.env.example` tem valores vazios.
- O `~/.fcc/.env` (gerenciado pela Admin UI) está fora do repo.
- Trate o repo como potencialmente público — não commite segredos, dumps de n8n, ou dados de cliente.

## Próximos passos (opcional)

- [ ] Subir PR upstream para `Alishahryar1/free-claude-code` (categoria providers).
- [ ] Adicionar teste de smoke no diretório `tests/providers/test_minimax.py`.
- [ ] Validar com `./scripts/ci.sh` antes do PR.

## Referências

- [free-claude-code upstream](https://github.com/Alishahryar1/free-claude-code)
- [MiniMax Platform](https://platform.minimax.io)
- [MiniMax Token Plan](https://platform.minimax.io/docs/token-plan/intro)
- [MiniMax Claude Code integration](https://platform.minimax.io/docs/token-plan/claude-code)
- [MiniMax Anthropic-compatible API](https://platform.minimax.io/docs/api-reference/text-anthropic-api)
