from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from threading import RLock
from typing import Dict, Optional

from base_types.ids_and_enums import (
    BrokerConnectionStatus,
    NetworkStatus,
    OMSId,
)
from ibkr_types import IbkrOrderId, IbkrPermId, IbkrClientId


@dataclass(slots=True)
class OrderMapping:
    """
    In-memory mapping glue between OMS ids and IBKR ids.

    This is NOT the source of truth. It only exists to route callbacks.
    """
    oms_id_by_order_id: Dict[IbkrOrderId, OMSId] = field(default_factory=dict)
    oms_id_by_perm_id: Dict[IbkrPermId, OMSId] = field(default_factory=dict)


@dataclass(slots=True)
class ConnectionSnapshotInternal:
    """
    Lightweight, thread-safe snapshot of connection state, exposed via snapshot().
    """
    status: BrokerConnectionStatus = BrokerConnectionStatus.DISCONNECTED
    network_status: NetworkStatus = NetworkStatus.UNKNOWN
    last_heartbeat_at: Optional[datetime] = None
    last_error: Optional[str] = None
    tws_client_id: Optional[IbkrClientId] = None
    tws_host: Optional[str] = None
    tws_port: Optional[int] = None


class IbkrAdapterState:
    """
    Thin wrapper around shared adapter state + lock.
    Keeps the main adapter class slimmer.
    """

    def __init__(self, tws_host: str, tws_port: int) -> None:
        self.lock = RLock()
        self.mapping = OrderMapping()
        self.conn_snapshot = ConnectionSnapshotInternal(
            tws_host=tws_host,
            tws_port=tws_port,
        )
