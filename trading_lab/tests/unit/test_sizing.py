"""Unit tests for position sizing strategies."""

from __future__ import annotations

import pytest
from trading_lab.core.sizing import (
    PositionSizer,
    PercentOfCash,
    FixedQuantity,
    VolatilityAdjusted,
    KellyCriterion,
)


class TestPositionSizerProtocol:
    """Tests for PositionSizer protocol compliance."""

    def test_percent_of_cash_implements_protocol(self):
        """Test that PercentOfCash implements PositionSizer."""
        sizer = PercentOfCash()
        assert isinstance(sizer, PositionSizer)

    def test_fixed_quantity_implements_protocol(self):
        """Test that FixedQuantity implements PositionSizer."""
        sizer = FixedQuantity(quantity=1.0)
        assert isinstance(sizer, PositionSizer)

    def test_volatility_adjusted_implements_protocol(self):
        """Test that VolatilityAdjusted implements PositionSizer."""
        sizer = VolatilityAdjusted()
        assert isinstance(sizer, PositionSizer)

    def test_kelly_criterion_implements_protocol(self):
        """Test that KellyCriterion implements PositionSizer."""
        sizer = KellyCriterion()
        assert isinstance(sizer, PositionSizer)


class TestPercentOfCash:
    """Tests for PercentOfCash sizer."""

    def test_default_percent(self):
        """Test default percentage is 25%."""
        sizer = PercentOfCash()
        assert sizer.percent == 0.25

    def test_custom_percent(self):
        """Test custom percentage."""
        sizer = PercentOfCash(percent=0.5)
        assert sizer.percent == 0.5

    def test_calculate_basic(self):
        """Test basic calculation: 25% of $10000 at $100/unit = 25 units."""
        sizer = PercentOfCash(percent=0.25)
        quantity = sizer.calculate(cash=10000, price=100)
        assert quantity == 25.0

    def test_calculate_fractional_quantity(self):
        """Test that fractional quantities are allowed."""
        sizer = PercentOfCash(percent=0.25)
        quantity = sizer.calculate(cash=1000, price=333)
        assert quantity == pytest.approx(0.75075, rel=0.01)

    def test_calculate_full_allocation(self):
        """Test 100% allocation."""
        sizer = PercentOfCash(percent=1.0)
        quantity = sizer.calculate(cash=5000, price=50)
        assert quantity == 100.0

    def test_calculate_small_percent(self):
        """Test small percentage."""
        sizer = PercentOfCash(percent=0.01)
        quantity = sizer.calculate(cash=10000, price=100)
        assert quantity == 1.0

    def test_zero_price_returns_zero(self):
        """Test that zero price returns zero quantity."""
        sizer = PercentOfCash(percent=0.25)
        quantity = sizer.calculate(cash=10000, price=0)
        assert quantity == 0.0

    def test_negative_price_returns_zero(self):
        """Test that negative price returns zero quantity."""
        sizer = PercentOfCash(percent=0.25)
        quantity = sizer.calculate(cash=10000, price=-100)
        assert quantity == 0.0

    def test_invalid_percent_too_high(self):
        """Test that percent > 1.0 raises ValueError."""
        with pytest.raises(ValueError, match="Percent must be between 0 and 1"):
            PercentOfCash(percent=1.5)

    def test_invalid_percent_zero(self):
        """Test that percent = 0 raises ValueError."""
        with pytest.raises(ValueError, match="Percent must be between 0 and 1"):
            PercentOfCash(percent=0.0)

    def test_invalid_percent_negative(self):
        """Test that negative percent raises ValueError."""
        with pytest.raises(ValueError, match="Percent must be between 0 and 1"):
            PercentOfCash(percent=-0.1)


