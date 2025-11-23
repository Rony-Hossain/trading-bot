# src/order_management_system/brokers/ibkr/ibkr_config.py

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Optional

# NOTE: we only depend on light base types here.
# If you want to avoid cross-layer imports, change AccountId to str.
try:
    from ...base_types.ids_and_enums import AccountId  # type: ignore
except Exception:  # during early bootstrapping, you can temporarily stub this
    AccountId = str  # type: ignore


# =============================================================================
# ERROR TYPE
# =============================================================================


class IbkrConfigError(ValueError):
    """Raised when IBKR adapter configuration is invalid or dangerous."""


# =============================================================================
# SMALL INTERNAL HELPERS
# =============================================================================


def _get_env(name: str, default: Optional[str] = None) -> Optional[str]:
    val = os.getenv(name)
    if val is None or val == "":
        return default
    return val


def _get_env_int(name: str, default: int) -> int:
    val = _get_env(name)
    if val is None:
        return default
    try:
        return int(val)
    except ValueError as exc:
        raise IbkrConfigError(f"{name} must be int, got {val!r}") from exc


def _get_env_float(name: str, default: float) -> float:
    val = _get_env(name)
    if val is None:
        return default
    try:
        return float(val)
    except ValueError as exc:
        raise IbkrConfigError(f"{name} must be float, got {val!r}") from exc


def _get_env_bool(name: str, default: bool) -> bool:
    val = _get_env(name)
    if val is None:
        return default
    val_lower = val.strip().lower()
    if val_lower in ("1", "true", "yes", "on"):
        return True
    if val_lower in ("0", "false", "no", "off"):
        return False
    raise IbkrConfigError(f"{name} must be boolean-like, got {val!r}")


# =============================================================================
# TWS / IB GATEWAY CONFIG
# =============================================================================
#
# ENV VARS (TWS / Gateway):
#   IBKR_ENV                       = "paper" | "live" | "sim"
#   IBKR_TWS_HOST                  = "127.0.0.1"
#   IBKR_TWS_PORT                  = "7497"    # 7497 paper, 7496 live (by convention)
#   IBKR_TWS_CLIENT_ID             = "101"
#   IBKR_TWS_CONNECT_TIMEOUT_SEC   = "5.0"
#   IBKR_TWS_READ_TIMEOUT_SEC      = "30.0"
#   IBKR_TWS_RECONNECT_BACKOFF_INITIAL_SEC = "1.0"
#   IBKR_TWS_RECONNECT_BACKOFF_MAX_SEC     = "30.0"
#   IBKR_TWS_USE_TLS               = "false"
# =============================================================================


@dataclass(slots=True)
class TwsGatewayConfig:
    """
    Connection parameters for TWS / IB Gateway via ib_insync.

    This is purely config; no network / ib_insync imports here.
    """

    host: str = "127.0.0.1"
    port: int = 7497  # default paper trading port
    client_id: int = 101

    connect_timeout_sec: float = 5.0
    read_timeout_sec: float = 30.0

    reconnect_backoff_initial_sec: float = 1.0
    reconnect_backoff_max_sec: float = 30.0

    use_tls: bool = False

    # "paper" | "live" | "sim"
    profile: str = "paper"

    def validate(self) -> None:
        if not self.host:
            raise IbkrConfigError("TWS host must not be empty")

        if self.port <= 0 or self.port > 65535:
            raise IbkrConfigError(f"Invalid TWS port: {self.port}")

        if self.client_id < 0:
            raise IbkrConfigError(f"client_id must be >= 0, got {self.client_id}")

        # Hard rule: do NOT share clientId=0 with TWS UI.
        if self.client_id == 0:
            raise IbkrConfigError(
                "client_id=0 is reserved for TWS UI. "
                "Use a dedicated client_id for the OMS."
            )

        if self.connect_timeout_sec <= 0:
            raise IbkrConfigError("connect_timeout_sec must be > 0")

        if self.read_timeout_sec <= 0:
            raise IbkrConfigError("read_timeout_sec must be > 0")

        if self.reconnect_backoff_initial_sec <= 0:
            raise IbkrConfigError("reconnect_backoff_initial_sec must be > 0")

        if self.reconnect_backoff_max_sec < self.reconnect_backoff_initial_sec:
            raise IbkrConfigError(
                "reconnect_backoff_max_sec must be >= reconnect_backoff_initial_sec"
            )

        if self.profile not in ("paper", "live", "sim"):
            raise IbkrConfigError(
                f"profile must be one of ['paper', 'live', 'sim'], got {self.profile!r}"
            )


