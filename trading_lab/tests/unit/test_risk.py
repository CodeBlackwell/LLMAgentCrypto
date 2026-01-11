"""Unit tests for risk management."""

from __future__ import annotations

import pytest
from datetime import date

from trading_lab.core.signals import Signal
from trading_lab.core.risk import (
    RiskState,
    RiskDecision,
    RiskRule,
    MaxPositionSizeRule,
    StopLossRule,
    TakeProfitRule,
    DrawdownCircuitBreaker,
    DailyLossLimit,
    RiskManager,
    create_default_risk_manager,
    create_aggressive_risk_manager,
    create_conservative_risk_manager,
)


class TestRiskState:
    """Tests for RiskState dataclass."""

    def test_default_values(self):
        """Test default state values."""
        state = RiskState()
        assert state.current_position == 0.0
        assert state.entry_price is None
        assert state.drawdown == 0.0
        assert state.daily_return == 0.0

    def test_drawdown_calculation(self):
        """Test drawdown calculation."""
        state = RiskState(
            peak_portfolio_value=100000.0,
            current_portfolio_value=90000.0,
        )
        assert state.drawdown == 0.10  # 10% drawdown

    def test_drawdown_zero_when_at_peak(self):
        """Test zero drawdown when at peak."""
        state = RiskState(
            peak_portfolio_value=100000.0,
            current_portfolio_value=100000.0,
        )
        assert state.drawdown == 0.0

    def test_drawdown_zero_when_no_peak(self):
        """Test zero drawdown when no peak value."""
        state = RiskState()
        assert state.drawdown == 0.0

    def test_daily_return_calculation(self):
        """Test daily return calculation."""
        state = RiskState(
            day_start_value=100000.0,
            current_portfolio_value=102000.0,
        )
        assert state.daily_return == 0.02  # 2% gain

    def test_daily_return_negative(self):
        """Test negative daily return."""
        state = RiskState(
            day_start_value=100000.0,
            current_portfolio_value=95000.0,
        )
        assert state.daily_return == -0.05  # 5% loss

    def test_daily_return_zero_when_no_start(self):
        """Test zero daily return when no start value."""
        state = RiskState()
        assert state.daily_return == 0.0


class TestMaxPositionSizeRule:
    """Tests for MaxPositionSizeRule."""

    def test_implements_protocol(self):
        """Test that rule implements RiskRule."""
        rule = MaxPositionSizeRule()
        assert isinstance(rule, RiskRule)

    def test_default_max_percent(self):
        """Test default max percent is 25%."""
        rule = MaxPositionSizeRule()
        assert rule.max_percent == 0.25

    def test_name_property(self):
        """Test name includes percentage."""
        rule = MaxPositionSizeRule(max_percent=0.25)
        assert "25%" in rule.name

    def test_allows_trade_within_limits(self):
        """Test trade allowed when within position limits."""
        rule = MaxPositionSizeRule(max_percent=0.25)
        state = RiskState(current_portfolio_value=100000.0)
        signal = Signal(action="buy", confidence=0.8)

        # 10 units at $100 = $1000, which is 1% of $100k
        decision = rule.evaluate(signal, quantity=10.0, price=100.0, state=state)

        assert decision.allow_trade is True
        assert decision.modified_quantity is None

    def test_reduces_quantity_when_exceeds_limit(self):
        """Test quantity reduced when exceeding limit."""
        rule = MaxPositionSizeRule(max_percent=0.25)
        state = RiskState(current_portfolio_value=100000.0)
        signal = Signal(action="buy", confidence=0.8)

        # 500 units at $100 = $50k, which is 50% (exceeds 25%)
        decision = rule.evaluate(signal, quantity=500.0, price=100.0, state=state)

        assert decision.allow_trade is True
        assert decision.modified_quantity is not None
        # Should be reduced to 25% = $25k / $100 = 250 units
        assert decision.modified_quantity == 250.0

    def test_invalid_max_percent_raises(self):
        """Test that invalid max_percent raises ValueError."""
        with pytest.raises(ValueError):
            MaxPositionSizeRule(max_percent=1.5)
        with pytest.raises(ValueError):
            MaxPositionSizeRule(max_percent=0.0)


class TestStopLossRule:
    """Tests for StopLossRule."""

    def test_default_percent(self):
        """Test default stop loss is 5%."""
        rule = StopLossRule()
        assert rule.percent == 0.05

    def test_sets_stop_loss_on_buy(self):
        """Test stop loss price set on buy signal."""
        rule = StopLossRule(percent=0.05)
        state = RiskState()
        signal = Signal(action="buy", confidence=0.8)

        decision = rule.evaluate(signal, quantity=10.0, price=100.0, state=state)

        assert decision.allow_trade is True
        assert decision.stop_loss_price == 95.0  # 100 * (1 - 0.05)

    def test_no_stop_loss_on_sell(self):
        """Test no stop loss set on sell signal."""
        rule = StopLossRule(percent=0.05)
        state = RiskState()
        signal = Signal(action="sell", confidence=0.8)

        decision = rule.evaluate(signal, quantity=10.0, price=100.0, state=state)

        assert decision.allow_trade is True
        assert decision.stop_loss_price is None

    def test_invalid_percent_raises(self):
        """Test that invalid percent raises ValueError."""
        with pytest.raises(ValueError):
            StopLossRule(percent=0.0)
        with pytest.raises(ValueError):
            StopLossRule(percent=1.0)


