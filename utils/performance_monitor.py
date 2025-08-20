"""
Performance Monitoring Utilities (Async Version)
================================================

This module provides async performance monitoring instrumentation for Playwright tests.
It captures page load times, Core Web Vitals, and resource usage metrics to ensure
applications meet modern performance standards.

Features:
    ✓ Page load time measurement via Navigation Timing API
    ✓ Core Web Vitals collection (LCP, FID, CLS, FCP)
    ✓ Resource usage metrics (CPU, memory, network requests, bytes transferred)
    ✓ JSON and CSV export of metrics for analysis
    ✓ Clean summary printing with pass/fail thresholds
    ✓ Context manager for easy integration with tests
    ✓ Tracking and averaging of metrics across multiple runs
    ✓ SPA route change detection and measurement
    ✓ Current page measurement without navigation

Usage:
    # In your async test file
    monitor = PerformanceMonitorAsync()
    async with PerformanceTestAsync(monitor, "https://example.com") as perf_test:
        metrics = await perf_test.measure(page)
        assert metrics.page_load_time < 3000  # threshold assertion

Dependencies:
    - playwright.async_api: Async Playwright Page and Browser
    - dataclasses: Structured performance metrics container
    - json / csv: Report serialization
    - pathlib: File management and output directories

Author: PMAC
Date: [2025-08-18]
"""

import json
import time
import csv
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from playwright.async_api import Page


@dataclass
class PerformanceMetrics:
    """Data class to store performance metrics"""
    url: str
    timestamp: float
    page_load_time: Optional[float] = None
    dom_content_loaded: Optional[float] = None
    first_contentful_paint: Optional[float] = None
    largest_contentful_paint: Optional[float] = None
    first_input_delay: Optional[float] = None
    cumulative_layout_shift: Optional[float] = None
    time_to_first_byte: Optional[float] = None
    js_heap_used_size: Optional[int] = None
    js_heap_total_size: Optional[int] = None
    task_duration: Optional[float] = None
    network_requests: Optional[int] = None
    total_bytes_transferred: Optional[int] = None


