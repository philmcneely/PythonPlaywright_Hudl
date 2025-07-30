"""
===============================================================================
AI Healing Service for Playwright Tests Using Ollama Model
===============================================================================

This module provides the OllamaAIHealingService class and related functions
for capturing test failure context, querying the Ollama AI model for healing
analysis, and generating detailed healing reports.

Features:
    - Async context capture including screenshots and DOM snapshot
    - Robust prompt building for AI analysis
    - Querying Ollama with retries and error handling
    - Parsing Ollama JSON responses with multiple fallback strategies
    - Saving detailed markdown reports and healed test code
    - Thread-safe context storage for parallel test runs

Environment Variables:
    OLLAMA_MODEL: Ollama model to use (default: llama3.1:8b)
    AI_HEALING_ENABLED: Enable AI healing (true|false, default: false)
    AI_HEALING_CONFIDENCE: Confidence threshold for healed tests (default: 0.7)
    OLLAMA_HOST: Ollama server URL (default: http://localhost:11434)
    OLLAMA_TEMPERATURE: Temperature setting for Ollama model (default: 0.1)

Author: PMAC
Date: [2025-07-29]
===============================================================================
"""

import functools
import json
import inspect
import os
import requests
from pathlib import Path
from datetime import datetime
import subprocess
import time
import shutil
import asyncio
from config.settings import settings

import ollama

# ------------------------------------------------------------------------------
# Class: OllamaAIHealingService
# ------------------------------------------------------------------------------

