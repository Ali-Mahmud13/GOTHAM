
from fastapi import APIRouter
from pydantic import BaseModel
from app.agent import medical_agent

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    message: str


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest):
  
    # Invoke the agent
    result = medical_agent.invoke({
        "message": request.message,
        "response": "",
    })
    
    return ChatResponse(
        message=result["response"]
    )
