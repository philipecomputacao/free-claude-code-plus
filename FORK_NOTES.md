# AGENTIC DIRECTIVE (fork)

Fork privado de `Alishahryar1/free-claude-code` com **provider nativo MiniMax**.
O `AGENTS.md` e `CLAUDE.md` do upstream foram preservados e continuam
autoritativos para padrões de código, versionamento e CI.

## Estrutura deste fork

- `main` — espelha upstream, recebe merges via `git pull upstream main`.
- `feat/provider-minimax` — branch ativa com provider MiniMax (este PR).
- `.git` mantido fora do Drive sync (git-dir separado).

## Provider MiniMax (este fork adiciona)

- `providers/minimax/__init__.py` — entry point
- `providers/minimax/client.py` — `MiniMaxProvider(AnthropicMessagesTransport)`
- Endpoint: `https://api.minimax.io/anthropic/v1` (Anthropic-compat)
- Header de auth: `x-api-key: ${MINIMAX_API_KEY}` (mesmo padrão do DeepSeek)
- Listagem: `https://api.minimax.io/v1/models` (OpenAI-compat root)

## Comandos úteis

```bash
# Reinstalar tool após mudanças no source
cd ~/free-claude-code-plus
uv tool install --reinstall .

# Reiniciar server
pkill -f fcc-server; sleep 2
nohup fcc-server > ~/.fcc/server.log 2>&1 &

# Ver log
tail -f ~/.fcc/server.log

# Validar provider MiniMax
curl -s -X POST http://127.0.0.1:8082/admin/api/providers/minimax/test \
  -H "Content-Type: application/json" -d '{}' | python3 -m json.tool

# Atualizar do upstream (rebase manual)
cd ~/free-claude-code-plus
git fetch upstream
git checkout main && git merge upstream/main
git checkout feat/provider-minimax && git rebase main
```

## Antes de PR upstream

1. `uv lock` e bump version em `pyproject.toml` (ver VERSIONING no AGENTS.md upstream).
2. `./scripts/ci.sh` deve passar.
3. Adicionar teste em `tests/providers/test_minimax.py` seguindo padrão do Kimi/DeepSeek.
4. Atualizar `README.md` upstream (criar PR separado — upstream não aceita PR de README).

## Sincronização automática com upstream

GitHub Action em `.github/workflows/upstream-sync.yml` roda toda segunda
9h BRT (12:00 UTC) e abre uma issue quando detecta divergência entre
`main` deste fork e `main` do upstream. Issues existentes com label
`upstream-sync` recebem comentário de update em vez de duplicar.

Disparo manual: aba **Actions → Upstream sync check → Run workflow**.

Para sincronizar quando a issue abrir:

```bash
cd ~/free-claude-code-plus
git fetch upstream
git checkout main && git merge upstream/main
git checkout feat/provider-minimax && git rebase main
# resolver conflitos se houver (locais comuns: api/admin_config.py, config/provider_catalog.py)
uv tool install --reinstall .
pkill -f fcc-server; sleep 2; nohup fcc-server > ~/.fcc/server.log 2>&1 &
```

Após sincronizar, feche a issue manualmente.

## Segredos

- Subscription Key do Token Plan é pessoal. Nunca commitar `~/.fcc/.env`.
- `.env.example` deste fork tem placeholders vazios.
