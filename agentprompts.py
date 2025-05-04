"""Collection of agent prompts."""

import datetime
import os
from pathlib import Path

import pytz
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX
from homeassistant_api import Client

from evehasstools import hass_get_calendar_events

hass_token = os.getenv("HASS_TOKEN")
hass_api_url = "http://"+os.getenv("HASS_API_URL")

client = Client(hass_api_url, hass_token)

# Eve Agent Prompt
with Path.open("prompts/eve_agent.txt") as file:
    eve_prompt = (
        RECOMMENDED_PROMPT_PREFIX
        + "\n\n"
        + file.read()
    )

# Meteorologist Agent Prompt
with Path.open("prompts/meteorologist_agent.txt") as file:
    meteorologist_prompt_template = file.read()
meteorologist_prompt = (
    RECOMMENDED_PROMPT_PREFIX
    + "\n\n"
    + client.get_rendered_template(meteorologist_prompt_template)
)

# CCTV Agent Prompt
with Path.open("prompts/cctv_agent.txt") as file:
    cctv_prompt = (
        RECOMMENDED_PROMPT_PREFIX
        + "\n\n"
        + file.read()
    )

# Smart Home Agent Prompt
with Path.open("prompts/smart_home_agent.txt") as file:
    smart_home_prompt_template = file.read()
smart_home_prompt = (
    RECOMMENDED_PROMPT_PREFIX
    + "\n\n"
    + client.get_rendered_template(smart_home_prompt_template)
)

# Executive Assistant Prompt
with Path.open("prompts/executive_assistant_agent.txt") as file:
    executive_assistant_prompt_template = file.read()
# Get current date and day of the week
nst = pytz.timezone("Canada/Newfoundland")
now = datetime.datetime.now(nst).strftime("%A %B %d %Y")
# Get the user's calendar events.
calendar_events = hass_get_calendar_events()
prompt_data = {"now":now,"calendar_events":calendar_events}
executive_assistant_prompt = (
    RECOMMENDED_PROMPT_PREFIX +
    "\n\n"
    + executive_assistant_prompt_template.format(**prompt_data)
)
