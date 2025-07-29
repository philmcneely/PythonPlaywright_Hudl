"""
===============================================================================
LoginPage Object
===============================================================================

This module defines the LoginPage class, which provides locators and helper
methods for interacting with and verifying login error messages and icons
on the application's login page using Playwright.

Features:
    ✓ Locators for error message containers and error icons (including those
      rendered as real DOM elements and those shown via CSS pseudo-elements).
    ✓ Methods to retrieve error message text and check for the presence of
      error icons.
    ✓ Usage of @property for clean locator access.
    ✓ Async methods for Playwright compatibility.

Usage Example:
    from pages.login_page import LoginPage

    @pytest.mark.asyncio
    async def test_password_error_icon_appears(page):
        login_page = LoginPage(page)
        await login_page.load_login_direct()
        await login_page.enter_email("test@example.com")
        await login_page.click_continue()
        await login_page.enter_password("wrongpassword")
        await login_page.click_continue()

        # Wait for error icon to appear
        assert await login_page.wait_for_password_error_icon()

        # Verify error icon is visible
        assert await login_page.is_password_error_icon_visible()

        # Verify error message text
        error_text = await login_page.get_password_error_text()
        assert "Incorrect username or password." in error_text

Conventions:
    - All locators are defined as @property methods for clarity and reusability.
    - All Playwright actions and queries are implemented as async methods.
    - Error icons rendered via CSS pseudo-elements are verified by checking
      the parent element's class and visibility, since pseudo-elements are
      not directly accessible via Playwright.

Author: PMAC
Date: [2025-07-26]
===============================================================================
"""
from .base_page import BasePage

