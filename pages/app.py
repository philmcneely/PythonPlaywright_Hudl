"""
===============================================================================
App Class
===============================================================================

This module defines the App class, which serves as a central aggregator for all
page objects in the Hudl application test suite. It provides a single entry point
for accessing all page objects, eliminating the need to pass multiple page fixtures
to test functions.

Features:
    ✓ Centralized access to all page objects through a single class.
    ✓ Eliminates the need for multiple page fixtures in test functions.
    ✓ Clean and organized approach to managing page objects.
    ✓ Easy to extend with new page objects as the test suite grows.
    ✓ Maintains separation of concerns while providing convenience.

Usage Example:
    from pages.app import App

    @pytest.mark.asyncio
    async def test_login_flow(app):
        await app.login_page.load_login_direct()
        await app.login_page.enter_email("user@example.com")
        await app.login_page.click_continue()
        
        # Access dashboard page through same app instance
        initials, name, email = await app.dashboard_page.get_user_profile_info()
        assert name == "Expected Name"

Conventions:
    - All page objects are instantiated in __init__ for immediate availability.
    - Page objects are stored as instance attributes for easy access.
    - No async operations are performed in __init__ to avoid fixture issues.
    - New page objects should be added as attributes following the same pattern.

Author: PMAC
Date: [2025-07-27]
===============================================================================
"""
from pages.login_page import LoginPage
from pages.dashboard_page import DashboardPage
from pages.profile_page import ProfilePage
from pages.privacy_page import PrivacyPolicyPage
from pages.terms_page import TermsPage

class App:
    def __init__(self, page):
        self.page = page
        self.login_page = LoginPage(page)
        self.dashboard_page = DashboardPage(page)
        self.profile_page = ProfilePage(page)
        self.privacy_page = PrivacyPolicyPage(page)
        self.terms_page = TermsPage(page)