# =============================================================================
# CLIENT PORTAL WEB API CONFIG
# =============================================================================
#
# ENV VARS (Client Portal):
#   IBKR_CP_ENABLED           = "false"
#   IBKR_CP_BASE_URL          = "https://localhost:5000/v1/api"
#   IBKR_CP_ACCOUNT_ID        = "U1234567"
#   IBKR_CP_API_TIMEOUT_SEC   = "10.0"
#   IBKR_CP_MAX_RETRIES       = "3"
#   IBKR_CP_RETRY_BACKOFF_INITIAL_SEC = "0.5"
#   IBKR_CP_RETRY_BACKOFF_MAX_SEC     = "5.0"
# =============================================================================


@dataclass(slots=True)
class ClientPortalConfig:
    """
    Configuration for the Client Portal Web API (REST).

    Used for:
      - backup reconciliation
      - position / account sanity checks
      - or disabled entirely if you only use TWS/ib_insync
    """

    enabled: bool = False
    base_url: str = "https://localhost:5000/v1/api"
    account_id: Optional[AccountId] = None

    api_timeout_sec: float = 10.0
    max_retries: int = 3
    retry_backoff_initial_sec: float = 0.5
    retry_backoff_max_sec: float = 5.0

    def validate(self) -> None:
        if not self.enabled:
            return  # nothing to validate further

        if not self.base_url:
            raise IbkrConfigError("ClientPortalConfig.base_url must not be empty")

        if self.api_timeout_sec <= 0:
            raise IbkrConfigError("ClientPortalConfig.api_timeout_sec must be > 0")

        if self.max_retries < 0:
            raise IbkrConfigError("ClientPortalConfig.max_retries must be >= 0")

        if self.retry_backoff_initial_sec <= 0:
            raise IbkrConfigError(
                "ClientPortalConfig.retry_backoff_initial_sec must be > 0"
            )

        if self.retry_backoff_max_sec < self.retry_backoff_initial_sec:
            raise IbkrConfigError(
                "ClientPortalConfig.retry_backoff_max_sec "
                "must be >= retry_backoff_initial_sec"
            )


# =============================================================================
# RATE LIMIT / THROTTLING CONFIG
# =============================================================================
#
# ENV VARS (Rate Limits / Throttling):
#   IBKR_RATE_MAX_ORDERS_PER_SEC        = "50"
#   IBKR_RATE_MAX_MESSAGES_PER_SEC      = "200"
#   IBKR_RATE_BURST_ORDERS              = "50"
#   IBKR_RATE_BURST_WINDOW_MS           = "1000"
#   IBKR_RATE_COOLDOWN_SEC              = "2"
# =============================================================================


@dataclass(slots=True)
class IbkrRateLimitConfig:
    """
    IBKR-specific rate limit knobs.

    These drive your internal throttler. They do NOT replace IBKR's own
    enforcement, but they help you avoid hitting hard broker limits.
    """

    max_orders_per_sec: int = 50
    max_messages_per_sec: int = 200

    burst_orders: int = 50
    burst_window_ms: int = 1000

    cooldown_sec_on_violation: int = 2

    def validate(self) -> None:
        if self.max_orders_per_sec <= 0:
            raise IbkrConfigError("max_orders_per_sec must be > 0")

        if self.max_messages_per_sec <= 0:
            raise IbkrConfigError("max_messages_per_sec must be > 0")

        if self.burst_orders < 0:
            raise IbkrConfigError("burst_orders must be >= 0")

        if self.burst_window_ms <= 0:
            raise IbkrConfigError("burst_window_ms must be > 0")

        if self.cooldown_sec_on_violation < 0:
            raise IbkrConfigError("cooldown_sec_on_violation must be >= 0")