class LoginPage(BasePage):

    def __init__(self, page: BasePage):
        self.page = page

    async def load(self, url: str):
        await self.page.goto(url)

    # =====================================
    # Navigation to Login
    # =====================================
    async def load_home(self):
        await self.page.goto("https://www.hudl.com/")

    async def load_login_direct_with_params(self):
        await self.page.goto("https://www.hudl.com/login?utm_content=hudl_primary&utm_source=www.hudl.com&utm_medium=login_dropdown&utm_campaign=platform_logins")

    async def load_login_direct(self):
        await self.page.goto("https://www.hudl.com/login")

    async def click_login_link(self):
        await self.page.get_by_role("link", name="Log in").click()

    async def click_second_hudl_link(self):
        await self.page.get_by_role("link", name="Hudl", exact=True).nth(1).click()

    # =====================================
    # Email Field
    # =====================================
    @property 
    def email_textbox(self):
        return self.page.get_by_role("textbox", name="Email")

    async def enter_email(self, email: str):
        await self.email_textbox.fill(email)

    async def get_email_text(self):
        """Get the current text value from the email input field."""
        return await self.email_textbox.input_value()
    
    # =====================================
    # Password Field
    # =====================================
    @property
    def password_textbox(self):
        """Locator for the password input textbox."""
        return self.page.get_by_role("textbox", name="Passwordx")

    async def enter_password(self, password: str):
        """
        Enter password into the password textbox.

        Args:
            password (str): The password to enter.
        """
        await self.password_textbox.fill(password)

    async def get_password_text(self):
        """Get the current text value from the password input field."""
        return await self.password_textbox.input_value()
    
    # =====================================
    # Convenience Methods
    # =====================================
    async def fill_email_and_password_without_submit(self, email: str, password: str):
        """Fill both the email and password fields in one step but do not submit."""
        await self.enter_email(email)
        await self.click_continue()  # Navigate to password field
        await self.enter_password(password)

    async def fill_email_and_password_submit(self, email: str, password: str):
        """Fill both the email and password fields in one step and submit."""
        await self.enter_email(email)
        await self.click_continue()  # Navigate to password field
        await self.enter_password(password)
        await self.click_continue() 

    # =====================================
    # Page Navigation
    # =====================================
    async def click_continue(self):
        await self.page.get_by_role("button", name="Continue", exact=True).click()

    # =====================================
    # Forgot Password
    # =====================================
    @property
    def reset_password_link(self):
        return self.page.get_by_role("link", name="Forgot Password")
    
    @property
    def go_back_reset_link(self):
        return self.page.get_by_role("button", name="Go Back")
    
    @property
    def reset_password_heading(self):
        return self.page.get_by_role("heading", name="Reset Password")
    
    @property
    def reset_password_heading(self):
        return self.page.get_by_text("We'll send you a link to reset your password.")

    # =====================================
    # Email or password incorrect
    # =====================================
    #This is reused for tests that check invalid email as well
    @property
    def error_message_email_or_password_incorrect(self):
        return self.page.locator("#error-element-password")
    
    @property
    def error_message_password_incorrect_text(self):
        return "Your email or password is incorrect. Try again."
    
    @property
    def error_message_email_incorrect_text(self):
        return "Incorrect username or password."
    
    async def get_error_message_email_incorrect_text(self):
        if await self.error_message_email_or_password_incorrect.is_visible():
            text = await self.error_message_email_or_password_incorrect.text_content()
            return text.strip() if text else ""
        return ""
    
    async def get_error_message_password_incorrect_text(self):
        if await self.error_message_email_or_password_incorrect.is_visible():
            text = await self.error_message_email_or_password_incorrect.text_content()
            return text.strip() if text else ""
        return ""
    
    async def has_email_or_password_incorrect_error_icon(self, timeout: int = 10000) -> bool:
        if await self.error_message_email_or_password_incorrect.is_visible():
            error_icon = self.error_message_email_or_password_incorrect.locator('.ulp-input-error-icon')
            await error_icon.wait_for(state="visible", timeout=timeout)
            return True
        else:
            return False
    
    # =====================================
    # Password missing
    # =====================================
    @property
    def error_message_password_required(self):
        return self.page.locator("#error-cs-password-required")
    
    @property
    def error_message_password_required_text(self):
        return "Enter your password."
    
    async def get_error_message_password_required_text(self):
        if await self.error_message_password_required.is_visible():
            text = await self.error_message_password_required.text_content()
            return text.strip() if text else ""
        return ""
    
    async def has_password_required_error_icon(self):
        """
        Locator for the password error icon within the password error message container.

        Returns:
            Locator: Playwright locator for the error icon element.
        """
        # Check if the class is present (which triggers the icon via CSS)
        classes = await self.error_message_password_required.get_attribute("class")
        return "ulp-error-info" in classes

    # =====================================
    # Email missing
    # =====================================
    @property
    def error_message_email_required(self):
        return self.page.locator("#error-cs-email-required")
    
    @property
    def error_message_email_required_text(self):
        return "Enter an email address" # Interesting no period here like all others?
    
    async def get_error_message_email_required_text(self):
        if await self.error_message_email_required.is_visible():
            text = await self.error_message_email_required.text_content()
            return text.strip() if text else ""
        return ""
    
    async def has_email_required_error_icon(self):
        # Check if the class is present (which triggers the icon via CSS)
        classes = await self.error_message_email_required.get_attribute("class")
        return "ulp-error-info" in classes
    
    # =====================================
    # Edit email
    # =====================================
    @property
    def edit_email_link(self):
        """Locator for the 'Edit' email address link."""
        return self.page.locator('a[data-link-name="edit-username"]')
    
    # =====================================
    # Email invalid
    # =====================================
    @property
    def error_message_email_invalid(self):
        return self.page.locator("#error-cs-email-invalid")
    
    @property
    def error_message_email_invalid_text(self):
        return "Enter a valid email."
    
    async def get_error_message_email_invalid_text(self):
        if await self.error_message_email_invalid.is_visible():
            text = await self.error_message_email_invalid.text_content()
            return text.strip() if text else ""
        return ""
    
    async def has_email_invalid_error_icon(self):
        # Check if the class is present (which triggers the icon via CSS)
        classes = await self.error_message_email_required.get_attribute("class")
        return "ulp-error-info" in classes
    
    # =====================================
    # Blocked Account related
    # =====================================
    @property
    def blocked_account_alert(self):
        return self.page.locator('#prompt-alert[data-error-code="user-blocked"]')
    
    @property
    def blocked_account_alert_text(self):
        return "You’ve tried to log in too many times, so we’ve temporarily blocked your account. To get help, contact support"

    @property
    def blocked_account_message(self):
        return self.blocked_account_alert.locator('p')  #in case I want to use it for something

    async def get_blocked_account_text(self):
        if await self.blocked_account_alert.is_visible():
            text = await self.blocked_account_message.text_content()
            return text.strip() if text else ""
        return ""

    async def is_account_blocked(self):
        return await self.blocked_account_alert.is_visible()
    
    # =====================================
    # Mask/Unmask Password
    # =====================================
    @property
    def show_password_button(self):
        return self.page.get_by_role("switch", name="Show password")
    
    # =====================================
    # Create Account
    # =====================================

    async def click_create_account(self):
        await self.page.get_by_role("link", name="Create Account").click()
        
    @property
    def first_name_textbox(self):
        """Locator for the first name input textbox."""
        return self.page.locator('input#first-name')
    
    async def enter_first_name(self, first_name: str):
        await self.first_name_textbox.fill(first_name)

    async def get_first_name_text(self):
        """Get the current text value from the first_name input field."""
        return await self.first_name_textbox.input_value()

    @property
    def last_name_textbox(self):
        """Locator for the last name input textbox."""
        return self.page.locator('input#last-name')
    
    async def enter_last_name(self, last_name: str):
        await self.last_name_textbox.fill(last_name)

    async def get_last_name_text(self):
        """Get the current text value from the last_name input field."""
        return await self.last_name_textbox.input_value()
    
    #email box is same

    @property
    def login_link(self):
        """Locator for the 'Log In' link."""
        return self.page.get_by_role("link", name="Log In")
    
    # add error conditions as well.  Probably should make a new page for create account if want to improve

    # =====================================
    # Privacy Policy
    # =====================================
    @property
    def privacy_policy_link(self):
        """Locator for the 'Privacy Policy' link."""
        return self.page.get_by_role("link", name="Privacy Policy")
    
    async def click_privacy_policy_link(self):
        await self.privacy_policy_link.click()

    # =====================================
    # Terms of Service
    # =====================================
    @property
    def terms_link(self):
        """Locator for the 'Terms of Service' link."""
        return self.page.get_by_role("link", name="Terms of Service")
    
    async def click_terms_link(self):
        await self.terms_link.click()
