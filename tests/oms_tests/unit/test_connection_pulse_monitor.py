# tests/oms_tests/unit/test_connection_pulse_monitor.py

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from order_management_system.connection.monitor import (
    ConnectionPulseMonitor,
    HeartbeatConfig,
    Clock,
)


class FakeClock:
    def __init__(self, start: datetime):
        self._now = start

    def now(self) -> datetime:
        return self._now

    def advance(self, delta: timedelta) -> None:
        self._now += delta


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock(start=datetime(2025, 1, 1, 9, 30, 0))


@pytest.fixture
def monitor(clock: FakeClock) -> ConnectionPulseMonitor:
    cfg = HeartbeatConfig(
        heartbeat_timeout=timedelta(seconds=60),
        probe_timeout=timedelta(seconds=10),
    )
    return ConnectionPulseMonitor(config=cfg, clock=clock)


# PULSE-01: Healthy Heartbeat
def test_pulse_01_healthy_heartbeat(monitor: ConnectionPulseMonitor, clock: FakeClock) -> None:
    # Precondition: system running, data received 1ms ago
    monitor.on_heartbeat(clock.now())
    clock.advance(timedelta(milliseconds=1))

    assert monitor.is_healthy() is True


# PULSE-02: Threshold Edge (59.9s)
def test_pulse_02_threshold_edge(monitor: ConnectionPulseMonitor, clock: FakeClock) -> None:
    monitor.on_heartbeat(clock.now())
    clock.advance(timedelta(seconds=59, milliseconds=900))

    assert monitor.is_healthy() is True


# PULSE-03: Cardiac Arrest (60.1s)
def test_pulse_03_cardiac_arrest(monitor: ConnectionPulseMonitor, clock: FakeClock) -> None:
    monitor.on_heartbeat(clock.now())
    clock.advance(timedelta(seconds=60, milliseconds=100))

    assert monitor.is_healthy() is False


# PULSE-04: Zombie Socket (never seen heartbeat)
def test_pulse_04_zombie_socket(monitor: ConnectionPulseMonitor) -> None:
    # No heartbeat ever
    assert monitor.is_healthy() is False


# PULSE-05: Resuscitation
def test_pulse_05_resuscitation(monitor: ConnectionPulseMonitor, clock: FakeClock) -> None:
    # First: let it go unhealthy
    monitor.on_heartbeat(clock.now())
    clock.advance(timedelta(seconds=61))
    assert monitor.is_healthy() is False

    # Then new data packet arrives
    monitor.on_heartbeat(clock.now())

    # Should recover
    assert monitor.is_healthy() is True


# PULSE-06: Active Probe Failure
def test_pulse_06_active_probe_failure(monitor: ConnectionPulseMonitor, clock: FakeClock) -> None:
    # Idle market: heartbeat is old
    monitor.on_heartbeat(clock.now())
    clock.advance(timedelta(seconds=61))  # beyond heartbeat timeout

    # Watchdog forces reqCurrentTime() probe
    monitor.on_probe_sent(clock.now())

    # No response for > probe_timeout (10s)
    clock.advance(timedelta(seconds=11))

    assert monitor.is_healthy() is False
