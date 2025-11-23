# src/order_management_system/base_interfaces/connection_interface.py

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Optional

from ..base_types.types import (
    BrokerType,
    BrokerConnectionStatus,
    NetworkStatus,
    now_utc,
)


@dataclass(slots=True)
class ConnectionSnapshot:
    """
    Immutable snapshot of current connectivity state.

    This is what your connection monitor / health endpoint can expose.
    """

    broker_type: BrokerType
    broker_status: BrokerConnectionStatus
    network_status: NetworkStatus

    last_connected_at: Optional[datetime] = None
    last_disconnected_at: Optional[datetime] = None
    last_heartbeat_at: Optional[datetime] = None

    # free-form extra info (e.g., last error code, gateway vs TWS, etc.)
    meta: Dict[str, str] = field(default_factory=dict)

    @property
    def is_healthy(self) -> bool:
        return (
            self.broker_status == BrokerConnectionStatus.CONNECTED
            and self.network_status in (NetworkStatus.ONLINE, NetworkStatus.DEGRADED)
        )


class ConnectionInterface(ABC):
    """
    Abstract interface for broker connectivity.

    Implementations:
      - brokers.ibkr.adapter.IbkrAdapter (implements both this + order interface)
      - brokers.dummy.adapter.DummyAdapter

    Engine / watchdog code should depend on THIS, not on ib_insync or any
    broker-specific objects.
    """

    @abstractmethod
    def broker_type(self) -> BrokerType:
        """Return which broker this connection is for (IBKR, DUMMY, etc.)."""

    @abstractmethod
    def start(self) -> None:
        """
        Establish connection to the broker in a non-blocking way.

        - May spawn a background thread / event loop.
        - Must eventually update internal state and allow `snapshot()` calls.
        """

    @abstractmethod
    def stop(self) -> None:
        """
        Cleanly disconnect from the broker and stop any background tasks.
        Safe to call multiple times.
        """

    @abstractmethod
    def get_broker_time(self) -> datetime:
        """For TIME_SKEW test; can be implemented via last serverTime event."""

    @abstractmethod
    def snapshot(self) -> ConnectionSnapshot:
        """
        Return a current snapshot of connectivity state.

        - Must be cheap and thread-safe to call.
        """

    @abstractmethod
    def last_heartbeat_at(self) -> Optional[datetime]:
        """
        Convenience for watchdog: last time we received *any* broker event
        (orderStatus, execDetails, heartbeat, etc.)
        """

    @abstractmethod
    def mark_network_status(self, status: NetworkStatus) -> None:
        """
        Called by outer monitoring code (e.g. ping tests) to update network status.
        Adapter may log / react, but should not block.
        """

    @abstractmethod
    def check_health(self) -> bool:
        """
        Lightweight health check for /health endpoints:

        - Should not block on network.
        - Should use cached state and simple time deltas (e.g., last_heartbeat_at).

        Returns True if connection is healthy enough to accept new orders.
        """
        ...
