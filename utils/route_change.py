"""
Async helpers for detecting and measuring Single-Page App (SPA) route changes in Playwright tests.

What this module does:
- Detects client-side navigations triggered via history.pushState, history.replaceState, and popstate.
- Provides a helper to wait for a route change and a convenience function to measure performance right after it.
- Designed to work with a PerformanceMonitor that exposes `measure_current_page(page, label=...)`.

Usage:
    from route_change import wait_for_route_change, measure_after_spa_route_change

    # After triggering a SPA navigation (e.g., clicking a link or button):
    await page.click("nav >> text=Teams")
    metrics = await measure_after_spa_route_change(page, perf_monitor, label="route:/teams")

Prerequisites:
- Ensure your test setup injects a small init script on each document to track route changes:
    await context.add_init_script(\"\"\"
      (function () {
        if (window.__routeChangeInstalled) return;
        window.__routeChangeInstalled = true;
        window.__routeChangeId = 0;
        function notifyRouteChange() {
          window.__routeChangeId++;
          window.dispatchEvent(new Event('routechange'));
        }
        const _pushState = history.pushState;
        history.pushState = function() { const ret = _pushState.apply(this, arguments); notifyRouteChange(); return ret; };
        const _replaceState = history.replaceState;
        history.replaceState = function() { const ret = _replaceState.apply(this, arguments); notifyRouteChange(); return ret; };
        window.addEventListener('popstate', notifyRouteChange, { passive: true });
      })();
    \"\"\")

Notes:
- On pure SPA transitions there is no new document load, so Navigation Timing metrics like page load time may be None.
  You will still get CLS, resource metrics, and sometimes LCP if a large element is rendered during the transition.

Author: PMAC
Date: [2025-08-18]
"""


__all__ = ["wait_for_route_change", "measure_after_spa_route_change"]

async def wait_for_route_change(page, timeout=5000):
    """
    Waits for a client-side route change triggered via pushState/replaceState/popstate.
    Returns True if a route change was detected within timeout, else False.
    """
    prev = await page.evaluate("() => window.__routeChangeId || 0")
    try:
        await page.wait_for_function(
            "prev => (window.__routeChangeId || 0) !== prev",
            arg=prev,
            timeout=timeout
        )
        return True
    except Exception:
        return False
    
async def measure_after_spa_route_change(page, perf_monitor, label=None, settle_ms=500, timeout=5000):
    """
    Measures performance after a SPA route change without full document navigation.
    Call this right after triggering the action that changes routes.
    """
    changed = await wait_for_route_change(page, timeout=timeout)
    if not changed:
        # Optional: still try to measure if your app updates content without modifying history
        # You can add additional waits here (e.g., a key selector visible)
        pass

    await page.wait_for_timeout(settle_ms)
    return await perf_monitor.measure_current_page(page, label=label or f"route:{page.url}")