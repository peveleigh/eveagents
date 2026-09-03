"""Fast API server for Connecting to EveAgents."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Annotated

from agents import Runner
from fastapi import FastAPI, HTTPException, Query

from conversation_storage import ConversationStorage
from eveagents import eve_agent
from log_setup import setup_logging

logger = logging.getLogger(__name__)

storage = ConversationStorage()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: configure logging once at startup."""
    setup_logging()
    yield


app = FastAPI(lifespan=lifespan)


@app.get("/eve_agent")
async def invoke_agent(
    query: Annotated[str | None, Query(min_length=3, description="A query")] = None,
    cid: Annotated[
        str | None,
        Query(min_length=1, description="Conversation id"),
    ] = None,
) -> str:
    """Invoke Eve Agent."""
    retrieved_items = None
    if cid:
        logger.info(
            "Invoking Eve Agent with conversation id: %s",
            cid,
        )
        retrieved_items: list[dict[str, str]] = storage.get_conversation(cid)
    else:
        logger.info(
            "Invoking Eve Agent without a conversation id.",
        )

    input_items: list[dict[str, str]] = [{"content": query, "role": "user"}]

    if retrieved_items:
        input_items = retrieved_items + input_items

    try:
        res = await Runner.run(
            eve_agent,
            input_items,
        )
    except Exception:
        logger.exception("Failed to run eve_agent.")
        raise HTTPException(status_code=500, detail="Failed to run eve_agent.") from None

    if cid:
        storage.save_conversation(cid, res.to_input_list())

    return res.final_output
