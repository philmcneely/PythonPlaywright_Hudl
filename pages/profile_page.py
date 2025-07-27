"""
===============================================================================
ProfilePage Object
===============================================================================

This module defines the ProfilePage class, which provides locators and helper
methods for interacting with and verifying elements on the Hudl user profile page
using Playwright.

Features:
    ✓ Locators for profile form fields, buttons, and user information elements.
    ✓ Methods to update user profile information and preferences.
    ✓ Usage of @property for clean locator access.
    ✓ Async methods for Playwright compatibility.
    ✓ Helper methods for form interactions and data retrieval.

Usage Example:
    from pages.profile_page import ProfilePage

    @pytest.mark.asyncio
    async def test_update_profile_info(page):
        profile_page = ProfilePage(page)
        
        # Update user information
        await profile_page.update_first_name("John")
        await profile_page.update_last_name("Doe")
        await profile_page.save_changes()
        
        # Verify changes were saved
        assert await profile_page.get_first_name_value() == "John"
        assert await profile_page.get_last_name_value() == "Doe"

Conventions:
    - All locators are defined as @property methods for clarity and reusability.
    - All Playwright actions and queries are implemented as async methods.
    - Form field interactions include clear() before fill() for reliability.
    - Focuses on user profile management and account preferences.

Author: PMAC
Date: [2025-07-27]
===============================================================================
"""

class ProfilePage:
    def __init__(self, page):
        self.page = page

    # =====================================
    # Page Header
    # =====================================
    @property
    def personal_info_heading(self):
        """Locator for the 'Personal Info' heading."""
        return self.page.get_by_role("heading", name="Personal Info")

    @property
    def privacy_policy_link(self):
        """Locator for the Privacy Policy link."""
        return self.page.get_by_role("link", name="Privacy Policy")

    # =====================================
    # Profile Avatar Section
    # =====================================
    @property
    def profile_initials(self):
        """Locator for the profile initials in the avatar."""
        return self.page.locator("h5.uni-avatar__initials.uni-avatar__initials--user")

    @property
    def edit_profile_picture_button(self):
        """Locator for the 'Edit Profile Picture' button."""
        return self.page.locator("#editProfileImage")

    # =====================================
    # Personal Information Form Fields
    # =====================================
    @property
    def first_name_input(self):
        """Locator for the first name input field."""
        return self.page.locator("#first_name")

    @property
    def last_name_input(self):
        """Locator for the last name input field."""
        return self.page.locator("#last_name")

    @property
    def email_input(self):
        """Locator for the email input field."""
        return self.page.locator("#email")

    @property
    def cell_phone_input(self):
        """Locator for the cell phone input field."""
        return self.page.locator("#cell")

    @property
    def cell_carrier_select(self):
        """Locator for the cell carrier dropdown."""
        return self.page.locator("#carrier")

    # =====================================
    # Account Preferences
    # =====================================
    @property
    def language_select(self):
        """Locator for the language dropdown."""
        return self.page.locator("#language")

    @property
    def timezone_select(self):
        """Locator for the timezone dropdown."""
        return self.page.locator("#timeZoneId")

    # =====================================
    # Password Section
    # =====================================
    @property
    def reset_password_heading(self):
        """Locator for the 'Reset Password' heading."""
        return self.page.get_by_role("heading", name="Reset Password")

    @property
    def reset_password_button(self):
        """Locator for the 'Reset Password' button."""
        return self.page.locator("#resetPassword")

    # =====================================
    # Form Actions
    # =====================================
    @property
    def cancel_button(self):
        """Locator for the 'Cancel' button."""
        return self.page.get_by_role("link", name="Cancel")

    @property
    def save_changes_button(self):
        """Locator for the 'Save Changes' button."""
        return self.page.locator("#save_basic")

    # =====================================
    # Toast Messages
    # =====================================
    @property
    def error_toast(self):
        """Locator for the error toast message."""
        return self.page.locator("#ErrorToast")

    @property
    def success_toast(self):
        """Locator for the success toast message."""
        return self.page.locator("#SuccessToast")

    # =====================================
    # Helper Methods
    # =====================================
    async def get_first_name_value(self):
        """Get the current value of the first name field."""
        return await self.first_name_input.input_value()

    async def get_last_name_value(self):
        """Get the current value of the last name field."""
        return await self.last_name_input.input_value()

    async def get_email_value(self):
        """Get the current value of the email field."""
        return await self.email_input.input_value()

    async def get_profile_initials_text(self):
        """Get the text content of the profile initials."""
        return await self.profile_initials.text_content()

    async def update_first_name(self, first_name: str):
        """Update the first name field."""
        await self.first_name_input.clear()
        await self.first_name_input.fill(first_name)

    async def update_last_name(self, last_name: str):
        """Update the last name field."""
        await self.last_name_input.clear()
        await self.last_name_input.fill(last_name)

    async def update_email(self, email: str):
        """Update the email field."""
        await self.email_input.clear()
        await self.email_input.fill(email)

    async def save_changes(self):
        """Click the Save Changes button."""
        await self.save_changes_button.click()

    async def reset_password(self):
        """Click the Reset Password button."""
        await self.reset_password_button.click()