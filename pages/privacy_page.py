"""
===============================================================================
PrivacyPolicyPage Object
===============================================================================

This module defines the PrivacyPolicyPage class, which provides locators and helper
methods for interacting with and verifying elements on the Hudl Privacy Policy page
using Playwright.

Features:
    ✓ Locators for privacy policy page headings and content elements.
    ✓ Methods to verify page content and navigation.
    ✓ Usage of @property for clean locator access.
    ✓ Async methods for Playwright compatibility.
    ✓ Handles new tab/window navigation from login page links.

Usage Example:
    from pages.privacy_policy_page import PrivacyPolicyPage

    @pytest.mark.asyncio
    async def test_privacy_policy_page_loads(page):
        login_page = LoginPage(page)
        await login_page.load_login_direct()
        
        # Click privacy policy link (opens in new tab)
        async with page.context.expect_page() as new_page_info:
            await login_page.privacy_policy_link.click()
        new_page = await new_page_info.value
        
        # Verify privacy policy page content
        privacy_page = PrivacyPolicyPage(new_page)
        await privacy_page.privacy_policy_heading.wait_for(state="visible")
        assert await privacy_page.privacy_policy_heading.is_visible()

Conventions:
    - All locators are defined as @property methods for clarity and reusability.
    - All Playwright actions and queries are implemented as async methods.
    - Page is designed to handle new tab/window contexts from external navigation.
    - Focuses on content verification and accessibility-based locators.

Author: PMAC
Date: [2025-07-26]
===============================================================================
"""

class PrivacyPolicyPage:
    def __init__(self, page):
        self.page = page

    @property
    def privacy_policy_heading(self):
        """Locator for the 'Hudl Privacy Policy' heading."""
        return self.page.get_by_role("heading", name="Hudl Privacy Policy")