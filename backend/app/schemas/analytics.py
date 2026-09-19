"""
Pydantic schemas for analytics response validation.
"""

from pydantic import BaseModel


class CategorySpending(BaseModel):
    """Spending for a single category."""
    category: str
    total: float
    percentage: float


class MonthlySummary(BaseModel):
    """Monthly financial summary."""
    month: str
    total_income: float
    total_expense: float
    net_savings: float


class FinancialSummary(BaseModel):
    """Overall financial summary."""
    total_income: float
    total_expense: float
    balance: float
    transaction_count: int
    top_expense_category: str | None = None
    top_expense_amount: float = 0.0


class AnalyticsSummaryResponse(BaseModel):
    """Complete analytics response."""
    summary: FinancialSummary
    category_breakdown: list[CategorySpending]
    monthly_trend: list[MonthlySummary]
