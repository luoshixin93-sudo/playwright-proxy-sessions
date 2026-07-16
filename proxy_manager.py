"""
ProxyPool -- rotating proxy manager with health checks and automatic failover.
Thread-safe, suitable for concurrent browser automation workflows.
"""
import threading
import time
from typing import Optional
import urllib.request
import urllib.error
import ssl

DEFAULT_HC_URL = "https://httpbin.org/ip"
DEFAULT_TIMEOUT = 10


class ProxyPool:
    """Thread-safe rotating proxy pool with health monitoring."""

    def __init__(self, proxies: list[str], healthcheck_url: str = DEFAULT_HC_URL,
                 timeout: int = DEFAULT_TIMEOUT, max_failures: int = 3,
                 initial_healthcheck: bool = True):
        self._lock = threading.Lock()
        self._proxies: dict[str, dict] = {}
        self._order: list[str] = []
        self._healthcheck_url = healthcheck_url
        self._timeout = timeout
        self._max_failures = max_failures
        self._health_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

        for p in proxies:
            self._proxies[p] = {"failures": 0, "last_used": 0.0, "working": True}
            self._order.append(p)

        if initial_healthcheck:
            self._run_healthcheck_all()

    # ---- public API ----

    def get_proxy(self) -> Optional[str]:
        """Return the next working proxy in round-robin order, or None if none available."""
        with self._lock:
            working = [p for p in self._order if self._proxies[p]["working"]]
            if not working:
                return None
            chosen = min(working, key=lambda p: self._proxies[p]["last_used"])
            self._proxies[chosen]["last_used"] = time.time()
            return chosen

    def mark_success(self, proxy: str) -> None:
        """Reset failure count for a proxy after a successful request."""
        with self._lock:
            if proxy in self._proxies:
                self._proxies[proxy]["failures"] = 0
                self._proxies[proxy]["working"] = True

    def mark_failed(self, proxy: str) -> None:
        """Increment failure count and mark proxy down if threshold exceeded."""
        with self._lock:
            if proxy not in self._proxies:
                return
            self._proxies[proxy]["failures"] += 1
            if self._proxies[proxy]["failures"] >= self._max_failures:
                self._proxies[proxy]["working"] = False
                print(f"[ProxyPool] Proxy marked DOWN: {proxy}")

    def remove(self, proxy: str) -> None:
        """Permanently remove a proxy from the pool."""
        with self._lock:
            if proxy in self._proxies:
                del self._proxies[proxy]
                if proxy in self._order:
                    self._order.remove(proxy)

    def add(self, proxy: str) -> None:
        """Add a new proxy to the pool."""
        with self._lock:
            if proxy not in self._proxies:
                self._proxies[proxy] = {"failures": 0, "last_used": 0.0, "working": True}
                self._order.append(proxy)

    def stats(self) -> dict:
        """Return pool statistics."""
        with self._lock:
            total = len(self._proxies)
            working = sum(1 for p in self._proxies if self._proxies[p]["working"])
            return {
                "total": total,
                "working": working,
                "down": total - working,
            }

    # ---- health checks ----

    def _run_healthcheck_all(self) -> None:
        """Synchronously check all proxies."""
        for proxy in list(self._order):
            ok = self._check_proxy(proxy)
            with self._lock:
                self._proxies[proxy]["working"] = ok

    def _check_proxy(self, proxy: str) -> bool:
        """Test a single proxy by making a request through it."""
        try:
            ctx = ssl.create_default_context()
            proxy_handler = urllib.request.ProxyHandler({"http": proxy, "https": proxy})
            opener = urllib.request.build_opener(proxy_handler)
            opener.addheaders = [("User-Agent", "Mozilla/5.0")]
            opener.open(self._healthcheck_url, timeout=self._timeout)
            return True
        except Exception:
            return False

    def start_async_checker(self, interval: int = 300) -> None:
        """Start a background thread that periodically rechecks all proxies."""
        def _runner():
            while not self._stop_event.wait(interval):
                self._run_healthcheck_all()
                print(f"[ProxyPool] Health check: {self.stats()['working']}/{self.stats()['total']} working")
        self._health_thread = threading.Thread(target=_runner, daemon=True)
        self._health_thread.start()

    def stop_async_checker(self) -> None:
        """Stop the background health checker."""
        self._stop_event.set()
        if self._health_thread:
            self._health_thread.join(timeout=5)


if __name__ == "__main__":
    demo_proxies = [
        "http://demo-proxy-1:8080",
        "http://demo-proxy-2:8080",
    ]
    pool = ProxyPool(demo_proxies, initial_healthcheck=False)
    print("Pool stats:", pool.stats())
    selected = pool.get_proxy()
    print(f"Selected proxy: {selected}")
