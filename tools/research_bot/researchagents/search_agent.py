"""Agent used to perform search queries."""
import os

from agents import Agent, function_tool
from agents.extensions.models.litellm_model import LitellmModel
from agents.model_settings import ModelSettings
from dotenv import load_dotenv
from exa_py import Exa

load_dotenv()

api_key = os.getenv("OPENROUTER_API_KEY") or ""
model_name = "openrouter/openai/gpt-4o-mini"
model = LitellmModel(model=model_name, api_key=api_key)

@function_tool
def web_search(query: str) -> str:
    """Search the web for information.

    Args:
        query: Search query

    """
    exa = Exa(os.getenv("EXA_API_KEY"))
    return exa.search(query, num_results=3)


INSTRUCTIONS = (
    "You are a research assistant. Given a search term, you search the web for "
    "that term and produce a concise summary of the results. The summary must "
    "2-3 paragraphs and less than 300 words. Capture the main points. Write "
    "succinctly, no need to have complete sentences or good grammar. This "
    "will be consumed by someone synthesizing a report, so its vital you capture "
    "the essence and ignore any fluff. Do not include any additional commentary "
    "other than the summary itself."
)

search_agent = Agent(
    name="Search agent",
    instructions=INSTRUCTIONS,
    tools=[web_search],
    model=model,
    model_settings=ModelSettings(tool_choice="required"),
)
