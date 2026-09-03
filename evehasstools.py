"""Collection of functions for interacting with Home Assistant."""
from __future__ import annotations

import json
import logging
import os

from dotenv import load_dotenv
from websocket import create_connection

load_dotenv()

logger = logging.getLogger(__name__)


def _get_hass_api_url() -> str:
    """Return the HA host (no scheme), validated.

    ``HASS_API_URL`` is expected to be a bare host optionally including a port,
    e.g. ``homeassistant.local:8123``. A leading scheme is stripped so callers
    can prepend their own.

    Raises:
        RuntimeError: if ``HASS_API_URL`` is unset.

    """
    url = os.getenv("HASS_API_URL")
    if not url:
        raise RuntimeError("HASS_API_URL is not set.")
    if "://" in url:
        url = url.split("://", 1)[1]
    return url


def get_hass_rest_url() -> str:
    """Return the fully-qualified REST URL for Home Assistant."""
    scheme = os.getenv("HASS_SCHEME", "http")
    return f"{scheme}://{_get_hass_api_url()}"


def get_hass_ws_url() -> str:
    """Return the fully-qualified WebSocket URL for Home Assistant.

    Set ``HASS_WSS_SCHEME=wss`` in the environment to use TLS.
    """
    scheme = os.getenv("HASS_WSS_SCHEME", "ws")
    return f"{scheme}://{_get_hass_api_url()}/websocket"


def run_hass_service(
    domain: str,
    service: str,
    entity_id: str,
    service_data: dict | None = None,
    *,
    return_response: bool = True,
    ) -> dict:
    """Run a Home Assistant service over the WebSocket API.

    Performs a proper auth handshake: reads the ``auth_required`` greeting,
    sends credentials, and asserts an ``auth_ok`` response before issuing the
    service call. The response ``id`` and ``success`` flag are validated, and
    the socket is always closed via ``try/finally``.

    Args:
        domain: HA service domain (e.g. ``switch``).
        service: HA service to call (e.g. ``turn_on``).
        entity_id: Target entity id.
        service_data: Optional service data payload.
        return_response: Whether HA should return a response.

    Returns:
        The parsed HA response message.

    Raises:
        RuntimeError: if ``HASS_TOKEN`` is unset, auth fails, or the service
            call returns an error.

    """
    if service_data is None:
        service_data = {}

    hass_token = os.getenv("HASS_TOKEN")
    if not hass_token:
        raise RuntimeError("HASS_TOKEN is not set.")

    ws = create_connection(get_hass_ws_url())
    try:
        # 1. Read the auth_required greeting.
        hello = json.loads(ws.recv())
        if hello.get("type") != "auth_required":
            raise RuntimeError(
                f"Unexpected HA greeting (expected auth_required): {hello}",
            )

        # 2. Authenticate.
        ws.send(json.dumps({"type": "auth", "access_token": hass_token}))
        auth_resp = json.loads(ws.recv())
        if auth_resp.get("type") != "auth_ok":
            raise RuntimeError(
                f"HA authentication failed: {auth_resp.get('message', auth_resp)}",
            )

        # 3. Call the service and validate the response.
        msg_id = 1
        message = {
            "type": "call_service",
            "domain": domain,
            "service": service,
            "target": {"entity_id": entity_id},
            "service_data": service_data,
            "id": msg_id,
            "return_response": return_response,
        }
        ws.send(json.dumps(message))
        result = json.loads(ws.recv())

        if result.get("id") != msg_id:
            raise RuntimeError(
                f"HA response id mismatch: expected {msg_id}, got {result.get('id')}",
            )
        if not result.get("success", False):
            raise RuntimeError(
                f"HA service call '{domain}.{service}' failed: "
                f"{result.get('error', result)}",
            )
        return result
    finally:
        ws.close()


def hass_get_todo_items(
    entity_id: str,
    service_data: dict | None = None,
    ) -> str:
    """Get items from to do list."""
    if service_data is None:
        service_data = {"status":"needs_action"}
    todo_items = run_hass_service("todo","get_items",entity_id,service_data)
    todo_items = [
        x["summary"]
        for x in todo_items["result"]["response"][entity_id]["items"]
    ]
    return ",".join(todo_items)

def hass_get_calendar_events() -> str:
    """Get calendar events."""
    service_data = {"duration":{"hours":24}}
    calendar_events = run_hass_service(
        "calendar",
        "get_events",
        "calendar.personal",
        service_data)
    calendar_events = [
        x["summary"]
        for x in calendar_events["result"]["response"]["calendar.personal"]["events"]
    ]
    return ",".join(calendar_events)
