import os
import pytest_asyncio
from playwright.async_api import async_playwright
from config.settings import settings

#BROWSER=firefox pytest
#BROWSER=webkit pytest
#BROWSER=chromium pytest
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

        print(f"\n🚀 Using {browser_name} browser (headless={headless})")
        yield page
        await browser.close()
