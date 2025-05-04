"""Fast API server for connecting to EveAgents."""

from __future__ import annotations

from typing import Annotated

from agents import Runner
from fastapi import FastAPI, Query

from eveagents import eve_agent

app = FastAPI()

@app.get("/eve_agent")
async def invoke_agent(
    query: Annotated[str | None, Query(min_length=3, description="A query")] = None,
) -> str:
    """Invoke Eve Agent."""
    res = await Runner.run(
        eve_agent,
        query,
    )
    return res.final_output
