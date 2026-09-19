"""
Tests for chat API endpoint.
"""

import pytest


class TestChatAPI:
    """Test chat endpoint."""

    def test_chat_endpoint(self, client):
        """Test that chat endpoint accepts messages and returns response."""
        response = client.post("/api/chat", json={
            "message": "Hello, what can you do?",
            "user_id": 1,
        })
        assert response.status_code == 200
        data = response.json()
        assert "reply" in data
        # Reply should not be empty even if AI is not configured
        assert len(data["reply"]) > 0

    def test_chat_empty_message(self, client):
        """Test that empty message is rejected."""
        response = client.post("/api/chat", json={
            "message": "",
            "user_id": 1,
        })
        assert response.status_code == 422

    def test_chat_long_message(self, client):
        """Test that excessively long message is rejected."""
        response = client.post("/api/chat", json={
            "message": "x" * 2001,
            "user_id": 1,
        })
        assert response.status_code == 422

    def test_chat_response_structure(self, client):
        """Test that response has correct structure."""
        response = client.post("/api/chat", json={
            "message": "How much did I spend?",
            "user_id": 1,
        })
        assert response.status_code == 200
        data = response.json()
        assert "reply" in data
        assert "action_taken" in data
        assert "data" in data


class TestHealthCheck:
    """Test health check endpoint."""

    def test_health_check(self, client):
        """Test health endpoint returns healthy status."""
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "app" in data
        assert "version" in data
