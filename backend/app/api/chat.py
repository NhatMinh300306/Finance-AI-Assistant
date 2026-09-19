"""
Chat API routes.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.ai_service import process_chat_message
from app.services.transaction_service import get_or_create_default_user

router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
def chat(
    data: ChatRequest,
    db: Session = Depends(get_db),
):
    """
    Process a chat message through the AI assistant.
    The AI uses function-calling to query real financial data.
    """
    if not data.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    user = get_or_create_default_user(db)
    result = process_chat_message(db=db, user_id=user.id, message=data.message)
    return ChatResponse(**result)
