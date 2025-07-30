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

import asyncio
import os
import pytest
import pytest_asyncio
from playwright.async_api import async_playwright
from config.settings import settings
from utils.ai_healing_decorator import OllamaAIHealingService
from collections import defaultdict
import threading
import subprocess
import requests
import time
import shutil
from datetime import datetime
from playwright.async_api import Locator, TimeoutError as PlaywrightTimeoutError

#Throw element not found when element selector times out, this helps with ai healing
class ElementNotFoundException(Exception):
    pass

def get_selector(locator):
    # Try to get the selector string safely
    return getattr(locator, "_selector", repr(locator))

# Patch wait_for
_original_wait_for = Locator.wait_for

async def patched_wait_for(self, state="visible", timeout=None):
    try:
        return await _original_wait_for(self, state=state, timeout=timeout)
    except PlaywrightTimeoutError:
        selector = get_selector(self)
        raise ElementNotFoundException(
            f"Element '{selector}' not found after waiting for state '{state}'"
        )

Locator.wait_for = patched_wait_for

# Patch click
_original_click = Locator.click

async def patched_click(self, *args, timeout=None, **kwargs):
    try:
        return await _original_click(self, *args, timeout=timeout, **kwargs)
    except PlaywrightTimeoutError:
        selector = get_selector(self)
        raise ElementNotFoundException(
            f"Element '{selector}' not found (click timeout after {timeout}ms)"
        )

Locator.click = patched_click

# Patch fill
_original_fill = Locator.fill

async def patched_fill(self, *args, timeout=None, **kwargs):
    try:
        return await _original_fill(self, *args, timeout=timeout, **kwargs)
    except PlaywrightTimeoutError:
        selector = get_selector(self)
        raise ElementNotFoundException(
            f"Element '{selector}' not found (fill timeout after {timeout}ms)"
        )

Locator.fill = patched_fill

# Thread-safe dictionary for parallel test runs
_ai_healing_fail_counts = defaultdict(int)
_ai_healing_lock = threading.Lock()
_ollama_checked = False
_ollama_service = OllamaAIHealingService()

def ensure_ollama_model_loaded(model_name=None, host=None, max_wait=180):
    """
    Check if the specified model is available and loaded.
    If not, attempt to pull and warm it up by waiting for a real response.
    """
    if not model_name:
        model_name = _ollama_service.model
    if not host:
        host = _ollama_service.ollama_host
    try:
        print(f"🤖 Checking if model {model_name} is available...")
        # List available models
        resp = requests.get(f"{host}/api/tags", timeout=5)
        if resp.status_code != 200:
            print(f"❌ Failed to get model list: {resp.status_code}")
            return False
        tags = resp.json().get("models", [])
        model_exists = any(model_name in m.get("name", "") for m in tags)
        if not model_exists:
            print(f"🤖 Model {model_name} not found. Attempting to pull...")
            pull_resp = requests.post(
                f"{host}/api/pull", 
                json={"name": model_name}, 
                timeout=180  # Pulling can take a while
            )
            if pull_resp.status_code == 200:
                print(f"🤖 Model {model_name} pulled successfully.")
            else:
                print(f"❌ Failed to pull model {model_name}: {pull_resp.text}")
                return False
        # Warm up the model by waiting for a real, non-error response
        print(f"🤖 Warming up model {model_name} (waiting for a real response)...")
        start = time.time()
        while time.time() - start < max_wait:
            try:
                gen_resp = requests.post(
                    f"{host}/api/generate",
                    json={
                        "model": model_name,
                        "prompt": "Hello",
                        "stream": False,
                        "options": {"num_predict": 5}
                    },
                    timeout=30
                )
                if gen_resp.status_code == 200:
                    response_data = gen_resp.json()
                    if "response" in response_data and response_data["response"].strip():
                        print(f"🤖 Model {model_name} is loaded and ready.")
                        return True
                    elif "error" in response_data:
                        print(f"🤖 Model not ready yet: {response_data['error']}")
                else:
                    print(f"🤖 Model not ready, status: {gen_resp.status_code}")
            except Exception as e:
                print(f"🤖 Waiting for model to load: {e}")
            time.sleep(3)
        print(f"❌ Model {model_name} did not become ready in {max_wait} seconds.")
        return False
    except requests.exceptions.Timeout:
        print(f"❌ Timeout while checking/loading model {model_name}")
        return False
    except Exception as e:
        print(f"❌ Error checking/loading model {model_name}: {e}")
        return False

