"""Agent used to synthesize a final report from the individual summaries."""
import os

from agents import Agent
from agents.extensions.models.litellm_model import LitellmModel
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()

api_key = os.getenv("OPENROUTER_API_KEY") or ""
model_name = "openrouter/openai/gpt-4o-mini"
model = LitellmModel(model=model_name, api_key=api_key)

PROMPT = (
    "You are a senior researcher tasked with writing a cohesive report for a "
    "research query. You will be provided with the original query, and some "
    "initial research done by a research assistant.\n"
    "You should first come up with an outline for the report that describes "
    "the structure and flow of the report. Then, generate the report and return "
    "that as your final output.\n"
    "The final output should be in markdown format, and it should be lengthy "
    "and detailed. Aim for 5-10 pages of content, at least 1000 words."
)


class ReportData(BaseModel):
    """Pydantic model for ReportData."""

    short_summary: str
    """A short 2-3 sentence summary of the findings."""

    markdown_report: str
    """The final report"""

    follow_up_questions: list[str]
    """Suggested topics to research further"""

    filename: str
    """A filename to use when saving the report. Do not include the file extension."""


writer_agent = Agent(
    name="WriterAgent",
    instructions=PROMPT,
    model=model,
    output_type=ReportData,
)
