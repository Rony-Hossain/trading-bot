# src/order_management_system/brokers/ibkr/ibkr_market_account.py

from __future__ import annotations

import logging
from typing import Iterable

from ib_insync import IB
from tools.ci.shims.AlgorithmImports import Symbol  # type: ignore

from ...base_types.contracts_and_specs import Contract
from ...base_types.ids_and_enums import AccountId
from .ibkr_mappers import (
    build_contract_query,
    map_details_to_contracts,
)

log = logging.getLogger(__name__)


# =============================================================================
# CONTRACT LOOKUP
# =============================================================================


async def request_contract_details(
    ib: IB,
    symbol: Symbol,
) -> Iterable[Contract]:
    """
    Asynchronously look up contract details via IBKR, preventing event loop blocking.

    This is the logic that used to live inside IbkrAsyncAdapter.request_contract_details.
    """
    query = build_contract_query(symbol)

    try:
        details_list = await ib.reqContractDetailsAsync(query)
    except Exception as exc:
        log.error("IBKR contract details request failed for %s: %s", symbol, exc)
        raise

    return map_details_to_contracts(details_list)


# =============================================================================
# MARKET DATA SUBSCRIPTIONS
# =============================================================================


def subscribe_market_data(
    ib: IB,
    contract: Contract,
) -> None:
    """
    Request real-time quote updates for a specific contract.

    NOTE: still a stub – you must implement Contract → ib_insync.Contract
    mapping when you wire real market data.
    """
    # TODO: convert domain `Contract` → ib_insync.Contract and call:
    #   ib.reqMktData(ib_contract, '', False, False)
    #
    # For now, just log so calls are visible in tests.
    log.debug("IBKR subscribe_market_data contract=%r (not yet implemented)", contract)


def unsubscribe_market_data(
    ib: IB,
    contract: Contract,
) -> None:
    """
    Cancel real-time quote updates for a specific contract.
    """
    # TODO: convert domain `Contract` → ib_insync.Contract and call:
    #   ib.cancelMktData(ib_contract)
    log.debug("IBKR unsubscribe_market_data contract=%r (not yet implemented)", contract)


# =============================================================================
# ACCOUNT / POSITION DATA
# =============================================================================


def req_account_data(
    ib: IB,
    account_id: AccountId,
) -> None:
    """
    Subscribe to account summary / portfolio / positions for risk + reconciliation.

    Still a thin stub – you will wire concrete ib.reqAccountSummary / reqPositions
    when you implement the account/risk pipeline.
    """
    # Examples of what you'll eventually call:
    #
    #   ib.reqAccountSummary(
    #       account=str(account_id),
    #       tags="NetLiquidation,BuyingPower,AvailableFunds"
    #   )
    #   ib.reqPositions()
    #
    log.debug("IBKR req_account_data account_id=%s (not yet implemented)", account_id)


def req_open_positions(ib: IB) -> None:
    """
    Request all currently held positions for reconciliation.
    """
    # Eventually:
    #   ib.reqPositions()
    log.debug("IBKR req_open_positions (not yet implemented)")
