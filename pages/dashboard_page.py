"""
===============================================================================
DashboardPage Object
===============================================================================

This module defines the DashboardPage class, which provides locators and helper
methods for interacting with and verifying user profile and menu elements
on the application's dashboard page using Playwright.

Features:
    ✓ Locators for user initials, display name, email, and user menu items.
    ✓ Methods to retrieve user information and interact with the user menu.
    ✓ Usage of @property for clean locator access.
    ✓ Async methods for Playwright compatibility.

Usage Example:
    from pages.dashboard_page import DashboardPage

    @pytest.mark.asyncio
    async def test_dashboard_user_info(page):
        dashboard_page = DashboardPage(page)
        await dashboard_page.click_user_avatar()
        initials = await dashboard_page.get_user_initials_text()
        name = await dashboard_page.get_user_name_text()
        email = await dashboard_page.get_user_email_text()
        assert initials == "PM"
        assert name == "Phil M"
        assert email == "pmcneely@gmail.com"

Conventions:
    - All locators are defined as @property methods for clarity and reusability.
    - All Playwright actions and queries are implemented as async methods.
    - Page object is designed for maintainability and ease of use in tests.

Author: PMAC
Date: [2025-07-27]
===============================================================================
"""
from data.personas import PERSONAS

class DashboardPage:
    def __init__(self, page):
        self.page = page

    # =====================================
    # User Profile Elements
    # =====================================
    @property
    def user_initials(self):
        """Locator for the user initials in the avatar."""
        return self.page.locator("h5.uni-avatar__initials.uni-avatar__initials--user")

    @property
    def user_name(self):
        """Locator for the user display name."""
        return self.page.locator("div.hui-globaluseritem__display-name > span")

    @property
    def user_email(self):
        """Locator for the user email address."""
        return self.page.locator("div.hui-globaluseritem__email")

    @property
    def user_menu(self):
        """Locator for the global user menu container."""
        return self.page.locator("div.hui-globalusermenu")

    @property
    def user_avatar(self):
        """Locator for the user avatar container."""
        return self.page.locator("div.hui-globaluseritem__avatar")

    # =====================================
    # User Menu Items
    # =====================================
    @property
    def your_profile_link(self):
        """Locator for the 'Your Profile' menu item."""
        return self.page.locator('[data-qa-id="webnav-usermenu-yourprofile"]')

    @property
    def account_settings_link(self):
        """Locator for the 'Account Settings' menu item."""
        return self.page.locator('[data-qa-id="webnav-usermenu-accountsettings"]')

    @property
    def livestream_purchases_link(self):
        """Locator for the 'Livestream Purchases' menu item."""
        return self.page.locator('[data-qa-id="webnav-usermenu-livestreampurchases"]')

    @property
    def tickets_passes_link(self):
        """Locator for the 'Tickets & Passes' menu item."""
        return self.page.locator('[data-qa-id="webnav-usermenu-ticketsandpasses"]')

    @property
    def get_help_link(self):
        """Locator for the 'Get Help' menu item."""
        return self.page.locator('[data-qa-id="webnav-usermenu-help"]')

    @property
    def logout_link(self):
        """Locator for the 'Log Out' menu item."""
        return self.page.get_by_role("link", name="Log Out")
    

    # =====================================
    # Helper Methods
    # =====================================
    async def get_user_initials_text(self):
        """Get the text content of the user initials."""
        return await self.user_initials.text_content()

    async def get_user_name_text(self):
        """Get the text content of the user display name."""
        return await self.user_name.text_content()

    async def get_user_email_text(self):
        """Get the text content of the user email."""
        return await self.user_email.text_content()

    async def click_user_avatar(self):
        """Click on the user avatar to open the user menu."""
        await self.user_avatar.click()

    async def click_logout(self):
        """Perform logout by clicking the logout link."""
        await self.logout_link.click()

    async def get_user_profile_info(self):
        """Return avatar (initials, name, email) as a tuple."""
        #await self.click_user_avatar()
        initials = await self.get_user_initials_text()
        name = await self.get_user_name_text()
        email = await self.get_user_email_text()
        return initials, name, email

    async def verify_user_profile_info(self):
        """Retrieve and validate user profile information"""
        initials, name, email = await self.get_user_profile_info()
        assert initials == f"{PERSONAS['user']['first_name'][0]}{PERSONAS['user']['last_name'][0]}"
        assert name == f"{PERSONAS['user']['first_name']} {PERSONAS['user']['last_name'][0]}"
        assert email == PERSONAS["user"]["email"]