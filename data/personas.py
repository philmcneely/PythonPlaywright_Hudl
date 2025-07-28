"""
===============================================================================
User Personas Configuration
===============================================================================

This module defines user personas with their credentials and profile information
for testing different user roles and scenarios in the Hudl application.
All sensitive data is loaded from environment variables for security.

Features:
    ✓ Multiple user personas with different roles (PM, Admin, Coach).
    ✓ Secure credential management through environment variables.
    ✓ Consistent data structure across all personas.
    ✓ Easy access to user information for test data scenarios.

Usage Example:
    from data.personas import PERSONAS
    
    @pytest.mark.asyncio
    async def test_login_as_pm(app):
        await app.login_page.enter_email(PERSONAS["pm"]["email"])
        await app.login_page.enter_password(PERSONAS["pm"]["password"])
        # Verify user info matches persona data
        assert initials == PERSONAS["pm"]["initials"]

Environment Variables Required:
    - USER_PM_EMAIL, USER_PM_PASSWORD, USER_PM_ROLE, USER_PM_FIRST, USER_PM_LAST, USER_PM_INITIALS
    - USER_ADMIN_EMAIL, USER_ADMIN_PASSWORD, USER_ADMIN_ROLE, USER_ADMIN_FIRST, USER_ADMIN_LAST, USER_ADMIN_INITIALS
    - USER_COACH_EMAIL, USER_COACH_PASSWORD, USER_COACH_ROLE, USER_COACH_FIRST, USER_COACH_LAST, USER_COACH_INITIALS

Conventions:
    - All persona keys use lowercase identifiers for consistency.
    - Each persona contains the same set of attributes for predictable access.
    - Sensitive information is never hardcoded, always loaded from environment.
    - Persona structure supports role-based testing scenarios.

Author: PMAC
Date: [2025-07-27]
===============================================================================
"""

import os

# ------------------------------------------------------------------------------
# User Personas Dictionary
# ------------------------------------------------------------------------------

PERSONAS = {
    "user": {
        "email": os.getenv("USER_PM_EMAIL"),
        "password": os.getenv("USER_PM_PASSWORD"),
        "role": os.getenv("USER_PM_ROLE"),
        "first_name": os.getenv("USER_PM_FIRST"),
        "last_name": os.getenv("USER_PM_LAST"),
        "initials": os.getenv("USER_PM_INITIALS"),
    },
    "admin": {
        "email": os.getenv("USER_ADMIN_EMAIL"),
        "password": os.getenv("USER_ADMIN_PASSWORD"),
        "role": os.getenv("USER_ADMIN_ROLE"),
        "first_name": os.getenv("USER_ADMIN_FIRST"),
        "last_name": os.getenv("USER_ADMIN_LAST"),
        "initials": os.getenv("USER_ADMIN_INITIALS"),
    },
    "coach": {
        "email": os.getenv("USER_COACH_EMAIL"),
        "password": os.getenv("USER_COACH_PASSWORD"),
        "role": os.getenv("USER_COACH_ROLE"),
        "first_name": os.getenv("USER_COACH_FIRST"),
        "last_name": os.getenv("USER_COACH_LAST"),
        "initials": os.getenv("USER_COACH_INITIALS"),
    },
}