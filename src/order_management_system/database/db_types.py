from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional

from ..base_types.types import (
    OMSId,
    AccountId,
    Symbol,
    OrderStatus,
    FlattenReason,
)


# ---------------------------------------------------------------------------
# ORDER ROW – persisted representation of OrderState
# ---------------------------------------------------------------------------

@dataclass(slots=True)
class OrderRow:
    """
    DB representation of a single order.

    This is what you actually store in SQLite. It mirrors OrderState, but uses
    only primitives / JSON-serializable fields.
    """

    oms_id: int                      # INTEGER PRIMARY KEY
    account_id: str                  # TEXT
    symbol: str                      # TEXT

    side: str                        # "BUY"/"SELL"/"SHORT_SELL"/...
    qty: float                       # requested quantity

    order_type: str                  # "MKT", "LMT", "STP", ...
    time_in_force: str               # "DAY", "GTC", ...

    status: str                      # same as OrderStatus.value

    broker_order_id: Optional[str] = None
    perm_id: Optional[int] = None

    limit_price: Optional[float] = None
    stop_price: Optional[float] = None

    filled_qty: float = 0.0
    avg_fill_price: float = 0.0
    last_fill_price: Optional[float] = None

    recovered: bool = False
    pending_reconcile: bool = False
    flatten_parent_id: Optional[int] = None
    flatten_reason: Optional[str] = None   # FlattenReason.value if applicable

    created_at: datetime = field(default_factory=datetime.utcnow)
    last_update: datetime = field(default_factory=datetime.utcnow)

    # Serialized JSON for misc metadata (risk flags, tags, adapter info, etc.)
    meta: Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# FILL ROW – individual executions (for PnL and audit)
# ---------------------------------------------------------------------------

@dataclass(slots=True)
class FillRow:
    """
    DB representation of a single execution/fill.

    You use this for:
      - audit trail
      - realized PnL calculations
      - duplicate execId detection (LIFE-05)
    """

    id: Optional[int]                # INTEGER PRIMARY KEY (auto)
    oms_id: int                      # FK → OrderRow.oms_id

    execution_id: str                # broker execution id (unique per broker)
    symbol: str

    qty: float                       # positive number
    price: float                     # execution price
    commission: Optional[float] = None

    fill_time: datetime = field(default_factory=datetime.utcnow)

    # raw broker fields if needed (exchange, liquidity, etc.)
    meta: Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# POSITION ROW – current positions per (account, symbol)
# ---------------------------------------------------------------------------

@dataclass(slots=True)
class PositionRow:
    """
    DB representation of a position snapshot.

    This is your local view; reconciliation will keep it aligned with broker.
    """

    account_id: str
    symbol: str

    qty: float                       # current quantity (positive or negative)
    avg_price: float                 # average cost

    realized_pnl_today: float = 0.0
    unrealized_pnl: float = 0.0

    last_update: datetime = field(default_factory=datetime.utcnow)

    meta: Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# ACCOUNT SNAPSHOT ROW – margin, cash, etc.
# ---------------------------------------------------------------------------

@dataclass(slots=True)
class AccountSnapshotRow:
    """
    Snapshot of account-level metrics used for risk checks.

    This typically comes from broker account summary (or your risk service)
    and is persisted periodically.
    """

    account_id: str

    net_liquidation: Optional[float] = None
    cash: Optional[float] = None
    buying_power: Optional[float] = None

    realized_pnl_today: float = 0.0
    unrealized_pnl: float = 0.0

    last_update: datetime = field(default_factory=datetime.utcnow)

    meta: Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# EVENT LOG ROW – for replay / debugging (REPLAY-01)
# ---------------------------------------------------------------------------

@dataclass(slots=True)
class EventLogRow:
    """
    Optional: DB representation of a serialized Command/Event.

    Used for REPLAY-01: engine.replay_from_log("execution.log") and for
    post-mortem analysis after crashes.
    """

    id: Optional[int]                # INTEGER PRIMARY KEY
    created_at: datetime
    direction: str                   # "INBOUND" (from broker) or "OUTBOUND" (to broker/strategy)
    kind: str                        # "COMMAND" or "EVENT"
    type_name: str                   # e.g. "OrderFilledEvent"
    payload_json: str                # serialized JSON representation
