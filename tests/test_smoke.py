"""Smoke test for the /eve_agent endpoint with a mocked Runner."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient


def test_eve_agent_returns_final_output():
    """The endpoint should return the agent's final_output for a valid query."""
    # Import lazily so conftest env defaults are in place first.
    import server  # noqa: PLC0415

    fake_result = MagicMock()
    fake_result.final_output = "hello back"
    fake_result.to_input_list.return_value = [{"role": "assistant", "content": "hello back"}]

    with patch.object(server, "Runner") as runner_mock, \
            patch.object(server, "eve_agent", MagicMock()):
        runner_mock.run = AsyncMock(return_value=fake_result)
        # TestClient runs the lifespan (configuring logging once).
        with TestClient(server.app) as client:
            resp = client.get("/eve_agent", params={"query": "hi there", "cid": "smoke-1"})
    assert resp.status_code == 200
    assert resp.json() == "hello back"


def test_eve_agent_short_query_rejected():
    import server  # noqa: PLC0415

    with TestClient(server.app) as client:
        resp = client.get("/eve_agent", params={"query": "hi"})
    assert resp.status_code == 422


def test_eve_agent_runner_failure_returns_500():
    import server  # noqa: PLC0415

    with patch.object(server, "Runner") as runner_mock, \
            patch.object(server, "eve_agent", MagicMock()):
        runner_mock.run = AsyncMock(side_effect=RuntimeError("boom"))
        with TestClient(server.app) as client:
            resp = client.get("/eve_agent", params={"query": "hello there"})
    assert resp.status_code == 500
