# src/order_management_system/brokers/ibkr/adapter.py

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
import logging
from datetime import datetime
from threading import RLock
from typing import Any, Callable, Dict, Iterable, Optional  # <-- Added Any

from ib_insync import IB
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
from tools.ci.shims.AlgorithmImports import Symbol  # type: ignore

from .ibkr_config import IbkrConfig
from .ibkr_types import (
    IbkrOrderId,
    IbkrPermId,
    IbkrClientId,
    IbkrConId,
    IbkrOrderAction,
    IbkrOrderType,
    IbkrTif,
    IbkrSecType,
    IbkrRight,
    TwsContract,
    TwsOrder,
    TwsOrderStatusEvent,
    TwsExecution,
    TwsCommissionReport,
    TwsAccountValue,
    TwsPortfolioItem,
    TwsPosition,
    TwsErrorEvent,
    CpOrderRequest,
    CpOrderStatus,
    CpPosition,
    CpAccountSummary,
    TwsGreeksUpdate,
    IbkrExecId,  # <-- Added
)

from ...base_types.ids_and_enums import (
    BrokerType,
    BrokerConnectionStatus,
    CancelReason,
    NetworkStatus,
    OMSId,
    AccountId,
)
from ...base_types.position_and_account import AccountSnapshot

from ...base_events.order_events import (
    BrokerOrderStatusEvent,
    BrokerExecutionEvent,
    BrokerOrderErrorEvent,
)
from ...base_events.connection_events import (
    BrokerConnectionUpEvent,
    BrokerConnectionDownEvent,
    BrokerHeartbeatEvent,
)

log = logging.getLogger(__name__)

# Reactor sink: engine gives us a function that pushes events into its queue.
EventSink = Callable[[object], None]  # later: Callable[[Event], None]


# =============================================================================
# ADAPTER INTERNAL STATE
# =============================================================================


@dataclass(slots=True)
class _OrderMapping:
    """
    In-memory mapping glue between OMS ids and IBKR ids.

    This is NOT the source of truth. It only exists to route callbacks.
    The real mapping is persisted via events in your DB.
    """

    oms_id_by_order_id: Dict[IbkrOrderId, OMSId] = field(default_factory=dict)
    oms_id_by_perm_id: Dict[IbkrPermId, OMSId] = field(default_factory=dict)


@dataclass(slots=True)
class _ConnectionSnapshotInternal:
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


# =============================================================================
# MAIN ADAPTER CLASS
# =============================================================================