class OllamaAIHealingService:
    """
    Service class to manage AI healing using Ollama model.
    Handles context capture, prompt building, querying, response parsing,
    and report generation.
    """

    def __init__(self):
        """
        Initialize the OllamaAIHealingService with environment variables.
        """
        self.model = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
        self.enabled = os.getenv("AI_HEALING_ENABLED", "false").lower() == "true"
        self.confidence_threshold = float(os.getenv("AI_HEALING_CONFIDENCE", "0.7"))
        self.ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        self.temperature = float(os.getenv("OLLAMA_TEMPERATURE", "0.1"))
        self.client = ollama.Client(host=self.ollama_host)

    async def capture_failure_context(self, page, error, test_name, test_function):
        """
        Capture all context needed for AI analysis including URL, title, screenshot, and DOM.

        Args:
            page: Playwright page object
            error: Exception instance from test failure
            test_name: Name of the test function
            test_function: The test function object

        Returns:
            tuple: (context dict, screenshot path or None)
        """
        context = {
            "test_name": test_name,
            "error_message": str(error),
            "error_type": type(error).__name__,
            "test_docstring": test_function.__doc__ or "",
        }

        screenshot_path = None
        try:
            if page:
                context.update({
                    "url": await page.url(),
                    "title": await page.title(),
                })

                # Capture screenshot
                screenshot_dir = Path("screenshots")
                screenshot_dir.mkdir(exist_ok=True)
                screenshot_path = screenshot_dir / f"{test_name}_ai_healing.png"

                await page.screenshot(path=str(screenshot_path))
                context["screenshot_path"] = str(screenshot_path)

                # Capture DOM (truncated for Ollama)
                dom_content = await page.content()
                # Limit DOM size for Ollama context window
                context["dom"] = dom_content[:5000] + "..." if len(dom_content) > 5000 else dom_content

        except Exception as e:
            context["capture_error"] = str(e)

        return context, screenshot_path

    def _build_healing_prompt(self, context, original_test_code):
        """
        Build a comprehensive prompt for Ollama AI model based on test failure context.

        Args:
            context (dict): Captured failure context
            original_test_code (str): Source code of the original test

        Returns:
            str: Formatted prompt string
        """
        prompt = f"""
            You are an expert Quality Assurance Engineer and test automation specialist. 

            A Playwright Python test has failed and needs analysis for potential auto-healing.

            ## Test Information:
            - **Test Name**: {context['test_name']}
            - **Error Type**: {context.get('error_type', 'Unknown')}
            - **URL**: {context.get('url', 'N/A')}
            - **Page Title**: {context.get('title', 'N/A')}

            ## Error Message:
            ```
            {context['error_message']}
            ```

            ## Original Test Code:
            ```python
            {original_test_code}
            ```

            ## Test Documentation:
            {context.get('test_docstring', 'No test docstring provided')}

            ## DOM Context (truncated):
            ```html
            {context.get('dom', 'No DOM captured')}
            ```

            ## Your Task:
            Analyze this test failure and provide:

            1. **Root Cause Analysis**: What exactly caused this test to fail?
            2. **Confidence Score**: Rate your confidence in the analysis (0.0 to 1.0)
            3. **Suggested Fix**: Specific code changes or approach to fix the test
            4. **Updated Test Code**: Always provide a corrected version of the test code that fixes the failure. Return only the updated test function code in Python.
            5. **Recommendations**: Additional suggestions for test stability

            IMPORTANT: Respond ONLY with a valid JSON object, no markdown formatting or extra text.

            {{
                "analysis": "Detailed analysis of what went wrong",
                "root_cause": "Specific root cause identified",
                "confidence": 0.85,
                "suggested_fix": "Specific fix recommendation",
                "updated_test_code": "Complete fixed test code (if confident)",
                "recommendations": "Additional recommendations for improvement"
            }}

            Focus on common Playwright issues like:
            - Element not found/changed selectors
            - Timing issues and race conditions  
            - Network/loading problems
            - State management issues
            - Flaky test patterns
            """
        return prompt

    def _query_ollama(self, prompt, screenshot_path=None):
        """
        Query Ollama with prompt and optional screenshot.

        Args:
            prompt (str): The prompt string to send
            screenshot_path (str): Optional path to screenshot image

        Returns:
            str or None: Ollama response text or None on failure
        """
        try:
            print(f"🧠 Querying Ollama model: {self.model}")

            # Prepare the request
            request_params = {
                'model': self.model,
                'prompt': prompt,
                'stream': False,
                'system': "You are an expert Quality Assurance Engineer and test automation specialist. Respond ONLY with valid JSON, no markdown or extra text.",
                'options': {
                    'temperature': self.temperature,
                    'num_ctx': 8192,  # Larger context window
                }
            }

            # Add screenshot if available
            if screenshot_path and Path(screenshot_path).exists():
                request_params['images'] = [screenshot_path]
                print(f"📸 Including screenshot: {screenshot_path}")

            response = self.client.generate(**request_params)
            return response['response']

        except Exception as e:
            print(f"🤖 Ollama query failed: {e}")
            return None

    def _parse_ollama_response(self, response_text):
        """
        Parse Ollama response and extract JSON with robust error handling.

        Args:
            response_text (str): Raw response text from Ollama

        Returns:
            dict or None: Parsed JSON dict or None if parsing failed
        """
        if not response_text:
            print("🤖 Empty response from Ollama")
            return None

        # Log the raw response for debugging
        print(f"🤖 Raw Ollama response (first 200 chars): {response_text[:200]}...")

        import re

        # Strategy 1: Try to find JSON inside a code block
        json_match = re.search(r'```json\s*({.*?})\s*```', response_text, re.DOTALL)
        if json_match:
            candidate = json_match.group(1)
            print("🤖 Found JSON in code block")
        else:
            # Strategy 2: Try to find any code block
            code_match = re.search(r'```(.*?)```', response_text, re.DOTALL)
            if code_match:
                candidate = code_match.group(1).strip()
                print("🤖 Found content in code block")
            else:
                # Strategy 3: Look for JSON-like structure anywhere in text
                json_pattern = re.search(r'({\s*"[^"]+":.*?})', response_text, re.DOTALL)
                if json_pattern:
                    candidate = json_pattern.group(1)
                    print("🤖 Found JSON-like structure in text")
                else:
                    # Strategy 4: Use the entire response
                    candidate = response_text.strip()
                    print("🤖 Using entire response as candidate")

        # Try to parse the candidate as JSON
        try:
            parsed = json.loads(candidate)
            print("✅ Successfully parsed JSON response")
            return parsed
        except json.JSONDecodeError as e:
            print(f"🤖 JSON parsing failed: {e}")

            # Strategy 5: Try to fix common JSON issues
            try:
                # Remove any leading/trailing non-JSON text
                cleaned = re.sub(r'^[^{]*', '', candidate)
                cleaned = re.sub(r'[^}]*$', '', cleaned)

                if cleaned:
                    parsed = json.loads(cleaned)
                    print("✅ Successfully parsed cleaned JSON")
                    return parsed
            except:
                pass

            # Strategy 6: Try to extract key information manually
            try:
                analysis_match = re.search(r'"analysis"\s*:\s*"([^"]*)"', response_text)
                root_cause_match = re.search(r'"root_cause"\s*:\s*"([^"]*)"', response_text)
                confidence_match = re.search(r'"confidence"\s*:\s*([0-9.]+)', response_text)

                manual_parse = {
                    "analysis": analysis_match.group(1) if analysis_match else response_text[:500],
                    "root_cause": root_cause_match.group(1) if root_cause_match else "Could not extract root cause",
                    "confidence": float(confidence_match.group(1)) if confidence_match else 0.3,
                    "suggested_fix": "Manual review required - JSON parsing failed",
                    "recommendations": "Check Ollama model output format"
                }
                print("🔧 Manually extracted key information")
                return manual_parse
            except:
                pass

            # Final fallback: Return raw response in structured format
            print("⚠️ All parsing strategies failed, returning raw response")
            return {
                "analysis": response_text,
                "root_cause": "Could not parse structured response",
                "confidence": 0.2,
                "suggested_fix": "Manual review required - response parsing failed",
                "recommendations": "Consider using a different Ollama model or adjusting prompt",
                "raw_unparsed_response": response_text
            }

    def call_ollama_healing(self, context, original_test_code, screenshot_path=None):
        """
        Call Ollama for test healing analysis.

        Args:
            context (dict): Captured failure context
            original_test_code (str): Source code of the original test
            screenshot_path (str): Optional path to screenshot image

        Returns:
            dict: Parsed Ollama response or error dict
        """
        try:
            #print("🤖 [DEBUG] Building healing prompt...")
            prompt = self._build_healing_prompt(context, original_test_code)
            #print(f"🤖 [DEBUG] Prompt built:\n{prompt}")

            #print("🤖 [DEBUG] Querying Ollama service...")
            raw_response = self._query_ollama(prompt, screenshot_path)
            #print(f"🤖 [DEBUG] Raw Ollama response:\n{raw_response}")

            if raw_response:
                #print("🤖 [DEBUG] Parsing Ollama response...")
                parsed_response = self._parse_ollama_response(raw_response)

                if parsed_response is None:
                    #print("🤖 [DEBUG] Parsed response is None, returning error dict")
                    return {"error": "Failed to parse Ollama response"}

                # Add raw response for debugging
                parsed_response['raw_ollama_response'] = raw_response

                #print(f"🤖 [DEBUG] Parsed Ollama response:\n{parsed_response}")
                return parsed_response

            #print("🤖 [DEBUG] No response received from Ollama")
            return {"error": "No response from Ollama"}

        except Exception as e:
            print(f"🤖 Ollama healing service error: {e}")
            import traceback
            traceback.print_exc()
            return {"error": str(e)}

    def stop_model(self):
        """
        Stop the Ollama model to free resources.
        """
        try:
            res = self.client.generate(
                model=self.model,
                stream=False,
                keep_alive=0,
            )
            if hasattr(res, 'done_reason') and str(res.done_reason) == "unload":
                print(f"🧠 AI Model Stopped: {self.model}")
        except Exception as e:
            print(f"🤖 Failed to stop model: {e}")

    def extract_test_source(self, test_function):
        """
        Extract the source code of the test function.

        Args:
            test_function (function): The test function object

        Returns:
            str: Source code string or fallback comment
        """
        try:
            return inspect.getsource(test_function)
        except:
            return f"# Could not extract source for {test_function.__name__}"

    async def generate_healing_report(self, test_name, ai_response, context):
        """
        Generate detailed healing report markdown and save healed test code if provided.

        Args:
            test_name (str): Name of the test
            ai_response (dict): Parsed Ollama AI response
            context (dict): Failure context

        Returns:
            None
        """
        healing_dir = Path("ai_healing_reports")
        healing_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = healing_dir / f"{test_name}_{timestamp}_ollama_analysis.md"

        report_content = f"""# 🧠 Ollama AI Healing Report

## Test Information
- **Test Name**: `{test_name}`
- **Timestamp**: `{timestamp}`
- **Model Used**: `{self.model}`
- **URL**: `{context.get('url', 'N/A')}`
- **Error Type**: `{context.get('error_type', 'Unknown')}`

## Error Details
```
{context.get('error_message', 'No error message')}
```

## Ollama Analysis
```
{ai_response.get('analysis', 'No analysis provided')}
```

## Root Cause
```
{ai_response.get('root_cause', 'Not identified')}
```

## Suggested Fix
```
{ai_response.get('suggested_fix', 'No fix suggested')}
```

## Updated Code
```
{ai_response.get('updated_test_code', 'No fix suggested')}
```

## Confidence Level
**{ai_response.get('confidence', 0):.1%}**

## Recommendations
```
{ai_response.get('recommendations', 'None provided')}
```

## Raw Ollama Response
<details>
<summary>Click to expand raw response</summary>

```
{ai_response.get('raw_ollama_response', 'No raw response')}
```
</details>

---
*Generated by Ollama AI Healing System*
"""

        with open(report_file, 'w') as f:
            f.write(report_content)

        # Save healed test if provided
        if 'updated_test_code' in ai_response and ai_response['updated_test_code']:
            healed_test_file = healing_dir / f"{test_name}_{timestamp}_ollama_healed.py"
            with open(healed_test_file, 'w') as f:
                f.write(ai_response['updated_test_code'])

            print(f"Ollama healed test saved: {healed_test_file}")

        # Console output
        print(f"\n{'='*80}")
        print(f"OLLAMA AI HEALING: {test_name}")
        print(f"{'='*80}")
        print(f"🤖 Model: {self.model}")
        print(f"📊 Confidence: {ai_response.get('confidence', 0):.1%}")
        print(f"🔍 Root Cause: {ai_response.get('root_cause', 'Unknown')}")
        print(f"💡 Suggestion: {ai_response.get('suggested_fix', 'None')}")
        print(f"📄 Full Report: {report_file}")

        if ai_response.get('confidence', 0) > self.confidence_threshold:
            print(f"✅ High confidence - Review the healed test")
        else:
            print(f"⚠️  Low confidence - Manual review recommended")

        print(f"{'='*80}\n")

