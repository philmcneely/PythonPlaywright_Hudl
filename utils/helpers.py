# """
# Utility helper functions for the test framework.
# """
# import asyncio
# import logging
# import os
# from datetime import datetime
# from pathlib import Path
# from typing import Optional
# from playwright.async_api import Page, Browser

# logger = logging.getLogger(__name__)

# class TestHelpers:
#     """Collection of helper methods for testing."""
    
#     @staticmethod
#     async def take_screenshot(page: Page, name: str, path: str = "screenshots") -> str:
#         """
#         Take a screenshot and save it with timestamp.
        
#         Args:
#             page: Playwright page object
#             name: Base name for the screenshot
#             path: Directory to save screenshots
            
#         Returns:
#             Path to the saved screenshot
#         """
#         timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#         filename = f"{name}_{timestamp}.png"
        
#         # Create screenshots directory if it doesn't exist
#         Path(path).mkdir(parents=True, exist_ok=True)
        
#         screenshot_path = os.path.join(path, filename)
#         await page.screenshot(path=screenshot_path, full_page=True)
        
#         logger.info(f"Screenshot saved: {screenshot_path}")
#         return screenshot_path
    
#     @staticmethod
#     async def wait_for_page_load(page: Page, timeout: int = 30000) -> None:
#         """
#         Wait for page to be fully loaded.
        
#         Args:
#             page: Playwright page object
#             timeout: Timeout in milliseconds
#         """
#         try:
#             await page.wait_for_load_state("networkidle", timeout=timeout)
#             await page.wait_for_load_state("domcontentloaded", timeout=timeout)
#         except Exception as e:
#             logger.warning(f"Page load wait timeout: {e}")
    
#     @staticmethod
#     async def scroll_to_element(page: Page, selector: str) -> None:
#         """
#         Scroll to an element on the page.
        
#         Args:
#             page: Playwright page object
#             selector: CSS selector of the element
#         """
#         try:
#             await page.locator(selector).scroll_into_view_if_needed()
#         except Exception as e:
#             logger.warning(f"Could not scroll to element {selector}: {e}")
    
#     @staticmethod
#     async def wait_and_click(page: Page, selector: str, timeout: int = 10000) -> None:
#         """
#         Wait for element to be visible and clickable, then click it.
        
#         Args:
#             page: Playwright page object
#             selector: CSS selector of the element
#             timeout: Timeout in milliseconds
#         """
#         element = page.locator(selector)
#         await element.wait_for(state="visible", timeout=timeout)
#         await element.wait_for(state="attached", timeout=timeout)
#         await element.click()
    
#     @staticmethod
#     async def wait_and_fill(page: Page, selector: str, text: str, timeout: int = 10000) -> None:
#         """
#         Wait for input element and fill it with text.
        
#         Args:
#             page: Playwright page object
#             selector: CSS selector of the input element
#             text: Text to fill
#             timeout: Timeout in milliseconds
#         """
#         element = page.locator(selector)
#         await element.wait_for(state="visible", timeout=timeout)
#         await element.clear()
#         await element.fill(text)
    
#     @staticmethod
#     async def get_element_text(page: Page, selector: str, timeout: int = 10000) -> str:
#         """
#         Get text content of an element.
        
#         Args:
#             page: Playwright page object
#             selector: CSS selector of the element
#             timeout: Timeout in milliseconds
            
#         Returns:
#             Text content of the element
#         """
#         element = page.locator(selector)
#         await element.wait_for(state="visible", timeout=timeout)
#         return await element.text_content() or ""
    
#     @staticmethod
#     async def is_element_visible(page: Page, selector: str, timeout: int = 5000) -> bool:
#         """
#         Check if an element is visible on the page.
        
#         Args:
#             page: Playwright page object
#             selector: CSS selector of the element
#             timeout: Timeout in milliseconds
            
#         Returns:
#             True if element is visible, False otherwise
#         """
#         try:
#             await page.locator(selector).wait_for(state="visible", timeout=timeout)
#             return True
#         except Exception:
#             return False
    
#     @staticmethod
#     def generate_test_data(base_email: str) -> dict:
#         """
#         Generate test data with timestamp.
        
#         Args:
#             base_email: Base email address
            
#         Returns:
#             Dictionary with test data
#         """
#         timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#         return {
#             "email": f"test_{timestamp}_{base_email}",
#             "timestamp": timestamp
#         }
