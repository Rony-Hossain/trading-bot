from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from .ids_and_enums import AccountId, Symbol
from .contracts_and_specs import ComboLegSpec
from .order_and_fill_state import now_utc

@dataclass(slots=True, frozen=True)
class Greeks:
    """The core Greeks vector (Delta, Gamma, Vega, Theta, Rho)."""
    delta: float = 0.0
    gamma: float = 0.0
    vega: float = 0.0
    theta: float = 0.0
    rho: float = 0.0

    def scaled(self, factor: float) -> "Greeks":
        """Returns a new Greeks scaled by 'factor'."""
        return Greeks(
            delta=self.delta * factor, gamma=self.gamma * factor, vega=self.vega * factor,
            theta=self.theta * factor, rho=self.rho * factor,
        )

    def __add__(self, other: "Greeks") -> "Greeks":
        """Adds two Greeks objects component-wise."""
        return Greeks(
            delta=self.delta + other.delta, gamma=self.gamma + other.gamma, vega=self.vega + other.vega,
            theta=self.theta + other.theta, rho=self.rho + other.rho,
        )

# --- AGGREGATION MODELS ---

@dataclass(slots=True, frozen=True)
class ComboLegGreeks:
    """Greeks contribution for a single leg within a combo."""
    leg: ComboLegSpec
    per_unit: Greeks
    quantity: float

    @property
    def total(self) -> Greeks:
        return self.per_unit.scaled(self.quantity)

@dataclass(slots=True, frozen=True)
class ComboGreeks:
    """Aggregated net Greeks for an entire multi-leg spread (single order)."""
    legs: List[ComboLegGreeks]

    @property
    def net(self) -> Greeks:
        total = Greeks()
        for lg in self.legs:
            total = total + lg.total
        return total

@dataclass(slots=True, frozen=True)
class PositionGreeks:
    """Aggregated Greeks for the total portfolio position (used for risk monitoring)."""
    account_id: AccountId
    symbol: Symbol
    greeks: Greeks
    as_of: datetime = field(default_factory=now_utc)
    meta: Dict[str, Any] = field(default_factory=dict)

@dataclass(slots=True)
class RiskLimitsConfig:
    """Configuration for hard risk limits."""
    # ... (existing limits: max_position, max_daily_loss, max_vega, etc.) ...
    max_position_per_symbol: Dict[Symbol, float] = field(default_factory=dict)
    max_daily_loss: float = 0.0
    max_portfolio_vega: Optional[float] = None
    max_portfolio_gamma: Optional[float] = None
    # ... (rest of the limits remain unchanged) ...