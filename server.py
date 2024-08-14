from fastapi import FastAPI, Query
from eveagents import Meteorologist_Agent, Executive_Assistant_Agent

app = FastAPI()

@app.get("/meteorologist_agent")
async def meteorologist(q: str = Query(None, min_length=3, description="A query")):
    agent = Meteorologist_Agent()
    return agent.invoke(q)

@app.get("/executive_assistant_agent")
async def executive_assistant(q: str = Query(None, min_length=3, description="A query")):
    agent = Executive_Assistant_Agent()
    return agent.invoke(q)
