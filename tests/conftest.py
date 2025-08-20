"""
===============================================================================
Pytest Configuration and Fixtures
===============================================================================

This module contains pytest configuration, fixtures, and shared test utilities
for the Hudl application test suite. It provides centralized fixture definitions
that are available across all test modules.

Features:
    ✓ App fixture that aggregates all page objects for easy test access.
    ✓ Login page fixture with automatic navigation for login-specific tests.
    ✓ Environment variable loading for configuration management.
    ✓ Centralized fixture management to avoid code duplication.

Usage Example:
    # Fixtures are automatically available in all test files
    @pytest.mark.asyncio
    async def test_something(app):
        await app.login_page.enter_email("user@example.com")
        await app.dashboard_page.verify_user_info()

Conventions:
    - All fixtures are async to maintain Playwright compatibility.
    - The app fixture provides access to all page objects through a single instance.
    - Environment variables are loaded once at module level.
    - Fixtures follow the naming convention of the classes they instantiate.

Author: PMAC
Date: [2025-07-27]
===============================================================================
"""

import time
import pytest
import os
from pages.login_page import LoginPage
from pages.app import App
from utils.performance_monitor import PerformanceMetrics, PerformanceMonitorAsync
from datetime import datetime
# ------------------------------------------------------------------------------
# Login Page Fixture with Auto-Navigation
# ------------------------------------------------------------------------------

@pytest.fixture
async def login_page(page):
    """
    Fixture that provides a LoginPage instance with automatic navigation
    to the login page. Useful for tests that focus specifically on login functionality.
    
    Args:
        page: Playwright page fixture
        
    Returns:
        LoginPage: Configured login page object with navigation completed
    """
    login_page = LoginPage(page)
    await login_page.load_login_direct()
    return login_page

# ------------------------------------------------------------------------------
# App Fixture - Central Page Object Aggregator
# ------------------------------------------------------------------------------

@pytest.fixture
async def app(page):
    """
    Fixture that provides an App instance containing all page objects.
    This is the primary fixture for most tests, eliminating the need
    to pass multiple page fixtures to test functions.
    
    Args:
        page: Playwright page fixture
        
    Returns:
        App: Application object with access to all page objects
        
    Usage:
        Any pages configured in pages/app.py will be available here through
        the app fixture (e.g., app.login_page, app.dashboard_page, etc.)
    """
    return App(page)

@pytest.fixture(scope="function")
async def perf_monitor():
    """
    Performance monitor fixture for each test.
    - If PERF_MONITOR=1 → use real PerformanceMonitorAsync and export files.
    - Otherwise → use DummyMonitor that returns minimal metrics and does nothing else.
    """
    if os.getenv("PERF_MONITOR", "0") != "1":
        class DummyMonitor:
            def __init__(self):
                self.metrics_history = []

            async def measure_page_performance(self, page, url):
                m = PerformanceMetrics(url=url, timestamp=time.time())
                self.metrics_history.append(m)
                return m

            async def measure_current_page(self, page, label=None):
                try:
                    current_url = await page.evaluate("() => location.href")
                except Exception:
                    current_url = "about:blank"
                m = PerformanceMetrics(url=label or current_url, timestamp=time.time())
                self.metrics_history.append(m)
                return m

            def save_metrics_to_json(self, *args, **kwargs):
                pass

            def save_metrics_to_csv(self, *args, **kwargs):
                pass

            def get_average_metrics(self):
                return {}

            def clear_metrics(self):
                self.metrics_history.clear()

            def print_metrics_summary(self, metrics):
                # No-op: keep API parity with real monitor
                pass

        yield DummyMonitor()
        return

    # Real monitor when enabled
    monitor = PerformanceMonitorAsync(output_dir="test_artifacts/performance/auto_perf_reports")
    yield monitor
    # Save results after each test
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    monitor.save_metrics_to_json(f"auto_measured_pages_{timestamp}.json")
    monitor.save_metrics_to_csv(f"auto_measured_pages_{timestamp}.csv")

@pytest.fixture
async def enhanced_page(page, perf_monitor):
    """Enhanced page with performance monitoring and SPA detection"""
    
    # Inject combined script
    combined_script = """
        // Web Vitals tracking
        window.webVitalsData = { lcp: null, fid: null, cls: null, fcp: null };
        function observeLCP(){const o=new PerformanceObserver(list=>{const e=list.getEntries();const last=e[e.length-1];window.webVitalsData.lcp=last.startTime;});o.observe({entryTypes:['largest-contentful-paint']});}
        function observeFCP(){const o=new PerformanceObserver(list=>{for(const e of list.getEntries()){if(e.name==='first-contentful-paint'){window.webVitalsData.fcp=e.startTime;}}});o.observe({entryTypes:['paint']});}
        function observeCLS(){let v=0;const o=new PerformanceObserver(list=>{for(const e of list.getEntries()){if(!e.hadRecentInput){v+=e.value;}}window.webVitalsData.cls=v;});o.observe({entryTypes:['layout-shift']});}
        function observeFID(){const o=new PerformanceObserver(list=>{for(const e of list.getEntries()){window.webVitalsData.fid=e.processingStart - e.startTime;}});o.observe({entryTypes:['first-input']});}
        if (document.readyState === 'loading') {
          document.addEventListener('DOMContentLoaded', () => {observeLCP(); observeFCP(); observeCLS(); observeFID();});
        } else {observeLCP(); observeFCP(); observeCLS(); observeFID();}

        // SPA route change detection
        (function () {
          if (window.__routeChangeInstalled) return;
          window.__routeChangeInstalled = true;
          window.__routeChangeId = 0;
          function notifyRouteChange() {
            window.__routeChangeId++;
            window.dispatchEvent(new Event('routechange'));
          }
          const _pushState = history.pushState;
          history.pushState = function() {
            const ret = _pushState.apply(this, arguments);
            notifyRouteChange();
            return ret;
          };
          const _replaceState = history.replaceState;
          history.replaceState = function() {
            const ret = _replaceState.apply(this, arguments);
            notifyRouteChange();
            return ret;
          };
          window.addEventListener('popstate', notifyRouteChange, { passive: true });
        })();
    """
    
    await page.add_init_script(combined_script)
    
    # Wrap page methods
    orig_goto = page.goto
    orig_reload = page.reload

    async def goto_with_metrics(url, *args, **kwargs):
        resp = await orig_goto(url, *args, **kwargs)
        await page.wait_for_load_state("networkidle")
        await page.wait_for_timeout(500)
        await perf_monitor.measure_current_page(page, label=f"goto:{url}")
        return resp

    async def reload_with_metrics(*args, **kwargs):
        resp = await orig_reload(*args, **kwargs)
        await page.wait_for_load_state("networkidle")
        await page.wait_for_timeout(500)
        await perf_monitor.measure_current_page(page, label=f"reload:{page.url}")
        return resp

    page.goto = goto_with_metrics
    page.reload = reload_with_metrics
    
    return page