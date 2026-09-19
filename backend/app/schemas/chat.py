"""
Pydantic schemas for chat request/response validation.
"""

from typing import Optional
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Schema for chat message request."""
    message: str = Field(
        ..., min_length=1, max_length=2000,
        description="User's chat message"
    )
    user_id: int = Field(default=1, description="User ID")


class ChatResponse(BaseModel):
    """Schema for chat message response."""
    reply: str = Field(..., description="AI assistant's reply")
    action_taken: Optional[str] = Field(
        default=None,
        description="Description of any action performed (e.g., transaction added)"
    )
    data: Optional[dict] = Field(
        default=None,
        description="Structured data returned (e.g., transaction details, summary)"
    )
