"""
SQLAlchemy ORM models for the application.
"""

from datetime import datetime, timezone

from sqlalchemy import (
    Column, Integer, String, Float, DateTime, ForeignKey, Enum as SAEnum
)
from sqlalchemy.orm import relationship
import enum

from app.db.database import Base


class TransactionType(str, enum.Enum):
    """Transaction type enumeration."""
    INCOME = "income"
    EXPENSE = "expense"


# Default categories - extensible by adding more values
DEFAULT_CATEGORIES = [
    "Food",
    "Transportation",
    "Shopping",
    "Entertainment",
    "Bills",
    "Healthcare",
    "Education",
    "Salary",
    "Freelance",
    "Investment",
    "Gift",
    "Housing",
    "Other",
]


class User(Base):
    """User model."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    created_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationships
    transactions = relationship(
        "Transaction", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<User(id={self.id}, name='{self.name}', email='{self.email}')>"


class Transaction(Base):
    """Financial transaction model."""
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    amount = Column(Float, nullable=False)
    transaction_type = Column(
        SAEnum(TransactionType), nullable=False
    )
    category = Column(String(50), nullable=False, default="Other")
    description = Column(String(500), nullable=True)
    transaction_date = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    created_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationships
    user = relationship("User", back_populates="transactions")

    def __repr__(self):
        return (
            f"<Transaction(id={self.id}, type='{self.transaction_type}', "
            f"amount={self.amount}, category='{self.category}')>"
        )