class TestTakeProfitRule:
    """Tests for TakeProfitRule."""

    def test_default_percent(self):
        """Test default take profit is 10%."""
        rule = TakeProfitRule()
        assert rule.percent == 0.10

    def test_sets_take_profit_on_buy(self):
        """Test take profit price set on buy signal."""
        rule = TakeProfitRule(percent=0.10)
        state = RiskState()
        signal = Signal(action="buy", confidence=0.8)

        decision = rule.evaluate(signal, quantity=10.0, price=100.0, state=state)

        assert decision.allow_trade is True
        assert decision.take_profit_price == pytest.approx(110.0)  # 100 * (1 + 0.10)

    def test_no_take_profit_on_sell(self):
        """Test no take profit set on sell signal."""
        rule = TakeProfitRule(percent=0.10)
        state = RiskState()
        signal = Signal(action="sell", confidence=0.8)

        decision = rule.evaluate(signal, quantity=10.0, price=100.0, state=state)

        assert decision.allow_trade is True
        assert decision.take_profit_price is None


class TestDrawdownCircuitBreaker:
    """Tests for DrawdownCircuitBreaker."""

    def test_default_max_drawdown(self):
        """Test default max drawdown is 20%."""
        rule = DrawdownCircuitBreaker()
        assert rule.max_drawdown == 0.20

    def test_allows_trade_within_limits(self):
        """Test trade allowed when drawdown within limits."""
        rule = DrawdownCircuitBreaker(max_drawdown=0.20)
        state = RiskState(
            peak_portfolio_value=100000.0,
            current_portfolio_value=90000.0,  # 10% drawdown
        )
        signal = Signal(action="buy", confidence=0.8)

        decision = rule.evaluate(signal, quantity=10.0, price=100.0, state=state)

        assert decision.allow_trade is True

    def test_blocks_trade_when_exceeds_limit(self):
        """Test trade blocked when drawdown exceeds limit."""
        rule = DrawdownCircuitBreaker(max_drawdown=0.20)
        state = RiskState(
            peak_portfolio_value=100000.0,
            current_portfolio_value=75000.0,  # 25% drawdown
        )
        signal = Signal(action="buy", confidence=0.8)

        decision = rule.evaluate(signal, quantity=10.0, price=100.0, state=state)

        assert decision.allow_trade is False
        assert "drawdown" in decision.reason.lower()

    def test_invalid_max_drawdown_raises(self):
        """Test that invalid max_drawdown raises ValueError."""
        with pytest.raises(ValueError):
            DrawdownCircuitBreaker(max_drawdown=0.0)
        with pytest.raises(ValueError):
            DrawdownCircuitBreaker(max_drawdown=1.0)


class TestDailyLossLimit:
    """Tests for DailyLossLimit."""

    def test_default_max_loss(self):
        """Test default max daily loss is 5%."""
        rule = DailyLossLimit()
        assert rule.max_daily_loss == 0.05

    def test_allows_trade_within_limits(self):
        """Test trade allowed when daily loss within limits."""
        rule = DailyLossLimit(max_daily_loss=0.05)
        state = RiskState(
            day_start_value=100000.0,
            current_portfolio_value=98000.0,  # 2% loss
        )
        signal = Signal(action="buy", confidence=0.8)

        decision = rule.evaluate(signal, quantity=10.0, price=100.0, state=state)

        assert decision.allow_trade is True

    def test_blocks_trade_when_exceeds_limit(self):
        """Test trade blocked when daily loss exceeds limit."""
        rule = DailyLossLimit(max_daily_loss=0.05)
        state = RiskState(
            day_start_value=100000.0,
            current_portfolio_value=94000.0,  # 6% loss
        )
        signal = Signal(action="buy", confidence=0.8)

        decision = rule.evaluate(signal, quantity=10.0, price=100.0, state=state)

        assert decision.allow_trade is False
        assert "daily" in decision.reason.lower()


