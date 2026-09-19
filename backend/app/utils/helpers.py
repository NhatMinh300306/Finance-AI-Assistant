"""
Utility helpers — seed data, formatting, etc.
"""

import random
from datetime import datetime, timezone, timedelta

from sqlalchemy.orm import Session

from app.db.models import Transaction, TransactionType, User


def seed_demo_data(db: Session) -> None:
    """
    Seed the database with realistic demo financial data.
    Creates a default user and 30 transactions across multiple categories.
    """
    # Check if data already exists
    existing = db.query(Transaction).count()
    if existing > 0:
        return

    # Create default user
    user = db.query(User).filter(User.id == 1).first()
    if not user:
        user = User(id=1, name="Demo User", email="demo@finmate.app")
        db.add(user)
        db.commit()
        db.refresh(user)

    now = datetime.now(timezone.utc)

    # Demo transactions — realistic personal finance data
    demo_transactions = [
        # This month — income
        {"amount": 15000, "type": "income", "category": "Salary", "desc": "Monthly salary", "days_ago": 1},
        {"amount": 2000, "type": "income", "category": "Freelance", "desc": "Freelance web design project", "days_ago": 5},
        # This month — expenses
        {"amount": 35, "type": "expense", "category": "Food", "desc": "Lunch at noodle shop", "days_ago": 0},
        {"amount": 88, "type": "expense", "category": "Food", "desc": "Grocery shopping", "days_ago": 1},
        {"amount": 25, "type": "expense", "category": "Food", "desc": "Morning coffee and pastry", "days_ago": 2},
        {"amount": 150, "type": "expense", "category": "Food", "desc": "Dinner with friends", "days_ago": 3},
        {"amount": 42, "type": "expense", "category": "Food", "desc": "Food delivery", "days_ago": 4},
        {"amount": 6, "type": "expense", "category": "Transportation", "desc": "Metro fare", "days_ago": 0},
        {"amount": 30, "type": "expense", "category": "Transportation", "desc": "DiDi ride to meeting", "days_ago": 2},
        {"amount": 15, "type": "expense", "category": "Transportation", "desc": "Bus pass top-up", "days_ago": 5},
        {"amount": 299, "type": "expense", "category": "Shopping", "desc": "New headphones", "days_ago": 3},
        {"amount": 89, "type": "expense", "category": "Shopping", "desc": "T-shirt from Uniqlo", "days_ago": 6},
        {"amount": 50, "type": "expense", "category": "Entertainment", "desc": "Movie tickets", "days_ago": 4},
        {"amount": 30, "type": "expense", "category": "Entertainment", "desc": "Music streaming subscription", "days_ago": 7},
        {"amount": 200, "type": "expense", "category": "Bills", "desc": "Electricity bill", "days_ago": 8},
        {"amount": 99, "type": "expense", "category": "Bills", "desc": "Mobile phone plan", "days_ago": 9},
        {"amount": 150, "type": "expense", "category": "Healthcare", "desc": "Pharmacy — cold medicine", "days_ago": 6},
        {"amount": 500, "type": "expense", "category": "Education", "desc": "Online course — Python", "days_ago": 10},
        {"amount": 2500, "type": "expense", "category": "Housing", "desc": "Monthly rent contribution", "days_ago": 2},
        # Last month
        {"amount": 15000, "type": "income", "category": "Salary", "desc": "Monthly salary", "days_ago": 32},
        {"amount": 1500, "type": "income", "category": "Freelance", "desc": "Logo design gig", "days_ago": 35},
        {"amount": 320, "type": "expense", "category": "Food", "desc": "Weekly groceries", "days_ago": 33},
        {"amount": 180, "type": "expense", "category": "Food", "desc": "Restaurant dinner", "days_ago": 36},
        {"amount": 45, "type": "expense", "category": "Transportation", "desc": "Taxi ride", "days_ago": 34},
        {"amount": 199, "type": "expense", "category": "Shopping", "desc": "Book bundle", "days_ago": 38},
        {"amount": 75, "type": "expense", "category": "Entertainment", "desc": "Concert ticket", "days_ago": 40},
        {"amount": 180, "type": "expense", "category": "Bills", "desc": "Internet bill", "days_ago": 37},
        {"amount": 2500, "type": "expense", "category": "Housing", "desc": "Monthly rent contribution", "days_ago": 33},
        # Two months ago
        {"amount": 15000, "type": "income", "category": "Salary", "desc": "Monthly salary", "days_ago": 62},
        {"amount": 400, "type": "expense", "category": "Food", "desc": "Monthly food expenses", "days_ago": 65},
        {"amount": 60, "type": "expense", "category": "Transportation", "desc": "Metro and bus", "days_ago": 63},
        {"amount": 350, "type": "expense", "category": "Shopping", "desc": "New running shoes", "days_ago": 68},
        {"amount": 2500, "type": "expense", "category": "Housing", "desc": "Monthly rent contribution", "days_ago": 64},
    ]

    for item in demo_transactions:
        txn = Transaction(
            user_id=user.id,
            amount=item["amount"],
            transaction_type=TransactionType(item["type"]),
            category=item["category"],
            description=item["desc"],
            transaction_date=now - timedelta(days=item["days_ago"]),
        )
        db.add(txn)

    db.commit()


def format_currency(amount: float) -> str:
    """Format amount as yuan currency string."""
    return f"¥{amount:,.2f}"
