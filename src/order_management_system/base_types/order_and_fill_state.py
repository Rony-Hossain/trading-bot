from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional
from .ids_and_enums import (
    OMSId, AccountId, BrokerOrderId, PermId, OrderStatus, EventPriority
)
from .contracts_and_specs import OrderSpec 

# --- HELPER FACTORIES ---
def now_utc() -> datetime:
    return datetime.utcnow()

def make_correlation_id(oms_id: OMSId) -> str:
    return f"OMS-{int(oms_id)}"

# --- MESSAGING BUS ---

@dataclass(slots=True)
class BaseMessage:
    """Common envelope for commands and events."""
    priority: EventPriority = EventPriority.P2_NORMAL
    created_at: datetime = field(default_factory=now_utc)
    correlation_id: Optional[str] = None
    source: str = ""

@dataclass(slots=True)
class Command(BaseMessage):
    """Intent flowing *into* the engine (Submit, Cancel, Halt)."""
    pass

@dataclass(slots=True)
class Event(BaseMessage):
    """Facts flowing *out of* the engine (Fills, Status Updates, Health)."""
    pass

# --- ORDER STATE ---

@dataclass(slots=True)
class OrderState:
    """Canonical state of a single order tracked by the OMS."""
    oms_id: OMSId
    account_id: AccountId
    spec: OrderSpec # Note: Must handle OrderSpec/ComboSpec Union in the main OMS logic

    status: OrderStatus = OrderStatus.NEW
    broker_order_id: Optional[BrokerOrderId] = None
    perm_id: Optional[PermId] = None

    # Fill / execution data
    filled_qty: float = 0.0
    avg_fill_price: float = 0.0
    last_fill_price: Optional[float] = None
    
    # Lifecycle / reconciliation flags
    recovered: bool = False
    pending_reconcile: bool = False
    flatten_parent_id: Optional[OMSId] = None
    created_at: datetime = field(default_factory=now_utc)
    last_update: datetime = field(default_factory=now_utc)
    meta: Dict[str, Any] = field(default_factory=dict)