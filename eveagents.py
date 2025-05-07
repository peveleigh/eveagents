"""Collection of EveAgents."""

import os

from agents import (
    Agent,
    set_tracing_disabled,
)
from agents.extensions.models.litellm_model import LitellmModel
from agents.model_settings import ModelSettings
from dotenv import load_dotenv

from agentprompts import (
    cctv_prompt,
    eve_prompt,
    executive_assistant_prompt,
    knowledge_prompt,
    meteorologist_prompt,
    smart_home_prompt,
)
from tools.evellmtools import (
    cctv_tools,
    executive_assistant_tools,
    smart_home_tools,
)
from tools.webtools import web_tools

load_dotenv()

set_tracing_disabled(disabled=True)

api_key = os.getenv("OPENROUTER_API_KEY") or ""
model_name = "openrouter/google/gemini-2.5-flash-preview"
model = LitellmModel(model=model_name, api_key=api_key)

# Possible future agents: Media, Wellness, Financial

meteorologist_agent = Agent(
    name="Meteorologist Agent",
    instructions=meteorologist_prompt,
    model=model,
    tools=[],
)

cctv_agent = Agent(
    name="CCTV Agent",
    instructions=cctv_prompt,
    model=model,
    tools=cctv_tools,
)

smart_home_agent = Agent(
    name="Smart Home Agent",
    instructions=smart_home_prompt,
    model=model,
    tools=smart_home_tools,
)

executive_assistant_agent = Agent(
    name="Executive Assistant Agent",
    instructions=executive_assistant_prompt,
    model=model,
    tools=executive_assistant_tools,
)

knowledge_agent = Agent(
    name="Knowledge Agent",
    instructions=knowledge_prompt,
    model=model,
    tools=web_tools,
    model_settings=ModelSettings(tool_choice="required"),
)

eve_agent = Agent(
    name="Eve Agent",
    instructions=eve_prompt,
    model=model,
    handoffs = [
        meteorologist_agent,
        cctv_agent,
        smart_home_agent,
        executive_assistant_agent,
        knowledge_agent,
    ],
)
