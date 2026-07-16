"""
Geo-targeting demo -- route Playwright traffic through country-specific proxies.
Demonstrates regional proxy pool usage for location-based testing.
"""
from proxy_manager import ProxyPool
from playwright.sync_api import sync_playwright

# Regional proxy pools -- replace with your actual regional proxies
US_PROXIES = ["http://us-proxy:8080"]
DE_PROXIES = ["http://de-proxy:8080"]
JP_PROXIES = ["http://jp-proxy:8080"]

# Separate pools per region
POOLS = {
    "US": ProxyPool(US_PROXIES, initial_healthcheck=False),
    "DE": ProxyPool(DE_PROXIES, initial_healthcheck=False),
    "JP": ProxyPool(JP_PROXIES, initial_healthcheck=False),
}

# Locale and timezone mapping per region
REGION_CONFIG = {
    "US": {"locale": "en-US", "timezone": "America/New_York", "viewport": {"width": 1280, "height": 720}},
    "DE": {"locale": "de-DE", "timezone": "Europe/Berlin",    "viewport": {"width": 1366, "height": 768}},
    "JP": {"locale": "ja-JP", "timezone": "Asia/Tokyo",       "viewport": {"width": 1920, "height": 1080}},
}

CHECK_URL = "https://httpbin.org/ip"


def geo_test(region: str):
    """Open browser in a specific region and check the visible IP."""
    cfg = REGION_CONFIG[region]
    pool = POOLS[region]
    proxy = pool.get_proxy()

    print(f"[{region}] locale={cfg['locale']}, tz={cfg['timezone']}, proxy={proxy}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            proxy={"server": proxy} if proxy else None,
            locale=cfg["locale"],
            timezone_id=cfg["timezone"],
            viewport=cfg["viewport"],
        )

        # Override webdriver flag
        context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
        """)

        page = context.new_page()
        try:
            page.goto(CHECK_URL, timeout=15000)
            ip_text = page.inner_text("pre") if page.query_selector("pre") else page.content()[:200]
            print(f"[{region}] IP info: {ip_text}")
            if proxy:
                pool.mark_success(proxy)
        except Exception as e:
            print(f"[{region}] FAILED: {e}")
            if proxy:
                pool.mark_failed(proxy)
        finally:
            browser.close()


def main():
    print("Geo-targeting demo -- testing US, DE, JP regions...")
    for region in ["US", "DE", "JP"]:
        try:
            geo_test(region)
        except Exception as e:
            print(f"[{region}] Error: {e}")


if __name__ == "__main__":
    main()
