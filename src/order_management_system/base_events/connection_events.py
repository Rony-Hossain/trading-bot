# src/order_management_system/base_events/connection_events.py

from __future__ import annotations

from dataclasses import dataclass
from ..base_types.order_and_fill_state import Event
from ..base_types.ids_and_enums import BrokerType, BrokerConnectionStatus


@dataclass(slots=True)
class BrokerConnectionUpEvent(Event):
    """
    Emitted when a broker connection transitions to CONNECTED.
    """
    broker: BrokerType
    status: BrokerConnectionStatus = BrokerConnectionStatus.CONNECTED


@dataclass(slots=True)
class BrokerConnectionDownEvent(Event):
    """
    Emitted when a broker connection transitions to DISCONNECTED / ERROR.
    """
    broker: BrokerType
    status: BrokerConnectionStatus = BrokerConnectionStatus.DISCONNECTED
    reason: str = ""


@dataclass(slots=True)
class BrokerHeartbeatEvent(Event):
    """
    Lightweight periodic heartbeat confirming the connection is still alive.
    Typically used for monitoring / HEALTH-01 style checks.
    """
    broker: BrokerType
    status: BrokerConnectionStatus = BrokerConnectionStatus.CONNECTED
