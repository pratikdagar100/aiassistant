"""Browser automation via Playwright (spec section 22).

A single persistent Chromium instance is reused across tool calls (each API
request is a separate HTTP call, but the browser session needs to survive
between "navigate" and the next "click") — see _get_session(). Prefer this
over screen-coordinate clicking for anything web-based (spec section 26).
"""

from __future__ import annotations

import asyncio

from app.core.logging import get_logger

logger = get_logger("computer.browser")


class BrowserError(RuntimeError):
    pass


class _Session:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.lock = asyncio.Lock()

    async def ensure_started(self):
        async with self.lock:
            if self.page is not None:
                return
            try:
                from playwright.async_api import async_playwright

                self.playwright = await async_playwright().start()
                self.browser = await self.playwright.chromium.launch(headless=False)
                self.context = await self.browser.new_context()
                self.page = await self.context.new_page()
            except Exception as exc:  # noqa: BLE001
                raise BrowserError(f"Could not start browser: {exc}") from exc

    async def close(self):
        async with self.lock:
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            self.browser = self.context = self.page = self.playwright = None


_session = _Session()


async def navigate(url: str) -> dict:
    await _session.ensure_started()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    await _session.page.goto(url, wait_until="domcontentloaded")
    return {"url": _session.page.url, "title": await _session.page.title()}


async def search(query: str, engine: str = "https://www.google.com/search?q=") -> dict:
    return await navigate(engine + query.replace(" ", "+"))


async def read_page_text() -> dict:
    await _session.ensure_started()
    text = await _session.page.inner_text("body")
    return {"url": _session.page.url, "text": text[:20000]}


async def click(selector: str) -> dict:
    await _session.ensure_started()
    await _session.page.click(selector, timeout=5000)
    return {"clicked": selector}


async def type_text(selector: str, text: str) -> dict:
    await _session.ensure_started()
    await _session.page.fill(selector, text, timeout=5000)
    return {"selector": selector, "text": text}


async def scroll(direction: str = "down", amount: int = 800) -> dict:
    await _session.ensure_started()
    delta = amount if direction == "down" else -amount
    await _session.page.mouse.wheel(0, delta)
    return {"direction": direction, "amount": amount}


async def screenshot() -> bytes:
    await _session.ensure_started()
    return await _session.page.screenshot()


async def page_state() -> dict:
    await _session.ensure_started()
    return {"url": _session.page.url, "title": await _session.page.title()}


async def close_browser() -> dict:
    await _session.close()
    return {"closed": True}
