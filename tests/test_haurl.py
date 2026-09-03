"""Unit tests for the Home Assistant URL helpers and WS auth flow."""
from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

import evehasstools


def test_rest_url_bare_host(monkeypatch):
    monkeypatch.setenv("HASS_API_URL", "ha.local:8123")
    monkeypatch.delenv("HASS_SCHEME", raising=False)
    assert evehasstools.get_hass_rest_url() == "http://ha.local:8123"


def test_ws_url_bare_host(monkeypatch):
    monkeypatch.setenv("HASS_API_URL", "ha.local:8123")
    monkeypatch.delenv("HASS_WSS_SCHEME", raising=False)
    assert evehasstools.get_hass_ws_url() == "ws://ha.local:8123/websocket"


def test_wss_scheme_supported(monkeypatch):
    monkeypatch.setenv("HASS_API_URL", "ha.local:8123")
    monkeypatch.setenv("HASS_WSS_SCHEME", "wss")
    assert evehasstools.get_hass_ws_url() == "wss://ha.local:8123/websocket"


def test_scheme_stripped_from_env(monkeypatch):
    monkeypatch.setenv("HASS_API_URL", "https://ha.local:8123")
    assert evehasstools.get_hass_rest_url() == "http://ha.local:8123"


def test_missing_url_raises(monkeypatch):
    monkeypatch.delenv("HASS_API_URL", raising=False)
    with pytest.raises(RuntimeError, match="HASS_API_URL"):
        evehasstools.get_hass_rest_url()


def _fake_ws(auth_ok=True, service_success=True, service_result=None):
    """Return a mock websocket whose recv() yields the HA handshake sequence."""
    msgs = [
        json.dumps({"type": "auth_required"}),
        json.dumps({"type": "auth_ok" if auth_ok else "auth_invalid", "message": "bad"}),
        json.dumps({
            "type": "result",
            "id": 1,
            "success": service_success,
            "result": service_result or {},
        }),
    ]
    ws = MagicMock()
    ws.recv.side_effect = msgs
    ws.close = MagicMock()
    return ws


def test_run_hass_service_success(monkeypatch):
    monkeypatch.setenv("HASS_TOKEN", "tok")
    monkeypatch.setenv("HASS_API_URL", "ha.local:8123")
    ws = _fake_ws(service_result={"response": {}})
    with patch("evehasstools.create_connection", return_value=ws):
        result = evehasstools.run_hass_service("switch", "turn_on", "switch.x")
    assert result["success"] is True
    ws.close.assert_called_once()


def test_run_hass_service_auth_failure(monkeypatch):
    monkeypatch.setenv("HASS_TOKEN", "tok")
    monkeypatch.setenv("HASS_API_URL", "ha.local:8123")
    ws = _fake_ws(auth_ok=False)
    with patch("evehasstools.create_connection", return_value=ws):
        with pytest.raises(RuntimeError, match="authentication failed"):
            evehasstools.run_hass_service("switch", "turn_on", "switch.x")
    ws.close.assert_called_once()


def test_run_hass_service_missing_token(monkeypatch):
    monkeypatch.setenv("HASS_API_URL", "ha.local:8123")
    monkeypatch.delenv("HASS_TOKEN", raising=False)
    with pytest.raises(RuntimeError, match="HASS_TOKEN"):
        evehasstools.run_hass_service("switch", "turn_on", "switch.x")


def test_run_hass_service_service_error(monkeypatch):
    monkeypatch.setenv("HASS_TOKEN", "tok")
    monkeypatch.setenv("HASS_API_URL", "ha.local:8123")
    ws = _fake_ws(service_success=False)
    with patch("evehasstools.create_connection", return_value=ws):
        with pytest.raises(RuntimeError, match="failed"):
            evehasstools.run_hass_service("switch", "turn_on", "switch.x")
    ws.close.assert_called_once()


def test_socket_closed_on_unexpected_greeting(monkeypatch):
    monkeypatch.setenv("HASS_TOKEN", "tok")
    monkeypatch.setenv("HASS_API_URL", "ha.local:8123")
    ws = MagicMock()
    ws.recv.side_effect = [json.dumps({"type": "not_what_we_expected"})]
    ws.close = MagicMock()
    with patch("evehasstools.create_connection", return_value=ws):
        with pytest.raises(RuntimeError, match="auth_required"):
            evehasstools.run_hass_service("switch", "turn_on", "switch.x")
    ws.close.assert_called_once()
