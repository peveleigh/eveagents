"""Agent used to develop search queries."""
import os

from agents import Agent
from agents.extensions.models.litellm_model import LitellmModel
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()

api_key = os.getenv("OPENROUTER_API_KEY") or ""
model_name = "openrouter/openai/gpt-4o"
model = LitellmModel(model=model_name, api_key=api_key)

PROMPT = (
    "You are a helpful research assistant. Given a query, come up with a set of web "
    "searches to perform to best answer the query. Output between 5 and 20 terms "
    "to query for."
)

class WebSearchItem(BaseModel):
    """Pydantic model for WebSearchItem."""

    reason: str
    "Your reasoning for why this search is important to the query."

    query: str
    "The search term to use for the web search."


class WebSearchPlan(BaseModel):
    """Pydantic model for WebSearchPlan."""

    searches: list[WebSearchItem]
    """A list of web searches to perform to best answer the query."""


planner_agent = Agent(
    name="PlannerAgent",
    instructions=PROMPT,
    model=model,
    output_type=WebSearchPlan,
)