# ------------------------------------------------------------------------------
# Global service instance
# ------------------------------------------------------------------------------

_ollama_service = OllamaAIHealingService()

# ------------------------------------------------------------------------------
# Decorator: ai_healing
# ------------------------------------------------------------------------------

def ai_healing(func):
    """
    Decorator that captures test failure context and saves it for AI healing.
    Works with any test that has 'app', 'login_page', or 'page' fixture.

    By convention, any fixture named 'app' or ending with '_page' is assumed
    to be a page object that has a .page attribute

    Note: This decorator will automatically find page objects from the test's
    fixture arguments, so you don't need to add 'request' to every test.

    Usage:
        @ai_healing
        @pytest.mark.asyncio
        async def test_something(app):  # No need for 'request' parameter
            # ... test code ...
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        if not _ollama_service.enabled:
            return await func(*args, **kwargs)

        # Find page object using the same scalable logic as screenshot decorator
        page = None
        page_source = None

        # Loop through all kwargs to find page objects
        for key, value in kwargs.items():
            try:
                # Check if this is the 'app' fixture with a page attribute
                if key == "app" and hasattr(value, "page"):
                    page = value.page
                    page_source = f"app fixture"
                    break

                # Check if this is a page object fixture (ends with '_page')
                elif key.endswith("_page") and hasattr(value, "page"):
                    page = value.page
                    page_source = f"{key} fixture"
                    break

                # Check if this is the raw Playwright 'page' fixture
                elif key == "page":
                    page = value
                    page_source = f"page fixture"
                    break

            except Exception:
                continue

        try:
            # Run the actual test function
            return await func(*args, **kwargs)
        except Exception as exc:
            print(f"\n🧠 Test failed, capturing context for AI healing: {func.__name__}")

            try:
                # Capture failure context
                context, screenshot_path = await _ollama_service.capture_failure_context(
                    page, exc, func.__name__, func
                )

                # Get original test source
                original_code = _ollama_service.extract_test_source(func)

                # Generate test key that matches pytest's item.nodeid
                # Convert module path from dots to file path
                module_path = func.__module__.replace('.', os.sep) + '.py'
                test_key = f"{module_path}::{func.__name__}"

                # Save context for the pytest hook to use later
                if not hasattr(_ollama_service, '_pending_contexts'):
                    _ollama_service._pending_contexts = {}

                _ollama_service._pending_contexts[test_key] = {
                    "test_name": func.__name__,
                    "error_message": str(exc),
                    "context": context,
                    "original_test_code": original_code,
                    "screenshot_path": str(screenshot_path) if screenshot_path else None,
                }
                print(f"💾 Context saved for AI healing hook (key: {test_key})")

            except Exception as healing_error:
                print(f"🧠 Failed to capture context for AI healing: {healing_error}")

            # Re-raise the original exception (let pytest handle retries)
            raise exc

    return wrapper

# ------------------------------------------------------------------------------
# Function: stop_ollama_model
# ------------------------------------------------------------------------------

def stop_ollama_model():
    """
    Stop the Ollama model to free resources.
    """
    _ollama_service.stop_model()

# ------------------------------------------------------------------------------
# Thread-safe dictionaries and locks
# ------------------------------------------------------------------------------

_ollama_checked = False
_ollama_service = OllamaAIHealingService()

# ------------------------------------------------------------------------------
# Function: ensure_ollama_model_loaded
# ------------------------------------------------------------------------------

def ensure_ollama_model_loaded(model_name=None, host=None, max_wait=180):
    """
    Check if the specified model is available and loaded.
    If not, attempt to pull and warm it up by waiting for a real response.

    Args:
        model_name (str): Model name to check/load
        host (str): Ollama host URL
        max_wait (int): Max wait time in seconds

    Returns:
        bool: True if model is loaded and ready, False otherwise
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

