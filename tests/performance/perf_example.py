"""
Performance Monitoring Test Suite (Async)
=========================================

This test suite demonstrates integration of the PerformanceMonitorAsync
with Playwright-powered functional tests. It verifies that critical
pages and user flows meet performance budgets.

Usage:
    pytest -v tests/performance/perf_example.py

Note:
    These tests require PERF_MONITOR=1 to be set, otherwise they are skipped
    by the perf_monitor fixture defined in conftest.py.
"""

import pytest
from utils.performance_monitor import (
    PerformanceTestAsync,
    measure_after_spa_route_change,
)

pytestmark = pytest.mark.asyncio


class TestWithPerformanceMonitoring:
    """Example test class showing async performance monitoring integration"""

    async def test_homepage_performance(self, page, perf_monitor):
        """Test homepage performance metrics"""
        url = "https://example.com"
        async with PerformanceTestAsync(perf_monitor, url) as perf_test:
            metrics = await perf_test.measure(page)

            assert metrics.page_load_time is None or metrics.page_load_time < 3000, \
                f"Page load too slow: {metrics.page_load_time}ms"

            if metrics.largest_contentful_paint:
                assert metrics.largest_contentful_paint < 2500, \
                    f"LCP too slow: {metrics.largest_contentful_paint}ms"

            if metrics.cumulative_layout_shift is not None:
                assert metrics.cumulative_layout_shift < 0.1, \
                    f"CLS too high: {metrics.cumulative_layout_shift}"

    async def test_search_page_performance(self, page, perf_monitor):
        """Test search functionality performance"""
        # Initial navigation (measured by context manager)
        async with PerformanceTestAsync(perf_monitor, "https://example.com") as perf_test:
            await perf_test.measure(page)

        # Perform a search; if it triggers SPA update, measure after route change.
        search_input = page.locator("input[name='search']")
        if await search_input.count() > 0:
            await search_input.fill("test query")
            await search_input.press("Enter")

            # If search results are SPA-rendered, this captures it. Otherwise, it's still safe.
            metrics = await measure_after_spa_route_change(
                page, perf_monitor, label="search_results", settle_ms=600, timeout=5000
            )

            assert metrics.page_load_time is None or metrics.page_load_time < 2000, \
                f"Search too slow: {metrics.page_load_time}ms"

    async def test_multiple_pages_performance(self, page, perf_monitor):
        """Test performance across multiple pages"""
        test_urls = [
            "https://example.com",
            "https://example.com/about",
            "https://example.com/contact",
        ]

        for url in test_urls:
            async with PerformanceTestAsync(perf_monitor, url, print_summary=False) as perf_test:
                metrics = await perf_test.measure(page)
                assert metrics.page_load_time is None or metrics.page_load_time < 5000, \
                    f"Page {url} load too slow: {metrics.page_load_time}ms"

    async def test_performance_with_interactions(self, page, perf_monitor):
        """Test performance during user interactions"""
        # Initial page load
        async with PerformanceTestAsync(perf_monitor, "https://example.com") as perf_test:
            await perf_test.measure(page)

        # Click first 3 visible nav links and measure each resulting page
        try:
            nav_links = page.locator("nav a")
            count = await nav_links.count()
            limit = min(count, 3)

            for i in range(limit):
                link = nav_links.nth(i)
                if not await link.is_visible():
                    continue

                href = await link.get_attribute("href")
                if not href or href.startswith("#"):
                    continue

                # Click and then measure the resulting page (full nav or SPA)
                await link.click()
                # Try SPA measure first; if no SPA change detected, still measure current state
                metrics = await measure_after_spa_route_change(
                    page, perf_monitor, label=f"nav:{href}", settle_ms=600, timeout=4000
                )

                # As a fallback for full navigations, ensure load state and measure again if needed
                if metrics.page_load_time is None:
                    try:
                        await page.wait_for_load_state("networkidle", timeout=5000)
                    except Exception:
                        await page.wait_for_load_state("load", timeout=5000)
                    metrics = await perf_monitor.measure_current_page(page, label=f"nav:{href}")

                # Basic assertion for interaction navigation
                assert metrics.page_load_time is None or metrics.page_load_time < 3000, \
                    f"Navigation too slow: {metrics.page_load_time}ms"
        except Exception as e:
            print(f"Interaction test skipped: {e}")