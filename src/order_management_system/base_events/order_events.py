from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional, TYPE_CHECKING

from ..base_types.ids_and_enums import (
    OMSId,
    AccountId,
    Symbol,
    OrderStatus,
)
from ..base_types.order_and_fill_state import Event, now_utc

# These are only needed for type hints in the factories;
# TYPE_CHECKING avoids runtime imports and circular deps.
if TYPE_CHECKING:  # pragma: no cover
    from ..brokers.ibkr.ibkr_types import (
        TwsOrderStatusEvent,
        TwsExecution,
        TwsCommissionReport,
        TwsErrorEvent,
    )


# =====================================================================
# BrokerOrderStatusEvent
# =====================================================================

@dataclass(slots=True)
class BrokerOrderStatusEvent(Event):
    """
    Broker-agnostic order status update.

    Emitted by adapters when they receive orderStatus-like callbacks.
    """

    oms_id: Optional[OMSId]          # None if we haven't mapped yet (orphan)
    account_id: AccountId
    symbol: Symbol

    status: OrderStatus
    filled: float
    remaining: float
    avg_fill_price: float

    last_fill_price: Optional[float] = None
    broker_order_id: Optional[str] = None
    perm_id: Optional[int] = None

    received_at: datetime = field(default_factory=now_utc)
    raw: Dict[str, Any] = field(default_factory=dict)

    # ------------------------------------------------------------------
    # Factory: IBKR → BrokerOrderStatusEvent
    # ------------------------------------------------------------------
    @classmethod
    def from_ibkr_tws(
        cls,
        *,
        oms_id: Optional[OMSId],
        tws: "TwsOrderStatusEvent",
    ) -> "BrokerOrderStatusEvent":
        """
        Create a BrokerOrderStatusEvent from an IBKR-specific TwsOrderStatusEvent.

        NOTE: account_id and symbol are currently best-effort; once you
        have a solid mapping from oms_id → (account_id, symbol), update
        this to use that instead of "UNKNOWN".
        """
        # Map IBKR status to your OrderStatus enum.
        status_raw = getattr(tws, "status", None)
        if isinstance(status_raw, OrderStatus):
            status = status_raw
        else:
            name = getattr(status_raw, "name", None)
            if name and name in OrderStatus.__members__:
                status = OrderStatus[name]
            else:
                # Fallback: first enum member, so it always has *some* value.
                status = list(OrderStatus)[0]

        # TODO: replace these with real mapping from your OMS.
        account_id = AccountId(getattr(tws, "account", "UNKNOWN"))
        symbol = Symbol(getattr(tws, "symbol", "UNKNOWN"))

        return cls(
            oms_id=oms_id,
            account_id=account_id,
            symbol=symbol,
            status=status,
            filled=float(getattr(tws, "filled", 0.0)),
            remaining=float(getattr(tws, "remaining", 0.0)),
            avg_fill_price=float(getattr(tws, "avg_fill_price", 0.0)),
            last_fill_price=getattr(tws, "last_fill_price", None),
            broker_order_id=(str(getattr(tws, "order_id", "")) or None),
            perm_id=getattr(tws, "perm_id", None),
            raw={"ibkr": tws},
        )


# =====================================================================
# BrokerExecutionEvent
# =====================================================================

@dataclass(slots=True)
class BrokerExecutionEvent(Event):
    """
    Broker-agnostic execution / fill event.
    """

    oms_id: Optional[OMSId]
    account_id: AccountId
    symbol: Symbol

    exec_id: str
    quantity: float
    price: float

    side: str  # "BUY" / "SELL" (direction already signed in PnL calc)
    trade_time: datetime = field(default_factory=now_utc)

    perm_id: Optional[int] = None
    broker_order_id: Optional[str] = None

    raw: Dict[str, Any] = field(default_factory=dict)

    # ------------------------------------------------------------------
    # Factory: IBKR → BrokerExecutionEvent
    # ------------------------------------------------------------------
    @classmethod
    def from_ibkr_tws(
        cls,
        *,
        oms_id: Optional[OMSId],
        tws: "TwsExecution",
    ) -> "BrokerExecutionEvent":
        """
        Create a BrokerExecutionEvent from an IBKR-specific TwsExecution.
        """
        side_raw = getattr(tws, "side", None)
        if hasattr(side_raw, "value"):
            side = str(side_raw.value)
        else:
            side = str(side_raw or "")

        # TODO: replace these with lookup via oms_id if available.
        account_id = AccountId(getattr(tws, "acct_number", "UNKNOWN"))
        symbol = Symbol(getattr(tws, "symbol", "UNKNOWN"))

        return cls(
            oms_id=oms_id,
            account_id=account_id,
            symbol=symbol,
            exec_id=str(getattr(tws, "exec_id", "")),
            quantity=float(getattr(tws, "shares", 0.0)),
            price=float(getattr(tws, "price", 0.0)),
            side=side,
            trade_time=getattr(tws, "time", now_utc()),
            perm_id=getattr(tws, "perm_id", None),
            broker_order_id=(str(getattr(tws, "order_id", "")) or None),
            raw={"ibkr": tws},
        )


