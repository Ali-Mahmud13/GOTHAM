from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
from .main_agent.graph import create_graph
from langchain_core.messages import HumanMessage
import asyncio
from uuid import uuid4

app = FastAPI()
graph = create_graph()
sessions = {}

class ChatRequest(BaseModel):
    message: str
    session_id: str = None

@app.post("/chat")
async def chat(request: ChatRequest):
    session_id = request.session_id or str(uuid4())
    config = {"configurable": {"thread_id": session_id}}
    
    state = {"messages": [HumanMessage(content=request.message)]}
    
    result = await graph.ainvoke(state, config=config)
    
    assistant_message = result["messages"][-1].content
    
    return {
        "response": assistant_message,
        "session_id": session_id
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}