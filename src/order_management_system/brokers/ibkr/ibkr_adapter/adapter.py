# src/order_management_system/brokers/ibkr/adapter.py

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Any, Callable, Iterable, Optional

from ib_insync import IB
from tools.ci.shims.AlgorithmImports import Symbol  # type: ignore

from src.order_management_system.base_interfaces.connection_interface import (
    ConnectionInterface,
)
from src.order_management_system.base_interfaces.order_interface import (
    BrokerAdapterInterface,
)
from src.order_management_system.base_types.contracts_and_specs import (
    ComboSpec,
    Contract,
    OrderSpec,
)
from src.order_management_system.base_types.ids_and_enums import (
    BrokerType,
    BrokerConnectionStatus,
    CancelReason,
    NetworkStatus,
    OMSId,
    AccountId,
)

from ibkr_config import IbkrConfig
from ibkr_types import (
    IbkrOrderId,
    IbkrPermId,
    IbkrClientId,
)
from .ibkr_state import (
    IbkrAdapterState,
    OrderMapping,
    ConnectionSnapshotInternal,
)
from .ibkr_mappers import (
    build_single_order,
    build_combo_order,
)
from .ibkr_market_account import (
    request_contract_details as ibkr_request_contract_details,
    subscribe_market_data as ibkr_subscribe_market_data,
    unsubscribe_market_data as ibkr_unsubscribe_market_data,
    req_account_data as ibkr_req_account_data,
    req_open_positions as ibkr_req_open_positions,
)
from .ibkr_callbacks import (
    handle_tws_order_status,
    handle_tws_exec_details,
    handle_tws_commission_report,
    handle_tws_error,
    handle_tws_account_value,
    handle_tws_portfolio,
    handle_tws_position,
)

from base_events.connection_events import (
    BrokerConnectionUpEvent,
    BrokerConnectionDownEvent,
    BrokerHeartbeatEvent
)

log = logging.getLogger(__name__)

# Reactor sink: engine gives us a function that pushes events into its queue.
EventSink = Callable[[object], None]  # later: Callable[[Event], None]


