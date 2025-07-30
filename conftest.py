"""
===============================================================================
Playwright Browser Configuration and Page Fixture with Auto AI Healing
===============================================================================

This module provides the core Playwright browser configuration and page fixture
for automated testing across multiple browsers (Chromium, Firefox, WebKit).
It handles browser selection, headless mode configuration, and provides a 
reusable async page fixture for all test modules.

NEW: Automatic AI healing is applied to ALL tests without needing decorators!
NEW: Automatically starts Ollama service if not running!
NEW: Automatically loads and warms up the specified model if not available!

Features:
    ✓ Multi-browser support (Chromium, Firefox, WebKit) via environment variables
    ✓ Configurable headless/headed mode for debugging and CI/CD environments
    ✓ Centralized browser options management through settings configuration
    ✓ Automatic browser cleanup after test execution
    ✓ Runtime browser selection without code changes
    ✓ AUTOMATIC AI healing for all test failures (no decorators needed!)
    ✓ Auto-starts Ollama service if not running
    ✓ Auto-loads and warms up specified model if not available
    ✓ Configurable Ollama host and model via environment variables
    ✓ Thread-safe for parallel test execution

Environment Variables:
    BROWSER: Specifies which browser to use (chromium|firefox|webkit)
    HEADLESS: Controls headless mode (true|false)
    OLLAMA_HOST: Ollama server URL (default: http://localhost:11434)
    OLLAMA_MODEL: Model to use for AI healing (default: llama3.1:8b)

Usage Examples:
    # Run tests with default browser and AI healing
    pytest

    # Run tests with specific browser, retries, and custom Ollama settings
    BROWSER=firefox OLLAMA_MODEL=llama3.2:3b pytest --reruns 3
    OLLAMA_HOST=http://remote-server:11434 pytest --reruns 2

    # Run tests in headed mode for debugging
    HEADLESS=false pytest

Fixture Usage:
    @pytest.mark.asyncio
    async def test_example(page):
        await page.goto("https://example.com")
        # Test implementation here...
        # AI healing will automatically capture context on failure!

Dependencies:
    - playwright.async_api: Async Playwright API
    - pytest_asyncio: Async test support
    - config.settings: Application configuration management
    - utils.ai_healing_decorator_fixed: AI healing service
    - requests: For Ollama service health checks

Author: PMAC
Date: [2025-07-29]
===============================================================================
"""

import os
import pytest
import pytest_asyncio
from playwright.async_api import async_playwright
from config.settings import settings
from playwright.async_api import Locator, TimeoutError as PlaywrightTimeoutError
import threading
from collections import defaultdict
import asyncio
from utils.ai_healing import _ollama_service, _capture_ai_healing_context, _find_page_object, ensure_ollama_running

# Thread-safe dictionary and lock for tracking test failure counts
_ai_healing_fail_counts = defaultdict(int)
_ai_healing_lock = threading.Lock()

# ------------------------------------------------------------------------------
# Class: ElementNotFoundException
# ------------------------------------------------------------------------------

class ElementNotFoundException(Exception):
    """
    Custom exception raised when a Playwright Locator times out waiting for an element.
    This helps AI healing to detect element-not-found scenarios explicitly.
    """
    pass

# ------------------------------------------------------------------------------
# Function: get_selector
# ------------------------------------------------------------------------------

def get_selector(locator):
    """
    Safely retrieve the selector string from a Playwright Locator object.
    Falls back to the string representation if the private _selector attribute is missing.

    Args:
        locator (Locator): Playwright Locator instance.

    Returns:
        str: Selector string or fallback string representation.
    """
    return getattr(locator, "_selector", repr(locator))

# ------------------------------------------------------------------------------
# Function: patched_wait_for
# ------------------------------------------------------------------------------

_original_wait_for = Locator.wait_for

async def patched_wait_for(self, state="visible", timeout=None):
    """
    Monkey-patched version of Locator.wait_for that raises ElementNotFoundException
    instead of Playwright's TimeoutError when the element is not found within timeout.

    Args:
        state (str): The state to wait for (default: "visible").
        timeout (int): Timeout in milliseconds.

    Raises:
        ElementNotFoundException: If the element is not found within the timeout.

    Returns:
        The result of the original wait_for method if successful.
    """
    try:
        return await _original_wait_for(self, state=state, timeout=timeout)
    except PlaywrightTimeoutError:
        selector = get_selector(self)
        raise ElementNotFoundException(
            f"Element '{selector}' not found after waiting for state '{state}'"
        )

Locator.wait_for = patched_wait_for

# ------------------------------------------------------------------------------
# Function: patched_click
# ------------------------------------------------------------------------------

_original_click = Locator.click