# =====================================================================
# BrokerCommissionEvent
# =====================================================================

@dataclass(slots=True)
class BrokerCommissionEvent(Event):
    """
    Commission / fee adjustment associated with an execution.
    """

    exec_id: str
    account_id: AccountId
    symbol: Symbol

    commission: float
    currency: str

    realized_pnl_delta: float = 0.0
    received_at: datetime = field(default_factory=now_utc)
    raw: Dict[str, Any] = field(default_factory=dict)

    # ------------------------------------------------------------------
    # Factory: IBKR → BrokerCommissionEvent
    # ------------------------------------------------------------------
    @classmethod
    def from_ibkr_tws(
        cls,
        *,
        tws: "TwsCommissionReport",
        account_id: AccountId,
        symbol: Symbol,
        realized_pnl_delta: float | None = None,
    ) -> "BrokerCommissionEvent":
        """
        Create a BrokerCommissionEvent from an IBKR-specific TwsCommissionReport.

        account_id & symbol must be supplied by the caller (e.g. via mapping
        from exec_id → order → symbol/account).
        """
        return cls(
            exec_id=str(getattr(tws, "exec_id", "")),
            account_id=account_id,
            symbol=symbol,
            commission=float(getattr(tws, "commission", 0.0)),
            currency=str(getattr(tws, "currency", "")),
            realized_pnl_delta=(
                realized_pnl_delta
                if realized_pnl_delta is not None
                else float(getattr(tws, "realized_pnl", 0.0) or 0.0)
            ),
            raw={"ibkr": tws},
        )


# =====================================================================
# BrokerOrderErrorEvent  (this is what your adapter imports)
# =====================================================================

@dataclass(slots=True)
class BrokerOrderErrorEvent(Event):
    """
    Broker-agnostic order error / rejection / warning.

    Used when the broker reports an error that is associated with an order,
    request, or account.
    """

    oms_id: Optional[OMSId]
    account_id: Optional[AccountId]
    symbol: Optional[Symbol]

    broker_order_id: Optional[str]
    error_code: int
    error_msg: str

    is_fatal: bool = False  # can be upgraded by engine logic
    received_at: datetime = field(default_factory=now_utc)
    raw: Dict[str, Any] = field(default_factory=dict)

    # ------------------------------------------------------------------
    # Factory: IBKR → BrokerOrderErrorEvent
    # ------------------------------------------------------------------
    @classmethod
    def from_ibkr_tws(
        cls,
        tws: "TwsErrorEvent",
        *,
        oms_id: Optional[OMSId] = None,
        account_id: Optional[AccountId] = None,
        symbol: Optional[Symbol] = None,
    ) -> "BrokerOrderErrorEvent":
        """
        Create a BrokerOrderErrorEvent from an IBKR-specific TwsErrorEvent.

        NOTE:
          - IB's error messages often *don't* include account/symbol/order
            context; those should be filled in by the caller if known.
        """
        return cls(
            oms_id=oms_id,
            account_id=account_id,
            symbol=symbol,
            broker_order_id=None,  # cannot reliably map here yet
            error_code=int(getattr(tws, "error_code", 0)),
            error_msg=str(getattr(tws, "error_msg", "")),
            is_fatal=False,
            raw={"ibkr": tws},
        )
