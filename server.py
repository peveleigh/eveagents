"""Fast API server for connecting to EveAgents."""

from __future__ import annotations

from typing import Annotated

from agents import Runner
from fastapi import FastAPI, Query

from conversation_storage import ConversationStorage
from eveagents import eve_agent

storage = ConversationStorage()

app = FastAPI()

@app.get("/eve_agent")
async def invoke_agent(
    query: Annotated[str | None, Query(min_length=3, description="A query")] = None,
    cid: Annotated[
        str | None,
        Query(min_length=1, description="Conversation id"),
    ] = None,
) -> str:
    """Invoke Eve Agent."""
    retrieved_items: list(dict[str, str]) = storage.get_conversation(cid)

    input_items: list(dict[str, str]) = [{"content": query, "role": "user"}]

    if retrieved_items:
        input_items = retrieved_items + input_items

    print(cid)

    res = await Runner.run(
        eve_agent,
        input_items,
    )

    storage.save_conversation(cid, res.to_input_list())

    return res.final_output
