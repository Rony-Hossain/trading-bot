from enum import Enum, IntEnum
from typing import NewType

# --- ID TYPES ---
OMSId = NewType("OMSId", int)
BrokerOrderId = NewType("BrokerOrderId", str)
PermId = NewType("PermId", int)
AccountId = NewType("AccountId", str)
Symbol = NewType("Symbol", str)

# --- ENUMS ---
class SecurityType(Enum):
    STK = "STK"
    OPT = "OPT"
    FUT = "FUT"
    IND = "IND"
    CASH = "CASH"
    CFD = "CFD"
    BAG = "BAG"
    CRYPTO = "CRYPTO"

class OrderAction(Enum):
    BUY = "BUY"
    SELL = "SELL"

class OrderType(Enum):
    MKT = "MKT"
    LMT = "LMT"
    STP = "STP"
    STP_LMT = "STP LMT"
    TRAIL = "TRAIL"
    REL = "REL"
    MID = "MID"
    MOC = "MOC"
    LOC = "LOC"
    MTL = "MTL"
    VWAP = "VWAP"
    AD = "AD"
    PEG_MKT = "PEGMKT"
    PEG_PRY = "PEGPRY"
    DAY = "DAY" # NOTE: TIF values here for compatibility, but use TimeInForce
    GTC = "GTC"
    GTD = "GTD"
    FOK = "FOK"
    IOC = "IOC"
    LIT = "LIT"
    IWO = "IWO"
    ONE_CANCELS_OTHER = "OCO"

class RightType(Enum):
    PUT = "P"
    CALL = "C"

class TimeInForce(str, Enum):
    DAY = "DAY"
    GTC = "GTC"
    IOC = "IOC"
    FOK = "FOK"
    GTD = "GTD"

class OrderStatus(str, Enum):
    NEW = "NEW"
    PENDING_SUBMIT = "PENDING_SUBMIT"
    WORKING = "WORKING"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    CANCELED = "CANCELED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"
    STALE = "STALE"
    UNKNOWN = "UNKNOWN"

class EventPriority(IntEnum):
    P0_CRITICAL = 0
    P1_HIGH = 1
    P2_NORMAL = 2

class FlattenReason(str, Enum):
    EOD = "EOD"
    KILL_SWITCH = "KILL_SWITCH"
    RISK_LIMIT = "RISK_LIMIT"
    MANUAL = "MANUAL"
    UNKNOWN = "UNKNOWN"

class CancelReason(str, Enum):
    USER_REQUEST = "USER_REQUEST"
    REPLACE = "REPLACE"
    RISK_REJECT = "RISK_REJECT"
    STALE_RECONCILE = "STALE_RECONCILE"
    FLATTEN = "FLATTEN"
    UNKNOWN = "UNKNOWN"

class BrokerType(str, Enum):
    IBKR = "IBKR"
    WEBULLS = "WEBULLS"
    MOOMOO = "MOOMOO"
    ALPACA = "ALPACA"
    DUMMY = "DUMMY"
    OTHER = "OTHER"

class BrokerConnectionStatus(str, Enum):
    CONNECTED = "CONNECTED"
    DISCONNECTED = "DISCONNECTED"
    RECONNECTING = "RECONNECTING"
    ERROR = "ERROR"
    UNKNOWN = "UNKNOWN"

class NetworkStatus(str, Enum):
    ONLINE = "ONLINE"
    OFFLINE = "OFFLINE"
    DEGRADED = "DEGRADED"
    UNKNOWN = "UNKNOWN"

class TradeSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    SHORT_SELL = "SHORT_SELL"
    COVER = "COVER"
    UNKNOWN = "UNKNOWN"