class PerformanceMonitorAsync:
    """Async performance monitoring utility for Playwright tests"""
    
    def __init__(self, output_dir: str = "performance_reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.metrics_history: List[PerformanceMetrics] = []
        
    async def inject_web_vitals_script(self, page: Page) -> None:
        """Inject web-vitals library and setup collectors"""
        web_vitals_script = """
        // Web Vitals collection script
        window.webVitalsData = {
            lcp: null,
            fid: null,
            cls: null,
            fcp: null
        };
        
        // Simplified Web Vitals implementation
        function observeLCP() {
            const observer = new PerformanceObserver((list) => {
                const entries = list.getEntries();
                const lastEntry = entries[entries.length - 1];
                window.webVitalsData.lcp = lastEntry.startTime;
            });
            observer.observe({entryTypes: ['largest-contentful-paint']});
        }
        
        function observeFCP() {
            const observer = new PerformanceObserver((list) => {
                const entries = list.getEntries();
                for (const entry of entries) {
                    if (entry.name === 'first-contentful-paint') {
                        window.webVitalsData.fcp = entry.startTime;
                    }
                }
            });
            observer.observe({entryTypes: ['paint']});
        }
        
        function observeCLS() {
            let clsValue = 0;
            const observer = new PerformanceObserver((list) => {
                for (const entry of list.getEntries()) {
                    if (!entry.hadRecentInput) {
                        clsValue += entry.value;
                    }
                }
                window.webVitalsData.cls = clsValue;
            });
            observer.observe({entryTypes: ['layout-shift']});
        }
        
        function observeFID() {
            const observer = new PerformanceObserver((list) => {
                for (const entry of list.getEntries()) {
                    window.webVitalsData.fid = entry.processingStart - entry.startTime;
                }
            });
            observer.observe({entryTypes: ['first-input']});
        }
        
        // Start observing
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                observeLCP();
                observeFCP();
                observeCLS();
                observeFID();
            });
        } else {
            observeLCP();
            observeFCP();
            observeCLS();
            observeFID();
        }
        """
        await page.add_init_script(web_vitals_script)
    
    async def collect_navigation_timing(self, page: Page) -> Dict[str, Any]:
        """Collect navigation timing metrics"""
        return await page.evaluate("""
            () => {
                const timing = performance.timing;
                const navigation = performance.getEntriesByType('navigation')[0];
                
                return {
                    navigationStart: timing.navigationStart,
                    domContentLoadedEventEnd: timing.domContentLoadedEventEnd,
                    loadEventEnd: timing.loadEventEnd,
                    responseStart: timing.responseStart,
                    domComplete: timing.domComplete,
                    timeToFirstByte: navigation ? navigation.responseStart : null
                };
            }
        """)
    
    async def collect_web_vitals(self, page: Page) -> Dict[str, Any]:
        """Collect Web Vitals metrics"""
        return await page.evaluate("() => window.webVitalsData || {}")
    
    async def collect_resource_metrics(self, page: Page) -> Dict[str, Any]:
        """Collect resource usage metrics"""
        try:
            # Get Playwright's built-in metrics (Chrome only)
            metrics = await page.evaluate("""
                () => {
                    const entries = performance.getEntriesByType('resource');
                    const totalBytes = entries.reduce((sum, entry) => {
                        return sum + (entry.transferSize || 0);
                    }, 0);
                    
                    return {
                        resourceCount: entries.length,
                        totalBytesTransferred: totalBytes,
                        jsHeapUsedSize: performance.memory ? performance.memory.usedJSHeapSize : null,
                        jsHeapTotalSize: performance.memory ? performance.memory.totalJSHeapSize : null
                    };
                }
            """)
            return metrics
        except Exception as e:
            print(f"Warning: Could not collect resource metrics: {e}")
            return {}
    
    async def measure_current_page(self, page: Page, label: Optional[str] = None) -> PerformanceMetrics:
        """
        Measure performance for the currently loaded page without triggering a new navigation.
        Useful after page.goto/reload or SPA route changes.
        """
        timestamp = time.time()

        # Safe to call multiple times; ensures the vitals observers are present
        await self.inject_web_vitals_script(page)

        # Give the page a moment to settle (network idle + small delay)
        try:
            await page.wait_for_load_state("networkidle")
        except Exception:
            # Some apps never reach 'networkidle'; fall back to 'load'
            await page.wait_for_load_state("load")
        await page.wait_for_timeout(500)

        navigation_timing = await self.collect_navigation_timing(page)
        web_vitals = await self.collect_web_vitals(page)
        resource_metrics = await self.collect_resource_metrics(page)

        # Derive metrics
        page_load_time = None
        dom_content_loaded = None
        time_to_first_byte = None

        if navigation_timing.get('navigationStart') and navigation_timing.get('loadEventEnd'):
            page_load_time = navigation_timing['loadEventEnd'] - navigation_timing['navigationStart']

        if navigation_timing.get('navigationStart') and navigation_timing.get('domContentLoadedEventEnd'):
            dom_content_loaded = navigation_timing['domContentLoadedEventEnd'] - navigation_timing['navigationStart']

        if navigation_timing.get('timeToFirstByte'):
            time_to_first_byte = navigation_timing['timeToFirstByte']

        metrics = PerformanceMetrics(
            url=label or page.url,
            timestamp=timestamp,
            page_load_time=page_load_time,
            dom_content_loaded=dom_content_loaded,
            first_contentful_paint=web_vitals.get('fcp'),
            largest_contentful_paint=web_vitals.get('lcp'),
            first_input_delay=web_vitals.get('fid'),
            cumulative_layout_shift=web_vitals.get('cls'),
            time_to_first_byte=time_to_first_byte,
            js_heap_used_size=resource_metrics.get('jsHeapUsedSize'),
            js_heap_total_size=resource_metrics.get('jsHeapTotalSize'),
            network_requests=resource_metrics.get('resourceCount'),
            total_bytes_transferred=resource_metrics.get('totalBytesTransferred'),
        )

        self.metrics_history.append(metrics)
        return metrics
    
    async def measure_page_performance(self, page: Page, url: str) -> PerformanceMetrics:
        """Comprehensive performance measurement for a page with navigation"""
        timestamp = time.time()
        
        # Inject Web Vitals script before navigation
        await self.inject_web_vitals_script(page)
        
        # Navigate to the page
        await page.goto(url)
        await page.wait_for_load_state('networkidle')
        
        # Wait a bit for Web Vitals to be collected
        await page.wait_for_timeout(2000)
        
        # Collect all metrics
        navigation_timing = await self.collect_navigation_timing(page)
        web_vitals = await self.collect_web_vitals(page)
        resource_metrics = await self.collect_resource_metrics(page)
        
        # Calculate derived metrics
        page_load_time = None
        dom_content_loaded = None
        time_to_first_byte = None
        
        if navigation_timing.get('navigationStart') and navigation_timing.get('loadEventEnd'):
            page_load_time = navigation_timing['loadEventEnd'] - navigation_timing['navigationStart']
        
        if navigation_timing.get('navigationStart') and navigation_timing.get('domContentLoadedEventEnd'):
            dom_content_loaded = navigation_timing['domContentLoadedEventEnd'] - navigation_timing['navigationStart']
        
        if navigation_timing.get('timeToFirstByte'):
            time_to_first_byte = navigation_timing['timeToFirstByte']
        
        # Create metrics object
        metrics = PerformanceMetrics(
            url=url,
            timestamp=timestamp,
            page_load_time=page_load_time,
            dom_content_loaded=dom_content_loaded,
            first_contentful_paint=web_vitals.get('fcp'),
            largest_contentful_paint=web_vitals.get('lcp'),
            first_input_delay=web_vitals.get('fid'),
            cumulative_layout_shift=web_vitals.get('cls'),
            time_to_first_byte=time_to_first_byte,
            js_heap_used_size=resource_metrics.get('jsHeapUsedSize'),
            js_heap_total_size=resource_metrics.get('jsHeapTotalSize'),
            network_requests=resource_metrics.get('resourceCount'),
            total_bytes_transferred=resource_metrics.get('totalBytesTransferred')
        )
        
        self.metrics_history.append(metrics)
        return metrics
    
    def save_metrics_to_json(self, filename: str = None) -> str:
        """Save collected metrics to JSON file with timestamp in filename"""
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        if not filename:
            filename = f"performance_metrics_{ts}.json"
        else:
            if not filename.endswith(".json"):
                filename = f"{filename}_{ts}.json"
            else:
                base = filename[:-5]
                filename = f"{base}_{ts}.json"
        
        filepath = self.output_dir / filename
        
        with open(filepath, 'w') as f:
            json.dump([asdict(metric) for metric in self.metrics_history], f, indent=2)
        
        return str(filepath)
    
    def save_metrics_to_csv(self, filename: str = None) -> str:
        """Save collected metrics to CSV file with timestamp in filename"""
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        if not filename:
            filename = f"performance_metrics_{ts}.csv"
        else:
            if not filename.endswith(".csv"):
                filename = f"{filename}_{ts}.csv"
            else:
                base = filename[:-4]
                filename = f"{base}_{ts}.csv"
        
        filepath = self.output_dir / filename
        
        if self.metrics_history:
            with open(filepath, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=asdict(self.metrics_history[0]).keys())
                writer.writeheader()
                for metric in self.metrics_history:
                    writer.writerow(asdict(metric))
        
        return str(filepath)
    
    def print_metrics_summary(self, metrics: PerformanceMetrics) -> None:
        """Print a formatted summary of performance metrics"""
        print(f"\n🚀 Performance Metrics for {metrics.url}")
        print("=" * 60)
        
        if metrics.page_load_time:
            print(f"📊 Page Load Time: {metrics.page_load_time:.2f} ms")
        
        if metrics.dom_content_loaded:
            print(f"🏗️  DOM Content Loaded: {metrics.dom_content_loaded:.2f} ms")
        
        if metrics.time_to_first_byte:
            print(f"⚡ Time to First Byte: {metrics.time_to_first_byte:.2f} ms")
        
        print("\n🎯 Core Web Vitals:")
        if metrics.largest_contentful_paint:
            lcp_status = "✅ Good" if metrics.largest_contentful_paint <= 2500 else "⚠️ Needs Improvement" if metrics.largest_contentful_paint <= 4000 else "❌ Poor"
            print(f"   LCP: {metrics.largest_contentful_paint:.2f} ms ({lcp_status})")
        
        if metrics.first_input_delay:
            fid_status = "✅ Good" if metrics.first_input_delay <= 100 else "⚠️ Needs Improvement" if metrics.first_input_delay <= 300 else "❌ Poor"
            print(f"   FID: {metrics.first_input_delay:.2f} ms ({fid_status})")
        
        if metrics.cumulative_layout_shift is not None:
            cls_status = "✅ Good" if metrics.cumulative_layout_shift <= 0.1 else "⚠️ Needs Improvement" if metrics.cumulative_layout_shift <= 0.25 else "❌ Poor"
            print(f"   CLS: {metrics.cumulative_layout_shift:.3f} ({cls_status})")
        
        if metrics.first_contentful_paint:
            print(f"   FCP: {metrics.first_contentful_paint:.2f} ms")
        
        print("\n💾 Resource Usage:")
        if metrics.js_heap_used_size:
            print(f"   JS Heap Used: {metrics.js_heap_used_size / 1024 / 1024:.2f} MB")
        
        if metrics.network_requests:
            print(f"   Network Requests: {metrics.network_requests}")
        
        if metrics.total_bytes_transferred:
            print(f"   Total Bytes: {metrics.total_bytes_transferred / 1024:.2f} KB")
        
        print("=" * 60)
    
    def get_average_metrics(self) -> Dict[str, float]:
        """Calculate average metrics across all measurements"""
        if not self.metrics_history:
            return {}
        
        metrics_sum = {}
        metrics_count = {}
        
        for metric in self.metrics_history:
            for key, value in asdict(metric).items():
                if isinstance(value, (int, float)) and value is not None:
                    metrics_sum[key] = metrics_sum.get(key, 0) + value
                    metrics_count[key] = metrics_count.get(key, 0) + 1
        
        return {key: metrics_sum[key] / metrics_count[key] 
                for key in metrics_sum if metrics_count[key] > 0}
    
    def clear_metrics(self) -> None:
        """Clear collected metrics history"""
        self.metrics_history.clear()


# Context manager for easy performance monitoring
class PerformanceTestAsync:
    """Async context manager for performance testing"""
    
    def __init__(self, monitor: PerformanceMonitorAsync, url: str, print_summary: bool = True):
        self.monitor = monitor
        self.url = url
        self.print_summary = print_summary
        self.metrics = None
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.metrics and self.print_summary:
            self.monitor.print_metrics_summary(self.metrics)
    
    async def measure(self, page: Page) -> PerformanceMetrics:
        """Measure performance for the given page"""
        self.metrics = await self.monitor.measure_page_performance(page, self.url)
        return self.metrics


# SPA Route Change Helpers
async def wait_for_route_change(page: Page, timeout: int = 5000) -> bool:
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


async def measure_after_spa_route_change(page: Page, perf_monitor: PerformanceMonitorAsync, 
                                       label: Optional[str] = None, settle_ms: int = 500, 
                                       timeout: int = 5000) -> PerformanceMetrics:
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