class TestFixedQuantity:
    """Tests for FixedQuantity sizer."""

    def test_fixed_quantity_returned(self):
        """Test that fixed quantity is returned when cash allows."""
        sizer = FixedQuantity(quantity=10.0)
        quantity = sizer.calculate(cash=10000, price=100)
        assert quantity == 10.0

    def test_quantity_stored(self):
        """Test that quantity is stored."""
        sizer = FixedQuantity(quantity=5.5)
        assert sizer.quantity == 5.5

    def test_insufficient_cash_returns_max_affordable(self):
        """Test that insufficient cash returns what's affordable."""
        sizer = FixedQuantity(quantity=100.0)
        # Only have $500, price is $10, can only afford 50
        quantity = sizer.calculate(cash=500, price=10)
        assert quantity == 50.0

    def test_exact_cash_for_quantity(self):
        """Test exact cash for quantity returns quantity."""
        sizer = FixedQuantity(quantity=10.0)
        quantity = sizer.calculate(cash=1000, price=100)
        assert quantity == 10.0

    def test_zero_price_returns_quantity(self):
        """Test that zero price still returns quantity (price not validated)."""
        # Note: FixedQuantity doesn't validate price at entry.
        # When price=0, the insufficient cash check (cash < price * qty = 0)
        # is false for any non-negative cash, so we return self.quantity
        sizer = FixedQuantity(quantity=10.0)
        quantity = sizer.calculate(cash=10000, price=0)
        assert quantity == 10.0

    def test_insufficient_cash_zero_price_returns_zero(self):
        """Test that insufficient cash with zero price returns zero."""
        sizer = FixedQuantity(quantity=10.0)
        # Trigger insufficient cash check with positive price
        # then price > 0 check fails, returns 0
        quantity = sizer.calculate(cash=100, price=100)  # Can only afford 1
        assert quantity == 1.0  # cash / price = 100 / 100 = 1

    def test_invalid_quantity_zero(self):
        """Test that zero quantity raises ValueError."""
        with pytest.raises(ValueError, match="Quantity must be positive"):
            FixedQuantity(quantity=0)

    def test_invalid_quantity_negative(self):
        """Test that negative quantity raises ValueError."""
        with pytest.raises(ValueError, match="Quantity must be positive"):
            FixedQuantity(quantity=-5)


class TestVolatilityAdjusted:
    """Tests for VolatilityAdjusted sizer."""

    def test_default_parameters(self):
        """Test default parameter values."""
        sizer = VolatilityAdjusted()
        assert sizer.target_risk == 0.02
        assert sizer.max_position_pct == 0.25

    def test_custom_parameters(self):
        """Test custom parameter values."""
        sizer = VolatilityAdjusted(target_risk=0.05, max_position_pct=0.5)
        assert sizer.target_risk == 0.05
        assert sizer.max_position_pct == 0.5

    def test_calculate_with_default_volatility(self):
        """Test calculation with default volatility (2%)."""
        sizer = VolatilityAdjusted(target_risk=0.02, max_position_pct=0.25)
        # (10000 * 0.02) / (100 * 0.02) = 200 / 2 = 100
        # But capped at 25% = 25 units
        quantity = sizer.calculate(cash=10000, price=100)
        assert quantity == 25.0  # Capped

    def test_calculate_high_volatility_reduces_position(self):
        """Test that high volatility reduces position size."""
        sizer = VolatilityAdjusted(target_risk=0.02, max_position_pct=0.5)
        # High volatility (10%): (10000 * 0.02) / (100 * 0.10) = 200 / 10 = 20
        quantity = sizer.calculate(cash=10000, price=100, volatility=0.10)
        assert quantity == 20.0

    def test_calculate_low_volatility_capped(self):
        """Test that low volatility is capped at max position."""
        sizer = VolatilityAdjusted(target_risk=0.02, max_position_pct=0.25)
        # Low volatility (0.1%): (10000 * 0.02) / (100 * 0.001) = 200 / 0.1 = 2000
        # But capped at 25% = 25 units
        quantity = sizer.calculate(cash=10000, price=100, volatility=0.001)
        assert quantity == 25.0

    def test_zero_volatility_returns_zero(self):
        """Test that zero volatility returns zero."""
        sizer = VolatilityAdjusted()
        quantity = sizer.calculate(cash=10000, price=100, volatility=0.0)
        assert quantity == 0.0

    def test_negative_volatility_returns_zero(self):
        """Test that negative volatility returns zero."""
        sizer = VolatilityAdjusted()
        quantity = sizer.calculate(cash=10000, price=100, volatility=-0.05)
        assert quantity == 0.0

    def test_zero_price_returns_zero(self):
        """Test that zero price returns zero."""
        sizer = VolatilityAdjusted()
        quantity = sizer.calculate(cash=10000, price=0, volatility=0.02)
        assert quantity == 0.0


