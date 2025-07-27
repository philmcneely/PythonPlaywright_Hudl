"""
===============================================================================
Login Flow and Navigation Tests
===============================================================================

This module contains tests that verify the Hudl application's login flows,
navigation paths, and related functionality such as password reset and
external link navigation.

Features:
    ✓ Tests for multiple login entry points (homepage, direct navigation).
    ✓ Verifies successful login with valid credentials and user profile data.
    ✓ Tests password reset workflow and navigation.
    ✓ Validates external link navigation (Privacy Policy, Terms of Service).
    ✓ Tests account creation flow (commented out to avoid test data pollution).

Usage Example:
    pytest tests/test_login_flows.py

Conventions:
    - Each test is marked as async and uses Playwright's async API.
    - Test data uses PERSONAS for valid credentials.
    - Comments explain the purpose and steps of each test.
    - External link tests handle new tab/window contexts properly.

Author: PMAC
Date: [2025-07-27]
===============================================================================
"""

import pytest
from pages.login_page import LoginPage
from config.settings import settings
from pages.privacy_page import PrivacyPolicyPage
from pages.terms_page import TermsPage
from data.personas import PERSONAS
from pages.dashboard_page import DashboardPage
from utils.screenshot_decorator import screenshot_on_failure

# ------------------------------------------------------------------------------
# Test: Loads page and fails to generate screenshot
# ------------------------------------------------------------------------------

@screenshot_on_failure
@pytest.mark.smoke
@pytest.mark.login
@pytest.mark.asyncio
async def test_login_direct_fail(app):
    """
    Test direct login navigation and fails
    """
    await app.login_page.load_login_direct()
    assert False, "This will trigger a screenshot"

# ------------------------------------------------------------------------------
# Test: Login from Homepage Navigation
# ------------------------------------------------------------------------------

@screenshot_on_failure
@pytest.mark.login
@pytest.mark.asyncio
async def test_login_from_home_valid_credentials(app):
    """
    Test the complete login flow starting from the homepage.
    Navigates through homepage -> login link -> second Hudl link -> login process.
    """
    await app.login_page.load_home()
    await app.login_page.click_login_link()
    await app.login_page.click_second_hudl_link()
    await app.login_page.enter_email(PERSONAS["pm"]["email"])
    await app.login_page.click_continue()
    await app.login_page.enter_password(PERSONAS["pm"]["password"])
    await app.login_page.click_continue()
    # Retrieve and validate user profile information
    initials, name, email = await app.dashboard_page.get_user_profile_info()
    assert initials == f"{PERSONAS['pm']['first_name'][0]}{PERSONAS['pm']['last_name'][0]}"
    assert name == f"{PERSONAS['pm']['first_name']} {PERSONAS['pm']['last_name'][0]}"
    assert email == PERSONAS["pm"]["email"]

# ------------------------------------------------------------------------------
# Test: Direct Login with Valid Credentials
# ------------------------------------------------------------------------------

@screenshot_on_failure
@pytest.mark.smoke
@pytest.mark.login
@pytest.mark.asyncio
async def test_login_direct_valid_credentials(app):
    """
    Test direct login navigation with valid credentials.
    Verifies successful login and validates user profile information on dashboard.
    """
    await app.login_page.load_login_direct()
    await app.login_page.enter_email(PERSONAS["pm"]["email"])
    await app.login_page.click_continue()
    await app.login_page.enter_password(PERSONAS["pm"]["password"])
    await app.login_page.click_continue()
    
    # Retrieve and validate user profile information
    initials, name, email = await app.dashboard_page.get_user_profile_info()
    assert initials == f"{PERSONAS['pm']['first_name'][0]}{PERSONAS['pm']['last_name'][0]}"
    assert name == f"{PERSONAS['pm']['first_name']} {PERSONAS['pm']['last_name'][0]}"
    assert email == PERSONAS["pm"]["email"]

# ------------------------------------------------------------------------------
# Test: Direct Login with Valid Credentials then Logout (could be combined with above)
# ------------------------------------------------------------------------------

@screenshot_on_failure
@pytest.mark.smoke
@pytest.mark.login
@pytest.mark.asyncio
async def test_login_direct_valid_credentials_then_logut(app):
    """
    Test direct login navigation with valid credentials.
    Verifies successful login and validates user profile information on dashboard.
    Logs out
    Verifies cannot see dashboard any longer
    """
    await app.login_page.load_login_direct()
    await app.login_page.enter_email(PERSONAS["pm"]["email"])
    await app.login_page.click_continue()
    await app.login_page.enter_password(PERSONAS["pm"]["password"])
    await app.login_page.click_continue()
    
    # Retrieve and validate user profile information
    initials, name, email = await app.dashboard_page.get_user_profile_info()
    assert initials == f"{PERSONAS['pm']['first_name'][0]}{PERSONAS['pm']['last_name'][0]}"
    assert name == f"{PERSONAS['pm']['first_name']} {PERSONAS['pm']['last_name'][0]}"
    assert email == PERSONAS["pm"]["email"]

    await app.dashboard_page.click_logout()
    await app.login_page.load_home()
    await app.login_page.email_textbox.is_visible()


