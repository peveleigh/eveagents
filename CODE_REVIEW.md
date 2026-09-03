# EveAgents Code Review

> Generated: Thu Sep 03 2026
> Reviewer: opencode (automated)
> Scope: correctness, security, reliability, maintainability, performance, test coverage, DX, architectural consistency

---

# Executive Summary

EveAgents is a small FastAPI service that orchestrates a set of LLM agents (OpenAI Agents SDK + OpenRouter/LiteLLM) over a Home Assistant install, with web search, email, and a research sub-system. **All previously identified High-severity findings (#4–#11) have been resolved**: import-time network I/O was made lazy, logging is configured once at startup with defaulted env vars, SMTP config is fully validated, SQLite access is thread-safe, the WebSocket auth flow was hardened with a unified URL helper, dependencies are pinned, and a test suite + CI (ruff, mypy, pytest) was added.

The remaining findings are Medium/Low and center on duplicated model config, a few bad type annotations, dead `exa_search` code, an undocumented research search cap, prompt path handling, and README completeness.

---

# Findings

| # | Priority | Category | Location | Issue | Why it matters | Recommendation | Effort/Risk |
|---|----------|----------|----------|-------|----------------|----------------|-------------|
| 12 | **Medium** | Maintainability | `eveagents.py`, `tools/research_bot/researchagents/*.py` | Duplicated `load_dotenv()` + `os.getenv("OPENROUTER_API_KEY") or ""` + `LitellmModel(...)` block in 4 files; model names hardcoded and inconsistent (gemini-2.5-flash vs gpt-4o vs gpt-4o-mini). | Drift; changing the provider requires editing multiple files; `or ""` hides a missing key until request time. | Centralize model config in one module (e.g. `models.py`) reading from env with validation; import the configured `model`/`model_name`. | Medium / Low |
| 13 | **Medium** | Bug | `tools/webtools.py:18` | `web_search` annotated `-> dict` but returns `list`; `exa_search` annotated `-> str` but returns an Exa object. | Type-checker noise now, but signals real confusion about return types that can cause downstream bugs (e.g. agents expecting a string get an object). | Fix annotations to `list[...]`, and `str`/serialized output respectively. | Small / Low |
| 14 | **Medium** | Bug / Dead code | `tools/webtools.py:113-122` (`exa_search`) | `exa_search` is defined but **not included in `web_tools`** (line 158), so no agent can call it. It also returns a non-string object. | Dead/misleading code; the Exa integration is effectively unused while the search-agent sub-system has its own copy. | Either add it to `web_tools` (with proper serialization) or delete it. | Small / Low |
| 15 | **Medium** | Maintainability / Performance | `tools/research_bot/manager.py:36-46` | Planner is prompted to produce 5–20 search terms, but only `searches[:2]` are executed. Undocumented, wasteful (planner tokens spent on unused items). | Either a bug (should run more) or an undocumented cost cap; future maintainers will be confused. | Make the limit a named constant (e.g. `MAX_SEARCHES = 2`) with a comment, or align the planner prompt to the actual limit. | Small / Low |
| 16 | **Medium** | Bug | `agentprompts.py` (static prompts) | Static prompt loading previously used `Path.open("prompts/...")` relative to CWD. Now fixed via `Path(__file__).parent / "prompts"`; verify no other CWD-relative path assumptions remain. | Running the app from a different working directory could still affect `research_worker.py`'s relative `research_reports/` output dir. | Audit remaining CWD-relative paths; consider anchoring all paths to `__file__`. | Small / Low |
| 17 | **Medium** | Documentation | `README.md` | Only lists 4 env vars; no run/test/lint instructions; no architecture overview. Missing: `SMTP_*`, `SENDER_EMAIL`, `RECIPIENT_EMAIL`, `SEARXNG_URL`, `LOG_DIR`, `MAIN_LOG_FILE`, `ERROR_LOG_FILE`, `HASS_SCHEME`, `HASS_WSS_SCHEME`, `OPENROUTER_API_URL` (read in `evehasstools.py` but unused/undocumented). | New contributors can't run the app; ops can't know what config to provide. | Expand README: full env-var table, `pip install -r requirements.txt`, `uvicorn server:app`, gunicorn example, project layout, lint/test commands. | Small / Low |
| 18 | **Low** | Bug | `tools/webtools.py:52-67` | `SEARXNG_URL` may be `None` → `f"{None}/search"`; `response.json()["results"]` assumes the key exists; raises a bare `Exception` with the full HTTP body (may leak info). | Misconfiguration or upstream change produces a confusing error and logs sensitive content. | Validate `SEARXNG_URL` at startup; use `.get("results", [])`; raise a typed, redacted error. | Small / Low |
| 19 | **Low** | Maintainability | (resolved in `conversation_storage.py`) | `print(...)` and bare `except Exception` were replaced with `logger.exception(...)` and narrowed `sqlite3.Error`. Remaining: audit other modules for `print`/bare-except patterns. | Bypasses the configured logger; swallows real errors silently. | Sweep remaining modules for `print`/bare `except` and route through the logger. | Small / Low |
| 20 | **Low** | Maintainability | `eveagents.py` | `set_tracing_disabled` is no longer imported (the dead commented call was removed). Decide explicitly whether tracing should be on or off via an env flag. | Either tracing should be on or off by default; leaving it unset invites accidental PII logging. | Set tracing explicitly (e.g. disabled in prod, enabled via env). | Small / Low |
| 21 | **Low** | Dead code | `tools/research_worker.py:6` import path; `evehasstools.py` | `openai_api_key`/`openai_api_url` reads were removed from `evehasstools.py`. `research_worker.py` still imports `emailer` directly (works only because it runs as a script in `tools/`). | Minor; the script-relative import is fragile if the file is moved. | Consider importing as `from tools.emailer import Emailer` for consistency. | Small / Low |

> Note: High-severity findings #4–#11 were resolved and removed from this table. See git history for the original review text.

---

# Quick Wins
(low-effort, high-value, mostly 1–10 lines each)

- **Delete `exa_search` dead code** (#14) or wire it up.
- **Fix `web_search`/`exa_search` return-type annotations** (#13).
- **Make the research search cap a named constant** (#15).
- **Expand README** with the full env-var table and run/lint/test instructions (#17).
- **Validate `SEARXNG_URL` and redact error bodies** (#18).

---

# Strategic Improvements

1. **Centralize configuration & model definitions.** A single `config.py` that validates required env vars at startup (fail fast with a clear message) and a single `models.py` for LiteLLM model wiring. (Finding #12.)
2. **Review the agent prompt/secret boundary.** Prompts embed live HA state via Jinja rendering; ensure no secrets leak into model context, and enable tracing only behind an explicit env flag. (Finding #20.)
3. **Stand up end-to-end tests** with a mock OpenRouter backend and a fake HA server, building on the unit tests now in `tests/`.
4. **Review and document the research sub-system's search limits** and remove dead `exa_search` (#14, #15).

---

# Test and Verification Gaps

The following are now covered by `tests/` (run `pytest`):

- Unit tests for `ConversationStorage` (CRUD, JSON round-trip, concurrent access).
- Tests for `Emailer` (SMTP mocked) and `SMTPConfigError` validation.
- Tests for `evehasstools` URL building / WS auth handshake (success, auth failure, service error, socket cleanup).
- A `TestClient` smoke test for `/eve_agent` with `Runner` mocked (success, validation rejection, 500 on failure).

CI (`.github/workflows/ci.yml`) runs `ruff check`, `mypy` (advisory), and `pytest` on every push.

**Remaining gaps to address next:**

- No integration test for the real HA WebSocket round-trip (covered via mock today).
- No tests for filename sanitization in `research_worker` or the `ResearchManager` pipeline.
- `mypy` is advisory; the codebase is not fully typed. Tighten types incrementally.

---

# Proposed Plan

**Near-term — Reliability & maintainability:**
1. Centralize config and model definitions (#12); fail fast on missing env.
2. Fix prompt path handling audit (#16) and bad annotations (#13).
3. Expand README with the full env-var table and run instructions (#17).

**Longer-term — Architecture & quality:**
4. Unify HA access further and document the research sub-system's search limits (#14, #15).
5. Add integration/E2E tests with a mock OpenRouter backend and a fake HA server.
6. Tighten mypy coverage incrementally and make it a fatal CI gate.
