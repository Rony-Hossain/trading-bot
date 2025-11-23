# src/order_management_system/brokers/ibkr/ibkr_types.py

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, NewType


# ============================================================================
# COMMON ID TYPES (IBKR-SPECIFIC)
# ============================================================================

IbkrOrderId = NewType("IbkrOrderId", int)      # TWS orderId
IbkrPermId = NewType("IbkrPermId", int)        # stable permId
IbkrClientId = NewType("IbkrClientId", int)    # ib_insync clientId
IbkrExecId = NewType("IbkrExecId", str)        # executionId / execId
IbkrConId = NewType("IbkrConId", int)          # contract id


# ============================================================================
# ENUMS / CONSTANTS
# ============================================================================


class IbkrSecType(str, Enum):
    STK = "STK"
    OPT = "OPT"
    FUT = "FUT"
    IND = "IND"
    CASH = "CASH"
    CFD = "CFD"
    FOP = "FOP"
    WAR = "WAR"
    BOND = "BOND"
    CMDTY = "CMDTY"
    FUND = "FUND"
    BAG = "BAG"
    CRYPTO = "CRYPTO"


class IbkrRight(str, Enum):
    CALL = "C"
    PUT = "P"


class IbkrOrderAction(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    SSHORT = "SSHORT"          # short sell
    BUY_TO_COVER = "BOTC"      # internal mapping if you choose to use it


class IbkrTif(str, Enum):
    DAY = "DAY"
    GTC = "GTC"
    IOC = "IOC"
    FOK = "FOK"
    GTD = "GTD"   # good-till-date
    OPG = "OPG"   # open auction
    DTC = "DTC"   # day-till-cancel (rare)


class IbkrOrderType(str, Enum):
    # Primary
    MKT = "MKT"
    LMT = "LMT"
    STP = "STP"
    STP_LMT = "STP LMT"
    MKT_PRT = "MKT PRT"
    LMT_PRT = "LMT PRT"

    # Auction / close
    MOC = "MOC"
    LOC = "LOC"
    MTL = "MTL"

    # Advanced / algos
    TRAIL = "TRAIL"
    REL = "REL"
    VWAP = "VWAP"
    AD = "AD"
    PEG_MKT = "PEGMKT"
    PEG_PRIM = "PEGPRIM"
    PEG_MID = "MIDPRICE"


class IbkrOrderStatusStr(str, Enum):
    """
    Raw status strings emitted by TWS orderStatus callbacks.
    """
    API_PENDING = "ApiPending"
    PENDING_SUBMIT = "PendingSubmit"
    PENDING_CANCEL = "PendingCancel"
    PRE_SUBMITTED = "PreSubmitted"
    SUBMITTED = "Submitted"
    CANCELLED = "Cancelled"
    FILLED = "Filled"
    INACTIVE = "Inactive"


# ============================================================================
# TWS / IB GATEWAY (ib_insync-style) DATA OBJECTS
# ============================================================================


@dataclass(slots=True)
class TwsComboLeg:
    """
    Strongly-typed representation of a single leg in a TWS Combo Contract (BAG).

    This mirrors the fields IB expects on ComboLeg:
      - conId:   underlying contract id
      - ratio:   leg ratio (1 for standard spreads)
      - action:  BUY / SELL for the leg
      - exchange: optional override exchange
    """
    conId: IbkrConId
    ratio: int
    action: IbkrOrderAction      # BUY or SELL for the leg
    exchange: Optional[str] = None


@dataclass(slots=True)
class TwsContract:
    """
    Minimal TWS Contract representation we care about.
    This maps 1:1 to ib_insync.Contract fields we actually use.
    """

    con_id: Optional[IbkrConId] = None
    symbol: Optional[str] = None
    sec_type: IbkrSecType = IbkrSecType.STK
    currency: str = "USD"
    exchange: str = "SMART"
    primary_exchange: Optional[str] = None

    # Option/Future specifics
    last_trade_date_or_contract_month: Optional[str] = None  # "20251219"
    strike: Optional[float] = None
    right: Optional[IbkrRight] = None
    multiplier: Optional[str] = None
    local_symbol: Optional[str] = None
    trading_class: Optional[str] = None

    # For combos (BAG)
    combo_legs: List[TwsComboLeg] = field(default_factory=list)


@dataclass(slots=True)
class TwsOrder:
    """
    Minimal TWS Order representation we use for live orders.
    """

    order_id: Optional[IbkrOrderId] = None
    action: IbkrOrderAction = IbkrOrderAction.BUY
    total_quantity: float = 0.0
    order_type: IbkrOrderType = IbkrOrderType.MKT

    lmt_price: Optional[float] = None      # for LMT, STP_LMT
    aux_price: Optional[float] = None      # for STP, TRAIL

    tif: IbkrTif = IbkrTif.DAY
    outside_rth: bool = False
    good_till_date: Optional[str] = None   # "YYYYMMDD HH:MM:SS"

    account: Optional[str] = None
    transmit: bool = True
    parent_id: Optional[IbkrOrderId] = None

    # Algo & advanced params
    algo_strategy: Optional[str] = None
    algo_params: Dict[str, Any] = field(default_factory=dict)

    # Misc flags
    what_if: bool = False
    oca_group: Optional[str] = None
    oca_type: Optional[int] = None      # 1, 2, 3 → IB's OCA type codes
    tif_override: Optional[str] = None  # rare IB quirks


@dataclass(slots=True)
class TwsOrderStatusEvent:
    """
    Data we get from TWS / ib_insync orderStatus callback.
    """

    order_id: IbkrOrderId
    status: IbkrOrderStatusStr

    filled: float
    remaining: float
    avg_fill_price: float

    perm_id: IbkrPermId
    parent_id: Optional[IbkrOrderId]
    last_fill_price: float
    client_id: IbkrClientId

    why_held: Optional[str] = None
    mkt_cap_price: Optional[float] = None

    # raw timestamp is not part of callback, but adapter may enrich
    received_at: datetime = field(default_factory=datetime.utcnow)
    raw: Dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class TwsExecution:
    """
    Data from IBKR ExecutionDetails / execDetails callback.
    """

    exec_id: IbkrExecId
    time: datetime
    acct_number: str
    exchange: str
    side: IbkrOrderAction
    shares: float
    price: float

    perm_id: IbkrPermId
    order_id: IbkrOrderId
    client_id: IbkrClientId

    liquidation: int = 0   # 1 if liquidation
    cum_qty: float = 0.0
    avg_price: float = 0.0

    raw: Dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class TwsCommissionReport:
    """
    Commission report associated with an execution (commissionReport callback).
    """

    exec_id: IbkrExecId
    commission: float
    currency: str

    realized_pnl: Optional[float] = None
    yield_: Optional[float] = None
    yield_redemption_date: Optional[str] = None  # "YYYYMMDD"

    raw: Dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class TwsAccountValue:
    """
    Account summary line (accountSummary callback).
    """

    key: str        # e.g. "NetLiquidation", "BuyingPower"
    value: str      # raw string as IB sends it
    currency: str
    account: str

    received_at: datetime = field(default_factory=datetime.utcnow)


@dataclass(slots=True)
class TwsPortfolioItem:
    """
    Portfolio-level position data (updatePortfolio callback).
    """

    contract: TwsContract
    position: float
    market_price: float
    market_value: float
    average_cost: float
    unrealized_pnl: float
    realized_pnl: float
    account: str

    received_at: datetime = field(default_factory=datetime.utcnow)


@dataclass(slots=True)
class TwsPosition:
    """
    Position from reqPositions / position callback.
    """

    account: str
    contract: TwsContract
    position: float
    avg_cost: float
    received_at: datetime = field(default_factory=datetime.utcnow)


@dataclass(slots=True)
class TwsErrorEvent:
    """
    Wrapper for IB's error(id, code, msg) callback.
    """

    req_id: int
    error_code: int
    error_msg: str
    is_warning: bool = False
    received_at: datetime = field(default_factory=datetime.utcnow)
    raw: Dict[str, Any] = field(default_factory=dict)


# ============================================================================
# CLIENT PORTAL WEB API (REST) TYPES
# ============================================================================


@dataclass(slots=True)
class CpOrderLeg:
    """
    One leg of a Client Portal Web order (used for combos as well).
    """

    conid: int           # contract id
    ratio: int           # leg ratio
    side: str            # "BUY" or "SELL"
    type: str = "LEG"    # IB's CP type code
    exchange: Optional[str] = None


@dataclass(slots=True)
class CpOrderRequest:
    """
    Request payload to place an order via Client Portal Web API.
    Roughly matches /iserver/account/{accountId}/orders.
    """

    account_id: str      # IB account id
    conid: int           # conid for primary instrument
    side: str            # "BUY" or "SELL"
    order_type: str      # "MKT", "LMT", "STP", etc.
    tif: str             # "DAY", "GTC", "IOC", etc.
    quantity: float

    price: Optional[float] = None
    aux_price: Optional[float] = None

    # Multi-leg support
    use_combo: bool = False
    legs: List[CpOrderLeg] = field(default_factory=list)

    outside_rth: Optional[bool] = None
    transmit: bool = True
    referrer: Optional[str] = None     # free-form tag / client-tag

    # Misc client-side metadata
    client_order_id: Optional[str] = None
    meta: Dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class CpOrderReply:
    """
    Immediate reply from place-order endpoint (may include warnings).
    """

    order_id: Optional[str] = None   # IB may return temp order id
    status: Optional[str] = None     # "submitted", "warning", etc.
    message: Optional[str] = None
    raw: Dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class CpOrderStatus:
    """
    Order status record from CP Web API (e.g. /iserver/account/orders).
    """

    order_id: str
    account_id: str
    conid: int

    status: str             # "Submitted", "Filled", etc.
    side: str               # "BUY" or "SELL"
    order_type: str         # "MKT", "LMT", etc.
    tif: str

    filled: float
    remaining: float
    avg_price: float

    perm_id: Optional[int] = None
    parent_id: Optional[int] = None

    last_fill_price: Optional[float] = None
    last_update: Optional[datetime] = None

    raw: Dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class CpPosition:
    """
    Position record from CP Web API (e.g. /portfolio/{accountId}/positions).
    """

    account_id: str
    conid: int
    symbol: str
    sec_type: str
    currency: str

    position: float
    avg_price: float
    market_price: Optional[float] = None
    market_value: Optional[float] = None
    unrealized_pnl: Optional[float] = None
    realized_pnl: Optional[float] = None

    raw: Dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class CpAccountSummary:
    """
    Account summary record from CP Web API (e.g. /portfolio/accounts,
    /portfolio/{id}/summary).
    """

    account_id: str
    alias: Optional[str]
    currency: str

    net_liquidation: Optional[float] = None
    cash: Optional[float] = None
    buying_power: Optional[float] = None
    maintenance_margin: Optional[float] = None

    realized_pnl_today: Optional[float] = None
    unrealized_pnl: Optional[float] = None

    raw: Dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class CpErrorResponse:
    """
    Generic error response wrapper for Client Portal Web API.
    """

    error: str
    code: Optional[int] = None
    details: Dict[str, Any] = field(default_factory=dict)


# ============================================================================
# RAW GREEKS / MODEL DATA FROM IBKR (FOR RISK PIPELINE)
# ============================================================================


@dataclass(slots=True)
class TwsGreeksUpdate:
    """
    Raw model-Greeks snapshot from IBKR (via market data / option model).

    This is an adapter-level DTO. Your adapter will map this into the
    domain-level Greeks / PositionGreeks types in base_types.risk_models.
    """

    con_id: IbkrConId
    symbol: str

    model_price: float                 # IB's option model price
    implied_vol: float                 # Implied volatility
    delta: float
    gamma: float
    vega: float
    theta: float
    und_price: float                   # underlying price used in model

    account: Optional[str] = None      # if account-specific
    received_at: datetime = field(default_factory=datetime.utcnow)
    raw: Dict[str, Any] = field(default_factory=dict)






# TODOs for ibkr_types.py
# 1. Combo / Multi-Leg Support (Structural)

#  Introduce TwsComboLeg dataclass
# Strongly-typed combo leg instead of Dict[str, Any]:

# conId: IbkrConId

# ratio: int

# action: IbkrOrderAction

# exchange: Optional[str]

#  Update TwsContract.combo_legs

# Change from List[Dict[str, Any]] → List[TwsComboLeg].

#  Document combo semantics

# Docstring note: IBKR expects ratio/action per leg; adapter must ensure sum(ratio * side) is correct for spreads (Iron Condor, Butterfly, etc.).

# 2. Greeks & Volatility Data Flow

#  Add a TWS Greeks DTO (wire-level, before mapping to domain Greeks)

# e.g. TwsGreeksUpdate with:

# con_id: IbkrConId

# underlying_price: float

# delta, gamma, vega, theta, implied_vol

# received_at: datetime

# raw: Dict[str, Any]

#  Clarify role of Greeks in this file

# Decide: Greeks here is domain or IBKR-specific?

# Add docstring stating: “Adapter maps TWS greeks into this canonical Greeks before sending to risk engine.”

#  Add comment about combo Greeks

# On ComboLegGreeks / ComboGreeks, document that:

# leg quantity = combo_qty * leg.ratio * direction_sign

# net is what gets sent to PositionGreeks / risk engine.

# 3. TWS Types Completeness / Cleanliness

#  Review IbkrOrderType coverage

# Confirm all order types you might use are listed:

# Already: MKT, LMT, STP, STP_LMT, MOC, LOC, MTL, TRAIL, REL, VWAP, AD, PEGMKT, PEGPRIM, MIDPRICE.

# If you rely on others (e.g., MKTCLS, LMTCLS), add them now so no “magic strings” appear later.

#  Remove confusing IOC/FOK comment

# The comment under IbkrOrderType about IOC/FOK being TIF is redundant since IbkrTif already exists.

# Clean comment block to avoid future confusion.

#  Standardize names with real API

# Make sure field names in TwsOrder / TwsContract match ib_insync.Contract / .Order as much as possible (lastTradeDateOrContractMonth, localSymbol, tradingClass, etc.), so your adapter mapping is trivial.

# 4. Client Portal Web (REST) DTOs

#  Validate CP model fields against actual endpoints

# Check that CpOrderRequest, CpOrderStatus, CpPosition, CpAccountSummary match the real JSON:

# conid vs conId

# secType vs sec_type

# currency key names.

# Add comments # matches /iserver/account/{id}/orders response etc.

#  Clarify multi-leg REST behavior

# In CpOrderLeg / CpOrderRequest, document:

# How IB expects combo orders (when use_combo=True, legs non-empty).

# That conid on root vs legs may both be present; adapter rules for mapping from ComboSpec.

# 5. Error / Status Handling

#  Extend TwsErrorEvent with severity classification hint

# Add docstring note for adapter:

# Error classes: connectivity vs order vs account vs warning.

# This will drive whether engine halts, retries, or ignores.

#  Unify status naming

# Confirm IbkrOrderStatusStr covers all states you care about:

# ApiPending, PendingSubmit, PendingCancel, PreSubmitted, Submitted, Cancelled, Filled, Inactive.

# Add comment mapping to your internal OrderStatus (e.g. Submitted → WORKING, Cancelled/Inactive → CANCELED).

# 6. Imports & Separation of Concerns

#  Keep ibkr_types.py pure DTOs

# Ensure:

# No ib_insync imports.

# No business logic.

# No engine/risk imports.

# This file = wire representation only.

#  Minimize cross-domain imports

# If PositionGreeks, ComboLegGreeks, etc. are truly OMS-level, consider moving them to base_types/risk_models.py and leaving only IBKR-specific DTOs here.

# If you keep them here, add a clear comment: “These are shared between adapter and OMS risk module.”

# 7. Documentation Hooks

#  Top-of-file docstring

# One paragraph: “This module defines all IBKR-specific wire-level data structures (TWS, Client Portal Web API) used by the IBKR adapter. No engine logic lives here.”

#  Per-section headings

# Already present (# TWS, # CLIENT PORTAL), but add short comments on how they are used:

# e.g. # Used as payloads for REST client in ibkr_adapter.py.

# 8. Test TODOs Tied to ibkr_types.py

# (Not writing tests now, just marking what ibkr_types.py must support.)

#  Round-trip combo test

# Ensure a ComboSpec → adapter mapping → TwsContract(combo_legs) → back to domain preserves:

# all leg conIds

# ratios

# BUY/SELL semantics.

#  Greeks integration test skeleton

# Ensure TwsGreeksUpdate → mapped Greeks → PositionGreeks matches expected math for a simple Iron Condor.
