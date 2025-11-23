# src/order_management_system/connection/monitor.py

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, Protocol


class Clock(Protocol):
    """
    Small abstraction so we can inject a fake clock in tests.
    """
    def now(self) -> datetime: ...


class SystemClock:
    """
    Default implementation using datetime.utcnow().
    """
    def now(self) -> datetime:
        from datetime import datetime as _dt
        return _dt.utcnow()


@dataclass(slots=True, frozen=True)
class HeartbeatConfig:
    """
    Configuration for heartbeat / health logic.

    - heartbeat_timeout: if no data for longer than this, connection is unhealthy
    - probe_timeout:     after forcing an active probe, if no reply within this
                         window, connection is unhealthy
    """
    heartbeat_timeout: timedelta = timedelta(seconds=60)   # PULSE-02/03 line
    probe_timeout: timedelta = timedelta(seconds=10)       # PULSE-06


@dataclass(slots=True)
class PulseState:
    """
    State tracked by the connection monitor.

    We do NOT store any network sockets here, just timestamps and flags.
    """
    last_heartbeat_at: Optional[datetime] = None
    last_probe_sent_at: Optional[datetime] = None
    last_probe_ok_at: Optional[datetime] = None

    # For convenience we can track the last health decision
    last_is_healthy: bool = True


class ConnectionPulseMonitor:
    """
    Pure logic for evaluating connection health based on heartbeats and probes.

    This is intentionally dumb + deterministic:
      - You push events in (on_heartbeat, on_probe_sent, on_probe_ok)
      - You query is_healthy() with current time
    """

    def __init__(
        self,
        config: HeartbeatConfig | None = None,
        clock: Clock | None = None,
    ) -> None:
        self._cfg = config or HeartbeatConfig()
        self._clock: Clock = clock or SystemClock()
        self._state = PulseState()

    # ------------------------------------------------------------------
    # EVENT HOOKS (called by adapter / reactor)
    # ------------------------------------------------------------------

    def on_heartbeat(self, ts: Optional[datetime] = None) -> None:
        """
        Call this whenever we receive ANY data from the broker:

          - market data tick
          - orderStatus event
          - execDetails
          - account update
        """
        now = ts or self._clock.now()
        self._state.last_heartbeat_at = now
        # A fresh heartbeat also implicitly confirms connectivity
        self._state.last_probe_ok_at = now

    def on_probe_sent(self, ts: Optional[datetime] = None) -> None:
        """
        Called when we actively ping the broker (e.g. reqCurrentTime()).
        """
        now = ts or self._clock.now()
        self._state.last_probe_sent_at = now

    def on_probe_ok(self, ts: Optional[datetime] = None) -> None:
        """
        Called when a probe response is received/validated.
        """
        now = ts or self._clock.now()
        self._state.last_probe_ok_at = now

    # ------------------------------------------------------------------
    # HEALTH EVALUATION
    # ------------------------------------------------------------------

    def is_healthy(self, now: Optional[datetime] = None) -> bool:
        """
        Core health decision logic implementing your PULSE-01 ... PULSE-06 table.
        """
        now = now or self._clock.now()
        cfg = self._cfg
        st = self._state

        # PULSE-04: Zombie socket – never had a heartbeat
        # If we have *never* seen data, treat as unhealthy even if TCP says connected.
        if st.last_heartbeat_at is None:
            self._state.last_is_healthy = False
            return False

        # Heartbeat age
        hb_age = now - st.last_heartbeat_at

        # PULSE-01 / PULSE-02: Heartbeat within threshold => healthy
        if hb_age <= cfg.heartbeat_timeout:
            self._state.last_is_healthy = True
            return True

        # At this point, heartbeat is older than heartbeat_timeout

        # PULSE-06: Active probe logic
        # If we have sent a probe but NOT received an OK within probe_timeout,
        # declare unhealthy.
        if st.last_probe_sent_at is not None:
            # If we *have* a probe OK and it's newer than the probe sent, we’re OK.
            if st.last_probe_ok_at is not None and st.last_probe_ok_at >= st.last_probe_sent_at:
                # Probe succeeded, but heartbeat might still be stale — however,
                # probe success proves connectivity.
                self._state.last_is_healthy = True
                return True

            # No probe OK yet; how long since we sent the probe?
            probe_age = now - st.last_probe_sent_at
            if probe_age > cfg.probe_timeout:
                # PULSE-06: Active probe failure
                self._state.last_is_healthy = False
                return False

        # PULSE-03: Cardiac arrest – heartbeat older than threshold,
        # and either no probe or probe still within its timeout window.
        self._state.last_is_healthy = False
        return False

    # ------------------------------------------------------------------
    # Introspection helpers for tests / monitoring
    # ------------------------------------------------------------------

    @property
    def state(self) -> PulseState:
        return self._state

    @property
    def config(self) -> HeartbeatConfig:
        return self._cfg
