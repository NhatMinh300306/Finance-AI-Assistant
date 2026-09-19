"""
Transaction service — business logic for CRUD and queries on transactions.
"""

from datetime import datetime, timezone, timedelta
from typing import Optional

from sqlalchemy import func, extract
from sqlalchemy.orm import Session

from app.db.models import Transaction, TransactionType, User


def get_or_create_default_user(db: Session) -> User:
    """Get default user or create one for the prototype."""
    user = db.query(User).filter(User.id == 1).first()
    if not user:
        user = User(id=1, name="Demo User", email="demo@finmate.app")
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


def create_transaction(
    db: Session,
    user_id: int,
    amount: float,
    transaction_type: str,
    category: str = "Other",
    description: Optional[str] = None,
    transaction_date: Optional[datetime] = None,
) -> Transaction:
    """Create a new transaction."""
    if transaction_date is None:
        transaction_date = datetime.now(timezone.utc)

    txn = Transaction(
        user_id=user_id,
        amount=amount,
        transaction_type=TransactionType(transaction_type),
        category=category,
        description=description,
        transaction_date=transaction_date,
    )
    db.add(txn)
    db.commit()
    db.refresh(txn)
    return txn


def get_transaction_by_id(db: Session, transaction_id: int) -> Optional[Transaction]:
    """Get a single transaction by ID."""
    return db.query(Transaction).filter(Transaction.id == transaction_id).first()


def get_transactions(
    db: Session,
    user_id: int,
    page: int = 1,
    page_size: int = 20,
    category: Optional[str] = None,
    transaction_type: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> tuple[list[Transaction], int]:
    """Get paginated transactions with optional filters."""
    query = db.query(Transaction).filter(Transaction.user_id == user_id)

    if category:
        query = query.filter(Transaction.category == category)
    if transaction_type:
        query = query.filter(
            Transaction.transaction_type == TransactionType(transaction_type)
        )
    if start_date:
        query = query.filter(Transaction.transaction_date >= start_date)
    if end_date:
        query = query.filter(Transaction.transaction_date <= end_date)

    total = query.count()
    transactions = (
        query.order_by(Transaction.transaction_date.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return transactions, total


def update_transaction(
    db: Session,
    transaction_id: int,
    **kwargs,
) -> Optional[Transaction]:
    """Update an existing transaction."""
    txn = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not txn:
        return None

    for key, value in kwargs.items():
        if value is not None:
            if key == "transaction_type":
                value = TransactionType(value)
            setattr(txn, key, value)

    db.commit()
    db.refresh(txn)
    return txn


def delete_transaction(db: Session, transaction_id: int) -> bool:
    """Delete a transaction. Returns True if deleted."""
    txn = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not txn:
        return False
    db.delete(txn)
    db.commit()
    return True


def calculate_balance(db: Session, user_id: int) -> dict:
    """Calculate total income, expense, and balance."""
    income = (
        db.query(func.coalesce(func.sum(Transaction.amount), 0.0))
        .filter(
            Transaction.user_id == user_id,
            Transaction.transaction_type == TransactionType.INCOME,
        )
        .scalar()
    )
    expense = (
        db.query(func.coalesce(func.sum(Transaction.amount), 0.0))
        .filter(
            Transaction.user_id == user_id,
            Transaction.transaction_type == TransactionType.EXPENSE,
        )
        .scalar()
    )
    return {
        "total_income": float(income),
        "total_expense": float(expense),
        "balance": float(income) - float(expense),
    }


def calculate_category_spending(
    db: Session,
    user_id: int,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> list[dict]:
    """Get spending breakdown by category."""
    query = db.query(
        Transaction.category,
        func.sum(Transaction.amount).label("total"),
    ).filter(
        Transaction.user_id == user_id,
        Transaction.transaction_type == TransactionType.EXPENSE,
    )

    if start_date:
        query = query.filter(Transaction.transaction_date >= start_date)
    if end_date:
        query = query.filter(Transaction.transaction_date <= end_date)

    results = query.group_by(Transaction.category).all()

    grand_total = sum(r.total for r in results) if results else 0
    return [
        {
            "category": r.category,
            "total": float(r.total),
            "percentage": round((r.total / grand_total) * 100, 1) if grand_total > 0 else 0,
        }
        for r in results
    ]


def get_monthly_summary(
    db: Session,
    user_id: int,
    months: int = 6,
) -> list[dict]:
    """Get monthly income/expense summary for the last N months."""
    now = datetime.now(timezone.utc)
    start = now - timedelta(days=months * 31)

    transactions = (
        db.query(Transaction)
        .filter(
            Transaction.user_id == user_id,
            Transaction.transaction_date >= start,
        )
        .all()
    )

    # Group by year-month
    monthly: dict[str, dict] = {}
    for txn in transactions:
        key = txn.transaction_date.strftime("%Y-%m")
        if key not in monthly:
            monthly[key] = {"income": 0.0, "expense": 0.0}
        if txn.transaction_type == TransactionType.INCOME:
            monthly[key]["income"] += txn.amount
        else:
            monthly[key]["expense"] += txn.amount

    result = []
    for month_key in sorted(monthly.keys()):
        data = monthly[month_key]
        result.append({
            "month": month_key,
            "total_income": round(data["income"], 2),
            "total_expense": round(data["expense"], 2),
            "net_savings": round(data["income"] - data["expense"], 2),
        })

    return result


def get_recent_transactions(
    db: Session,
    user_id: int,
    days: int = 7,
    limit: int = 20,
) -> list[Transaction]:
    """Get recent transactions from the last N days."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    return (
        db.query(Transaction)
        .filter(
            Transaction.user_id == user_id,
            Transaction.transaction_date >= cutoff,
        )
        .order_by(Transaction.transaction_date.desc())
        .limit(limit)
        .all()
    )


def get_spending_for_period(
    db: Session,
    user_id: int,
    start_date: datetime,
    end_date: datetime,
    category: Optional[str] = None,
) -> float:
    """Get total spending for a specific period, optionally by category."""
    query = db.query(
        func.coalesce(func.sum(Transaction.amount), 0.0)
    ).filter(
        Transaction.user_id == user_id,
        Transaction.transaction_type == TransactionType.EXPENSE,
        Transaction.transaction_date >= start_date,
        Transaction.transaction_date <= end_date,
    )
    if category:
        query = query.filter(Transaction.category == category)
    return float(query.scalar())


def get_income_for_period(
    db: Session,
    user_id: int,
    start_date: datetime,
    end_date: datetime,
) -> float:
    """Get total income for a specific period."""
    result = db.query(
        func.coalesce(func.sum(Transaction.amount), 0.0)
    ).filter(
        Transaction.user_id == user_id,
        Transaction.transaction_type == TransactionType.INCOME,
        Transaction.transaction_date >= start_date,
        Transaction.transaction_date <= end_date,
    ).scalar()
    return float(result)