# ------------------------------------------------------------------------------
# Test: Forgot Password Flow - Email Verification
# ------------------------------------------------------------------------------

@screenshot_on_failure
@pytest.mark.login
@pytest.mark.asyncio
async def test_forgot_password_email_verification(app):
    """
    Test the forgot password flow to verify email is pre-populated correctly.
    Stops before actually sending the reset email to avoid system pollution.
    """
    await app.login_page.load_login_direct()
    await app.login_page.enter_email(PERSONAS["pm"]["email"])
    await app.login_page.click_continue()
    # Verify password field is visible before proceeding to reset
    assert await app.login_page.password_textbox.is_visible()
    await app.login_page.reset_password_link.click()
    # Verify email is pre-populated in the reset form
    await app.login_page.get_email_text() == PERSONAS["pm"]["email"]
    # Note: Actual email sending is not tested to avoid system pollution

    #click link to continue
    #verify message for email sent
    #ideally here we'd then actually check the email or perhaps look in db for audit log?

# ------------------------------------------------------------------------------
# Test: Forgot Password Flow - Go Back Navigation
# ------------------------------------------------------------------------------

@screenshot_on_failure
@pytest.mark.login
@pytest.mark.asyncio
async def test_forgot_password_go_back(app):
    """
    Test the forgot password flow with go back navigation.
    Verifies that users can navigate back from the reset password screen.
    """
    await app.login_page.load_login_direct()
    await app.login_page.enter_email(PERSONAS["pm"]["email"])
    await app.login_page.click_continue()
    # Verify password field is visible
    assert await app.login_page.password_textbox.is_visible()
    
    # Navigate to reset password screen
    await app.login_page.reset_password_link.click()
    await app.login_page.get_email_text() == PERSONAS["pm"]["email"]
    assert await app.login_page.reset_password_heading.is_visible()
    
    # Navigate back to login screen
    await app.login_page.go_back_reset_link.click()
    await app.login_page.get_email_text() == PERSONAS["pm"]["email"]

# ------------------------------------------------------------------------------
# Test: Privacy Policy Link Navigation
# ------------------------------------------------------------------------------

@screenshot_on_failure
@pytest.mark.login
@pytest.mark.asyncio
async def test_privacy_link(page):
    """
    Test navigation to Privacy Policy page from login screen.
    Handles new tab/window context and verifies page loads correctly.
    """
    login_page = LoginPage(page)
    await login_page.load_login_direct()
    context = page.context
    
    # Handle new tab/window opening
    async with context.expect_page() as new_page_info:
        await login_page.privacy_policy_link.click()
    new_page = await new_page_info.value
    
    # Verify Privacy Policy page loads correctly
    privacy_policy_page = PrivacyPolicyPage(new_page)
    await privacy_policy_page.privacy_policy_heading.wait_for(state="visible")
    assert await privacy_policy_page.privacy_policy_heading.is_visible()

# ------------------------------------------------------------------------------
# Test: Terms of Service Link Navigation
# ------------------------------------------------------------------------------

@screenshot_on_failure
@pytest.mark.login
@pytest.mark.asyncio
async def test_terms_link(page):
    """
    Test navigation to Terms of Service page from login screen.
    Handles new tab/window context and verifies page loads correctly.
    """
    login_page = LoginPage(page)
    await login_page.load_login_direct()
    context = page.context
    
    # Handle new tab/window opening
    async with context.expect_page() as new_page_info:
        await login_page.terms_link.click()
    new_page = await new_page_info.value
    
    # Verify Terms of Service page loads correctly
    terms_page = TermsPage(new_page)
    await terms_page.site_terms_heading.wait_for(state="visible")
    assert await terms_page.site_terms_heading.is_visible()

# ------------------------------------------------------------------------------
# (Commented Out) Test: Account Creation Flow
# ------------------------------------------------------------------------------

# The following test is commented out to avoid creating test accounts in the system.
# It demonstrates how to test the account creation workflow.

# @screenshot_on_failure
# @pytest.mark.login
# @pytest.mark.asyncio
# async def test_create_account_flow(app):
#     """
#     Test the account creation flow without actually creating an account.
#     Demonstrates the workflow but navigates back to avoid system pollution.
#     """
#     await app.login_page.load_login_direct()
#     await app.login_page.click_create_account()
#     await app.login_page.enter_first_name("Phil")
#     await app.login_page.enter_last_name("McNeely")
#     await app.login_page.enter_email(PERSONAS["pm"]["email"])
#     # Navigate back to login instead of creating account
#     await app.login_page.click_login_link()

# ------------------------------------------------------------------------------
# (Commented Out) additional test ideas
# ------------------------------------------------------------------------------
# Invalid account forget password - itll try to send either way it seems, so not a valid case from my limited knowledge
# not valid? buttons clickable even when fields empty
# Create account but with validation on each field errors - not impl
# login - homepage - login remains logged in
# logout is logged out?