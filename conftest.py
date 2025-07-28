"""
===============================================================================
Playwright Browser Configuration and Page Fixture
===============================================================================

This module provides the core Playwright browser configuration and page fixture
for automated testing across multiple browsers (Chromium, Firefox, WebKit).
It handles browser selection, headless mode configuration, and provides a 
reusable async page fixture for all test modules.

Features:
    ✓ Multi-browser support (Chromium, Firefox, WebKit) via environment variables
    ✓ Configurable headless/headed mode for debugging and CI/CD environments
    ✓ Centralized browser options management through settings configuration
    ✓ Automatic browser cleanup after test execution
    ✓ Runtime browser selection without code changes

Environment Variables:
    BROWSER: Specifies which browser to use (chromium|firefox|webkit)
    HEADLESS: Controls headless mode (true|false)

Usage Examples:
    # Run tests with default browser (from settings)
    pytest
    
    # Run tests with specific browser
    BROWSER=firefox pytest
    BROWSER=webkit pytest
    BROWSER=chromium pytest
    
    # Run tests in headed mode for debugging
    HEADLESS=false pytest

Fixture Usage:
    @pytest.mark.asyncio
    async def test_example(page):
        await page.goto("https://example.com")
        # Test implementation here...

Dependencies:
    - playwright.async_api: Async Playwright API
    - pytest_asyncio: Async test support
    - config.settings: Application configuration management

Author: PMAC
Date: [2025-07-28]
===============================================================================
"""

import os
import pytest_asyncio
from playwright.async_api import async_playwright
from config.settings import settings

@pytest_asyncio.fixture
async def page():
    async with async_playwright() as p:
        browser_name = os.getenv("BROWSER", settings.BROWSER).lower()
        headless = os.getenv("HEADLESS", str(settings.HEADLESS)).lower() == "true"

        browser_options = settings.get_browser_options()
        browser_options["headless"] = headless

        if browser_name == "chromium":
            browser = await p.chromium.launch(**browser_options)
        elif browser_name == "firefox":
            browser = await p.firefox.launch(**browser_options)
        elif browser_name == "webkit":
            browser = await p.webkit.launch(**browser_options)
        else:
            raise ValueError(f"Unsupported BROWSER value: {browser_name}")

        context = await browser.new_context()
        page = await context.new_page()

        print(f"\n Using {browser_name} browser (headless={headless})")
        yield page
        await browser.close()
