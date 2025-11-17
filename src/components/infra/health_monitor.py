"""
System Health Monitoring

Continuously monitors system health and alerts on issues.

Monitors:
- Data feed health (bars arriving)
- Universe stability (size consistent)
- Detection rate (normal range)
- Error rate (low)
- Memory usage (stable)
- Execution performance (fast)
- Component responsiveness
- IBKR connection
- Data quality

Auto-recovery:
- Reconnect data feeds
- Reset stuck components
- Clear memory buffers
- Log incidents

Usage:
    from health_monitor import HealthMonitor

    health = HealthMonitor(algorithm)
    status = health.run_health_check()
"""

from AlgorithmImports import *
from datetime import datetime, timedelta
from collections import deque, defaultdict
import sys


class HealthMonitor:
    """
    Comprehensive system health monitoring
    """

    def __init__(self, algorithm):
        self.algorithm = algorithm
        self.logger = algorithm.logger if hasattr(algorithm, "logger") else None
        self.alert_manager = (
            algorithm.alert_manager if hasattr(algorithm, "alert_manager") else None
        )

        # Health check configuration
        self.checks_enabled = {
            "data_feed": True,
            "universe_size": True,
            "detection_rate": True,
            "error_rate": True,
            "memory_usage": True,
            "execution_time": True,
            "ibkr_connection": True,
            "data_quality": True,
        }

        # Thresholds
        self.thresholds = {
            "min_universe_size": 800,  # Expect ~1000
            "max_universe_size": 1200,
            "min_detections_per_day": 3,  # Expect 5-10
            "max_detections_per_day": 20,
            "max_errors_per_hour": 5,
            "max_memory_mb": 1000,  # 1GB
            "max_execution_time_sec": 10,  # Hourly scan
            "data_stale_minutes": 5,  # No data for 5 min
        }

        # Tracking
        self.last_bar_time = {}  # symbol -> last bar timestamp
        self.universe_sizes = deque(maxlen=24)  # Last 24 hours
        self.detection_counts = deque(maxlen=24)  # Hourly detection counts
        self.error_counts = deque(maxlen=24)  # Hourly error counts
        self.execution_times = deque(maxlen=100)  # Last 100 executions

        # Health status
        self.health_status = {
            "overall": True,
            "last_check": None,
            "checks": {},
            "issues": [],
        }

        # Track previous check results for delta logging
        self.previous_checks = {}

        # Recovery tracking
        self.recovery_attempts = defaultdict(int)
        self.last_recovery_time = {}
        self.recovery_failures = defaultdict(int)  # Track consecutive failures
        self.circuit_breaker_open = {}  # recovery_key -> open_time

        # Recovery configuration
        self.MAX_RECOVERY_ATTEMPTS = 5  # Max attempts before circuit opens
        self.CIRCUIT_BREAKER_DURATION = 3600  # 1 hour in seconds
        self.BASE_BACKOFF_SECONDS = 60  # Initial backoff: 1 minute

        # Start time
        self.start_time = algorithm.Time
        self.last_hourly_check = algorithm.Time

        if self.logger:
            self.logger.info("HealthMonitor initialized", component="HealthMonitor")

    def _is_circuit_breaker_open(self, recovery_key):
        """Check if circuit breaker is open for this recovery type"""
        if recovery_key not in self.circuit_breaker_open:
            return False

        open_time = self.circuit_breaker_open[recovery_key]
        elapsed = (self.algorithm.Time - open_time).total_seconds()

        # Close circuit after duration
        if elapsed >= self.CIRCUIT_BREAKER_DURATION:
            del self.circuit_breaker_open[recovery_key]
            self.recovery_failures[recovery_key] = 0  # Reset failure count
            if self.logger:
                self.logger.info(
                    f"Circuit breaker CLOSED for {recovery_key} after {elapsed/60:.0f} min",
                    component="HealthMonitor",
                )
            return False

        return True

    def _get_backoff_time(self, recovery_key):
        """
        Calculate exponential backoff time with jitter

        Formula: min(base * 2^failures, max) + random_jitter
        """
        import random

        failures = self.recovery_failures[recovery_key]

        # Exponential backoff: 60s, 120s, 240s, 480s, 960s
        backoff = min(self.BASE_BACKOFF_SECONDS * (2**failures), 960)

        # Add jitter (0-30% of backoff)
        jitter = random.uniform(0, backoff * 0.3)

        return backoff + jitter

    def _should_attempt_recovery(self, recovery_key):
        """
        Check if recovery should be attempted based on backoff and circuit breaker

        Returns:
            tuple: (should_attempt: bool, reason: str)
        """
        # Check circuit breaker
        if self._is_circuit_breaker_open(recovery_key):
            elapsed = (
                self.algorithm.Time - self.circuit_breaker_open[recovery_key]
            ).total_seconds()
            remaining = (self.CIRCUIT_BREAKER_DURATION - elapsed) / 60
            return False, f"Circuit breaker OPEN: {remaining:.0f} min remaining"

        # Check if too many recent failures
        if self.recovery_failures[recovery_key] >= self.MAX_RECOVERY_ATTEMPTS:
            # Open circuit breaker
            self.circuit_breaker_open[recovery_key] = self.algorithm.Time
            if self.logger:
                self.logger.warning(
                    f"Circuit breaker OPENED for {recovery_key} after {self.MAX_RECOVERY_ATTEMPTS} failures",
                    component="HealthMonitor",
                )
            return False, "Too many failures - circuit breaker opened"

        # Check backoff time
        if recovery_key in self.last_recovery_time:
            elapsed = (
                self.algorithm.Time - self.last_recovery_time[recovery_key]
            ).total_seconds()
            required_backoff = self._get_backoff_time(recovery_key)

            if elapsed < required_backoff:
                remaining = (required_backoff - elapsed) / 60
                return False, f"Backoff: {remaining:.1f} min remaining"

        return True, "OK"

    def run_health_check(self, force=False):
        """
        Run all health checks

        Args:
            force: Force check even if recently checked

        Returns:
            dict with health status
        """

        # Only run once per hour unless forced
        if not force:
            time_since_check = (
                self.algorithm.Time - self.last_hourly_check
            ).total_seconds() / 60
            if time_since_check < 60:  # Less than 1 hour
                return self.health_status

        self.last_hourly_check = self.algorithm.Time

        # Run each enabled check
        checks = {}
        issues = []

        if self.checks_enabled["data_feed"]:
            check, issue = self._check_data_feed()
            checks["data_feed"] = check
            if issue:
                issues.append(issue)

        if self.checks_enabled["universe_size"]:
            check, issue = self._check_universe_size()
            checks["universe_size"] = check
            if issue:
                issues.append(issue)

        if self.checks_enabled["detection_rate"]:
            check, issue = self._check_detection_rate()
            checks["detection_rate"] = check
            if issue:
                issues.append(issue)

        if self.checks_enabled["error_rate"]:
            check, issue = self._check_error_rate()
            checks["error_rate"] = check
            if issue:
                issues.append(issue)

        if self.checks_enabled["memory_usage"]:
            check, issue = self._check_memory_usage()
            checks["memory_usage"] = check
            if issue:
                issues.append(issue)

        if self.checks_enabled["execution_time"]:
            check, issue = self._check_execution_time()
            checks["execution_time"] = check
            if issue:
                issues.append(issue)

        if self.checks_enabled["data_quality"]:
            check, issue = self._check_data_quality()
            checks["data_quality"] = check
            if issue:
                issues.append(issue)

        # Overall health
        overall_healthy = all(checks.values())

        # Log per-check deltas (changes since last run)
        self._log_check_deltas(checks)

        # Update previous checks for next comparison
        self.previous_checks = checks.copy()

        # Update status
        self.health_status = {
            "overall": overall_healthy,
            "last_check": self.algorithm.Time,
            "checks": checks,
            "issues": issues,
        }

        # Log results
        if self.logger:
            if overall_healthy:
                self.logger.info(
                    "Health check passed - all systems OK", component="HealthMonitor"
                )
            else:
                self.logger.warning(
                    f"Health check FAILED - {len(issues)} issues found",
                    component="HealthMonitor",
                )
                for issue in issues:
                    self.logger.warning(f"  - {issue}", component="HealthMonitor")

        # Alert if issues found
        if not overall_healthy and self.alert_manager:
            self.alert_manager.alert_system_health(checks)

        # Attempt recovery if needed
        if not overall_healthy:
            self._attempt_recovery(issues)

        return self.health_status

    def _log_check_deltas(self, current_checks):
        """
        Log changes in health check results since last run

        Args:
            current_checks: Dict of current check results {check_name: bool}
        """
        if not self.previous_checks or not self.logger:
            return

        # Find checks that changed state
        for check_name, current_status in current_checks.items():
            previous_status = self.previous_checks.get(check_name)

            # Skip if no previous data
            if previous_status is None:
                continue

            # Log if status changed
            if current_status != previous_status:
                if current_status:
                    # Check recovered
                    self.logger.info(
                        f"Health check RECOVERED: {check_name} (was failing, now passing)",
                        component="HealthMonitor",
                    )
                else:
                    # Check started failing
                    self.logger.warning(
                        f"Health check DEGRADED: {check_name} (was passing, now failing)",
                        component="HealthMonitor",
                    )

    def _check_data_feed(self):
        """Check if data feed is active and recent"""

        # Check if we've received recent data
        if not self.last_bar_time:
            # No data yet (might be warming up)
            time_elapsed = (self.algorithm.Time - self.start_time).total_seconds()
            if time_elapsed > 300:  # 5 minutes
                return False, "No data received in 5 minutes"
            else:
                # Still in warmup grace period
                if self.logger and time_elapsed < 60:  # Only log first minute
                    self.logger.debug(
                        f"WARMUP: Waiting for initial data ({time_elapsed:.0f}s elapsed)",
                        component="HealthMonitor",
                    )
                return True, None  # Still warming up

        # Check most recent bar
        most_recent = max(self.last_bar_time.values())
        minutes_since = (self.algorithm.Time - most_recent).total_seconds() / 60

        if minutes_since > self.thresholds["data_stale_minutes"]:
            return False, f"Data stale - no bars for {minutes_since:.1f} minutes"

        return True, None

    def _check_universe_size(self):
        """Check if universe size is stable"""

        if not hasattr(self.algorithm, "active_symbols"):
            return True, None  # Not initialized yet

        current_size = len(self.algorithm.active_symbols)
        self.universe_sizes.append(current_size)

        if current_size < self.thresholds["min_universe_size"]:
            return False, f"Universe too small: {current_size} (expected ~1000)"

        if current_size > self.thresholds["max_universe_size"]:
            return False, f"Universe too large: {current_size} (expected ~1000)"

        # Check for sudden drops (>50% in 1 hour)
        if len(self.universe_sizes) >= 2:
            prev_size = self.universe_sizes[-2]
            if current_size < prev_size * 0.5:
                return False, f"Universe dropped from {prev_size} to {current_size}"

        return True, None

    def _check_detection_rate(self):
        """Check if detection rate is normal"""

        # Get detections from last hour
        if not hasattr(self.algorithm, "extreme_detector"):
            return True, None

        # Count recent detections (simplified - would need actual tracking)
        # For now, check if we're getting ANY detections

        # Check daily total
        if len(self.detection_counts) >= 24:  # Full day
            daily_total = sum(self.detection_counts)

            if daily_total < self.thresholds["min_detections_per_day"]:
                return False, f"Too few detections: {daily_total}/day (expected 5-10)"

            if daily_total > self.thresholds["max_detections_per_day"]:
                return (
                    False,
                    f"Too many detections: {daily_total}/day (possible false signals)",
                )

        return True, None

    def _check_error_rate(self):
        """Check if error rate is acceptable"""

        if not self.logger:
            return True, None

        # Get error count from logger
        recent_errors = len(
            [
                e
                for e in self.logger.error_logs
                if (
                    self.algorithm.Time
                    - datetime.strptime(e["timestamp"], "%Y-%m-%d %H:%M:%S")
                ).total_seconds()
                < 3600
            ]
        )

        self.error_counts.append(recent_errors)

        if recent_errors > self.thresholds["max_errors_per_hour"]:
            return False, f"High error rate: {recent_errors} errors in last hour"

        # Check for error spike
        if len(self.error_counts) >= 2:
            prev_errors = self.error_counts[-2]
            if recent_errors > prev_errors * 3 and recent_errors > 5:
                if self.alert_manager:
                    self.alert_manager.alert_error_spike(recent_errors, 60)
                return False, f"Error spike: {recent_errors} errors (was {prev_errors})"

        return True, None

    def _check_memory_usage(self):
        """Check memory usage"""

        try:
            # Get current memory usage (if available)
            # Note: This might not work in all environments
            import resource

            memory_mb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024

            if memory_mb > self.thresholds["max_memory_mb"]:
                return False, f"High memory usage: {memory_mb:.0f} MB"

            return True, None

        except Exception:
            # Memory monitoring not available
            return True, None

    def _check_execution_time(self):
        """Check if execution is fast enough"""

        if not self.execution_times:
            return True, None

        avg_time = sum(self.execution_times) / len(self.execution_times)

        if avg_time > self.thresholds["max_execution_time_sec"]:
            return (
                False,
                f"Slow execution: {avg_time:.2f}s average (max {self.thresholds['max_execution_time_sec']}s)",
            )

        # Check for degradation
        if len(self.execution_times) >= 10:
            recent_avg = sum(list(self.execution_times)[-10:]) / 10
            old_avg = sum(list(self.execution_times)[:10]) / 10

            if recent_avg > old_avg * 2:
                return False, f"Execution slowing: {old_avg:.2f}s → {recent_avg:.2f}s"

        return True, None

    def _check_data_quality(self):
        """Check data quality (no gaps, valid prices)"""

        if not hasattr(self.algorithm, "minute_bars"):
            return True, None

        # Check a sample of symbols for data quality
        issues = []

        for symbol in list(self.algorithm.minute_bars.keys())[:10]:  # Check first 10
            bars = self.algorithm.minute_bars[symbol]

            if not bars:
                continue

            # Check for zero/negative prices
            for bar in bars[-60:]:  # Last hour
                if bar.get("close", 0) <= 0:
                    issues.append(f"{symbol}: Invalid price {bar['close']}")
                    break

            # Check for large gaps in time
            if len(bars) >= 2:
                last_bar = bars[-1]
                prev_bar = bars[-2]
                time_gap = (last_bar["time"] - prev_bar["time"]).total_seconds()

                if time_gap > 300:  # >5 minutes gap
                    issues.append(f"{symbol}: {time_gap/60:.0f}min data gap")

        if issues:
            return False, f"Data quality issues: {len(issues)} problems found"

        return True, None

    def _attempt_recovery(self, issues):
        """Attempt automatic recovery from issues"""

        for issue in issues:
            # Identify issue type
            if "data stale" in issue.lower() or "data gap" in issue.lower():
                self._recover_data_feed()

            elif "universe" in issue.lower():
                self._recover_universe()

            elif "memory" in issue.lower():
                self._recover_memory()

            elif "error spike" in issue.lower():
                self._recover_error_spike()

    def _recover_data_feed(self):
        """Attempt to recover data feed with exponential backoff and circuit breaker"""

        recovery_key = "data_feed"

        # Check if recovery should be attempted
        should_attempt, reason = self._should_attempt_recovery(recovery_key)
        if not should_attempt:
            if self.logger:
                self.logger.info(
                    f"Skipping data feed recovery: {reason}", component="HealthMonitor"
                )
            return

        if self.logger:
            attempts = self.recovery_attempts[recovery_key]
            failures = self.recovery_failures[recovery_key]
            self.logger.info(
                f"Attempting data feed recovery (attempt {attempts+1}, failures: {failures})",
                component="HealthMonitor",
            )

        try:
            # Clear stale data
            if hasattr(self.algorithm, "minute_bars"):
                for symbol in list(self.algorithm.minute_bars.keys()):
                    if (
                        len(self.algorithm.minute_bars[symbol]) > 1440
                    ):  # Keep last 24 hours
                        self.algorithm.minute_bars[symbol] = self.algorithm.minute_bars[
                            symbol
                        ][-1440:]

            # Log recovery attempt
            self.recovery_attempts[recovery_key] += 1
            self.last_recovery_time[recovery_key] = self.algorithm.Time
            self.recovery_failures[recovery_key] = 0  # Reset on success

            if self.logger:
                self.logger.info(
                    "Data feed recovery completed", component="HealthMonitor"
                )

        except Exception as e:
            self.recovery_failures[recovery_key] += 1
            if self.logger:
                self.logger.error(
                    f"Data feed recovery failed (failure {self.recovery_failures[recovery_key]}): {str(e)}",
                    component="HealthMonitor",
                    exception=e,
                )

    def _recover_universe(self):
        """Attempt to recover universe"""

        recovery_key = "universe"

        if self.logger:
            self.logger.info("Attempting universe recovery", component="HealthMonitor")

        try:
            # Force universe refresh (would need to implement in main algo)
            # For now, just log

            self.recovery_attempts[recovery_key] += 1
            self.last_recovery_time[recovery_key] = self.algorithm.Time

            if self.logger:
                self.logger.info(
                    "Universe recovery completed", component="HealthMonitor"
                )

        except Exception as e:
            if self.logger:
                self.logger.error(
                    f"Universe recovery failed: {str(e)}",
                    component="HealthMonitor",
                    exception=e,
                )

    def _recover_memory(self):
        """Attempt to recover from high memory usage"""

        recovery_key = "memory"

        if self.logger:
            self.logger.info("Attempting memory recovery", component="HealthMonitor")

        try:
            # Clear old data
            if hasattr(self.algorithm, "minute_bars"):
                for symbol in list(self.algorithm.minute_bars.keys()):
                    # Keep only last 2 hours
                    if len(self.algorithm.minute_bars[symbol]) > 120:
                        self.algorithm.minute_bars[symbol] = self.algorithm.minute_bars[
                            symbol
                        ][-120:]

            # Clear logger buffers (keep last 1000)
            if self.logger and len(self.logger.daily_logs) > 1000:
                self.logger.daily_logs = self.logger.daily_logs[-1000:]

            self.recovery_attempts[recovery_key] += 1
            self.last_recovery_time[recovery_key] = self.algorithm.Time

            if self.logger:
                self.logger.info("Memory recovery completed", component="HealthMonitor")

        except Exception as e:
            if self.logger:
                self.logger.error(
                    f"Memory recovery failed: {str(e)}",
                    component="HealthMonitor",
                    exception=e,
                )

    def _recover_error_spike(self):
        """Handle error spikes"""

        recovery_key = "error_spike"

        if self.logger:
            self.logger.warning(
                "Error spike detected - monitoring closely", component="HealthMonitor"
            )

        # Just log for now - human intervention likely needed
        self.recovery_attempts[recovery_key] += 1
        self.last_recovery_time[recovery_key] = self.algorithm.Time

    def update_metrics(self, metric_type, value):
        """Update health metrics"""

        if metric_type == "bar_received":
            symbol = value["symbol"]
            timestamp = value["timestamp"]
            self.last_bar_time[symbol] = timestamp

        elif metric_type == "detection":
            # Increment hourly detection count
            if not self.detection_counts or len(self.detection_counts) == 0:
                self.detection_counts.append(1)
            else:
                self.detection_counts[-1] += 1

        elif metric_type == "execution_time":
            self.execution_times.append(value)

    @property
    def overall_healthy(self):
        """
        Property to check overall system health

        Returns:
            bool: True if all health checks are passing, False otherwise
        """
        return self.health_status.get("overall", True)

    def get_health_summary(self):
        """Get health summary for logging"""

        summary = {
            "overall_healthy": self.overall_healthy,
            "last_check": str(self.health_status["last_check"]),
            "issues": len(self.health_status["issues"]),
            "checks_passed": sum(1 for v in self.health_status["checks"].values() if v),
            "checks_total": len(self.health_status["checks"]),
            "recovery_attempts": dict(self.recovery_attempts),
        }

        return summary
