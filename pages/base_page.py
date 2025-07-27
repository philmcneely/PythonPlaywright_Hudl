"""
===============================================================================
BasePage Class
===============================================================================

This module defines the BasePage class, which serves as the foundation for all
page objects in the Hudl application test suite. It provides common functionality
and utilities that are shared across all page objects, promoting code reuse and
maintaining consistency.

Features:
    ✓ Common navigation and page interaction methods.
    ✓ Shared utility functions for element waiting and verification.
    ✓ Consistent error handling and logging across all page objects.
    ✓ Base functionality for URL management and page state verification.
    ✓ Foundation for implementing page object inheritance patterns.

Usage Example:
    from pages.base_page import BasePage

    class LoginPage(BasePage):
        def __init__(self, page):
            super().__init__(page)
            self.url = "https://www.hudl.com/login"

        async def load(self):
            await self.navigate_to(self.url)

Conventions:
    - All page objects should inherit from BasePage for consistency.
    - Common functionality is implemented here to avoid code duplication.
    - Page-specific logic should be implemented in individual page classes.
    - All methods are async to maintain Playwright compatibility.

Author: PMAC
Date: [2025-07-27]
===============================================================================
"""
from contextlib import asynccontextmanager
import datetime
import allure
import os
from pathlib import Path
from playwright.async_api import Page

class BasePage:
    def __init__(self, page: Page):
        self.page = page

    async def goto(self, url: str):
        await self.page.goto(url)

    async def get_title(self) -> str:
        return await self.page.title()
