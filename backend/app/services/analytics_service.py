"""
Analytics service — aggregation and analysis logic.
"""

from datetime import datetime, timezone, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from app.services.transaction_service import (
    calculate_balance,
    calculate_category_spending,
    get_monthly_summary,
    get_recent_transactions,
    get_spending_for_period,
    get_income_for_period,
)


def get_financial_summary(db: Session, user_id: int) -> dict:
    """Get comprehensive financial summary."""
    balance_data = calculate_balance(db, user_id)
    categories = calculate_category_spending(db, user_id)

    top_category = None
    top_amount = 0.0
    if categories:
        top = max(categories, key=lambda c: c["total"])
        top_category = top["category"]
        top_amount = top["total"]

    from app.db.models import Transaction
    count = db.query(Transaction).filter(Transaction.user_id == user_id).count()

    return {
        "summary": {
            "total_income": balance_data["total_income"],
            "total_expense": balance_data["total_expense"],
            "balance": balance_data["balance"],
            "transaction_count": count,
            "top_expense_category": top_category,
            "top_expense_amount": top_amount,
        },
        "category_breakdown": categories,
        "monthly_trend": get_monthly_summary(db, user_id),
    }


def get_category_analytics(
    db: Session,
    user_id: int,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> list[dict]:
    """Get category spending analytics."""
    return calculate_category_spending(db, user_id, start_date, end_date)


def get_monthly_analytics(
    db: Session,
    user_id: int,
    months: int = 6,
) -> list[dict]:
    """Get monthly analytics."""
    return get_monthly_summary(db, user_id, months)


def get_spending_trend(
    db: Session,
    user_id: int,
    days: int = 30,
) -> list[dict]:
    """Get daily spending for the last N days."""
    now = datetime.now(timezone.utc)
    transactions = get_recent_transactions(db, user_id, days=days, limit=1000)

    daily: dict[str, float] = {}
    for i in range(days):
        day = (now - timedelta(days=i)).strftime("%Y-%m-%d")
        daily[day] = 0.0

    for txn in transactions:
        if txn.transaction_type.value == "expense":
            day_key = txn.transaction_date.strftime("%Y-%m-%d")
            if day_key in daily:
                daily[day_key] += txn.amount

    return [
        {"date": date, "amount": round(amount, 2)}
        for date, amount in sorted(daily.items())
    ]


def detect_unusual_spending(
    db: Session,
    user_id: int,
) -> list[dict]:
    """Detect categories with unusually high spending this month vs last month."""
    now = datetime.now(timezone.utc)
    this_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    last_month_end = this_month_start - timedelta(seconds=1)
    last_month_start = last_month_end.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    current = calculate_category_spending(
        db, user_id, start_date=this_month_start, end_date=now
    )
    previous = calculate_category_spending(
        db, user_id, start_date=last_month_start, end_date=last_month_end
    )

    prev_map = {c["category"]: c["total"] for c in previous}
    alerts = []
    for cat in current:
        prev_total = prev_map.get(cat["category"], 0)
        if prev_total > 0 and cat["total"] > prev_total * 1.5:
            alerts.append({
                "category": cat["category"],
                "current_month": cat["total"],
                "previous_month": prev_total,
                "increase_pct": round(
                    ((cat["total"] - prev_total) / prev_total) * 100, 1
                ),
            })

    return alerts