class IbkrAsyncAdapter(BrokerAdapterInterface, ConnectionInterface):
    """
    The ONLY class in your entire codebase that touches IBKR directly.

    Responsibilities:
      - Manage TWS / IB Gateway connection via ib_insync (in a non-blocking way)
      - Convert domain OrderSpec / ComboSpec to TwsContract + TwsOrder
      - Submit, cancel, and replace orders
      - Subscribe to broker callbacks (orderStatus, execDetails, error, etc.)
      - Convert TWS callbacks into canonical Broker* events
      - Enforce adapter-level invariants (clientId, clock skew, etc.)

    Non-responsibilities:
      - No risk rules (RiskEngine does that)
      - No DB writes (ExecutionEngine handles persistence)
      - No strategy logic (Strategy/Engine layer only)
    """

    def __init__(
        self,
        config: IbkrConfig,
        event_sink: EventSink,
        *,
        loop: Optional[asyncio.AbstractEventLoop] = None,
    ) -> None:
        self._cfg = config
        self._event_sink = event_sink

        # Async loop used to schedule connect/reconnect tasks
        # SAFE: works in pytest, sync scripts, or inside an existing loop.
        if loop is not None:
            self._loop = loop
        else:
            try:
                # Use running loop if already inside async code
                self._loop = asyncio.get_running_loop()
            except RuntimeError:
                # No running loop (e.g., plain pytest/sync script) → create one
                self._loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self._loop)

        # ib_insync IB instance (lazy)
        self._ib: IB | None = None

        # Shared internal state (mapping + connection snapshot + lock)
        self._state = IbkrAdapterState(
            tws_host=self._cfg.tws.host,
            tws_port=self._cfg.tws.port,
        )
        # Convenience aliases
        self._lock = self._state.lock
        self._mapping: OrderMapping = self._state.mapping
        self._conn_snapshot: ConnectionSnapshotInternal = self._state.conn_snapshot

        # Housekeeping tasks
        self._connect_task: Optional[asyncio.Task] = None
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._stopped: bool = False

    # -------------------------------------------------------------------------
    # ConnectionInterface implementation
    # -------------------------------------------------------------------------

    def broker_type(self) -> BrokerType:
        return BrokerType.IBKR

    def start(self) -> None:
        """
        Establish connection in a non-blocking way.

        This schedules an async task on the loop; it does not block the caller.
        """
        with self._lock:
            if self._stopped:
                raise RuntimeError("IbkrAsyncAdapter.start() called after stop()")

            if self._connect_task and not self._connect_task.done():
                log.debug("IbkrAsyncAdapter.start(): already connecting/connected")
                return

            self._connect_task = self._loop.create_task(self._connect_loop())
            self._heartbeat_task = self._loop.create_task(self._heartbeat_loop())

    def stop(self) -> None:
        """
        Cleanly disconnect and stop background tasks.
        """
        with self._lock:
            self._stopped = True
            if self._connect_task:
                self._connect_task.cancel()
            if self._heartbeat_task:
                self._heartbeat_task.cancel()

        # Schedule async disconnect
        self._loop.create_task(self._disconnect())

    def get_broker_time(self) -> datetime:
        """
        Sync-safe wrapper. Detects misuse from async threads.
        """
        try:
            running = asyncio.get_running_loop()
            if running is self._loop:
                raise RuntimeError(
                    "get_broker_time() called from inside adapter event loop. "
                    "Use await get_broker_time_async() instead."
                )
        except RuntimeError:
            # No running loop → safe
            pass

        return asyncio.run(self.get_broker_time_async())

    async def get_broker_time_async(self) -> datetime:
        if self._ib is None:
            raise RuntimeError("IBKR adapter not connected")

        return await self._loop.run_in_executor(None, self._ib.reqCurrentTime)

    def snapshot(self) -> ConnectionSnapshotInternal:
        """
        Return a snapshot of connectivity state (cheap, thread-safe).
        You can later map this to a ConnectionSnapshot domain type.
        """
        with self._lock:
            return ConnectionSnapshotInternal(
                status=self._conn_snapshot.status,
                network_status=self._conn_snapshot.network_status,
                last_heartbeat_at=self._conn_snapshot.last_heartbeat_at,
                last_error=self._conn_snapshot.last_error,
                tws_client_id=self._conn_snapshot.tws_client_id,
                tws_host=self._conn_snapshot.tws_host,
                tws_port=self._conn_snapshot.tws_port,
            )

    def last_heartbeat_at(self) -> Optional[datetime]:
        with self._lock:
            return self._conn_snapshot.last_heartbeat_at

    def mark_network_status(self, status: NetworkStatus) -> None:
        with self._lock:
            self._conn_snapshot.network_status = status

    def check_health(self) -> bool:
        """
        Lightweight health check: True if connection is healthy enough for orders.
        """
        snap = self.snapshot()
        if snap.status != BrokerConnectionStatus.CONNECTED:
            return False
        # Optionally, enforce heartbeat freshness based on config.
        return True

    # -------------------------------------------------------------------------
    # Market & Account Data – delegate to ibkr_market_account
    # -------------------------------------------------------------------------

    async def request_contract_details(self, symbol: Symbol) -> Iterable[Contract]:
        if self._ib is None:
            raise RuntimeError("IBKR adapter not connected (no IB instance)")
        return await ibkr_request_contract_details(self._ib, symbol)

    def subscribe_market_data(self, contract: Contract) -> None:
        if self._ib is None:
            raise RuntimeError("IBKR adapter not connected (no IB instance)")
        ibkr_subscribe_market_data(self._ib, contract)

    def unsubscribe_market_data(self, contract: Contract) -> None:
        if self._ib is None:
            return
        ibkr_unsubscribe_market_data(self._ib, contract)

    def req_account_data(self, account_id: AccountId) -> None:
        if self._ib is None:
            raise RuntimeError("IBKR adapter not connected (no IB instance)")
        ibkr_req_account_data(self._ib, account_id)

    def req_open_positions(self) -> None:
        if self._ib is None:
            raise RuntimeError("IBKR adapter not connected (no IB instance)")
        ibkr_req_open_positions(self._ib)

    # -------------------------------------------------------------------------
    # BrokerAdapterInterface implementation – order lifecycle
    # -------------------------------------------------------------------------

    def submit_order(
        self,
        oms_id: OMSId,
        account_id: AccountId,
        spec: OrderSpec | ComboSpec,
    ) -> None:
        """
        Non-blocking submit. Validation + DB persistence already happened
        in the ExecutionEngine; adapter only translates and sends.
        """
        if self._ib is None:
            raise RuntimeError("IBKR adapter not connected, cannot submit order")

        log.debug("IBKR submit_order oms_id=%s spec=%r", oms_id, spec)

        if isinstance(spec, ComboSpec):
            tws_contract, tws_order = build_combo_order(account_id, spec)
        else:
            tws_contract, tws_order = build_single_order(account_id, spec)

        # TODO: replace with real ib_insync placeOrder:
        #
        #   ib_contract = convert_to_ib_contract(tws_contract)
        #   ib_order = convert_to_ib_order(tws_order)
        #   trade = self._ib.placeOrder(ib_contract, ib_order)
        #
        # For now, we assume TWS assigns orderId immediately (ib_insync behaviour).
        order_id = tws_order.order_id
        if order_id is None:
            log.warning(
                "IBKR submit_order: no order_id assigned yet for oms_id=%s",
                oms_id,
            )
        else:
            with self._lock:
                self._mapping.oms_id_by_order_id[order_id] = oms_id

    def cancel_order(
        self,
        oms_id: OMSId,
        reason: CancelReason,
    ) -> None:
        """
        Non-blocking cancel. Engine has already decided this is safe & valid.
        """
        if self._ib is None:
            raise RuntimeError("IBKR adapter not connected, cannot cancel order")

        ib_order_id = self._lookup_order_id_for_oms(oms_id)
        if ib_order_id is None:
            log.warning(
                "IBKR cancel_order: no known order_id for oms_id=%s; "
                "may rely on reconciliation.",
                oms_id,
            )
            return

        log.debug(
            "IBKR cancel_order oms_id=%s ib_order_id=%s reason=%s",
            oms_id,
            ib_order_id,
            reason,
        )

        # TODO: ib_insync cancelOrder(order_id) or cancel specific Trade
        #   self._ib.cancelOrder(trade)
        #   or self._ib.cancelOrder(ib_order_id)

    def replace_order(
        self,
        oms_id: OMSId,
        new_spec: OrderSpec,
    ) -> None:
        """
        Cancel/replace pattern. Engine owns semantics; adapter just sends.
        Usually implemented as: cancel old + submit new with same oms_id mapping.
        """
        log.debug("IBKR replace_order oms_id=%s new_spec=%r", oms_id, new_spec)
        raise NotImplementedError(
            "replace_order is not yet implemented at adapter level"
        )

    def req_open_orders(self) -> None:
        """
        Force a refresh of open orders from IBKR for reconciliation.
        """
        if self._ib is None:
            raise RuntimeError("IBKR adapter not connected, cannot req_open_orders")
        # TODO: self._ib.reqOpenOrders()

    # -------------------------------------------------------------------------
    # ASYNC CONNECTION LOOP
    # -------------------------------------------------------------------------

    async def _connect_loop(self) -> None:
        """
        Long-running task: maintains connection with backoff retries.

        This should:
          - attempt connect
          - set up event subscriptions
          - on disconnect/error → update snapshot + emit events
          - apply reconnect backoff from config
        """
        backoff = self._cfg.tws.reconnect_backoff_initial_sec

        while not self._stopped:
            try:
                await self._connect_once()
                backoff = self._cfg.tws.reconnect_backoff_initial_sec

                # Block here until disconnected
                await self._wait_for_disconnect()
            except asyncio.CancelledError:
                break
            except Exception as exc:
                log.exception("IBKR connect_loop error: %s", exc)
                with self._lock:
                    self._conn_snapshot.last_error = str(exc)
                    self._conn_snapshot.status = BrokerConnectionStatus.ERROR

                # Emit connection down event
                self._emit_connection_down(reason=str(exc))

            if self._stopped:
                break

            # Reconnect with backoff
            log.warning("IBKR reconnecting in %.2f seconds", backoff)
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, self._cfg.tws.reconnect_backoff_max_sec)

    async def _connect_once(self) -> None:
        """
        Single connect attempt.

        Actual ib_insync calls go here.
        """
        log.info(
            "IBKR connecting to %s:%s client_id=%s profile=%s",
            self._cfg.tws.host,
            self._cfg.tws.port,
            self._cfg.tws.client_id,
            self._cfg.env,
        )

        # TODO: move to real ib_insync connection:
        #
        #   self._ib = IB()
        #   await self._ib.connectAsync(
        #       host=self._cfg.tws.host,
        #       port=self._cfg.tws.port,
        #       clientId=self._cfg.tws.client_id,
        #       timeout=self._cfg.tws.connect_timeout_sec,
        #   )
        #
        #   # Register callbacks on ib_insync IB object
        #   self._ib.orderStatusEvent += lambda raw: handle_tws_order_status(self, raw)
        #   self._ib.execDetailsEvent += lambda c, e: handle_tws_exec_details(self, c, e)
        #   self._ib.commissionReportEvent += lambda c: handle_tws_commission_report(self, c)
        #   self._ib.errorEvent += lambda i, code, msg, j=None: handle_tws_error(self, i, code, msg, j)
        #   self._ib.updateAccountValueEvent += lambda r: handle_tws_account_value(self, r)
        #   self._ib.updatePortfolioEvent += lambda r: handle_tws_portfolio(self, r)
        #   self._ib.positionEvent += lambda r: handle_tws_position(self, r)

        with self._lock:
            self._conn_snapshot.status = BrokerConnectionStatus.CONNECTED
            self._conn_snapshot.tws_client_id = IbkrClientId(self._cfg.tws.client_id)
            self._conn_snapshot.last_heartbeat_at = datetime.utcnow()
            self._conn_snapshot.last_error = None

        self._emit_connection_up()

    async def _disconnect(self) -> None:
        if self._ib is None:
            with self._lock:
                self._conn_snapshot.status = BrokerConnectionStatus.DISCONNECTED
            self._emit_connection_down(reason="stop() called")
            return

        log.info("IBKR disconnecting...")

        try:
            # TODO: self._ib.disconnect()
            pass
        except Exception as exc:
            log.warning("IBKR disconnect error: %s", exc)

        with self._lock:
            self._conn_snapshot.status = BrokerConnectionStatus.DISCONNECTED

        self._emit_connection_down(reason="stop() called")

    async def _wait_for_disconnect(self) -> None:
        """
        Block until IBKR disconnects. For ib_insync, you can subscribe to
        connection up/down events or poll.
        """
        # TODO: implement proper wait using ib_insync / event
        while not self._stopped and self.check_health():
            await asyncio.sleep(1.0)

    async def _heartbeat_loop(self) -> None:
        """
        Periodic heartbeat check, used for HEART-01 / health reporting.
        """
        interval = self._cfg.heartbeat.heartbeat_expect_interval_sec
        while not self._stopped:
            await asyncio.sleep(interval)
            with self._lock:
                self._conn_snapshot.last_heartbeat_at = datetime.utcnow()
            self._emit_heartbeat()

    # -------------------------------------------------------------------------
    # ID RESOLUTION & MAPPING
    # -------------------------------------------------------------------------

    def _lookup_order_id_for_oms(self, oms_id: OMSId) -> Optional[IbkrOrderId]:
        """
        Reverse lookup: given an oms_id, find an IbkrOrderId if we have one.
        NOTE: this is purely in-memory and only best-effort.
        """
        with self._lock:
            for order_id, o in self._mapping.oms_id_by_order_id.items():
                if o == oms_id:
                    return order_id
        return None

    def _resolve_oms_id(
        self,
        order_id: Optional[IbkrOrderId],
        perm_id: Optional[IbkrPermId],
    ) -> Optional[OMSId]:
        """
        Given TWS ids, resolve the corresponding OMS id using in-memory mapping.
        """
        with self._lock:
            if perm_id is not None and perm_id in self._mapping.oms_id_by_perm_id:
                return self._mapping.oms_id_by_perm_id[perm_id]
            if order_id is not None and order_id in self._mapping.oms_id_by_order_id:
                return self._mapping.oms_id_by_order_id[order_id]
        return None

    # -------------------------------------------------------------------------
    # EVENT EMITTER SHORTCUTS
    # -------------------------------------------------------------------------

    def _emit_connection_up(self) -> None:
        ev = BrokerConnectionUpEvent(
            broker=BrokerType.IBKR,
            when=datetime.utcnow(),
        )
        self._event_sink(ev)

    def _emit_connection_down(self, reason: str) -> None:
        ev = BrokerConnectionDownEvent(
            broker=BrokerType.IBKR,
            when=datetime.utcnow(),
            reason=reason,
        )
        self._event_sink(ev)

    def _emit_heartbeat(self) -> None:
        ev = BrokerHeartbeatEvent(
            broker=BrokerType.IBKR,
            when=datetime.utcnow(),
        )
        self._event_sink(ev)
