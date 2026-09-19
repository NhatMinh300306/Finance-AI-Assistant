"""
Pydantic schemas for transaction request/response validation.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class TransactionCreate(BaseModel):
    """Schema for creating a new transaction."""
    amount: float = Field(..., gt=0, description="Transaction amount (must be positive)")
    transaction_type: str = Field(..., description="'income' or 'expense'")
    category: str = Field(default="Other", max_length=50)
    description: Optional[str] = Field(default=None, max_length=500)
    transaction_date: Optional[datetime] = None

    @field_validator("transaction_type")
    @classmethod
    def validate_transaction_type(cls, v: str) -> str:
        v = v.lower().strip()
        if v not in ("income", "expense"):
            raise ValueError("transaction_type must be 'income' or 'expense'")
        return v

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        return v.strip().title() if v else "Other"


class TransactionUpdate(BaseModel):
    """Schema for updating a transaction."""
    amount: Optional[float] = Field(default=None, gt=0)
    transaction_type: Optional[str] = None
    category: Optional[str] = Field(default=None, max_length=50)
    description: Optional[str] = Field(default=None, max_length=500)
    transaction_date: Optional[datetime] = None

    @field_validator("transaction_type")
    @classmethod
    def validate_transaction_type(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.lower().strip()
        if v not in ("income", "expense"):
            raise ValueError("transaction_type must be 'income' or 'expense'")
        return v

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        return v.strip().title()


class TransactionResponse(BaseModel):
    """Schema for transaction response."""
    id: int
    user_id: int
    amount: float
    transaction_type: str
    category: str
    description: Optional[str] = None
    transaction_date: datetime
    created_at: datetime

    model_config = {"from_attributes": True}


class TransactionListResponse(BaseModel):
    """Schema for paginated transaction list."""
    transactions: list[TransactionResponse]
    total: int
    page: int
    page_size: int
