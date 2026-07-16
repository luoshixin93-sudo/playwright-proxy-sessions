"""
Multi-session isolation demo -- run multiple concurrent browser sessions
with different proxies, locales, and fingerprints simultaneously.
"""
import threading
import time
from proxy_manager import ProxyPool
from playwright.sync_api import sync_playwright

# Replace with your actual proxy list
POOL = ProxyPool([
    "http://user:pass@proxy-1.example.com:8080",
    "http://user:pass@proxy-2.example.com:8080",
    "http://user:pass@proxy-3.example.com:8080",
    "http://user:pass@proxy-4.example.com:8080",
], initial_healthcheck=False)


def run_session(session_id: int, url: str = "https://httpbin.org/headers"):
    """Run one isolated browser session and print its headers."""
    proxy = POOL.get_proxy()
    locale = ["en-US", "de-DE", "fr-FR", "ja-JP"][session_id % 4]
    user_agent = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    print(f"[Session {session_id}] Starting -- locale={locale}, proxy={proxy}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            proxy={"server": proxy} if proxy else None,
            locale=locale,
            timezone_id="America/New_York",
            viewport={"width": 1920, "height": 1080},
            user_agent=user_agent,
            extra_http_headers={"Accept-Language": locale},
        )

        # Anti-detection: override navigator.webdriver
        context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            window.navigator.chrome = {runtime: {}};
        """)

        page = context.new_page()
        try:
            response = page.goto(url, timeout=15000)
            print(f"[Session {session_id}] HTTP status: {response.status}")
            if proxy:
                POOL.mark_success(proxy)
        except Exception as e:
            print(f"[Session {session_id}] FAILED: {e}")
            if proxy:
                POOL.mark_failed(proxy)
        finally:
            browser.close()

    print(f"[Session {session_id}] Done.")


def main():
    print("Starting 4 concurrent isolated sessions...")
    threads = []
    for i in range(4):
        t = threading.Thread(target=run_session, args=(i,))
        threads.append(t)
        t.start()
        time.sleep(0.5)  # stagger starts slightly

    for t in threads:
        t.join()

    print("\nPool final stats:", POOL.stats())


if __name__ == "__main__":
    main()
