from fastapi import APIRouter
from pydantic import BaseModel, Field
from ..core.llm_gateway import chat
from ..core.audit import audit

router = APIRouter(prefix="/api/chat", tags=["chat"])

class ChatIn(BaseModel):
    messages: list[dict] = Field(default_factory=list)
    temperature: float = 0.2

@router.post("")
def chat_post(payload: ChatIn):
    audit("chat.request", {"n": len(payload.messages)})
    result = chat(payload.messages, payload.temperature)
    audit("chat.response", {"ok": bool(result.get("ok"))})
    return result
