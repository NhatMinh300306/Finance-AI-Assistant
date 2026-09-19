"""
User API routes.
Simplified for prototype — no authentication.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.services.transaction_service import get_or_create_default_user

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("/me")
def get_current_user(db: Session = Depends(get_db)):
    """Get current user profile (prototype: returns default user)."""
    user = get_or_create_default_user(db)
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }
