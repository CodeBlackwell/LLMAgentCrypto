"""Unit tests for strategy registry."""

from __future__ import annotations

import pytest
from lumibot.strategies.strategy import Strategy

from trading_lab.strategies.registry import (
    register,
    get_strategy,
    list_strategies,
    get_strategy_info,
    get_all_strategies_info,
    _registry,
    _metadata,
)


class TestRegisterDecorator:
    """Tests for the @register decorator."""

    def test_register_adds_to_registry(self):
        """Test that @register adds class to registry."""
        # Clear existing test registrations
        test_name = "_test_strategy_1"
        if test_name in _registry:
            del _registry[test_name]
            del _metadata[test_name]

        @register(name=test_name, description="Test strategy")
        class TestStrategy(Strategy):
            pass

        assert test_name in _registry
        assert _registry[test_name] is TestStrategy

        # Cleanup
        del _registry[test_name]
        del _metadata[test_name]

    def test_register_stores_metadata(self):
        """Test that @register stores metadata."""
        test_name = "_test_strategy_2"
        if test_name in _registry:
            del _registry[test_name]
            del _metadata[test_name]

        @register(
            name=test_name,
            description="Test description",
            default_provider="test_provider",
            asset_types=["crypto", "stock"]
        )
        class TestStrategy(Strategy):
            pass

        assert test_name in _metadata
        assert _metadata[test_name]["description"] == "Test description"
        assert _metadata[test_name]["default_provider"] == "test_provider"
        assert _metadata[test_name]["asset_types"] == ["crypto", "stock"]
        assert _metadata[test_name]["class_name"] == "TestStrategy"

        # Cleanup
        del _registry[test_name]
        del _metadata[test_name]

    def test_register_default_asset_types(self):
        """Test that @register uses default asset types."""
        test_name = "_test_strategy_3"
        if test_name in _registry:
            del _registry[test_name]
            del _metadata[test_name]

        @register(name=test_name)
        class TestStrategy(Strategy):
            pass

        assert _metadata[test_name]["asset_types"] == ["crypto", "stock", "forex"]

        # Cleanup
        del _registry[test_name]
        del _metadata[test_name]

    def test_register_returns_class(self):
        """Test that @register returns the decorated class unchanged."""
        test_name = "_test_strategy_4"
        if test_name in _registry:
            del _registry[test_name]
            del _metadata[test_name]

        @register(name=test_name)
        class TestStrategy(Strategy):
            custom_attr = "test"

        assert TestStrategy.custom_attr == "test"
        assert _registry[test_name] is TestStrategy

        # Cleanup
        del _registry[test_name]
        del _metadata[test_name]


class TestGetStrategy:
    """Tests for get_strategy function."""

    def test_get_existing_strategy(self):
        """Test getting an existing strategy."""
        # The 'random' strategy should be registered from imports
        from trading_lab.strategies import random  # Ensure registered

        strategy_class = get_strategy("random")
        assert strategy_class is not None
        assert issubclass(strategy_class, Strategy)

    def test_get_nonexistent_strategy_raises(self):
        """Test that missing strategy raises KeyError."""
        with pytest.raises(KeyError) as exc_info:
            get_strategy("nonexistent_strategy_xyz")

        assert "nonexistent_strategy_xyz" in str(exc_info.value)
        assert "not found" in str(exc_info.value)

    def test_keyerror_includes_available_strategies(self):
        """Test that KeyError message includes available strategies."""
        from trading_lab.strategies import random  # Ensure registered

        with pytest.raises(KeyError) as exc_info:
            get_strategy("missing")

        error_msg = str(exc_info.value)
        assert "Available:" in error_msg


class TestListStrategies:
    """Tests for list_strategies function."""

    def test_returns_list(self):
        """Test that list_strategies returns a list."""
        from trading_lab.strategies import random  # Ensure registered

        strategies = list_strategies()
        assert isinstance(strategies, list)

    def test_includes_registered_strategies(self):
        """Test that list includes registered strategies."""
        from trading_lab.strategies import random  # Ensure registered

        strategies = list_strategies()
        assert "random" in strategies

    def test_list_is_not_empty(self):
        """Test that list is not empty after imports."""
        from trading_lab.strategies import random, sentiment  # Ensure registered

        strategies = list_strategies()
        assert len(strategies) > 0


class TestGetStrategyInfo:
    """Tests for get_strategy_info function."""

    def test_get_info_for_existing_strategy(self):
        """Test getting info for an existing strategy."""
        from trading_lab.strategies import random  # Ensure registered

        info = get_strategy_info("random")
        assert isinstance(info, dict)
        assert "description" in info
        assert "default_provider" in info
        assert "asset_types" in info
        assert "class_name" in info

    def test_get_info_for_nonexistent_raises(self):
        """Test that missing strategy raises KeyError."""
        with pytest.raises(KeyError) as exc_info:
            get_strategy_info("nonexistent_xyz")

        assert "not found" in str(exc_info.value)

    def test_info_is_copy(self):
        """Test that returned info is a copy, not the original."""
        from trading_lab.strategies import random  # Ensure registered

        info1 = get_strategy_info("random")
        info2 = get_strategy_info("random")

        # Modify one
        info1["test_key"] = "test_value"

        # Other should be unaffected
        assert "test_key" not in info2


class TestGetAllStrategiesInfo:
    """Tests for get_all_strategies_info function."""

    def test_returns_dict(self):
        """Test that function returns a dict."""
        from trading_lab.strategies import random  # Ensure registered

        all_info = get_all_strategies_info()
        assert isinstance(all_info, dict)

    def test_includes_all_registered(self):
        """Test that dict includes all registered strategies."""
        from trading_lab.strategies import random, sentiment  # Ensure registered

        all_info = get_all_strategies_info()
        assert "random" in all_info

    def test_each_entry_has_required_keys(self):
        """Test that each entry has required keys."""
        from trading_lab.strategies import random  # Ensure registered

        all_info = get_all_strategies_info()

        for name, info in all_info.items():
            assert "description" in info, f"{name} missing description"
            assert "default_provider" in info, f"{name} missing default_provider"
            assert "asset_types" in info, f"{name} missing asset_types"
            assert "class_name" in info, f"{name} missing class_name"

    def test_returned_dict_is_copy(self):
        """Test that returned dict is a copy."""
        from trading_lab.strategies import random  # Ensure registered

        all_info1 = get_all_strategies_info()
        all_info2 = get_all_strategies_info()

        # Modify one
        all_info1["random"]["test_key"] = "test"

        # Other should be unaffected
        assert "test_key" not in all_info2.get("random", {})


class TestRegistryIntegration:
    """Integration tests for the registry system."""

    def test_registered_strategies_are_valid_classes(self):
        """Test that all registered strategies are valid Strategy subclasses."""
        from trading_lab.strategies import random, sentiment, contrarian

        for name in list_strategies():
            strategy_class = get_strategy(name)
            assert issubclass(strategy_class, Strategy), f"{name} is not a Strategy subclass"

    def test_strategy_info_matches_class(self):
        """Test that strategy info class_name matches actual class."""
        from trading_lab.strategies import random

        for name in list_strategies():
            info = get_strategy_info(name)
            strategy_class = get_strategy(name)
            assert info["class_name"] == strategy_class.__name__
