# src/order_management_system/base_interfaces/order_interface.py

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional, Protocol, runtime_checkable


from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Awaitable, Callable, Protocol

from ..base_types.ids_and_enums import AccountId, OMSId, Symbol
from ..base_types.contracts_and_specs import OrderSpec, ComboSpec
from ..base_events.order_events import (
    BrokerOrderStatusEvent,
    BrokerExecutionEvent,
    BrokerCommissionEvent,
)
from ..base_events.connection_events import (
    BrokerConnectionUpEvent,
    BrokerConnectionDownEvent,
)



# ----------------------------------------------------------------------------
# Reactor sink: where adapters push events/commands
# ----------------------------------------------------------------------------

@runtime_checkable
class ReactorSink(Protocol):
    """
    Minimal protocol for the OMS reactor queue.

    The adapter will only rely on a `.put(message)`-like API that accepts
    domain Commands/Events (BaseMessage subclasses).
    """

    def put(self, message: object) -> None:
        """
        Enqueue a message (Command/Event) to be processed by the reactor.

        Implementations:
          - queue.Queue
          - asyncio.Queue wrapper
          - custom single-threaded reactor
        """
        ...


# ----------------------------------------------------------------------------
# ExecutionEngine public API – Strategy ↔ OMS boundary
# ----------------------------------------------------------------------------

class ExecutionEngineInterface(ABC):
    """
    Public surface for strategies / host platforms.

    This is the ONE thing your strategy layer should know about the OMS.
    Everything else (broker adapters, DB, etc) stays behind this interface.
    """

    @abstractmethod
    def submit_order(self, account_id: AccountId, spec: OrderSpec) -> OMSId:
        """
        Core API to submit a new order.

        Implementation must:
          - run safety checks
          - persist intent in DB
          - hand off to the BrokerAdapter asynchronously

        Returns:
          The allocated OMSId for this order.
        """

    @abstractmethod
    def cancel_order(
        self,
        oms_id: OMSId,
        reason: CancelReason = CancelReason.USER_REQUEST,
    ) -> None:
        """
        Cancel an existing order by OMS id.

        Implementation must:
          - persist cancel intent
          - route to broker via BrokerAdapter
        """

    @abstractmethod
    def replace_order(self, oms_id: OMSId, new_spec: OrderSpec) -> OMSId:
        """
        Cancel/Replace semantic:

        - Uses same oms_id logically (for PnL / risk),
        - But may result in a new underlying broker order id.
        """

    @abstractmethod
    def flatten_all(self, account_id: AccountId, reason: FlattenReason) -> None:
        """
        Trigger EOD or emergency flatten for an entire account.

        Implementation:
          - Must go through safety rules (e.g. margin what-if checks).
          - Must be idempotent and recursion-safe (no FLATTEN-during-FLATTEN loops).
        """

    @abstractmethod
    def get_order_state(self, oms_id: OMSId) -> Optional[OrderState]:
        """Return the current OrderState, or None if not found."""

    @abstractmethod
    def get_position(
        self,
        account_id: AccountId,
        symbol: Symbol,
    ) -> Optional[PositionState]:
        """Return current PositionState for (account, symbol), or None."""

    @abstractmethod
    def get_account_snapshot(self, account_id: AccountId) -> Optional[AccountSnapshot]:
        """Return the last known AccountSnapshot for the specified account."""


# ----------------------------------------------------------------------------
# BrokerAdapter – OMS ↔ Broker boundary
# ----------------------------------------------------------------------------


class BrokerAdapterInterface(ABC):
    """
    Broker-facing adapter interface.

    - Only this layer knows about IBKR / Alpaca / Webull APIs.
    - Everything it emits MUST be broker-agnostic events.
    - ExecutionEngine never sees Tws*/Cp* DTOs directly.
    """

    @abstractmethod
    def broker_name(self) -> str:
        """Human-readable name, e.g. 'IBKR-TWS', 'IBKR-CP', 'DUMMY'."""
        raise NotImplementedError

    # ---------- lifecycle -----------------------------------------------------

    @abstractmethod
    async def start(self) -> None:
        """Connect to the broker and start background listeners."""
        raise NotImplementedError

    @abstractmethod
    async def stop(self) -> None:
        """Disconnect and stop all background tasks."""
        raise NotImplementedError

    # ---------- routing of domain intents ------------------------------------

    @abstractmethod
    async def submit_order(
        self,
        account: AccountId,
        spec: OrderSpec,
        oms_correlation_id: str,
    ) -> None:
        """
        Send a single-leg order intent to the broker.

        NOTE: The OMS has already:
          - persisted the intent
          - run risk checks
        """
        raise NotImplementedError

    @abstractmethod
    async def submit_combo_order(
        self,
        account: AccountId,
        combo: ComboSpec,
        oms_correlation_id: str,
    ) -> None:
        """
        Send a multi-leg spread (BAG) to the broker.

        Same guarantees as submit_order.
        """
        raise NotImplementedError

    @abstractmethod
    async def cancel_order(
        self,
        account: AccountId,
        oms_correlation_id: str,
    ) -> None:
        """
        Cancel an existing order.

        Adapter is responsible for mapping:
          oms_correlation_id → (orderId / permId / clientOrderId)
        """
        raise NotImplementedError

    # ---------- reconciliation hooks -----------------------------------------

    @abstractmethod
    async def request_open_orders(self, account: AccountId) -> None:
        """Force the broker to send all open orders for reconciliation."""
        raise NotImplementedError

    @abstractmethod
    async def request_open_positions(self, account: AccountId) -> None:
        """Force the broker to send all positions for reconciliation."""
        raise NotImplementedError

    @abstractmethod
    async def request_account_snapshot(self, account: AccountId) -> None:
        """Request current account PnL / NetLiq / margin snapshot."""
        raise NotImplementedError

    # ---------- event sink wiring --------------------------------------------

    @abstractmethod
    def set_event_sink(self, sink: BrokerEventSink) -> None:
        """
        Provide the callback the adapter must use to emit events
        into the ExecutionEngine's reactor.
        """
        raise NotImplementedError

    # ----- Inbound Broker → OMS (via callbacks) -------------------------------
    # NOTE: The concrete implementation will define actual callback signatures
    # to match ib_insync / REST client, and from there, emit domain events
    # into a ReactorSink. We do not put those callback hooks into the interface
    # because they are broker-SDK-specific.
