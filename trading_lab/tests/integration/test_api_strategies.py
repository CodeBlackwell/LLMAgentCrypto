"""Integration tests for strategy API endpoints."""

from __future__ import annotations

import pytest


class TestListStrategies:
    """Tests for GET /api/strategies endpoint."""

    def test_list_strategies_returns_200(self, test_client):
        """Test that endpoint returns 200 OK."""
        response = test_client.get("/api/strategies")
        assert response.status_code == 200

    def test_list_strategies_returns_json(self, test_client):
        """Test that endpoint returns JSON."""
        response = test_client.get("/api/strategies")
        assert response.headers["content-type"] == "application/json"

    def test_list_strategies_has_strategies_key(self, test_client):
        """Test that response has 'strategies' key."""
        response = test_client.get("/api/strategies")
        data = response.json()
        assert "strategies" in data

    def test_list_strategies_returns_list(self, test_client):
        """Test that strategies is a list."""
        response = test_client.get("/api/strategies")
        data = response.json()
        assert isinstance(data["strategies"], list)

    def test_list_strategies_not_empty(self, test_client):
        """Test that strategies list is not empty."""
        response = test_client.get("/api/strategies")
        data = response.json()
        assert len(data["strategies"]) > 0

    def test_list_strategies_includes_random(self, test_client):
        """Test that 'random' strategy is included."""
        response = test_client.get("/api/strategies")
        data = response.json()
        names = [s["name"] for s in data["strategies"]]
        assert "random" in names

    def test_strategy_has_required_fields(self, test_client):
        """Test that each strategy has required fields."""
        response = test_client.get("/api/strategies")
        data = response.json()

        for strategy in data["strategies"]:
            assert "name" in strategy
            assert "description" in strategy
            assert "default_provider" in strategy
            assert "asset_types" in strategy
            assert "class_name" in strategy

    def test_strategy_asset_types_is_list(self, test_client):
        """Test that asset_types is a list."""
        response = test_client.get("/api/strategies")
        data = response.json()

        for strategy in data["strategies"]:
            assert isinstance(strategy["asset_types"], list)


class TestGetStrategy:
    """Tests for GET /api/strategies/{name} endpoint."""

    def test_get_existing_strategy_returns_200(self, test_client):
        """Test that existing strategy returns 200."""
        response = test_client.get("/api/strategies/random")
        assert response.status_code == 200

    def test_get_existing_strategy_returns_data(self, test_client):
        """Test that existing strategy returns correct data."""
        response = test_client.get("/api/strategies/random")
        data = response.json()

        assert data["name"] == "random"
        assert "description" in data
        assert "default_provider" in data
        assert "asset_types" in data
        assert "class_name" in data

    def test_get_nonexistent_strategy_returns_404(self, test_client):
        """Test that nonexistent strategy returns 404."""
        response = test_client.get("/api/strategies/nonexistent_xyz")
        assert response.status_code == 404

    def test_get_nonexistent_strategy_has_detail(self, test_client):
        """Test that 404 response includes detail message."""
        response = test_client.get("/api/strategies/nonexistent_xyz")
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()

    def test_get_strategy_name_matches_request(self, test_client):
        """Test that returned name matches requested name."""
        response = test_client.get("/api/strategies/random")
        data = response.json()
        assert data["name"] == "random"


class TestHealthEndpoint:
    """Tests for health check endpoint."""

    def test_health_returns_200(self, test_client):
        """Test that health endpoint returns 200."""
        response = test_client.get("/health")
        assert response.status_code == 200

    def test_health_returns_healthy_status(self, test_client):
        """Test that health returns healthy status."""
        response = test_client.get("/health")
        data = response.json()
        assert data["status"] == "healthy"


class TestRootEndpoint:
    """Tests for root endpoint."""

    def test_root_returns_200(self, test_client):
        """Test that root endpoint returns 200."""
        response = test_client.get("/")
        assert response.status_code == 200

    def test_root_returns_api_info(self, test_client):
        """Test that root returns API info."""
        response = test_client.get("/")
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert data["name"] == "Trading Lab API"
