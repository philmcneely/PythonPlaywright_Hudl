"""
===============================================================================
Login Performance and Navigation Metrics
===============================================================================

This module contains an end-to-end performance test for the Hudl login flow,
capturing key page load KPIs and SPA route-change metrics from login through
dashboard verification and logout.

Features:
✓ Auto-measures all full navigations (page.goto/reload) via enhanced_page wrapper.
✓ Captures Core Web Vitals (LCP, FCP, CLS) and timing metrics where available.
✓ Measures SPA transitions using measure_after_spa_route_change for client-side updates.
✓ Aggregates results across the flow and prints summary plus simple budgets.

Usage:
# Enable full performance collection and report exports
PERF_MONITOR=1 pytest -v tests/performance/test_login_perf.py::test_login_direct_valid_credentials_then_logout_performance

# Run without PERF_MONITOR (uses DummyMonitor with minimal metrics, no exports)
pytest -v tests/performance/test_login_perf.py::test_login_direct_valid_credentials_then_logout_performance
Conventions:
- Uses async Playwright fixtures (enhanced_page, perf_monitor) from conftest.py.
- Uses data.personas.PERSONAS for credentials; no secrets hardcoded in tests.
- SPA interactions are followed by measure_after_spa_route_change with a clear label.
- Assertions use tolerant guards (e.g., metric is None or < budget) for SPA cases.

Requirements:
- PERF_MONITOR=1 to collect real metrics and export JSON/CSV reports.
- Without PERF_MONITOR, a DummyMonitor returns minimal metrics to keep tests runnable.

Todo:
- Add per-step budgets (login page, dashboard, logout) and tag regressions per route label.
- Parameterize user personas and environments (staging/prod) via pytest options.

Author: PMAC
Date: [2025-08-18]
===============================================================================
"""

import pytest
from utils.performance_monitor import measure_after_spa_route_change
from utils.decorators.screenshot_decorator import screenshot_on_failure  # Add this import if the decorator is defined in utils/screenshot.py
from data.personas import PERSONAS

@screenshot_on_failure
@pytest.mark.performance
@pytest.mark.asyncio
async def test_login_direct_valid_credentials_then_logout_performance(app, enhanced_page, perf_monitor):
    """
    Test direct login navigation with valid credentials.
    Auto-measures all page navigations + manual SPA route measurements.
    """
    
    # Use enhanced_page instead of page - it has auto-measurement built in
    page = enhanced_page
    
    # All page.goto calls are now auto-measured!
    await app.login_page.load_login_direct()  # Auto-measured
    
    await app.login_page.fill_email_and_password_submit(
        PERSONAS["user"]["email"], 
        PERSONAS["user"]["password"]
    )
    # Dashboard load after login is auto-measured
    
    await app.dashboard_page.verify_user_profile_info()
    
    # If clicking user avatar triggers SPA navigation, measure it:
    await app.dashboard_page.click_user_avatar()
    # If this is a SPA route change (dropdown/modal), measure it:
    await measure_after_spa_route_change(page, perf_monitor, label="user_menu_opened")
    
    await app.dashboard_page.click_logout()
    # Logout navigation is auto-measured
    
    await app.login_page.load_home()  # Auto-measured
    await app.login_page.email_textbox.is_visible()

    # Print summary of all measurements
    print(f"\n📊 Total pages measured: {len(perf_monitor.metrics_history)}")
    
    avg_metrics = perf_monitor.get_average_metrics()
    if avg_metrics and avg_metrics.get('page_load_time'):
        print(f"📈 Average page load time: {avg_metrics['page_load_time']:.2f} ms")
    
    # Performance assertions across the entire flow
    for metric in perf_monitor.metrics_history:
        if metric.page_load_time:
            assert metric.page_load_time < 5000, f"Page {metric.url} too slow: {metric.page_load_time}ms"