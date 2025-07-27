
"""
===============================================================================
TermsPage Object
===============================================================================

This module defines the TermsPage class, which provides locators and helper
methods for interacting with and verifying elements on the Hudl Site Terms page
using Playwright.

Features:
    ✓ Locators for site terms page headings and content elements.
    ✓ Methods to verify page content and navigation.
    ✓ Usage of @property for clean locator access.
    ✓ Async methods for Playwright compatibility.
    ✓ Handles new tab/window navigation from login page links.

Usage Example:
    from pages.terms_page import TermsPage

    @pytest.mark.asyncio
    async def test_terms_page_loads(page):
        login_page = LoginPage(page)
        await login_page.load_login_direct()
        
        # Click terms link (opens in new tab)
        async with page.context.expect_page() as new_page_info:
            await login_page.terms_link.click()
        new_page = await new_page_info.value
        
        # Verify terms page content
        terms_page = TermsPage(new_page)
        await terms_page.site_terms_heading.wait_for(state="visible")
        assert await terms_page.site_terms_heading.is_visible()

Conventions:
    - All locators are defined as @property methods for clarity and reusability.
    - All Playwright actions and queries are implemented as async methods.
    - Page is designed to handle new tab/window contexts from external navigation.
    - Focuses on content verification and accessibility-based locators.

Author: PMAC
Date: [2025-07-26]
===============================================================================
"""
class TermsPage:
    def __init__(self, page):
        self.page = page

    @property
    def site_terms_heading(self):
        """Locator for the 'Hudl Site Terms' heading."""
        return self.page.get_by_role("heading", name="Hudl Site Terms")
    