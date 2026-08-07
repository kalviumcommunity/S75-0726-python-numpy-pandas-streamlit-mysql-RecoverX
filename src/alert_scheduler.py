
import threading
import time
import logging
from typing import Any, Callable, Dict, List, Optional

from src.payment_queries import (
    generate_alerts_from_rules,
    generate_all_alerts,
)
from src.email_service import send_test_email

logger = logging.getLogger(__name__)


DEFAULT_INTERVAL_SECONDS = 5 * 60
_SESSION_KEY_LAST_RUN = "_recoverx_alerts_last_run_ts"
_SESSION_KEY_CACHE = "_recoverx_alerts_last_result"


class AlertScheduler:
    """
    Background alert runner.

    Two modes of operation (both can be active):
      1. Threaded background polling (the real "near-real-time" engine):
         spawns a daemon thread that invokes generate_all_alerts() every
         `interval_seconds` (default 5 minutes). Persists across user
         sessions as long as the Python process is alive.
      2. Per-session "once per load" fallback (the "demo" shortcut):
         `run_once_per_session()` uses Streamlit session_state to ensure
         alerts are generated at most once per user session load. The
         Dashboard page calls this on render to simulate near-real-time
         on fresh user visits.

    Newly detected alerts (new IDs / new rule_ids compared to the
    previous run) are optionally dispatched via email_service.
    """

    def __init__(
        self,
        interval_seconds: int = DEFAULT_INTERVAL_SECONDS,
        on_new_alerts: Optional[Callable[[List[Dict[str, Any]]], None]] = None,
    ) -> None:
        self.interval = int(interval_seconds or DEFAULT_INTERVAL_SECONDS)
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        self._last_result: Dict[str, Any] = {"alerts": [], "active_count": 0}
        self._last_seen_keys = set()
        self._on_new_alerts = on_new_alerts or self._default_email_hook

    # ---------- Background thread API ----------

    def start(self) -> None:
        """Start the polling daemon thread. Idempotent."""
        with self._lock:
            if self._thread and self._thread.is_alive():
                return
            self._stop_event.clear()
            self._thread = threading.Thread(
                target=self._run_loop,
                name="recoverx-alert-scheduler",
                daemon=True,
            )
            self._thread.start()
            logger.info(
                "Alert scheduler started (interval=%ss)",
                self.interval,
            )

    def stop(self) -> None:
        """Signal the polling thread to stop and wait for it to exit."""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=max(self.interval + 5, 10))
            self._thread = None

    @property
    def is_running(self) -> bool:
        return bool(self._thread and self._thread.is_alive())

    @property
    def last_result(self) -> Dict[str, Any]:
        with self._lock:
            return dict(self._last_result)

    # ---------- Session-scoped fallback ----------

    def run_once_per_session(
        self,
        session_state: Dict[str, Any],
        min_interval_seconds: int = 60,
        start_date: Any = None,
        end_date: Any = None,
    ) -> Dict[str, Any]:
        """
        Streamlit-friendly: run alerts at most once every
        `min_interval_seconds` for this session_state. For a typical user
        landing on Dashboard the first call triggers; later calls within
        the grace window return the cached result.
        """
        now = time.time()
        last_run = session_state.get(_SESSION_KEY_LAST_RUN, 0) or 0
        cached = session_state.get(_SESSION_KEY_CACHE)
        if cached and (now - last_run) < min_interval_seconds:
            return cached

        result = self.run_now(start_date=start_date, end_date=end_date)
        session_state[_SESSION_KEY_LAST_RUN] = now
        session_state[_SESSION_KEY_CACHE] = result
        return result

    # ---------- Core execution ----------

    def run_now(
        self,
        start_date: Any = None,
        end_date: Any = None,
        rules: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Run alert evaluation immediately.

        Returns the same {"alerts": [...], "active_count": N} structure
        as generate_all_alerts() and invokes the configured "new alert"
        hook on any alerts that weren't visible in the previous run.
        """
        if rules is not None:
            alerts = generate_alerts_from_rules(rules, start_date, end_date)
            result = {"alerts": alerts, "active_count": len(alerts)}
        else:
            result = generate_all_alerts(start_date, end_date)

        new_alerts = self._diff_and_store(result.get("alerts") or [])
        if new_alerts and self._on_new_alerts is not None:
            try:
                self._on_new_alerts(new_alerts)
            except Exception as e:  # pragma: no cover
                logger.error("on_new_alerts hook failed: %s", e)
        return result

    # ---------- Internal ----------

    def _run_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                self.run_now()
            except Exception as e:  # pragma: no cover - defensive
                logger.exception("Alert scheduler iteration failed: %s", e)
            self._stop_event.wait(self.interval)

    def _diff_and_store(self, alerts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Return alerts whose (rule_id + message) key is new this run."""
        def key(a: Dict[str, Any]) -> str:
            return "|".join(
                [
                    str(a.get("rule_id", "")),
                    str(a.get("rule_type", "")),
                    str(a.get("message", "")),
                ]
            )

        current_keys = {key(a) for a in alerts}
        new_keys = current_keys - self._last_seen_keys
        new_alerts = [a for a in alerts if key(a) in new_keys]
        with self._lock:
            self._last_seen_keys = current_keys
            self._last_result = {"alerts": alerts, "active_count": len(alerts)}
        return new_alerts

    @staticmethod
    def _default_email_hook(new_alerts: List[Dict[str, Any]]) -> None:
        if not new_alerts:
            return
        subject = f"[RecoverX] {len(new_alerts)} new alert(s)"
        send_test_email(subject=subject, alerts=new_alerts)


# Singleton instance - use this rather than constructing your own.
_scheduler: Optional[AlertScheduler] = None
_singleton_lock = threading.Lock()


def get_alert_scheduler(interval_seconds: int = DEFAULT_INTERVAL_SECONDS) -> AlertScheduler:
    """Return the process-wide alert scheduler singleton, creating it if needed."""
    global _scheduler
    if _scheduler is None:
        with _singleton_lock:
            if _scheduler is None:
                _scheduler = AlertScheduler(interval_seconds=interval_seconds)
    return _scheduler


def ensure_scheduler_running(interval_seconds: int = DEFAULT_INTERVAL_SECONDS) -> AlertScheduler:
    """Create (if needed) AND start the background polling thread."""
    sched = get_alert_scheduler(interval_seconds=interval_seconds)
    if not sched.is_running:
        sched.start()
    return sched
