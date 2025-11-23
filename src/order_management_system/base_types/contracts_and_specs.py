from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, List, Optional
from .ids_and_enums import (
    Symbol, SecurityType, OrderAction, OrderType, TimeInForce, RightType, TradeSide
)

@dataclass(slots=True)
class Contract:
    """Represents a financial instrument."""
    symbol: Symbol
    secType: SecurityType
    currency: str = "USD"
    exchange: str = "SMART"
    primaryExchange: Optional[str] = None
    conId: Optional[int] = None # Added conId for IBKR mapping

@dataclass(slots=True)
class Stock(Contract):
    secType: SecurityType = SecurityType.STK

@dataclass(slots=True)
class Option(Contract):
    lastTradeDateOrContractMonth: str = field(default="")
    strike: float = 0.0
    right: RightType = RightType.CALL
    tradingClass: str = ""
    secType: SecurityType = SecurityType.OPT

@dataclass(slots=True)
class Order:
    """Represents a trade order (used internally for fills/events)."""
    orderId: int
    action: OrderAction
    orderType: OrderType
    totalQuantity: float
    lmtPrice: Optional[float] = None
    auxPrice: Optional[float] = None
    timeInForce: Optional[TimeInForce] = None


# --- ORDER SPECIFICATIONS ---

@dataclass(slots=True, frozen=True)
class OrderSpec:
    """Immutable intent for single-leg orders."""
    symbol: Symbol
    side: TradeSide
    qty: float
    order_type: OrderType = OrderType.MKT
    limit_price: Optional[float] = None
    stop_price: Optional[float] = None
    time_in_force: TimeInForce = TimeInForce.DAY
    expire_at: Optional[datetime] = None
    tag: str = ""
    client_tag: Optional[str] = None
    allow_partial: bool = True
    reduce_only: bool = False

@dataclass(slots=True, frozen=True)
class ComboLegSpec:
    """Defines one leg of a multi-leg combination."""
    contract: Contract
    action: OrderAction
    ratio: int = 1

@dataclass(slots=True, frozen=True)
class ComboSpec:
    """Immutable intent for multi-leg orders (e.g., Iron Condor)."""
    legs: List[ComboLegSpec]
    order_type: OrderType = OrderType.LMT
    limit_price: Optional[float] = None
    time_in_force: TimeInForce = TimeInForce.DAY
    total_quantity: float = 1.0 # Quantity of the spread itself
    tag: str = ""
    client_tag: Optional[str] = None