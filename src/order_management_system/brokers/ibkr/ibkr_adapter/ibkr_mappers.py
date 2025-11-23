from __future__ import annotations

from typing import Any, Iterable

from base_types.ids_and_enums import AccountId
from base_types.contracts_and_specs import OrderSpec, ComboSpec, Contract
from ibkr_types import (
    IbkrOrderAction,
    IbkrOrderType,
    IbkrTif,
    IbkrSecType,
    TwsContract,
    TwsOrder,
)


def build_single_order(
    account_id: AccountId,
    spec: OrderSpec,
) -> tuple[TwsContract, TwsOrder]:
    """
    Map a single-leg OMS OrderSpec → TwsContract + TwsOrder.
    """
    tws_contract = TwsContract(
        symbol=str(spec.symbol),
        sec_type=IbkrSecType.STK,  # TODO: derive from Contract / SecurityType
        currency="USD",
        exchange="SMART",
    )

    action = (
        IbkrOrderAction.BUY
        if spec.side.name.startswith("BUY")
        else IbkrOrderAction.SELL
    )

    order_type = map_order_type(spec.order_type)
    tif = map_tif(spec.time_in_force)

    tws_order = TwsOrder(
        order_id=None,  # TWS will assign
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


def build_combo_order(
    account_id: AccountId,
    spec: ComboSpec,
) -> tuple[TwsContract, TwsOrder]:
    """
    Map a multi-leg ComboSpec → TwsContract (BAG) + TwsOrder.
    """
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

    order_type = map_order_type(spec.order_type)
    tif = map_tif(spec.time_in_force)

    tws_order = TwsOrder(
        order_id=None,
        action=IbkrOrderAction.BUY,  # net action is in legs
        total_quantity=spec.total_quantity,
        order_type=order_type,
        lmt_price=spec.limit_price,
        tif=tif,
        account=str(account_id),
        transmit=True,
    )

    return tws_contract, tws_order


def map_order_type(order_type: Any) -> IbkrOrderType:
    """
    Map your OrderType enum → IbkrOrderType.
    """
    try:
        return IbkrOrderType(order_type.value)  # type: ignore
    except Exception:
        if getattr(order_type, "name", None) == "MKT":
            return IbkrOrderType.MKT
        if getattr(order_type, "name", None) == "LMT":
            return IbkrOrderType.LMT
        raise


def map_tif(tif: Any) -> IbkrTif:
    try:
        return IbkrTif(tif.value)  # type: ignore
    except Exception:
        if getattr(tif, "name", None) == "DAY":
            return IbkrTif.DAY
        if getattr(tif, "name", None) == "GTC":
            return IbkrTif.GTC
        raise


def build_contract_query(symbol: "Symbol") -> TwsContract:
    """
    Creates a partial TwsContract suitable for searching.
    """
    # import here to avoid circular deps
    from tools.ci.shims.AlgorithmImports import Symbol as QC_Symbol  # type: ignore

    return TwsContract(
        symbol=str(symbol),
        sec_type=IbkrSecType.STK,
        currency="USD",
        exchange="SMART",
    )


def map_details_to_contracts(details_list: list) -> Iterable[Contract]:
    """
    Maps a list of ib_insync ContractDetails objects to your domain Contract type.
    """
    if not details_list:
        return []

    # TODO: replace placeholder with real mapping
    return [Contract(...) for details in details_list]
