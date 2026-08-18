"""Drives a real Chromium instance via Playwright — no mocking. The browser
window is visible (headless=False) by design (spec: computer control must
be transparent, never hidden), so this test briefly pops up a window.
"""

import pytest

from app.computer import browser


@pytest.mark.asyncio
async def test_navigate_and_read_page():
    result = await browser.navigate("https://example.com")
    assert "example" in result["url"]
    assert result["title"]

    page = await browser.read_page_text()
    assert "Example Domain" in page["text"]

    await browser.close_browser()


@pytest.mark.asyncio
async def test_page_state_reflects_navigation():
    await browser.navigate("https://example.com")
    state = await browser.page_state()
    assert "example.com" in state["url"]
    await browser.close_browser()
