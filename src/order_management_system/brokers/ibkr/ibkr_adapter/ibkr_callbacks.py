from __future__ import annotations

from typing import Any

from ibkr_types import (
    IbkrOrderId,
    IbkrPermId,
    IbkrClientId,
    IbkrExecId,
    TwsOrderStatusEvent,
    TwsExecution,
    TwsCommissionReport,
    TwsAccountValue,
    TwsPortfolioItem,
    TwsPosition,
    TwsErrorEvent,
    TwsContract,
    IbkrSecType,
    IbkrConId,
)
from base_types.ids_and_enums import AccountId
from base_events.order_events import (
    BrokerOrderStatusEvent,
    BrokerExecutionEvent,
    BrokerOrderErrorEvent,
)
from base_types.position_and_account import AccountSnapshot  # if needed


def handle_tws_order_status(adapter: "IbkrAsyncAdapter", raw_order_status: Any) -> None:
    tws_ev = TwsOrderStatusEvent(
        order_id=IbkrOrderId(raw_order_status.orderId),  # type: ignore
        status=raw_order_status.status,                  # type: ignore (IbkrOrderStatusStr)
        filled=raw_order_status.filled,                  # type: ignore
        remaining=raw_order_status.remaining,            # type: ignore
        avg_fill_price=raw_order_status.avgFillPrice,    # type: ignore
        perm_id=IbkrPermId(raw_order_status.permId),     # type: ignore
        parent_id=None,
        last_fill_price=raw_order_status.lastFillPrice,  # type: ignore
        client_id=IbkrClientId(raw_order_status.clientId),  # type: ignore
    )

    oms_id = adapter._resolve_oms_id(tws_ev.order_id, tws_ev.perm_id)

    ev = BrokerOrderStatusEvent.from_ibkr_tws(
        oms_id=oms_id,
        tws=tws_ev,
    )
    adapter._event_sink(ev)


def handle_tws_exec_details(
    adapter: "IbkrAsyncAdapter",
    raw_contract: Any,
    raw_execution: Any,
) -> None:
    tws_exec = TwsExecution(
        exec_id=IbkrExecId(raw_execution.execId),  # type: ignore
        time=raw_execution.time,                  # type: ignore
        acct_number=raw_execution.acctNumber,     # type: ignore
        exchange=raw_execution.exchange,          # type: ignore
        side=raw_execution.side,                  # type: ignore (IbkrOrderAction)
        shares=raw_execution.shares,              # type: ignore
        price=raw_execution.price,                # type: ignore
        perm_id=IbkrPermId(raw_execution.permId), # type: ignore
        order_id=IbkrOrderId(raw_execution.orderId),  # type: ignore
        client_id=IbkrClientId(raw_execution.clientId),  # type: ignore
        liquidation=raw_execution.liquidation,    # type: ignore
        cum_qty=raw_execution.cumQty,             # type: ignore
        avg_price=raw_execution.avgPrice,         # type: ignore
    )

    oms_id = adapter._resolve_oms_id(tws_exec.order_id, tws_exec.perm_id)

    ev = BrokerExecutionEvent.from_ibkr_tws(
        oms_id=oms_id,
        tws=tws_exec,
    )
    adapter._event_sink(ev)


def handle_tws_commission_report(
    adapter: "IbkrAsyncAdapter",
    raw_comm: Any,
) -> None:
    tws_comm = TwsCommissionReport(
        exec_id=IbkrExecId(raw_comm.execId),      # type: ignore
        commission=raw_comm.commission,          # type: ignore
        currency=raw_comm.currency,              # type: ignore
        realized_pnl=getattr(raw_comm, "realizedPNL", None),
        yield_=getattr(raw_comm, "yield", None),
        yield_redemption_date=getattr(raw_comm, "yieldRedemptionDate", None),
    )
    # TODO: build BrokerCommissionEvent.from_ibkr_tws(...) once you wire commissions


def handle_tws_error(adapter: "IbkrAsyncAdapter", id_: int, code: int, msg: str,
                     advancedOrderRejectJson: str | None = None) -> None:
    tws_err = TwsErrorEvent(
        req_id=id_,
        error_code=code,
        error_msg=msg,
    )

    ev = BrokerOrderErrorEvent.from_ibkr_tws(tws_err)
    adapter._event_sink(ev)


def handle_tws_account_value(adapter: "IbkrAsyncAdapter", raw: Any) -> None:
    tws_av = TwsAccountValue(
        key=raw.key,          # type: ignore
        value=raw.value,      # type: ignore
        currency=raw.currency,# type: ignore
        account=raw.account,  # type: ignore
    )
    # TODO: aggregate into AccountSnapshot and emit an event


def handle_tws_portfolio(adapter: "IbkrAsyncAdapter", raw: Any) -> None:
    tws_pf = TwsPortfolioItem(
        contract=TwsContract(
            con_id=IbkrConId(raw.contract.conId),        # type: ignore
            symbol=raw.contract.symbol,                  # type: ignore
            sec_type=IbkrSecType(raw.contract.secType),  # type: ignore
            currency=raw.contract.currency,              # type: ignore
            exchange=raw.contract.exchange,              # type: ignore
        ),
        position=raw.position,          # type: ignore
        market_price=raw.marketPrice,   # type: ignore
        market_value=raw.marketValue,   # type: ignore
        average_cost=raw.averageCost,   # type: ignore
        unrealized_pnl=raw.unrealizedPNL,  # type: ignore
        realized_pnl=raw.realizedPNL,      # type: ignore
        account=raw.account,           # type: ignore
    )
    # TODO: map to PositionState and emit


def handle_tws_position(adapter: "IbkrAsyncAdapter", raw: Any) -> None:
    tws_pos = TwsPosition(
        account=raw.account,  # type: ignore
        contract=TwsContract(
            con_id=IbkrConId(raw.contract.conId),        # type: ignore
            symbol=raw.contract.symbol,                  # type: ignore
            sec_type=IbkrSecType(raw.contract.secType),  # type: ignore
            currency=raw.contract.currency,              # type: ignore
            exchange=raw.contract.exchange,              # type: ignore
        ),
        position=raw.position,  # type: ignore
        avg_cost=raw.avgCost,   # type: ignore
    )
    # TODO: map to PositionState and emit
