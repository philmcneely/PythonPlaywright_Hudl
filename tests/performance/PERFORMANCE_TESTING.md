# 🚀 Performance Testing

This project includes a robust performance testing suite built with Playwright and Pytest, designed to measure key performance indicators (KPIs) for web pages and user flows.

## Features
- **Page Load Metrics:** Captures traditional page load times, DOM content loaded, and time to first byte.
- **Core Web Vitals:** Monitors modern user experience metrics like Largest Contentful Paint (LCP), First Input Delay (FID), and Cumulative Layout Shift (CLS).
- **Resource Usage:** Tracks JavaScript heap size, network requests, and total bytes transferred.
- **SPA Route Change Detection:** Measures performance for client-side navigations in Single-Page Applications (SPAs).
- **Conditional Execution:** Enabled only with an environment variable to prevent overhead during normal runs.
- **Automated Reporting:** Generates JSON and CSV reports with timestamps.

## How to Run Performance Tests

Performance tests are opt-in.

### 1. Enable Performance Monitoring

**Linux/macOS**
```bash
PERF_MONITOR=1 pytest -v tests/performance/
```

**Windows (Command Prompt)**
```cmd
set PERF_MONITOR=1
pytest -v tests/performance/
```

**Windows (PowerShell)**
```powershell
$env:PERF_MONITOR="1"
pytest -v tests/performance/
```

### 2. Run Specific Tests
```bash
PERF_MONITOR=1 pytest -v tests/performance/perf_example.py::TestWithPerformanceMonitoring::test_homepage_performance
```

### 3. Disable Performance Monitoring
Default behavior (no metrics collection):
```bash
pytest -v tests/performance/
```

## Understanding the Output

- **Console Output:** Summaries for each measured page/interaction with KPIs.
- **Reports Directory:** `test_artifacts/performance/performance_reports/`
  - JSON reports with full raw metrics (timestamped file names).
  - CSV reports ready for spreadsheets/graphing.

Metrics include:
- `url`, `timestamp`
- `page_load_time`, `dom_content_loaded`, `time_to_first_byte`
- `first_contentful_paint`, `largest_contentful_paint`, `first_input_delay`, `cumulative_layout_shift`
- `js_heap_used_size`, `js_heap_total_size`
- `network_requests`, `total_bytes_transferred`

## Adding New Performance Tests

1. Add a new async test in `tests/performance/`.
2. Import `PerformanceTestAsync` & `measure_after_spa_route_change` from `utils.performance_monitor`.
3. Use `PerformanceTestAsync` for full navigations.
4. Use `measure_after_spa_route_change` after SPA interactions.
5. Define assert budgets for relevant metrics.
