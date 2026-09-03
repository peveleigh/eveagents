# AGENTS.md

Compact guidance for OpenCode sessions working in this repo. Verified against the current codebase; see `CODE_REVIEW.md` for a detailed list of known defects.

## Stack

FastAPI service orchestrating LLM agents built on the **OpenAI Agents SDK** with models served via **OpenRouter/LiteLLM**. Integrates with **Home Assistant** (REST + WebSocket), **SearXNG**, **Exa**, **r.jina.ai**, and SMTP. Conversation history persists in SQLite.

## Run

```bash
pip install -r requirements.txt        # runtime deps (pinned)
pip install -r requirements-dev.txt     # adds pytest, ruff, mypy, httpx
uvicorn server:app                      # dev
gunicorn -k uvicorn.workers.UvicornWorker server:app   # prod (see gunicorn.service.example)
ruff check .                             # lint
mypy .                                   # type check (advisory; codebase not fully typed)
pytest -q                                # tests
```

Always start from the repo root: `agentprompts.py` reads `prompts/*.txt` via `Path(__file__).parent / "prompts"`, and `research_worker.py` writes to `research_reports/`.

Tests live in `tests/` (run `pytest`); CI runs ruff, mypy (advisory), and pytest on every push via `.github/workflows/ci.yml`.

## Architecture

- `server.py` — FastAPI app; single endpoint `/eve_agent` runs `eve_agent` via `agents.Runner`, optionally persisting conversation by `cid` to SQLite (`conversation_storage.py`).
- `eveagents.py` — defines the agent graph. `eve_agent` is the entry agent with handoffs to `meteorologist_agent`, `cctv_agent`, `smart_home_agent`, `executive_assistant_agent`, `knowledge_agent`. Each agent gets its tools from `tools/evellmtools.py` or `tools/webtools.py`.
- `agentprompts.py` — loads/renders prompts. Static prompts are read at import; dynamic prompts that need HA (template rendering, calendar events) are built lazily on first use and cached with a TTL, so importing `eveagents` no longer requires HA to be reachable.
- `tools/research_bot/` — separate `ResearchManager` pipeline (planner → search → writer) invoked as a subprocess by the `research` tool; writes a Markdown report and emails it.

## Model config

Model name is hardcoded as `openrouter/google/gemini-2.5-flash` in `eveagents.py` and is **duplicated** (with inconsistencies, e.g. `gpt-4o-mini` for CCTV) across `tools/research_bot/researchagents/*.py`. Changing the provider means editing multiple files.

## Environment variables

`README.md` only documents 4; the code requires more. All read via `python-dotenv` from `.env` (gitignored):

- Home Assistant: `HASS_TOKEN`, `HASS_API_URL` (bare host, may include port; a leading scheme is stripped). Optional `HASS_SCHEME` (default `http`), `HASS_WSS_SCHEME` (default `ws`, set `wss` for TLS).
- LLM: `OPENROUTER_API_KEY` (and `OPENROUTER_API_URL` is read but unused)
- Search/web: `EXA_API_KEY`, `SEARXNG_URL`
- Email: `SMTP_HOST`, `SMTP_PORT` (default `587`), `SMTP_USER`, `SMTP_PASSWORD`, `SENDER_EMAIL`, `RECIPIENT_EMAIL` (all five validated; `Emailer` raises `SMTPConfigError` listing missing ones)
- Logging: `LOG_DIR` (default `logs`), `MAIN_LOG_FILE` (default `eveagents.log`), `ERROR_LOG_FILE` (default `error.log`)

## Gotchas

- `conversation_storage.py` uses a single shared SQLite connection (`check_same_thread=False`) guarded by a `threading.Lock`; safe across async handlers and gunicorn workers.
- `log_setup.py:setup_logging()` is idempotent and called once at app startup via the FastAPI `lifespan`; safe to call again (no-op).
- `exa_search` is defined in `webtools.py` but not included in `web_tools`, so no agent can call it.

## Conventions

- Agents and tools use `@function_tool` from the Agents SDK; tool docstrings become the LLM-facing schema, so keep them precise.
- Prompts live as plain `.txt` in `prompts/` and are prefixed with `RECOMMENDED_PROMPT_PREFIX` from `agents.extensions.handoff_prompt`.
- `requirements.txt` pins all runtime deps; `requirements-dev.txt` adds `pytest`, `ruff`, `mypy`, `httpx`. `requests` is declared.