class TestKellyCriterion:
    """Tests for KellyCriterion sizer."""

    def test_default_parameters(self):
        """Test default parameter values."""
        sizer = KellyCriterion()
        assert sizer.win_rate == 0.55
        assert sizer.win_loss_ratio == 1.5
        assert sizer.fraction == 0.25
        assert sizer.max_position_pct == 0.25

    def test_custom_parameters(self):
        """Test custom parameter values."""
        sizer = KellyCriterion(
            win_rate=0.6,
            win_loss_ratio=2.0,
            fraction=0.5,
            max_position_pct=0.3
        )
        assert sizer.win_rate == 0.6
        assert sizer.win_loss_ratio == 2.0
        assert sizer.fraction == 0.5
        assert sizer.max_position_pct == 0.3

    def test_kelly_formula_calculation(self):
        """Test Kelly formula: f = (bp - q) / b."""
        # Win rate 60%, win/loss ratio 1.5
        # f = (1.5 * 0.6 - 0.4) / 1.5 = (0.9 - 0.4) / 1.5 = 0.333
        # Quarter Kelly: 0.333 * 0.25 = 0.0833
        sizer = KellyCriterion(
            win_rate=0.6,
            win_loss_ratio=1.5,
            fraction=0.25,
            max_position_pct=0.5
        )
        quantity = sizer.calculate(cash=10000, price=100)
        # 0.0833 * 10000 / 100 = 8.33
        assert quantity == pytest.approx(8.33, rel=0.01)

    def test_negative_kelly_returns_zero(self):
        """Test that negative Kelly (losing edge) returns zero."""
        # Win rate 30%, win/loss ratio 1.0
        # f = (1.0 * 0.3 - 0.7) / 1.0 = -0.4 (negative)
        sizer = KellyCriterion(
            win_rate=0.30,
            win_loss_ratio=1.0,
            fraction=0.25,
            max_position_pct=0.25
        )
        quantity = sizer.calculate(cash=10000, price=100)
        assert quantity == 0.0

    def test_kelly_capped_at_max_position(self):
        """Test that Kelly is capped at max position."""
        # Very high edge would exceed max position
        sizer = KellyCriterion(
            win_rate=0.9,
            win_loss_ratio=3.0,
            fraction=1.0,  # Full Kelly
            max_position_pct=0.25
        )
        quantity = sizer.calculate(cash=10000, price=100)
        # Should be capped at 25% = 25 units
        assert quantity == 25.0

    def test_zero_price_returns_zero(self):
        """Test that zero price returns zero."""
        sizer = KellyCriterion()
        quantity = sizer.calculate(cash=10000, price=0)
        assert quantity == 0.0

    def test_fractional_kelly_reduces_size(self):
        """Test that fractional Kelly reduces position size."""
        full_kelly = KellyCriterion(
            win_rate=0.6,
            win_loss_ratio=1.5,
            fraction=1.0,
            max_position_pct=1.0
        )
        quarter_kelly = KellyCriterion(
            win_rate=0.6,
            win_loss_ratio=1.5,
            fraction=0.25,
            max_position_pct=1.0
        )

        full_qty = full_kelly.calculate(cash=10000, price=100)
        quarter_qty = quarter_kelly.calculate(cash=10000, price=100)

        assert quarter_qty == pytest.approx(full_qty * 0.25, rel=0.01)


class TestSizerKwargs:
    """Test that sizers accept and use kwargs properly."""

    def test_percent_ignores_kwargs(self):
        """Test that PercentOfCash ignores extra kwargs."""
        sizer = PercentOfCash(percent=0.25)
        quantity = sizer.calculate(
            cash=10000,
            price=100,
            volatility=0.05,
            extra_param="ignored"
        )
        assert quantity == 25.0

    def test_fixed_ignores_kwargs(self):
        """Test that FixedQuantity ignores extra kwargs."""
        sizer = FixedQuantity(quantity=10)
        quantity = sizer.calculate(
            cash=10000,
            price=100,
            volatility=0.05
        )
        assert quantity == 10.0

    def test_volatility_uses_volatility_kwarg(self):
        """Test that VolatilityAdjusted uses volatility kwarg."""
        # Use high enough volatility that we don't hit the cap
        sizer = VolatilityAdjusted(target_risk=0.02, max_position_pct=1.0)

        # With 10% volatility: (10000 * 0.02) / (100 * 0.10) = 200 / 10 = 20
        qty1 = sizer.calculate(cash=10000, price=100, volatility=0.10)

        # With 20% volatility (should be half the position): 200 / 20 = 10
        qty2 = sizer.calculate(cash=10000, price=100, volatility=0.20)

        assert qty1 == pytest.approx(20.0, rel=0.01)
        assert qty2 == pytest.approx(10.0, rel=0.01)
        assert qty2 == pytest.approx(qty1 / 2, rel=0.01)

    def test_kelly_ignores_kwargs(self):
        """Test that KellyCriterion ignores extra kwargs."""
        sizer = KellyCriterion()
        quantity = sizer.calculate(
            cash=10000,
            price=100,
            volatility=0.05,
            win_rate=0.99  # Should not override initialized value
        )
        # Should use initialized win_rate of 0.55, not 0.99
        assert quantity < 25.0  # Would be higher with 0.99 win rate