class IbkrAsyncAdapter(BrokerAdapterInterface, ConnectionInterface):
    """
    The ONLY class in your entire codebase that touches IBKR directly.
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
                # Use running loop if we’re already inside async code
                self._loop = asyncio.get_running_loop()
            except RuntimeError:
                # No running loop (e.g., plain pytest/sync script) → create one
                self._loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self._loop)

        # ib_insync IB instance (lazy)
        self._ib: IB | None = None  # will be IB from ib_insync at runtime

        # Internal state
        self._mapping = _OrderMapping()
        self._conn_snapshot = _ConnectionSnapshotInternal(
            status=BrokerConnectionStatus.DISCONNECTED,
            network_status=NetworkStatus.UNKNOWN,
            tws_client_id=None,
            tws_host=self._cfg.tws.host,
            tws_port=self._cfg.tws.port,
        )

        # Housekeeping
        self._lock = RLock()
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

    # This is complex and should be avoided if you can use async
    def get_broker_time(self) -> datetime:
        if self._ib is None:
            raise RuntimeError("IBKR adapter not connected (no IB instance)")

        def blocking_ib_call():
            return self._ib.reqCurrentTime()

        future = asyncio.run_coroutine_threadsafe(
            self._loop.run_in_executor(None, blocking_ib_call), self._loop
        )
        return future.result()  # BLOCKS calling thread

    def snapshot(self) -> _ConnectionSnapshotInternal:
        """
        Return a snapshot of connectivity state (cheap, thread-safe).
        """
        with self._lock:
            return _ConnectionSnapshotInternal(
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
        return True

    # ------------------ Market & Account Data -------------------------

    async def request_contract_details(self, symbol: Symbol) -> Iterable[Contract]:
        """
        Asynchronously look up contract details via IBKR.
        """
        if self._ib is None:
            raise RuntimeError("IBKR adapter not connected (no IB instance)")

        ib_query_contract = self._build_contract_query(symbol)

        try:
            details_list = await self._ib.reqContractDetailsAsync(ib_query_contract)
        except Exception as e:
            log.error("IBKR contract details request failed for %s: %s", symbol, e)
            raise

        return self._map_details_to_contracts(details_list)

    def subscribe_market_data(self, contract: Contract) -> None:
        if self._ib is None:
            raise RuntimeError("IBKR adapter not connected (no IB instance)")
        # TODO: ib_insync ib.reqMktData(...)

    def unsubscribe_market_data(self, contract: Contract) -> None:
        if self._ib is None:
            return
        # TODO: ib_insync ib.cancelMktData(...)

    def req_account_data(self, account_id: AccountId) -> None:
        if self._ib is None:
            raise RuntimeError("IBKR adapter not connected (no IB instance)")
        # TODO: ib_insync ib.reqAccountSummary, ib.reqPositions, etc.

    def req_open_positions(self) -> None:
        if self._ib is None:
            raise RuntimeError("IBKR adapter not connected (no IB instance)")
        # TODO: ib_insync ib.reqPositions()

    # -------------------------------------------------------------------------
    # BrokerAdapterInterface implementation – order lifecycle
    # -------------------------------------------------------------------------

    def submit_order(
        self,
        oms_id: OMSId,
        account_id: AccountId,
        spec: OrderSpec | ComboSpec,
    ) -> None:
        if self._ib is None:
            raise RuntimeError("IBKR adapter not connected, cannot submit order")

        log.debug("IBKR submit_order oms_id=%s spec=%r", oms_id, spec)

        if isinstance(spec, ComboSpec):
            tws_contract, tws_order = self._build_combo_order(account_id, spec)
        else:
            tws_contract, tws_order = self._build_single_order(account_id, spec)

        # TODO: real ib_insync placeOrder() usage
        order_id = tws_order.order_id
        if order_id is None:
            log.warning(
                "IBKR submit_order: no order_id assigned yet for oms_id=%s", oms_id
            )
        else:
            with self._lock:
                self._mapping.oms_id_by_order_id[order_id] = oms_id

    def cancel_order(
        self,
        oms_id: OMSId,
        reason: CancelReason,
    ) -> None:
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
        # TODO: ib_insync cancelOrder

    def replace_order(
        self,
        oms_id: OMSId,
        new_spec: OrderSpec,
    ) -> None:
        log.debug("IBKR replace_order oms_id=%s new_spec=%r", oms_id, new_spec)
        raise NotImplementedError(
            "replace_order is not yet implemented at adapter level"
        )

    def req_open_orders(self) -> None:
        if self._ib is None:
            raise RuntimeError("IBKR adapter not connected, cannot req_open_orders")
        # TODO: ib_insync ib.reqOpenOrders()

    # -------------------------------------------------------------------------
    # ASYNC CONNECTION LOOP
    # -------------------------------------------------------------------------

    async def _connect_loop(self) -> None:
        backoff = self._cfg.tws.reconnect_backoff_initial_sec

        while not self._stopped:
            try:
                await self._connect_once()
                backoff = self._cfg.tws.reconnect_backoff_initial_sec
                await self._wait_for_disconnect()
            except asyncio.CancelledError:
                break
            except Exception as exc:
                log.exception("IBKR connect_loop error: %s", exc)
                with self._lock:
                    self._conn_snapshot.last_error = str(exc)
                    self._conn_snapshot.status = BrokerConnectionStatus.ERROR

                self._emit_connection_down(reason=str(exc))

            if self._stopped:
                break

            log.warning("IBKR reconnecting in %.2f seconds", backoff)
            await asyncio.sleep(backoff)
            backoff = min(
                backoff * 2, self._cfg.tws.reconnect_backoff_max_sec
            )

    async def _connect_once(self) -> None:
        log.info(
            "IBKR connecting to %s:%s client_id=%s profile=%s",
            self._cfg.tws.host,
            self._cfg.tws.port,
            self._cfg.tws.client_id,
            self._cfg.env,
        )

        # TODO: real ib_insync connectAsync + callback registrations

        with self._lock:
            self._conn_snapshot.status = BrokerConnectionStatus.CONNECTED
            self._conn_snapshot.tws_client_id = IbkrClientId(self._cfg.tws.client_id)
            self._conn_snapshot.last_heartbeat_at = datetime.utcnow()
            self._conn_snapshot.last_error = None

        self._emit_connection_up()

    async def _disconnect(self) -> None:
        if self._ib is None:
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
        while not self._stopped and self.check_health():
            await asyncio.sleep(1.0)

    async def _heartbeat_loop(self) -> None:
        interval = self._cfg.heartbeat.heartbeat_expect_interval_sec
        while not self._stopped:
            await asyncio.sleep(interval)
            with self._lock:
                self._conn_snapshot.last_heartbeat_at = datetime.utcnow()
            self._emit_heartbeat()

    # -------------------------------------------------------------------------
    # CALLBACKS FROM IBKR (TWS / ib_insync side)
    # -------------------------------------------------------------------------

    def _on_tws_order_status(
        self,
        raw_order_status: Any,  # ib_insync.OrderStatus
    ) -> None:
        tws_ev = TwsOrderStatusEvent(
            order_id=IbkrOrderId(raw_order_status.orderId),  # type: ignore
            status=...,
            filled=...,
            remaining=...,
            avg_fill_price=...,
            perm_id=IbkrPermId(raw_order_status.permId),  # type: ignore
            parent_id=None,
            last_fill_price=...,
            client_id=IbkrClientId(raw_order_status.clientId),  # type: ignore
        )

        oms_id = self._resolve_oms_id(tws_ev.order_id, tws_ev.perm_id)

        ev = BrokerOrderStatusEvent.from_ibkr_tws(
            oms_id=oms_id,
            tws=tws_ev,
        )
        self._event_sink(ev)

    def _on_tws_exec_details(
        self,
        raw_contract: Any,
        raw_execution: Any,
    ) -> None:
        tws_exec = TwsExecution(
            exec_id=IbkrExecId(raw_execution.execId),  # type: ignore
            time=raw_execution.time,  # type: ignore
            acct_number=raw_execution.acctNumber,  # type: ignore
            exchange=raw_execution.exchange,  # type: ignore
            side=IbkrOrderAction(raw_execution.side),  # type: ignore
            shares=raw_execution.shares,  # type: ignore
            price=raw_execution.price,  # type: ignore
            perm_id=IbkrPermId(raw_execution.permId),  # type: ignore
            order_id=IbkrOrderId(raw_execution.orderId),  # type: ignore
            client_id=IbkrClientId(raw_execution.clientId),  # type: ignore
            liquidation=raw_execution.liquidation,  # type: ignore
            cum_qty=raw_execution.cumQty,  # type: ignore
            avg_price=raw_execution.avgPrice,  # type: ignore
        )

        oms_id = self._resolve_oms_id(tws_exec.order_id, tws_exec.perm_id)

        ev = BrokerExecutionEvent.from_ibkr_tws(
            oms_id=oms_id,
            tws=tws_exec,
        )
        self._event_sink(ev)

    def _on_tws_commission_report(self, raw_comm: Any) -> None:
        tws_comm = TwsCommissionReport(
            exec_id=IbkrExecId(raw_comm.execId),  # type: ignore
            commission=raw_comm.commission,  # type: ignore
            currency=raw_comm.currency,  # type: ignore
            realized_pnl=getattr(raw_comm, "realizedPNL", None),
            yield_=getattr(raw_comm, "yield", None),
            yield_redemption_date=getattr(
                raw_comm, "yieldRedemptionDate", None
            ),
        )
        # TODO: fold into execution events or separate account PnL event.

    def _on_tws_error(
        self,
        id_: int,
        code: int,
        msg: str,
        advancedOrderRejectJson: str | None = None,
    ) -> None:
        tws_err = TwsErrorEvent(
            req_id=id_,
            error_code=code,
            error_msg=msg,
        )

        ev = BrokerOrderErrorEvent.from_ibkr_tws(tws_err)
        self._event_sink(ev)

    def _on_tws_account_value(self, raw: Any) -> None:
        tws_av = TwsAccountValue(
            key=raw.key,  # type: ignore
            value=raw.value,  # type: ignore
            currency=raw.currency,  # type: ignore
            account=raw.account,  # type: ignore
        )
        # TODO: aggregate into AccountSnapshot and emit account update event.

    def _on_tws_portfolio(self, raw: Any) -> None:
        tws_pf = TwsPortfolioItem(
            contract=TwsContract(
                con_id=IbkrConId(raw.contract.conId),  # type: ignore
                symbol=raw.contract.symbol,  # type: ignore
                sec_type=IbkrSecType(raw.contract.secType),  # type: ignore
                currency=raw.contract.currency,  # type: ignore
                exchange=raw.contract.exchange,  # type: ignore
            ),
            position=raw.position,  # type: ignore
            market_price=raw.marketPrice,  # type: ignore
            market_value=raw.marketValue,  # type: ignore
            average_cost=raw.averageCost,  # type: ignore
            unrealized_pnl=raw.unrealizedPNL,  # type: ignore
            realized_pnl=raw.realizedPNL,  # type: ignore
            account=raw.account,  # type: ignore
        )
        # TODO: map to PositionState + greeks and emit.

    def _on_tws_position(self, raw: Any) -> None:
        tws_pos = TwsPosition(
            account=raw.account,  # type: ignore
            contract=TwsContract(
                con_id=IbkrConId(raw.contract.conId),  # type: ignore
                symbol=raw.contract.symbol,  # type: ignore
                sec_type=IbkrSecType(raw.contract.secType),  # type: ignore
                currency=raw.contract.currency,  # type: ignore
                exchange=raw.contract.exchange,  # type: ignore
            ),
            position=raw.position,  # type: ignore
            avg_cost=raw.avgCost,  # type: ignore
        )
        # TODO: map to PositionState and emit.

    # -------------------------------------------------------------------------
    # MAPPING HELPERS: domain → Tws* DTOs
    # -------------------------------------------------------------------------

    def _build_single_order(
        self,
        account_id: AccountId,
        spec: OrderSpec,
    ) -> tuple[TwsContract, TwsOrder]:
        tws_contract = TwsContract(
            symbol=str(spec.symbol),
            sec_type=IbkrSecType.STK,
            currency="USD",
            exchange="SMART",
        )

        action = (
            IbkrOrderAction.BUY
            if spec.side.name.startswith("BUY")
            else IbkrOrderAction.SELL
        )

        order_type = self._map_order_type(spec.order_type)
        tif = self._map_tif(spec.time_in_force)

        tws_order = TwsOrder(
            order_id=None,
            action=action,
            total_quantity=spec.qty,
            order_type=order_type,
            lmt_price=spec.limit_price,
            aux_price=spec.stop_price,
            tif=tif,
            account=str(account_id),
            transmit=True,
        )

        return tws_contract, tws_order

    def _build_combo_order(
        self,
        account_id: AccountId,
        spec: ComboSpec,
    ) -> tuple[TwsContract, TwsOrder]:
        combo_legs = []
        for leg in spec.legs:
            contract: Contract = leg.contract
            action = (
                IbkrOrderAction.BUY
                if leg.action == IbkrOrderAction.BUY
                or leg.action.name.startswith("BUY")
                else IbkrOrderAction.SELL
            )
            combo_legs.append(
                {
                    "conId": contract.conId or 0,
                    "ratio": leg.ratio,
                    "action": action.value,
                    "exchange": contract.exchange or "SMART",
                }
            )

        tws_contract = TwsContract(
            symbol=None,
            sec_type=IbkrSecType.BAG,
            currency="USD",
            exchange="SMART",
            combo_legs=combo_legs,
        )

        order_type = self._map_order_type(spec.order_type)
        tif = self._map_tif(spec.time_in_force)

        tws_order = TwsOrder(
            order_id=None,
            action=IbkrOrderAction.BUY,
            total_quantity=spec.total_quantity,
            order_type=order_type,
            lmt_price=spec.limit_price,
            tif=tif,
            account=str(account_id),
            transmit=True,
        )

        return tws_contract, tws_order

    def _map_order_type(self, order_type: Any) -> IbkrOrderType:
        try:
            return IbkrOrderType(order_type.value)  # type: ignore
        except Exception:
            if getattr(order_type, "name", None) == "MKT":
                return IbkrOrderType.MKT
            if getattr(order_type, "name", None) == "LMT":
                return IbkrOrderType.LMT
            raise

    def _map_tif(self, tif: Any) -> IbkrTif:
        try:
            return IbkrTif(tif.value)  # type: ignore
        except Exception:
            if getattr(tif, "name", None) == "DAY":
                return IbkrTif.DAY
            if getattr(tif, "name", None) == "GTC":
                return IbkrTif.GTC
            raise

    # -------------------------------------------------------------------------
    # ID RESOLUTION & MAPPING
    # -------------------------------------------------------------------------

    def _build_contract_query(self, symbol: Symbol) -> TwsContract:
        return TwsContract(
            symbol=str(symbol),
            sec_type=IbkrSecType.STK,
            currency="USD",
            exchange="SMART",
        )

    def _map_details_to_contracts(self, details_list: list) -> Iterable[Contract]:
        if not details_list:
            return []
        # TODO: implement proper mapping Contract.from_ibkr_details(...)
        return [Contract(...) for details in details_list]

    def _lookup_order_id_for_oms(self, oms_id: OMSId) -> Optional[IbkrOrderId]:
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
