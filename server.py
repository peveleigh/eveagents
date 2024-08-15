from fastapi import FastAPI, Query
from eveagents import (
    CCTV_Agent, 
    Executive_Assistant_Agent, 
    Meteorologist_Agent, 
    Smart_Home_Agent
)

app = FastAPI()

agents = {
    "cctv_agent": CCTV_Assistant_Agent,
    "executive_assistant_agent": Executive_Assistant_Agent,
    "meteorologist_agent": Meteorologist_Agent,
    "smart_home_agent": Smart_Home_Agent,
}

@app.get("/{agent_name}")
async def invoke_agent(
    agent_name: str,
    q: str = Query(None, min_length=3, description="A query"),
):
    if agent_name not in agents:
        return {"error": f"Agent '{agent_name}' not found"}
    
    agent = agents[agent_name]()
    return agent.invoke(q)
