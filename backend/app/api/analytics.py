"""
Analytics API routes.
"""

from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.services.analytics_service import (
    get_financial_summary,
    get_category_analytics,
    get_monthly_analytics,
    get_spending_trend,
    detect_unusual_spending,
)
from app.services.transaction_service import get_or_create_default_user

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/summary")
def analytics_summary(db: Session = Depends(get_db)):
    """Get comprehensive financial summary."""
    user = get_or_create_default_user(db)
    return get_financial_summary(db, user.id)


@router.get("/categories")
def analytics_categories(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
):
    """Get spending by category."""
    user = get_or_create_default_user(db)
    return get_category_analytics(db, user.id, start_date, end_date)


@router.get("/monthly")
def analytics_monthly(
    months: int = Query(default=6, ge=1, le=24),
    db: Session = Depends(get_db),
):
    """Get monthly income/expense breakdown."""
    user = get_or_create_default_user(db)
    return get_monthly_analytics(db, user.id, months)


@router.get("/trend")
def analytics_trend(
    days: int = Query(default=30, ge=1, le=365),
    db: Session = Depends(get_db),
):
    """Get daily spending trend."""
    user = get_or_create_default_user(db)
    return get_spending_trend(db, user.id, days)


@router.get("/alerts")
def analytics_alerts(db: Session = Depends(get_db)):
    """Detect unusual spending patterns."""
    user = get_or_create_default_user(db)
    return detect_unusual_spending(db, user.id)