async def patched_click(self, *args, timeout=None, **kwargs):
    """
    Monkey-patched version of Locator.click that raises ElementNotFoundException
    instead of Playwright's TimeoutError when the element is not clickable within timeout.

    Args:
        *args: Positional arguments for click.
        timeout (int): Timeout in milliseconds.
        **kwargs: Keyword arguments for click.

    Raises:
        ElementNotFoundException: If the element is not clickable within the timeout.

    Returns:
        The result of the original click method if successful.
    """
    try:
        return await _original_click(self, *args, timeout=timeout, **kwargs)
    except PlaywrightTimeoutError:
        selector = get_selector(self)
        raise ElementNotFoundException(
            f"Element '{selector}' not found (click timeout after {timeout}ms)"
        )

Locator.click = patched_click

# ------------------------------------------------------------------------------
# Function: patched_fill
# ------------------------------------------------------------------------------

_original_fill = Locator.fill

async def patched_fill(self, *args, timeout=None, **kwargs):
    """
    Monkey-patched version of Locator.fill that raises ElementNotFoundException
    instead of Playwright's TimeoutError when the element is not fillable within timeout.

    Args:
        *args: Positional arguments for fill.
        timeout (int): Timeout in milliseconds.
        **kwargs: Keyword arguments for fill.

    Raises:
        ElementNotFoundException: If the element is not fillable within the timeout.

    Returns:
        The result of the original fill method if successful.
    """
    try:
        return await _original_fill(self, *args, timeout=timeout, **kwargs)
    except PlaywrightTimeoutError:
        selector = get_selector(self)
        raise ElementNotFoundException(
            f"Element '{selector}' not found (fill timeout after {timeout}ms)"
        )

Locator.fill = patched_fill

# ------------------------------------------------------------------------------
# Fixture: page
# ------------------------------------------------------------------------------

@pytest_asyncio.fixture
async def page():
    """
    Async pytest fixture that launches a Playwright browser page based on environment
    variables or settings configuration. Supports Chromium, Firefox, and WebKit.

    Yields:
        Page: An instance of Playwright's Page object for test use.

    Raises:
        ValueError: If an unsupported browser name is specified.
    """
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

# ------------------------------------------------------------------------------
# Hook: pytest_runtest_makereport
# ------------------------------------------------------------------------------

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    Hook that runs after each test phase (setup, call, teardown).
    Automatically captures context for AI healing on ANY test failure.
    Triggers AI healing only on final failure (after all retries).
    Thread-safe for parallel test runs.

    NO DECORATORS NEEDED - this applies to ALL tests automatically!
    """
    outcome = yield
    rep = outcome.get_result()

    print(f"DEBUG: rep.when={rep.when}, rep.failed={rep.failed}, item={item.nodeid}")

    setattr(item, "rep_" + rep.when, rep)

    if rep.when == "call" and rep.failed:
        test_key = item.nodeid
        max_reruns = item.config.getoption("reruns") or 0

        # Increment fail count in a thread-safe way
        with _ai_healing_lock:
            _ai_healing_fail_counts[test_key] += 1
            fail_count = _ai_healing_fail_counts[test_key]

        print(f"DEBUG: {test_key} fail_count={fail_count} (max_reruns={max_reruns})")

        # Capture context on EVERY failure (for screenshot, etc.)
        page = _find_page_object(item)
        error_message = str(call.excinfo.value) if call.excinfo else "Unknown error"
        _capture_ai_healing_context(item, page, error_message)

        # Only trigger AI healing on the final failure
        if fail_count > max_reruns:
            print(f"\n🧠 Final failure detected for {item.name}, triggering AI healing")
            if hasattr(_ollama_service, '_pending_contexts'):
                context_data = _ollama_service._pending_contexts.get(test_key)
                if not context_data:
                    context_data = _ollama_service._pending_contexts.get(item.name)
                if context_data and _ollama_service.enabled:
                    if not ensure_ollama_running():
                        print("🧠 AI healing skipped - Ollama service or model unavailable")
                        return
                    try:
                        ai_response = _ollama_service.call_ollama_healing(
                            context_data["context"],
                            context_data["original_test_code"],
                            context_data["screenshot_path"]
                        )
                        if ai_response:
                            asyncio.run(_ollama_service.generate_healing_report(
                                context_data["test_name"],
                                ai_response,
                                context_data["context"]
                            ))
                        else:
                            print(f"🧠 Ollama analysis failed for {item.name}")
                        # Clean up
                        if test_key in _ollama_service._pending_contexts:
                            del _ollama_service._pending_contexts[test_key]
                        if item.name in _ollama_service._pending_contexts:
                            del _ollama_service._pending_contexts[item.name]
                    except Exception as e:
                        print(f"🧠 AI healing hook failed: {e}")
                else:
                    if not context_data:
                        print(f"🧠 No context data found for {item.name}")
                    if not _ollama_service.enabled:
                        print(f"🧠 AI healing disabled for {item.name}")
            else:
                print(f"🧠 No pending contexts found")
            # Clean up fail count
            with _ai_healing_lock:
                if test_key in _ai_healing_fail_counts:
                    del _ai_healing_fail_counts[test_key]
        else:
            print(f"🔄 Test {item.name} will be retried (attempt {fail_count}), skipping AI healing")