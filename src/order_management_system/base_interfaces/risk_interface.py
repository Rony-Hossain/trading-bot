# src/order_management_system/base_interfaces/risk_interface.py

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, Iterable, Optional

from ..base_types.types import (
    AccountId,
    Symbol,
    OrderSpec,  # later you can switch this to OrderIntent if you want
    OrderState,
    PositionState,
    AccountSnapshot,
    RiskLimitsConfig,
    FlattenReason,
    Greeks,
)


class RiskViolationError(Exception):
    """
    Raised when a proposed action (new order, replace, flatten) violates
    configured risk limits and must be hard-rejected.
    """


class RiskEngineInterface(ABC):
    """
    Abstract interface for the risk / safety engine.

    The ExecutionEngine MUST call into this BEFORE:
      - creating intents in the DB
      - sending anything to the BrokerAdapter

    This keeps all risk logic in one place and makes it testable in isolation.
    """

    # ---------------------------------------------------------------------
    # Configuration / limits
    # ---------------------------------------------------------------------

    @abstractmethod
    def limits(self) -> RiskLimitsConfig:
        """Return the current risk limit configuration."""

    # ---------------------------------------------------------------------
    # Order-level checks (size / PnL / counts)
    # ---------------------------------------------------------------------

    @abstractmethod
    def validate_new_order(
        self,
        account: AccountId,
        spec: OrderSpec,
        open_orders: Iterable[OrderState],
        positions: Dict[Symbol, PositionState],
        account_snapshot: Optional[AccountSnapshot],
    ) -> None:
        """
        Validate a new order against:
          - max position per symbol / notional
          - daily loss / drawdown limits
          - duplicate intent (same spec in short time)
          - max orders per second / max open orders

        Must raise RiskViolationError on hard reject.
        """

    @abstractmethod
    def validate_replace_order(
        self,
        account: AccountId,
        existing: OrderState,
        new_spec: OrderSpec,
        positions: Dict[Symbol, PositionState],
        account_snapshot: Optional[AccountSnapshot],
    ) -> None:
        """
        Validate a cancel/replace.

        Must ensure:
          - new notional / size does not exceed limits
          - no sneaky size increase beyond config
        """

    @abstractmethod
    def validate_flatten_all(
        self,
        account: AccountId,
        reason: FlattenReason,
        positions: Dict[Symbol, PositionState],
        account_snapshot: Optional[AccountSnapshot],
    ) -> None:
        """
        Validate a flatten-all operation.

        Must handle:
          - FAIL-01: flatten rejected in frozen markets
          - FAIL-07: what-if margin violation on flatten

        May raise RiskViolationError if flatten itself is too dangerous
        (and must be escalated to human).
        """

    # ---------------------------------------------------------------------
    # Greeks / volatility risk hooks
    # ---------------------------------------------------------------------

    @abstractmethod
    def on_position_greeks_update(
        self,
        account: AccountId,
        symbol: Symbol,
        greeks: Greeks,
    ) -> None:
        """
        Called whenever the aggregated Greeks for (account, symbol) are updated.

        Implementation may:
          - track per-symbol vega/gamma/theta against RiskLimitsConfig
          - trip circuit breakers if limits are breached
        """

    @abstractmethod
    def validate_new_order_greeks(
        self,
        account: AccountId,
        spec: OrderSpec,
        projected_position_greeks: Greeks,
    ) -> None:
        """
        Optional, but recommended: validate a new order against Greeks limits.

        'projected_position_greeks' represents the Greeks AFTER this order
        would be filled (i.e., current position + this order's effect).

        Must raise RiskViolationError if:
          - per-symbol vega/gamma/theta exceed configured limits
          - portfolio-level Greeks exceed configured caps
          - stress scenarios (vol shock) exceed max_stress_loss_pct
        """

    # ---------------------------------------------------------------------
    # Circuit breaker / global state
    # ---------------------------------------------------------------------

    @abstractmethod
    def is_trading_halted(self, account: AccountId) -> bool:
        """Return True if this account is currently under a trading halt."""

    @abstractmethod
    def halt_trading(self, account: AccountId, reason: str) -> None:
        """
        Engage circuit breaker for an account.

        Triggered by:
          - daily loss breach
          - ops/manual override
          - repeated connectivity failures
        """

    @abstractmethod
    def resume_trading(self, account: AccountId, reason: str) -> None:
        """Lift a trading halt after manual review / reset."""

    @abstractmethod
    def on_realized_pnl_update(
        self,
        account: AccountId,
        realized_pnl_today: float,
    ) -> None:
        """
        Called whenever realized PnL changes.

        Implementation:
          - check vs max_daily_loss
          - if breached → halt_trading
        """

    @abstractmethod
    def on_unrealized_pnl_update(
        self,
        account: AccountId,
        unrealized_pnl: float,
    ) -> None:
        """
        Optional: track intraday drawdowns / risk before they realize.

        Can be a no-op in simple implementations.
        """
