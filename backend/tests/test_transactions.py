"""
Tests for transaction API endpoints and service logic.
"""

import pytest


class TestTransactionAPI:
    """Test transaction CRUD endpoints."""

    def test_create_transaction(self, client):
        """Test creating a new transaction."""
        response = client.post("/api/transactions", json={
            "amount": 100.0,
            "transaction_type": "expense",
            "category": "Food",
            "description": "Test lunch",
        })
        assert response.status_code == 201
        data = response.json()
        assert data["amount"] == 100.0
        assert data["transaction_type"] == "expense"
        assert data["category"] == "Food"
        assert data["description"] == "Test lunch"
        assert data["id"] is not None

    def test_create_income_transaction(self, client):
        """Test creating an income transaction."""
        response = client.post("/api/transactions", json={
            "amount": 5000.0,
            "transaction_type": "income",
            "category": "Salary",
            "description": "Monthly salary",
        })
        assert response.status_code == 201
        data = response.json()
        assert data["transaction_type"] == "income"
        assert data["category"] == "Salary"

    def test_create_transaction_invalid_amount(self, client):
        """Test that negative amount is rejected."""
        response = client.post("/api/transactions", json={
            "amount": -50.0,
            "transaction_type": "expense",
            "category": "Food",
        })
        assert response.status_code == 422

    def test_create_transaction_invalid_type(self, client):
        """Test that invalid transaction type is rejected."""
        response = client.post("/api/transactions", json={
            "amount": 50.0,
            "transaction_type": "invalid",
            "category": "Food",
        })
        assert response.status_code == 422

    def test_create_transaction_zero_amount(self, client):
        """Test that zero amount is rejected."""
        response = client.post("/api/transactions", json={
            "amount": 0,
            "transaction_type": "expense",
            "category": "Food",
        })
        assert response.status_code == 422

    def test_get_transactions(self, client):
        """Test getting transaction list."""
        # Create some transactions first
        client.post("/api/transactions", json={
            "amount": 50.0,
            "transaction_type": "expense",
            "category": "Food",
        })
        client.post("/api/transactions", json={
            "amount": 100.0,
            "transaction_type": "income",
            "category": "Salary",
        })

        response = client.get("/api/transactions")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["transactions"]) == 2

    def test_get_transactions_pagination(self, client):
        """Test pagination works."""
        for i in range(5):
            client.post("/api/transactions", json={
                "amount": 10.0 * (i + 1),
                "transaction_type": "expense",
                "category": "Food",
            })

        response = client.get("/api/transactions?page=1&page_size=2")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5
        assert len(data["transactions"]) == 2
        assert data["page"] == 1
        assert data["page_size"] == 2

    def test_get_transactions_filter_by_category(self, client):
        """Test filtering by category."""
        client.post("/api/transactions", json={
            "amount": 50.0,
            "transaction_type": "expense",
            "category": "Food",
        })
        client.post("/api/transactions", json={
            "amount": 30.0,
            "transaction_type": "expense",
            "category": "Transportation",
        })

        response = client.get("/api/transactions?category=Food")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["transactions"][0]["category"] == "Food"

    def test_get_single_transaction(self, client):
        """Test getting a single transaction by ID."""
        create_resp = client.post("/api/transactions", json={
            "amount": 75.0,
            "transaction_type": "expense",
            "category": "Shopping",
            "description": "New book",
        })
        txn_id = create_resp.json()["id"]

        response = client.get(f"/api/transactions/{txn_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == txn_id
        assert data["amount"] == 75.0

    def test_get_nonexistent_transaction(self, client):
        """Test 404 for nonexistent transaction."""
        response = client.get("/api/transactions/99999")
        assert response.status_code == 404

    def test_update_transaction(self, client):
        """Test updating a transaction."""
        create_resp = client.post("/api/transactions", json={
            "amount": 50.0,
            "transaction_type": "expense",
            "category": "Food",
        })
        txn_id = create_resp.json()["id"]

        response = client.put(f"/api/transactions/{txn_id}", json={
            "amount": 75.0,
            "category": "Shopping",
            "description": "Updated description",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["amount"] == 75.0
        assert data["category"] == "Shopping"
        assert data["description"] == "Updated description"

    def test_update_nonexistent_transaction(self, client):
        """Test 404 when updating nonexistent transaction."""
        response = client.put("/api/transactions/99999", json={
            "amount": 50.0,
        })
        assert response.status_code == 404

    def test_delete_transaction(self, client):
        """Test deleting a transaction."""
        create_resp = client.post("/api/transactions", json={
            "amount": 50.0,
            "transaction_type": "expense",
            "category": "Food",
        })
        txn_id = create_resp.json()["id"]

        response = client.delete(f"/api/transactions/{txn_id}")
        assert response.status_code == 204

        # Verify deletion
        get_resp = client.get(f"/api/transactions/{txn_id}")
        assert get_resp.status_code == 404

    def test_delete_nonexistent_transaction(self, client):
        """Test 404 when deleting nonexistent transaction."""
        response = client.delete("/api/transactions/99999")
        assert response.status_code == 404


class TestTransactionService:
    """Test transaction service functions directly."""

    def test_calculate_balance(self, db_session):
        from app.services.transaction_service import calculate_balance, create_transaction

        create_transaction(db_session, 1, 5000, "income", "Salary")
        create_transaction(db_session, 1, 1000, "expense", "Food")
        create_transaction(db_session, 1, 500, "expense", "Transportation")

        balance = calculate_balance(db_session, 1)
        assert balance["total_income"] == 5000.0
        assert balance["total_expense"] == 1500.0
        assert balance["balance"] == 3500.0

    def test_calculate_category_spending(self, db_session):
        from app.services.transaction_service import (
            calculate_category_spending, create_transaction
        )

        create_transaction(db_session, 1, 300, "expense", "Food")
        create_transaction(db_session, 1, 200, "expense", "Food")
        create_transaction(db_session, 1, 100, "expense", "Transportation")

        categories = calculate_category_spending(db_session, 1)
        food = next(c for c in categories if c["category"] == "Food")
        transport = next(c for c in categories if c["category"] == "Transportation")

        assert food["total"] == 500.0
        assert transport["total"] == 100.0
        assert abs(food["percentage"] - 83.3) < 0.5

    def test_empty_balance(self, db_session):
        from app.services.transaction_service import calculate_balance

        balance = calculate_balance(db_session, 1)
        assert balance["total_income"] == 0.0
        assert balance["total_expense"] == 0.0
        assert balance["balance"] == 0.0
