"""Strategy-related API routes."""

from fastapi import APIRouter, HTTPException

from ...strategies.registry import list_strategies, get_strategy_info, get_all_strategies_info
from ..schemas import StrategyInfo, StrategyListResponse

router = APIRouter(tags=["strategies"])


@router.get("", response_model=StrategyListResponse)
async def list_all_strategies():
    """List all available trading strategies."""
    all_info = get_all_strategies_info()

    strategies = [
        StrategyInfo(name=name, **info)
        for name, info in all_info.items()
    ]

    return StrategyListResponse(strategies=strategies)


@router.get("/{name}", response_model=StrategyInfo)
async def get_strategy_details(name: str):
    """Get details about a specific strategy."""
    try:
        info = get_strategy_info(name)
        return StrategyInfo(name=name, **info)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Strategy '{name}' not found")
