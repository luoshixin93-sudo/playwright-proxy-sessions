# Playwright Proxy Sessions

> A practical guide to running Playwright browser automation with proxy rotation, session isolation, and anti-detection patterns. Designed for web scraping, testing, and automation workflows that require clean, geographically diverse browser sessions.

## Features

- **Proxy Pool Management** -- rotating proxies with health checks and automatic failover
- **Session Isolation** -- each browser context is fully isolated with its own cookies, storage, and fingerprint
- **Geo-Targeting** -- route traffic through proxies in specific countries/regions for location-based testing
- **Anti-Detection Patterns** -- navigator.webdriver flag override, canvas/WebGL fingerprint randomization, WebRTC leak prevention
- **Rate Limiting** -- built-in request throttling to avoid triggering bot protections

## Installation

```bash
pip install playwright
playwright install chromium  # or: playwright install --with-deps chromium
pip install requests aiohttp  # for proxy health checks
```

## Quick Start

```python
from proxy_manager import ProxyPool
from playwright.sync_api import sync_playwright

# Initialize proxy pool (replace with your proxy list)
pool = ProxyPool([
    "http://user:pass@proxy1.example.com:8080",
    "http://user:pass@proxy2.example.com:8080",
])

# Get a working proxy
proxy = pool.get_proxy()
print(f"Using proxy: {proxy}")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(
        proxy={"server": proxy},
        locale="en-US",
        timezone_id="America/New_York",
        viewport={"width": 1920, "height": 1080},
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    )
    page = context.new_page()
    page.goto("https://httpbin.org/ip")
    print(page.content())
    browser.close()
```

## Project Structure

```
playwright-proxy-sessions/
  proxy_manager.py        -- ProxyPool: rotation, health checks, failover
  examples/
    session_demo.py        -- Multi-session isolation demo
    geo_targeting.py       -- Country-specific routing demo
  README.md
```

## Proxy Pool Manager

The `ProxyPool` class handles proxy rotation and health monitoring:

```python
pool = ProxyPool(proxies, healthcheck_url="https://httpbin.org/ip", timeout=10)
proxy = pool.get_proxy()          # Get next proxy in round-robin
pool.mark_failed(proxy)           # Remove a failing proxy
pool.mark_success(proxy)          # Reset failure count
print(pool.stats())               # Pool health statistics
```

## Session Isolation

Each browser context is completely independent -- cookies, localStorage, sessionStorage, and permissions are never shared between sessions:

```python
context1 = browser.new_context(locale="en-US")
context2 = browser.new_context(locale="zh-CN")
# context1 and context2 share nothing
```

## Geo-Targeting

Route traffic through proxies in specific geographic regions:

```python
us_proxies = ["http://us-proxy-1:8080", "http://us-proxy-2:8080"]
pool_us = ProxyPool(us_proxies)
proxy = pool_us.get_proxy()
# Use proxy in new_context(...)
```

## Anti-Detection

Override the navigator.webdriver flag and randomize canvas fingerprint:

```python
context = browser.new_context()
script = """
Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
"""
context.add_init_script(script)
```

## Disclaimer

This project is for **educational and legitimate testing purposes** only. Unauthorized automated access to websites may violate their Terms of Service. Always respect robots.txt and applicable laws.

## Contact

- **Website**: https://www.qtphone.com
- **WhatsApp**: @along915
- **Telegram**: @Alongyun
- **Email**: ailong9281@gmail.com