# =============================================================================
# RECONCILIATION & HEARTBEAT CONFIG
# =============================================================================
#
# ENV VARS (Reconciliation / Stale Order / Clock Skew):
#   IBKR_RECONCILE_STARTUP              = "true"
#   IBKR_RECONCILE_INTERVAL_SEC         = "60"
#   IBKR_RECONCILE_LOOKBACK_DAYS        = "1"
#   IBKR_STALE_ORDER_THRESHOLD_SEC      = "300"     # CONN-03
#   IBKR_CLOCK_SKEW_WARNING_SEC         = "30"      # CONN-05 warning
#   IBKR_CLOCK_SKEW_HARD_FAIL_SEC       = "90"      # CONN-05 hard fail
#
# ENV VARS (Heartbeat / Health):
#   IBKR_HEARTBEAT_EXPECT_INTERVAL_SEC  = "60"      # HEART-01
#   IBKR_HEARTBEAT_MAX_MISSES           = "2"
#   IBKR_HEARTBEAT_BLOCK_SUBMITS        = "true"
# =============================================================================


@dataclass(slots=True)
class IbkrReconciliationConfig:
    """
    Settings for startup + periodic reconciliation against IBKR.

    These directly support:
      - CONN-01, CONN-02, CONN-03, CONN-05
      - FAIL-05, FAIL-06
    """

    startup_reconcile: bool = True
    periodic_reconcile_interval_sec: int = 60
    max_reconcile_lookback_days: int = 1

    stale_order_threshold_sec: int = 300

    clock_skew_warning_sec: int = 30
    clock_skew_hard_fail_sec: int = 90

    def validate(self) -> None:
        if self.periodic_reconcile_interval_sec <= 0:
            raise IbkrConfigError(
                "periodic_reconcile_interval_sec must be > 0 (in seconds)"
            )

        if self.max_reconcile_lookback_days <= 0:
            raise IbkrConfigError("max_reconcile_lookback_days must be > 0")

        if self.stale_order_threshold_sec <= 0:
            raise IbkrConfigError("stale_order_threshold_sec must be > 0")

        if self.clock_skew_warning_sec <= 0:
            raise IbkrConfigError("clock_skew_warning_sec must be > 0")

        if self.clock_skew_hard_fail_sec < self.clock_skew_warning_sec:
            raise IbkrConfigError(
                "clock_skew_hard_fail_sec must be >= clock_skew_warning_sec"
            )


@dataclass(slots=True)
class IbkrHeartbeatConfig:
    """
    Heartbeat expectations and behavior when the link goes silent.

    This directly backs:
      - HEART-01: No Events for 60s
    """

    heartbeat_expect_interval_sec: int = 60
    max_missed_heartbeats: int = 2
    block_submits_when_unhealthy: bool = True

    def validate(self) -> None:
        if self.heartbeat_expect_interval_sec <= 0:
            raise IbkrConfigError("heartbeat_expect_interval_sec must be > 0")

        if self.max_missed_heartbeats <= 0:
            raise IbkrConfigError("max_missed_heartbeats must be > 0")


# =============================================================================
# BROKER-SPECIFIC RISK OVERRIDES
# =============================================================================
#
# ENV VARS (IBKR-specific risk caps):
#   IBKR_RISK_MAX_MARGIN_USAGE_PCT      = "90.0"
#   IBKR_RISK_MAX_LEVERAGE              = "4.0"
#   IBKR_RISK_MAX_OPEN_ORDERS           = "500"
# =============================================================================


@dataclass(slots=True)
class IbkrRiskOverridesConfig:
    """
    IBKR-specific risk caps that sit on top of global RiskLimitsConfig.

    They exist here because some limits are tied to how IBKR reports margin.
    """

    max_margin_usage_pct: Optional[float] = 90.0
    max_leverage: Optional[float] = None
    max_open_orders: Optional[int] = None

    def validate(self) -> None:
        if self.max_margin_usage_pct is not None:
            if not (0.0 < self.max_margin_usage_pct <= 100.0):
                raise IbkrConfigError(
                    f"max_margin_usage_pct must be in (0, 100], "
                    f"got {self.max_margin_usage_pct}"
                )

        if self.max_leverage is not None and self.max_leverage <= 0:
            raise IbkrConfigError("max_leverage must be > 0 if set")

        if self.max_open_orders is not None and self.max_open_orders <= 0:
            raise IbkrConfigError("max_open_orders must be > 0 if set")


