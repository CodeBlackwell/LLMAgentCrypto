"""Strategy registration and discovery."""

from __future__ import annotations

from typing import Type, Callable
from lumibot.strategies.strategy import Strategy


_registry: dict[str, Type[Strategy]] = {}
_metadata: dict[str, dict] = {}


def register(
    name: str,
    description: str = "",
    default_provider: str = "random",
    asset_types: list[str] | None = None
) -> Callable[[Type[Strategy]], Type[Strategy]]:
    """Decorator to register a strategy class.

    Args:
        name: Unique strategy identifier
        description: Human-readable description
        default_provider: Default signal provider name
        asset_types: Supported asset types (default: all)

    Returns:
        Decorator function

    Example:
        @register("sentiment", description="Sentiment-based trading")
        class SentimentStrategy(BaseStrategy):
            ...
    """
    def decorator(cls: Type[Strategy]) -> Type[Strategy]:
        _registry[name] = cls
        _metadata[name] = {
            "description": description,
            "default_provider": default_provider,
            "asset_types": asset_types or ["crypto", "stock", "forex"],
            "class_name": cls.__name__,
        }
        return cls
    return decorator


def get_strategy(name: str) -> Type[Strategy]:
    """Get a registered strategy class by name.

    Args:
        name: Strategy identifier

    Returns:
        Strategy class

    Raises:
        KeyError: If strategy not found
    """
    if name not in _registry:
        available = ", ".join(_registry.keys())
        raise KeyError(f"Strategy '{name}' not found. Available: {available}")
    return _registry[name]


def list_strategies() -> list[str]:
    """Get list of all registered strategy names."""
    return list(_registry.keys())


def get_strategy_info(name: str) -> dict:
    """Get metadata for a registered strategy.

    Args:
        name: Strategy identifier

    Returns:
        Dictionary with description, default_provider, asset_types, class_name
    """
    if name not in _metadata:
        raise KeyError(f"Strategy '{name}' not found")
    return _metadata[name].copy()


def get_all_strategies_info() -> dict[str, dict]:
    """Get metadata for all registered strategies."""
    return {name: info.copy() for name, info in _metadata.items()}
