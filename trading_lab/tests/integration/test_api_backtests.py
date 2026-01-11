"""Integration tests for backtest API endpoints."""

from __future__ import annotations

import pytest
from unittest.mock import patch, AsyncMock


class TestListBacktests:
    """Tests for GET /api/backtests endpoint."""

    def test_list_backtests_returns_200(self, test_client):
        """Test that endpoint returns 200 OK."""
        response = test_client.get("/api/backtests")
        assert response.status_code == 200

    def test_list_backtests_has_backtests_key(self, test_client):
        """Test that response has 'backtests' key."""
        response = test_client.get("/api/backtests")
        data = response.json()
        assert "backtests" in data
        assert isinstance(data["backtests"], list)

    def test_list_backtests_has_total(self, test_client):
        """Test that response includes total count."""
        response = test_client.get("/api/backtests")
        data = response.json()
        assert "total" in data
        assert isinstance(data["total"], int)


class TestCreateBacktest:
    """Tests for POST /api/backtests endpoint."""

    def test_create_backtest_returns_200(self, test_client, backtest_config):
        """Test that creating a backtest returns 200."""
        # Mock the runner.submit to avoid actual backtest execution
        with patch("trading_lab.api.routes.backtests.get_runner") as mock_get_runner:
            mock_runner = mock_get_runner.return_value
            mock_runner.submit = AsyncMock(return_value=1)

            response = test_client.post("/api/backtests", json=backtest_config)
            assert response.status_code == 200

    def test_create_backtest_returns_id(self, test_client, backtest_config):
        """Test that response includes backtest_id."""
        with patch("trading_lab.api.routes.backtests.get_runner") as mock_get_runner:
            mock_runner = mock_get_runner.return_value
            mock_runner.submit = AsyncMock(return_value=42)

            response = test_client.post("/api/backtests", json=backtest_config)
            data = response.json()
            assert "backtest_id" in data
            assert data["backtest_id"] == 42

    def test_create_backtest_returns_pending_status(self, test_client, backtest_config):
        """Test that status is pending after creation."""
        with patch("trading_lab.api.routes.backtests.get_runner") as mock_get_runner:
            mock_runner = mock_get_runner.return_value
            mock_runner.submit = AsyncMock(return_value=1)

            response = test_client.post("/api/backtests", json=backtest_config)
            data = response.json()
            assert data["status"] == "pending"

    def test_create_backtest_includes_message(self, test_client, backtest_config):
        """Test that response includes helpful message."""
        with patch("trading_lab.api.routes.backtests.get_runner") as mock_get_runner:
            mock_runner = mock_get_runner.return_value
            mock_runner.submit = AsyncMock(return_value=1)

            response = test_client.post("/api/backtests", json=backtest_config)
            data = response.json()
            assert "message" in data

    def test_create_backtest_missing_required_field(self, test_client):
        """Test that missing required field returns 422."""
        incomplete_config = {
            "strategy_name": "random",
            # Missing asset, start_date, end_date
        }
        response = test_client.post("/api/backtests", json=incomplete_config)
        assert response.status_code == 422


class TestGetBacktest:
    """Tests for GET /api/backtests/{id} endpoint."""

    def test_get_nonexistent_backtest_returns_404(self, test_client):
        """Test that nonexistent backtest returns 404."""
        response = test_client.get("/api/backtests/99999")
        assert response.status_code == 404


class TestDeleteBacktest:
    """Tests for DELETE /api/backtests/{id} endpoint."""

    def test_delete_nonexistent_returns_404(self, test_client):
        """Test deleting nonexistent backtest returns 404."""
        response = test_client.delete("/api/backtests/99999")
        assert response.status_code == 404


class TestCancelBacktest:
    """Tests for POST /api/backtests/{id}/cancel endpoint."""

    def test_cancel_nonexistent_returns_400(self, test_client):
        """Test cancelling nonexistent/non-running backtest."""
        response = test_client.post("/api/backtests/99999/cancel")
        assert response.status_code == 400

    def test_cancel_response_has_detail(self, test_client):
        """Test that cancel error includes detail."""
        response = test_client.post("/api/backtests/99999/cancel")
        data = response.json()
        assert "detail" in data


class TestBacktestFiltering:
    """Tests for backtest list filtering."""

    def test_filter_by_nonexistent_strategy(self, test_client):
        """Test filtering by nonexistent strategy returns empty."""
        response = test_client.get(
            "/api/backtests",
            params={"strategy_name": "nonexistent_xyz"}
        )
        data = response.json()
        assert data["backtests"] == []

    def test_pagination_limit(self, test_client):
        """Test limit parameter."""
        response = test_client.get("/api/backtests", params={"limit": 5})
        assert response.status_code == 200

    def test_pagination_offset(self, test_client):
        """Test offset parameter."""
        response = test_client.get("/api/backtests", params={"offset": 10})
        assert response.status_code == 200