# =============================================================================
# LOGGING / DEBUG CONFIG
# =============================================================================
#
# ENV VARS (Logging / Debug):
#   IBKR_LOG_LEVEL                 = "INFO" | "DEBUG" | "WARNING" | "ERROR"
#   IBKR_LOG_RAW_TWS_EVENTS        = "false"
#   IBKR_LOG_RAW_REST_PAYLOADS     = "false"
#   IBKR_LOG_REDACT_ACCOUNT_IDS    = "true"
# =============================================================================


@dataclass(slots=True)
class IbkrLoggingConfig:
    """
    Controls verbosity and data sensitivity for the IBKR adapter logs.
    """

    log_level: str = "INFO"
    log_raw_tws_events: bool = False
    log_raw_rest_payloads: bool = False
    redact_account_ids: bool = True

    def validate(self) -> None:
        if self.log_level not in ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"):
            raise IbkrConfigError(
                f"log_level must be one of "
                f"['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], "
                f"got {self.log_level!r}"
            )


# =============================================================================
# ROOT CONFIG OBJECT
# =============================================================================


@dataclass(slots=True)
class IbkrConfig:
    """
    Root configuration for the IBKR adapter.

    This is what the adapter should receive at construction time.
    """

    schema_version: str = "1.0.0"

    env: str = "paper"  # "paper" | "live" | "sim"

    tws: TwsGatewayConfig = field(default_factory=TwsGatewayConfig)
    client_portal: ClientPortalConfig = field(default_factory=ClientPortalConfig)

    rate_limits: IbkrRateLimitConfig = field(default_factory=IbkrRateLimitConfig)
    reconcile: IbkrReconciliationConfig = field(
        default_factory=IbkrReconciliationConfig
    )
    heartbeat: IbkrHeartbeatConfig = field(default_factory=IbkrHeartbeatConfig)
    risk_overrides: IbkrRiskOverridesConfig = field(
        default_factory=IbkrRiskOverridesConfig
    )
    logging: IbkrLoggingConfig = field(default_factory=IbkrLoggingConfig)

    def validate(self) -> None:
        # env and TWS.profile must be consistent
        if self.env not in ("paper", "live", "sim"):
            raise IbkrConfigError(
                f"env must be one of ['paper', 'live', 'sim'], got {self.env!r}"
            )

        # Optional: enforce TWS profile == env for sanity
        if self.tws.profile != self.env:
            raise IbkrConfigError(
                f"TWS profile {self.tws.profile!r} does not match env {self.env!r}. "
                f"Use consistent values to avoid mixing live/paper orders."
            )

        self.tws.validate()
        self.client_portal.validate()
        self.rate_limits.validate()
        self.reconcile.validate()
        self.heartbeat.validate()
        self.risk_overrides.validate()
        self.logging.validate()


# =============================================================================
# ENV LOADER
# =============================================================================