# ------------------------------------------------------------------------------
# Function: ensure_ollama_running
# ------------------------------------------------------------------------------

def ensure_ollama_running():
    """
    Check if Ollama service is running and start it if not.
    Also ensures the specified model is loaded and ready.

    Returns:
        bool: True if service and model are available, False otherwise
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

# ------------------------------------------------------------------------------
# Function: _find_page_object
# ------------------------------------------------------------------------------

def _find_page_object(item):
    """
    Find the Playwright page object from pytest test item fixtures.

    Args:
        item: Pytest test item

    Returns:
        Playwright page object or None
    """
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

# ------------------------------------------------------------------------------
# Async Function: _capture_page_info
# ------------------------------------------------------------------------------

async def _capture_page_info(page, screenshot_path):
    """
    Capture screenshot and page title asynchronously.

    Args:
        page: Playwright page object
        screenshot_path (str): Path to save screenshot

    Returns:
        str: Page title
    """
    await page.screenshot(path=screenshot_path)
    title = await page.title()
    return title

# ------------------------------------------------------------------------------
# Function: _capture_ai_healing_context
# ------------------------------------------------------------------------------

def _capture_ai_healing_context(item, page, error_message):
    """
    Capture test failure context for AI healing and save it in the global service.

    Args:
        item: Pytest test item
        page: Playwright page object
        error_message (str): Error message from test failure

    Returns:
        None
    """
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
