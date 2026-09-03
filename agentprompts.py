"""Collection of agent prompts.

Static prompts (those that only read a file) are built at import time. Dynamic
prompts that require Home Assistant network I/O (template rendering, calendar
events) are built lazily on first use and cached with a TTL so the service can
boot without HA being reachable and prompts stay fresh.
"""

import datetime
import logging
import os
import time
from functools import lru_cache
from pathlib import Path

import pytz
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX
from homeassistant_api import Client

from evehasstools import get_hass_rest_url, hass_get_calendar_events

logger = logging.getLogger(__name__)

_PROMPTS_DIR = Path(__file__).parent / "prompts"
_PROMPT_TTL_SECONDS = 300


def _read_prompt(name: str) -> str:
    """Read a prompt file from the prompts/ directory."""
    return (_PROMPTS_DIR / name).read_text(encoding="utf-8")


@lru_cache(maxsize=1)
def get_ha_client() -> Client:
    """Lazily construct the Home Assistant REST client.

    Construction is deferred to first use so importing this module never
    requires HA to be reachable.
    """
    hass_token = os.getenv("HASS_TOKEN")
    return Client(get_hass_rest_url(), hass_token)


# --- Static prompts (file I/O only, safe at import time) ---

eve_prompt = RECOMMENDED_PROMPT_PREFIX + "\n\n" + _read_prompt("eve_agent.txt")
knowledge_prompt = RECOMMENDED_PROMPT_PREFIX + "\n\n" + _read_prompt("knowledge_agent.txt")
cctv_prompt = RECOMMENDED_PROMPT_PREFIX + "\n\n" + _read_prompt("cctv_agent.txt")

# --- Dynamic prompts (require HA; built lazily with TTL cache) ---


class _TTLCache:
    """A minimal TTL cache for prompt strings."""

    def __init__(self) -> None:
        self._store: dict[str, tuple[float, str]] = {}

    def get(self, key: str, builder):
        now = time.monotonic()
        entry = self._store.get(key)
        if entry is None or now - entry[0] > _PROMPT_TTL_SECONDS:
            value = builder()
            self._store[key] = (now, value)
            return value
        return entry[1]


_prompt_cache = _TTLCache()


def _build_meteorologist_prompt() -> str:
    template = _read_prompt("meteorologist_agent.txt")
    rendered = get_ha_client().get_rendered_template(template)
    return RECOMMENDED_PROMPT_PREFIX + "\n\n" + rendered


def _build_smart_home_prompt() -> str:
    template = _read_prompt("smart_home_agent.txt")
    rendered = get_ha_client().get_rendered_template(template)
    return RECOMMENDED_PROMPT_PREFIX + "\n\n" + rendered


def _build_executive_assistant_prompt() -> str:
    template = _read_prompt("executive_assistant_agent.txt")
    nst = pytz.timezone("Canada/Newfoundland")
    now = datetime.datetime.now(nst).strftime("%A %B %d %Y")
    calendar_events = hass_get_calendar_events()
    return (
        RECOMMENDED_PROMPT_PREFIX
        + "\n\n"
        + template.format(now=now, calendar_events=calendar_events)
    )


def get_meteorologist_prompt() -> str:
    """Return the meteorologist prompt, rebuilding it if the TTL has expired."""
    return _prompt_cache.get("meteorologist", _build_meteorologist_prompt)


def get_smart_home_prompt() -> str:
    """Return the smart-home prompt, rebuilding it if the TTL has expired."""
    return _prompt_cache.get("smart_home", _build_smart_home_prompt)


def get_executive_assistant_prompt() -> str:
    """Return the executive-assistant prompt, rebuilding it if the TTL expired."""
    return _prompt_cache.get("executive_assistant", _build_executive_assistant_prompt)
