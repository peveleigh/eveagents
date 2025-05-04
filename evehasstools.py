"""Collection of functions for interacting with Home Assistant."""
from __future__ import annotations

import json
import os

from dotenv import load_dotenv
from websocket import create_connection

load_dotenv()

hass_token = os.getenv("HASS_TOKEN")
openai_api_key = os.getenv("OPENROUTER_API_KEY")

hass_api_url = os.getenv("HASS_API_URL")
openai_api_url = os.getenv("OPENROUTER_API_URL")

def run_hass_service(
    domain: str,
    service: str,
    entity_id: str,
    service_data: dict | None = None,
    *,
    return_response: bool = True,
    ) -> dict:
    """Run a Home Assistant service."""
    if service_data is None:
        service_data = {}
    ws = create_connection(f"ws://{hass_api_url}/websocket")
    message = {
    "type": "auth",
    "access_token": hass_token,
    }
    ws.send(json.dumps(message))
    result =  ws.recv()
    result =  ws.recv()
    message = {
    "type": "call_service",
    "domain": f"{domain}",
    "service": f"{service}",
    "target": { "entity_id": f"{entity_id}" },
    "service_data": service_data,
    "id": 1,
    "return_response": return_response,
    }
    ws.send(json.dumps(message))
    result =  json.loads(ws.recv())
    ws.close()
    return result

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