def ensure_ollama_running():
    """
    Check if Ollama service is running and start it if not.
    Also ensures the specified model is loaded and ready.
    Returns True if service and model are available, False otherwise.
    """
    global _ollama_checked
    if _ollama_checked:
        return True
    print(f"🤖 Checking Ollama service at {_ollama_service.ollama_host}...")
    print(f"🤖 Ollama executable path: {shutil.which('ollama')}")
    try:
        # Try to ping the Ollama API
        response = requests.get(f"{_ollama_service.ollama_host}/api/tags", timeout=3)
        if response.status_code == 200:
            print("🤖 Ollama service is already running.")
        else:
            print(f"🤖 Ollama service responded with status {response.status_code}")
    except Exception:
        print("🤖 Ollama service not running, attempting to start...")
        try:
            if not shutil.which("ollama"):
                print("❌ Ollama command not found. Please install Ollama first.")
                return False
            print("🤖 Attempting to start Ollama with: ollama serve")
            proc = subprocess.Popen(
                ["ollama", "serve"], 
                stdout=subprocess.DEVNULL, 
                stderr=subprocess.DEVNULL
            )
            print(f"🤖 Ollama process started with PID: {proc.pid}")
            print("🤖 Waiting for Ollama service to start...")
            for i in range(30):
                try:
                    response = requests.get(f"{_ollama_service.ollama_host}/api/tags", timeout=2)
                    if response.status_code == 200:
                        print("🤖 Ollama service started successfully.")
                        break
                except Exception:
                    time.sleep(1)
                    if i % 5 == 0:
                        print(f"🤖 Still waiting for Ollama... ({i+1}/30)")
            else:
                print("❌ Failed to start Ollama service within 30 seconds.")
                return False
        except Exception as e:
            print(f"❌ Could not start Ollama service: {e}")
            return False
    # Now ensure the model is loaded and warmed up
    if not ensure_ollama_model_loaded():
        print(f"❌ Failed to load/warmup model {_ollama_service.model}")
        return False
    _ollama_checked = True
    return True

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

def _find_page_object(item):
    page = None
    funcargs = getattr(item, 'funcargs', {})
    if not page:
        for name, value in funcargs.items():
            if name == "page" and hasattr(value, 'screenshot'):
                page = value
                break
            elif name == "app" and hasattr(value, "page"):
                page = value.page
                break
            elif name.endswith("_page") and hasattr(value, "screenshot"):
                page = value
                break
            elif hasattr(value, "pages") and value.pages:
                page = value.pages[0]
                break
    return page

async def _capture_page_info(page, screenshot_path):
    await page.screenshot(path=screenshot_path)
    title = await page.title()
    return title

