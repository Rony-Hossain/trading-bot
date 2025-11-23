from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional
from .ids_and_enums import (
    AccountId, Symbol, SecurityType, BrokerConnectionStatus, NetworkStatus
)
from .order_and_fill_state import now_utc

@dataclass(slots=True)
class PositionState:
    """Canonical view of a single symbol position in one account."""
    account_id: AccountId
    symbol: Symbol
    security_type: SecurityType = SecurityType.STK
    qty: float = 0.0
    avg_price: float = 0.0
    realized_pnl: float = 0.0
    unrealized_pnl: float = 0.0
    last_price: Optional[float] = None
    last_update: datetime = field(default_factory=now_utc)
    meta: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_flat(self) -> bool:
        return abs(self.qty) < 1e-9

@dataclass(slots=True)
class AccountSnapshot:
    """Normalized snapshot of account-level state (NetLiq, Buying Power, PnL)."""
    account_id: AccountId
    currency: str = "USD"
    net_liquidation: Optional[float] = None
    cash: Optional[float] = None
    buying_power: Optional[float] = None
    realized_pnl_today: float = 0.0
    unrealized_pnl: float = 0.0
    raw: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=now_utc)

@dataclass(slots=True)
class EngineHealth:
    """High-level health view for the ExecutionEngine / OMS."""
    is_healthy: bool
    reason: str = ""
    last_event_at: datetime = field(default_factory=now_utc)
    last_broker_heartbeat_at: Optional[datetime] = None
    broker_status: BrokerConnectionStatus = BrokerConnectionStatus.UNKNOWN
    network_status: NetworkStatus = NetworkStatus.UNKNOWN
    meta: Dict[str, Any] = field(default_factory=dict)