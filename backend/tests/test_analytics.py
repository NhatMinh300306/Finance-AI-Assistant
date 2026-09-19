"""
Tests for analytics API endpoints.
"""

import pytest
from app.services.transaction_service import create_transaction


def _seed_transactions(db):
    """Helper to seed test transactions."""
    create_transaction(db, 1, 10000, "income", "Salary", "Monthly salary")
    create_transaction(db, 1, 2000, "income", "Freelance", "Side gig")
    create_transaction(db, 1, 500, "expense", "Food", "Groceries")
    create_transaction(db, 1, 200, "expense", "Food", "Restaurant")
    create_transaction(db, 1, 150, "expense", "Transportation", "Metro")
    create_transaction(db, 1, 300, "expense", "Shopping", "Clothes")
    create_transaction(db, 1, 100, "expense", "Entertainment", "Movies")


class TestAnalyticsAPI:
    """Test analytics endpoints."""

    def test_analytics_summary(self, client, db_session):
        """Test getting financial summary."""
        _seed_transactions(db_session)

        response = client.get("/api/analytics/summary")
        assert response.status_code == 200
        data = response.json()
        assert "summary" in data
        assert "category_breakdown" in data
        assert "monthly_trend" in data
        assert data["summary"]["total_income"] == 12000.0
        assert data["summary"]["total_expense"] == 1250.0
        assert data["summary"]["balance"] == 10750.0

    def test_analytics_categories(self, client, db_session):
        """Test category breakdown endpoint."""
        _seed_transactions(db_session)

        response = client.get("/api/analytics/categories")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        # Food should be the highest
        food = next(c for c in data if c["category"] == "Food")
        assert food["total"] == 700.0

    def test_analytics_monthly(self, client, db_session):
        """Test monthly analytics endpoint."""
        _seed_transactions(db_session)

        response = client.get("/api/analytics/monthly?months=3")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_analytics_trend(self, client, db_session):
        """Test spending trend endpoint."""
        _seed_transactions(db_session)

        response = client.get("/api/analytics/trend?days=7")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_analytics_alerts(self, client, db_session):
        """Test unusual spending alerts."""
        response = client.get("/api/analytics/alerts")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_empty_analytics(self, client):
        """Test analytics with no data."""
        response = client.get("/api/analytics/summary")
        assert response.status_code == 200
        data = response.json()
        assert data["summary"]["total_income"] == 0.0
        assert data["summary"]["total_expense"] == 0.0
        assert data["summary"]["balance"] == 0.0


class TestAnalyticsService:
    """Test analytics service functions."""

    def test_financial_summary(self, db_session):
        from app.services.analytics_service import get_financial_summary

        _seed_transactions(db_session)
        summary = get_financial_summary(db_session, 1)

        assert summary["summary"]["transaction_count"] == 7
        assert summary["summary"]["top_expense_category"] == "Food"
        assert summary["summary"]["top_expense_amount"] == 700.0

    def test_spending_trend(self, db_session):
        from app.services.analytics_service import get_spending_trend

        _seed_transactions(db_session)
        trend = get_spending_trend(db_session, 1, days=7)

        assert isinstance(trend, list)
        assert len(trend) == 7
        # All entries should have 'date' and 'amount'
        for entry in trend:
            assert "date" in entry
            assert "amount" in entry