def _capture_ai_healing_context(item, page, error_message):
    try:
        test_name = item.name
        test_key = item.nodeid
        if not _ollama_service.enabled:
            print(f"🧠 AI healing is disabled via AI_HEALING_ENABLED flag. Skipping healing for {item.name}")
            return
        print(f"🧠 Test failed, capturing context for AI healing: {test_name}")
        original_test_code = ""
        try:
            test_file = item.fspath
            with open(test_file, 'r') as f:
                original_test_code = f.read()
        except Exception as e:
            print(f"Warning: Could not read test file: {e}")
        screenshot_path = None
        page_title = None
        if page:
            try:
                timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                screenshot_filename = f"{test_key.replace('::', '_').replace('/', '_')}_{timestamp}.png"
                screenshot_path = f"screenshots/{screenshot_filename}"
                os.makedirs("screenshots", exist_ok=True)
                page_title = asyncio.get_event_loop().run_until_complete(
                    _capture_page_info(page, screenshot_path)
                )
                print(f"Screenshot saved and attached to Allure: {screenshot_path}")
            except Exception as e:
                print(f"Warning: Could not capture screenshot: {e}")
        context = {
            "test_name": test_name,
            "test_file": str(item.fspath),
            "error_message": error_message,
            "timestamp": datetime.now().isoformat(),
            "browser": os.getenv("BROWSER", settings.BROWSER),
            "headless": os.getenv("HEADLESS", str(settings.HEADLESS)),
            "ollama_host": _ollama_service.ollama_host,
            "ollama_model": _ollama_service.model,
        }
        if page and page_title:
            try:
                context.update({
                    "current_url": getattr(page, 'url', None),
                    "page_title": page_title,
                    "viewport_size": getattr(page, 'viewport_size', None),
                })
            except Exception as e:
                print(f"Warning: Could not capture additional page context: {e}")
        if not hasattr(_ollama_service, '_pending_contexts'):
            _ollama_service._pending_contexts = {}
        _ollama_service._pending_contexts[test_key] = {
            "test_name": test_name,
            "context": context,
            "original_test_code": original_test_code,
            "screenshot_path": screenshot_path,
        }
        print(f"💾 Context saved for AI healing hook (key: {test_key})")
    except Exception as e:
        print(f"🧠 Error capturing AI healing context: {e}")

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    setattr(item, "rep_" + rep.when, rep)
    if rep.when == "call" and rep.failed:
        test_key = item.nodeid
        max_reruns = item.config.getoption("reruns") or 0
        with _ai_healing_lock:
            _ai_healing_fail_counts[test_key] += 1
            fail_count = _ai_healing_fail_counts[test_key]
        print(f"DEBUG: {test_key} fail_count={fail_count} (max_reruns={max_reruns})")
        page = _find_page_object(item)
        error_message = str(call.excinfo.value) if call.excinfo else "Unknown error"
        _capture_ai_healing_context(item, page, error_message)
        if fail_count > max_reruns:
            print(f"DEBUG: _ollama_service.enabled ={_ollama_service.enabled})")
            if not _ollama_service.enabled:
                print(f"🧠 AI healing is disabled via AI_HEALING_ENABLED flag. Skipping healing for {item.name}")
                return
            print(f"\n🧠 Final failure detected for {item.name}, triggering AI healing")
            print(f"🤖 Using Ollama at {_ollama_service.ollama_host} with model {_ollama_service.model}")
            if not ensure_ollama_running():
                print("🧠 AI healing skipped - Ollama service or model unavailable")
                return
            if hasattr(_ollama_service, '_pending_contexts'):
                context_data = _ollama_service._pending_contexts.get(test_key)
                if not context_data:
                    context_data = _ollama_service._pending_contexts.get(item.name)
            if context_data and _ollama_service.enabled:
                try:
                    print("🧠 Calling Ollama for AI healing analysis...")
                    ai_response = _ollama_service.call_ollama_healing(
                        context_data["context"],
                        context_data["original_test_code"],
                        context_data["screenshot_path"]
                    )
                    print("🤖 Full Ollama response:", ai_response)

                    # Defensive: handle None, string, or dict
                    if not ai_response:
                        print("🤖 Ollama service did not return a response. Is it running?")
                        print(f"🧠 Ollama analysis failed for {item.name}")
                        return  # Do not proceed

                    # If response is a string, try to parse as JSON
                    if isinstance(ai_response, str):
                        try:
                            import json
                            ai_response = json.loads(ai_response)
                        except Exception:
                            print("🤖 Ollama response is not valid JSON:", ai_response)
                            print(f"🧠 Ollama analysis failed for {item.name}")
                            return

                    # Check for error keys
                    if isinstance(ai_response, dict) and ("error" in ai_response or "error_type" in ai_response):
                        print("🤖 Ollama returned an error:", ai_response.get("error") or ai_response.get("error_type"))
                        print(f"🧠 Ollama analysis failed for {item.name}")
                        return

                    # If we get here, we have a valid response
                    print("🧠 AI analysis complete, generating healing report...")
                    asyncio.run(_ollama_service.generate_healing_report(
                        context_data["test_name"],
                        ai_response,
                        context_data["context"]
                    ))

                    # Clean up
                    if test_key in _ollama_service._pending_contexts:
                        del _ollama_service._pending_contexts[test_key]
                    if item.name in _ollama_service._pending_contexts:
                        del _ollama_service._pending_contexts[item.name]

                except Exception as e:
                    print(f"🧠 AI healing hook failed: {e}")
                    import traceback
                    traceback.print_exc()
            else:
                print(f"🧠 No pending contexts found")
            with _ai_healing_lock:
                if test_key in _ai_healing_fail_counts:
                    del _ai_healing_fail_counts[test_key]
        else:
            print(f"🔄 Test {item.name} will be retried (attempt {fail_count}), skipping AI healing")
