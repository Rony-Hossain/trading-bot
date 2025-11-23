# src/order_management_system/base_interfaces/execution_engine_interface.py
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable, Optional, Dict

from ..base_types.ids_and_enums import AccountId, OMSId, Symbol
from ..base_types.contracts_and_specs import OrderSpec, ComboSpec
from ..base_types.position_and_account import PositionState, AccountSnapshot


class ExecutionEngineInterface(ABC):
    """
    Broker-agnostic OMS execution interface.

    - This is what your TradeEngine (or any strategy host) talks to.
    - Underneath, the engine is free to be async, use a reactor, DB, adapters, etc.
    """

    # ------------ ORDER SUBMISSION -----------------------------------------

    @abstractmethod
    def submit_order(
        self,
        account_id: AccountId,
        spec: OrderSpec,
    ) -> OMSId:
        """
        Submit a single-leg order.

        IMPORTANT:
          - This MUST be fast and non-blocking from the caller's POV.
          - It should:
              1) persist intent
              2) enqueue command for reactor
              3) return the assigned OMSId
        """
        raise NotImplementedError

    @abstractmethod
    def submit_combo_order(
        self,
        account_id: AccountId,
        combo: ComboSpec,
    ) -> OMSId:
        """
        Submit a multi-leg spread (Iron Condor, Butterfly, etc.).

        Same guarantees as submit_order.
        """
        raise NotImplementedError

    # ------------ CANCEL / FLATTEN -----------------------------------------

    @abstractmethod
    def cancel_order(self, account_id: AccountId, oms_id: OMSId) -> None:
        """Request cancel of an existing order."""
        raise NotImplementedError

    @abstractmethod
    def flatten_symbol(self, account_id: AccountId, symbol: Symbol, reason: str) -> None:
        """
        Flatten a single symbol in this account (submit offsetting orders).
        """
        raise NotImplementedError

    @abstractmethod
    def flatten_all(self, account_id: AccountId, reason: str) -> None:
        """
        Global flatten (used for kill switch, EOD, etc.).
        """
        raise NotImplementedError

    # ------------ STATE QUERIES (READ-ONLY) --------------------------------

    @abstractmethod
    def get_position(self, account_id: AccountId, symbol: Symbol) -> Optional[PositionState]:
        """Return current PositionState for given account+symbol, if any."""
        raise NotImplementedError

    @abstractmethod
    def get_all_positions(self, account_id: AccountId) -> Iterable[PositionState]:
        """Return all open positions for account."""
        raise NotImplementedError

    @abstractmethod
    def get_account_snapshot(self, account_id: AccountId) -> Optional[AccountSnapshot]:
        """Return latest account snapshot (NetLiq, BP, PnL)."""
        raise NotImplementedError