def load_ibkr_config_from_env(prefix: str = "IBKR_") -> IbkrConfig:
    """
    Build IbkrConfig from environment variables.

    This is the *only* place you should read IBKR_* env vars.
    Everywhere else, pass an IbkrConfig instance.
    """

    env = _get_env(f"{prefix}ENV", "paper")

    # --- TWS ---
    tws = TwsGatewayConfig(
        host=_get_env(f"{prefix}TWS_HOST", "127.0.0.1"),
        port=_get_env_int(f"{prefix}TWS_PORT", 7497),
        client_id=_get_env_int(f"{prefix}TWS_CLIENT_ID", 101),
        connect_timeout_sec=_get_env_float(
            f"{prefix}TWS_CONNECT_TIMEOUT_SEC", 5.0
        ),
        read_timeout_sec=_get_env_float(
            f"{prefix}TWS_READ_TIMEOUT_SEC", 30.0
        ),
        reconnect_backoff_initial_sec=_get_env_float(
            f"{prefix}TWS_RECONNECT_BACKOFF_INITIAL_SEC", 1.0
        ),
        reconnect_backoff_max_sec=_get_env_float(
            f"{prefix}TWS_RECONNECT_BACKOFF_MAX_SEC", 30.0
        ),
        use_tls=_get_env_bool(f"{prefix}TWS_USE_TLS", False),
        profile=env or "paper",
    )

    # --- Client Portal ---
    cp_enabled = _get_env_bool(f"{prefix}CP_ENABLED", False)
    cp = ClientPortalConfig(
        enabled=cp_enabled,
        base_url=_get_env(f"{prefix}CP_BASE_URL", "https://localhost:5000/v1/api"),
        account_id=_get_env(f"{prefix}CP_ACCOUNT_ID", None),
        api_timeout_sec=_get_env_float(f"{prefix}CP_API_TIMEOUT_SEC", 10.0),
        max_retries=_get_env_int(f"{prefix}CP_MAX_RETRIES", 3),
        retry_backoff_initial_sec=_get_env_float(
            f"{prefix}CP_RETRY_BACKOFF_INITIAL_SEC", 0.5
        ),
        retry_backoff_max_sec=_get_env_float(
            f"{prefix}CP_RETRY_BACKOFF_MAX_SEC", 5.0
        ),
    )

    # --- Rate limits ---
    rate = IbkrRateLimitConfig(
        max_orders_per_sec=_get_env_int(f"{prefix}RATE_MAX_ORDERS_PER_SEC", 50),
        max_messages_per_sec=_get_env_int(f"{prefix}RATE_MAX_MESSAGES_PER_SEC", 200),
        burst_orders=_get_env_int(f"{prefix}RATE_BURST_ORDERS", 50),
        burst_window_ms=_get_env_int(f"{prefix}RATE_BURST_WINDOW_MS", 1000),
        cooldown_sec_on_violation=_get_env_int(
            f"{prefix}RATE_COOLDOWN_SEC", 2
        ),
    )

    # --- Reconcile ---
    reconcile = IbkrReconciliationConfig(
        startup_reconcile=_get_env_bool(
            f"{prefix}RECONCILE_STARTUP", True
        ),
        periodic_reconcile_interval_sec=_get_env_int(
            f"{prefix}RECONCILE_INTERVAL_SEC", 60
        ),
        max_reconcile_lookback_days=_get_env_int(
            f"{prefix}RECONCILE_LOOKBACK_DAYS", 1
        ),
        stale_order_threshold_sec=_get_env_int(
            f"{prefix}STALE_ORDER_THRESHOLD_SEC", 300
        ),
        clock_skew_warning_sec=_get_env_int(
            f"{prefix}CLOCK_SKEW_WARNING_SEC", 30
        ),
        clock_skew_hard_fail_sec=_get_env_int(
            f"{prefix}CLOCK_SKEW_HARD_FAIL_SEC", 90
        ),
    )

    # --- Heartbeat ---
    hb = IbkrHeartbeatConfig(
        heartbeat_expect_interval_sec=_get_env_int(
            f"{prefix}HEARTBEAT_EXPECT_INTERVAL_SEC", 60
        ),
        max_missed_heartbeats=_get_env_int(
            f"{prefix}HEARTBEAT_MAX_MISSES", 2
        ),
        block_submits_when_unhealthy=_get_env_bool(
            f"{prefix}HEARTBEAT_BLOCK_SUBMITS", True
        ),
    )

    # --- Risk overrides ---
    risk = IbkrRiskOverridesConfig(
        max_margin_usage_pct=_get_env_float(
            f"{prefix}RISK_MAX_MARGIN_USAGE_PCT", 90.0
        ),
        max_leverage=(
            _get_env_float(f"{prefix}RISK_MAX_LEVERAGE", 0.0) or None
        ),
        max_open_orders=(
            _get_env_int(f"{prefix}RISK_MAX_OPEN_ORDERS", 0) or None
        ),
    )

    # --- Logging ---
    logging_cfg = IbkrLoggingConfig(
        log_level=_get_env(f"{prefix}LOG_LEVEL", "INFO"),
        log_raw_tws_events=_get_env_bool(
            f"{prefix}LOG_RAW_TWS_EVENTS", False
        ),
        log_raw_rest_payloads=_get_env_bool(
            f"{prefix}LOG_RAW_REST_PAYLOADS", False
        ),
        redact_account_ids=_get_env_bool(
            f"{prefix}LOG_REDACT_ACCOUNT_IDS", True
        ),
    )

    cfg = IbkrConfig(
        env=env or "paper",
        tws=tws,
        client_portal=cp,
        rate_limits=rate,
        reconcile=reconcile,
        heartbeat=hb,
        risk_overrides=risk,
        logging=logging_cfg,
    )

    cfg.validate()
    return cfg
