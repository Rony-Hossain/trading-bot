from __future__ import annotations

from abc import ABC, abstractmethod
from contextlib import AbstractContextManager
from typing import Callable, Iterable, List, Optional, TypeVar

from ..base_types.types import (
    OMSId,
    AccountId,
    Symbol,
    OrderStatus,
)
from ..database.db_types import (
    OrderRow,
    FillRow,
    PositionRow,
    AccountSnapshotRow,
    EventLogRow,
)


T = TypeVar("T")


class DatabaseSession(AbstractContextManager["DatabaseSession"]):
    """
    Optional explicit session/transaction boundary.

    Implementations may use this as a thin wrapper over a sqlite connection
    with BEGIN IMMEDIATE / COMMIT / ROLLBACK semantics.
    """

    def __enter__(self) -> "DatabaseSession":  # type: ignore[override]
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # type: ignore[override]
        # Concrete implementation will decide whether to commit/rollback.
        ...


class DatabaseInterface(ABC):
    """
    Abstract interface for the OMS database (SQLite in WAL mode for v1).

    The reactor / engine will depend on this interface ONLY.
    No other part of the system interacts with sqlite directly.
    """

    # ------------------------------------------------------------------
    # Transaction management
    # ------------------------------------------------------------------

    @abstractmethod
    def run_in_transaction(self, fn: Callable[[DatabaseSession], T]) -> T:
        """
        Execute 'fn(session)' inside a single DB transaction.

        - Must be atomic (either all writes visible or none).
        - Used by the reactor when applying Commands/Events.
        """
        ...

    # ------------------------------------------------------------------
    # Orders
    # ------------------------------------------------------------------

    @abstractmethod
    def get_order(self, oms_id: OMSId) -> Optional[OrderRow]:
        """Fetch a single order row by OMS id."""

    @abstractmethod
    def insert_order(self, session: DatabaseSession, row: OrderRow) -> None:
        """Insert a new OrderRow (called when creating a new order)."""

    @abstractmethod
    def update_order(self, session: DatabaseSession, row: OrderRow) -> None:
        """
        Update an existing OrderRow.

        Must be used for all status/field changes (NEW→WORKING→FILLED, etc.).
        """

    @abstractmethod
    def load_non_terminal_orders(self) -> List[OrderRow]:
        """
        Load all orders that are not in a terminal state.

        Used on startup and periodic reconciliation (PERSIST-01, FAIL-05, FAIL-06).
        """

    @abstractmethod
    def load_orders_for_account(
        self,
        account_id: AccountId,
    ) -> List[OrderRow]:
        """Load all orders belonging to a specific account (for risk / ops)."""

    # ------------------------------------------------------------------
    # Fills
    # ------------------------------------------------------------------

    @abstractmethod
    def insert_fill(self, session: DatabaseSession, row: FillRow) -> None:
        """
        Insert a new FillRow.

        Must be called exactly once per unique execution_id (LIFE-05).
        """

    @abstractmethod
    def has_execution_id(self, execution_id: str) -> bool:
        """Return True if this execution_id already exists (duplicate fill)."""

    @abstractmethod
    def load_fills_for_order(self, oms_id: OMSId) -> List[FillRow]:
        """Load all fills for a given order."""

    # ------------------------------------------------------------------
    # Positions
    # ------------------------------------------------------------------

    @abstractmethod
    def load_positions_for_account(self, account_id: AccountId) -> List[PositionRow]:
        """Load all position rows for the given account."""

    @abstractmethod
    def upsert_position(
        self,
        session: DatabaseSession,
        row: PositionRow,
    ) -> None:
        """
        Insert or update a PositionRow.

        Used when applying fills and during reconciliation.
        """

    # ------------------------------------------------------------------
    # Account snapshots
    # ------------------------------------------------------------------

    @abstractmethod
    def get_account_snapshot(
        self,
        account_id: AccountId,
    ) -> Optional[AccountSnapshotRow]:
        """Get the latest account snapshot for risk checks."""

    @abstractmethod
    def upsert_account_snapshot(
        self,
        session: DatabaseSession,
        row: AccountSnapshotRow,
    ) -> None:
        """Insert/update an account snapshot row."""

    # ------------------------------------------------------------------
    # Event log (optional, for REPLAY-01)
    # ------------------------------------------------------------------

    @abstractmethod
    def append_event_log(
        self,
        session: DatabaseSession,
        row: EventLogRow,
    ) -> None:
        """Append an event log row for replay / debugging."""

    @abstractmethod
    def load_event_log(
        self,
        limit: Optional[int] = None,
    ) -> List[EventLogRow]:
        """Load recent event log rows (for replay / diagnostics)."""