class TestRiskManager:
    """Tests for RiskManager."""

    def test_empty_manager_allows_trade(self):
        """Test manager with no rules allows trades."""
        manager = RiskManager()
        signal = Signal(action="buy", confidence=0.8)

        decision = manager.evaluate_trade(signal, quantity=10.0, price=100.0)

        assert decision.allow_trade is True

    def test_add_rule_fluent(self):
        """Test fluent interface for adding rules."""
        manager = (
            RiskManager()
            .add_rule(MaxPositionSizeRule())
            .add_rule(StopLossRule())
        )

        assert len(manager.rules) == 2

    def test_all_rules_must_pass(self):
        """Test that all rules must pass for trade to be allowed."""
        manager = RiskManager([
            MaxPositionSizeRule(max_percent=0.25),
            DrawdownCircuitBreaker(max_drawdown=0.20),
        ])
        manager.state.peak_portfolio_value = 100000.0
        manager.state.current_portfolio_value = 75000.0  # 25% drawdown

        signal = Signal(action="buy", confidence=0.8)
        decision = manager.evaluate_trade(signal, quantity=10.0, price=100.0)

        assert decision.allow_trade is False

    def test_quantity_modifications_accumulate(self):
        """Test that quantity modifications are cumulative (takes minimum)."""
        manager = RiskManager([
            MaxPositionSizeRule(max_percent=0.30),  # Would allow 300 units
            MaxPositionSizeRule(max_percent=0.20),  # Would allow 200 units
        ])
        manager.state.current_portfolio_value = 100000.0

        signal = Signal(action="buy", confidence=0.8)
        # Request 500 units at $100 = $50k
        decision = manager.evaluate_trade(signal, quantity=500.0, price=100.0)

        assert decision.allow_trade is True
        assert decision.modified_quantity == 200.0  # Takes the more restrictive

    def test_stop_loss_and_take_profit_set(self):
        """Test that stop loss and take profit are set from rules."""
        manager = RiskManager([
            StopLossRule(percent=0.05),
            TakeProfitRule(percent=0.10),
        ])

        signal = Signal(action="buy", confidence=0.8)
        decision = manager.evaluate_trade(signal, quantity=10.0, price=100.0)

        assert decision.stop_loss_price == pytest.approx(95.0)
        assert decision.take_profit_price == pytest.approx(110.0)

    def test_update_state_sets_values(self):
        """Test update_state updates values correctly."""
        manager = RiskManager()
        manager.update_state(portfolio_value=100000.0, position=10.0, entry_price=50.0)

        assert manager.state.current_portfolio_value == 100000.0
        assert manager.state.current_position == 10.0
        assert manager.state.entry_price == 50.0
        assert manager.state.peak_portfolio_value == 100000.0

    def test_update_state_tracks_peak(self):
        """Test that update_state tracks peak portfolio value."""
        manager = RiskManager()
        manager.update_state(portfolio_value=100000.0)
        manager.update_state(portfolio_value=110000.0)
        manager.update_state(portfolio_value=105000.0)

        assert manager.state.peak_portfolio_value == 110000.0

    def test_check_stop_loss(self):
        """Test stop loss trigger check."""
        manager = RiskManager()
        manager.state.stop_loss_price = 95.0

        assert manager.check_stop_loss(94.0) is True
        assert manager.check_stop_loss(95.0) is True
        assert manager.check_stop_loss(96.0) is False

    def test_check_take_profit(self):
        """Test take profit trigger check."""
        manager = RiskManager()
        manager.state.take_profit_price = 110.0

        assert manager.check_take_profit(111.0) is True
        assert manager.check_take_profit(110.0) is True
        assert manager.check_take_profit(109.0) is False

    def test_reset_exit_prices(self):
        """Test resetting exit prices."""
        manager = RiskManager()
        manager.state.stop_loss_price = 95.0
        manager.state.take_profit_price = 110.0

        manager.reset_exit_prices()

        assert manager.state.stop_loss_price is None
        assert manager.state.take_profit_price is None


class TestFactoryFunctions:
    """Tests for risk manager factory functions."""

    def test_create_default_risk_manager(self):
        """Test default risk manager creation."""
        manager = create_default_risk_manager()
        assert len(manager.rules) == 5
        rule_names = [r.name for r in manager.rules]
        assert any("position" in n.lower() for n in rule_names)
        assert any("stop" in n.lower() for n in rule_names)
        assert any("profit" in n.lower() for n in rule_names)
        assert any("drawdown" in n.lower() for n in rule_names)
        assert any("daily" in n.lower() for n in rule_names)

    def test_create_aggressive_risk_manager(self):
        """Test aggressive risk manager creation."""
        manager = create_aggressive_risk_manager()
        assert len(manager.rules) == 4
        # Aggressive should have higher limits
        for rule in manager.rules:
            if isinstance(rule, MaxPositionSizeRule):
                assert rule.max_percent == 0.50
            if isinstance(rule, DrawdownCircuitBreaker):
                assert rule.max_drawdown == 0.30

    def test_create_conservative_risk_manager(self):
        """Test conservative risk manager creation."""
        manager = create_conservative_risk_manager()
        assert len(manager.rules) == 5
        # Conservative should have lower limits
        for rule in manager.rules:
            if isinstance(rule, MaxPositionSizeRule):
                assert rule.max_percent == 0.10
            if isinstance(rule, DrawdownCircuitBreaker):
                assert rule.max_drawdown == 0.10
