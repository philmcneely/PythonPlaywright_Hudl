# """
# Hudl API Login Test
# Tests the login flow using Playwright's APIRequestContext to authenticate via HTTP requests
# and extract session cookies for further API testing.

# This test validates:
# - Login page accessibility
# - Email submission step
# - Password submission step  
# - Successful authentication
# - Session cookie extraction

# Author: Test Automation Team
# Created: 2025-07-27
# """

# import pytest
# import re
# from playwright.async_api import APIRequestContext, Playwright

# # Test credentials
# EMAIL = "pmcneely@gmail.com"
# PASSWORD = "Matrix93!"

# class TestAPILogin:
#     """Test class for API-based login functionality"""

#     @pytest.fixture
#     async def api_context(self, playwright: Playwright) -> APIRequestContext:
#         """
#         Create an API request context for HTTP-based testing
        
#         Returns:
#             APIRequestContext: Configured request context with base URL and headers
#         """
#         request_context = await playwright.request.new_context(
#             base_url="https://identity.hudl.com",
#             extra_http_headers={
#                 "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
#                 "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
#             }
#         )
#         yield request_context
#         await request_context.dispose()

#     @pytest.mark.asyncio
#     async def test_api_login_flow(self, api_context: APIRequestContext):
#         """
#         Test the complete API login flow and extract session cookies
        
#         This test performs the Auth0 Universal Login flow:
#         1. GET login page to extract state parameter
#         2. POST email to /u/login/identifier
#         3. POST password to /u/login/password
#         4. Follow redirects to complete authentication
#         5. Extract and validate session cookies
#         """
        
#         # Step 1: Get the login page and extract state parameter
#         print("Step 1: Getting login page...")
#         response = await api_context.get("/login")
#         assert response.ok, f"Failed to get login page: {response.status}"
        
#         html_content = await response.text()
#         print(f"Login page loaded successfully: {response.status}")

#         # Extract state value from hidden input field
#         state_match = re.search(r'name="state"\s+value="([^"]+)"', html_content)
#         if not state_match:
#             # Try alternative regex pattern for different quote styles
#             state_match = re.search(r'name=["\']state["\']\s+value=["\']([^"\']+)["\']', html_content)
        
#         assert state_match, "Could not find state value in login page HTML"
#         state = state_match.group(1)
#         print(f"Extracted state parameter: {state[:20]}...")

#         # Step 2: Submit email to identifier endpoint
#         print("Step 2: Submitting email...")
#         email_data = {
#             "state": state,
#             "username": EMAIL,
#             "js-available": "true",
#             "webauthn-available": "true", 
#             "is-brave": "false",
#             "webauthn-platform-available": "true",
#             "action": "default"
#         }

#         email_response = await api_context.post(
#             f"/u/login/identifier?state={state}",
#             form=email_data
#         )
#         print(f"Email submission response: {email_response.status}")
#         assert email_response.ok or email_response.status == 302, f"Email submission failed: {email_response.status}"

#         # Handle potential redirect after email submission
#         if email_response.status == 302:
#             location = email_response.headers.get("location")
#             if location:
#                 email_response = await api_context.get(location)

#         email_html = await email_response.text()

#         # Extract state parameter for password step (may be same or different)
#         state_match2 = re.search(r'name="state"\s+value="([^"]+)"', email_html)
#         if not state_match2:
#             state_match2 = re.search(r'name=["\']state["\']\s+value=["\']([^"\']+)["\']', email_html)
        
#         state2 = state_match2.group(1) if state_match2 else state
#         print(f"State for password step: {state2[:20]}...")

#         # Step 3: Submit password to complete authentication
#         print("Step 3: Submitting password...")
#         password_data = {
#             "state": state2,
#             "username": EMAIL,
#             "password": PASSWORD,
#             "action": "default"
#         }

#         password_response = await api_context.post(
#             f"/u/login/password?state={state2}",
#             form=password_data
#         )
#         print(f"Password submission response: {password_response.status}")

#         # Step 4: Follow redirects to complete authentication flow
#         final_response = password_response
#         redirect_count = 0
#         max_redirects = 5

#         while final_response.status in [302, 301] and redirect_count < max_redirects:
#             location = final_response.headers.get("location")
#             if not location:
#                 break
            
#             print(f"Following redirect {redirect_count + 1}: {location}")
#             final_response = await api_context.get(location)
#             redirect_count += 1

#         print(f"Final response status: {final_response.status}")
#         assert final_response.ok, f"Final response failed: {final_response.status}"

#         # Step 5: Extract and validate session cookies
#         print("\n=== EXTRACTING SESSION COOKIES ===")
#         storage_state = await api_context.storage_state()
#         cookies = storage_state.get("cookies", [])
        
#         # Validate that we have cookies (indicates successful authentication)
#         assert len(cookies) > 0, "No cookies found - login may have failed"
        
#         # Print all cookies for debugging/verification
#         for cookie in cookies:
#             print(f"{cookie['name']} = {cookie['value'][:50]}...")
#             print(f"  Domain: {cookie['domain']}")
#             print(f"  Path: {cookie['path']}")
#             print(f"  Secure: {cookie.get('secure', False)}")
#             print(f"  HttpOnly: {cookie.get('httpOnly', False)}")
#             print("---")

#         # Step 6: Validate successful login by checking response content
#         final_html = await final_response.text()
#         success_indicators = ["dashboard", "welcome", "profile", "logout", "hudl"]
#         error_indicators = ["error", "invalid", "failed", "incorrect"]
        
#         # Check for success indicators
#         has_success_indicator = any(keyword in final_html.lower() for keyword in success_indicators)
#         has_error_indicator = any(keyword in final_html.lower() for keyword in error_indicators)
        
#         if has_error_indicator:
#             pytest.fail("Login failed - error indicators found in response")
        
#         # Assert that we have either success indicators or valid cookies
#         assert has_success_indicator or len(cookies) > 0, "Login success could not be verified"
        
#         print("\n✅ API login test completed successfully!")
#         print(f"Total cookies extracted: {len(cookies)}")

#     @pytest.mark.asyncio
#     async def test_login_page_accessibility(self, api_context: APIRequestContext):
#         """
#         Test that the login page is accessible and returns expected content
#         """
#         response = await api_context.get("/login")
        
#         # Verify response is successful
#         assert response.ok, f"Login page not accessible: {response.status}"
        
#         # Verify content type is HTML
#         content_type = response.headers.get("content-type", "")
#         assert "text/html" in content_type, f"Expected HTML content, got: {content_type}"
        
#         # Verify page contains expected elements
#         html_content = await response.text()
#         assert "state" in html_content, "Login page missing state parameter"
#         assert "login" in html_content.lower(), "Login page missing login elements"
        
#         print("✅ Login page accessibility test passed")

#     @pytest.mark.asyncio
#     async def test_invalid_credentials(self, api_context: APIRequestContext):
#         """
#         Test login with invalid credentials to ensure proper error handling
#         """
#         # Get login page and extract state
#         response = await api_context.get("/login")
#         html_content = await response.text()
        
#         state_match = re.search(r'name="state"\s+value="([^"]+)"', html_content)
#         assert state_match, "Could not find state value"
#         state = state_match.group(1)

#         # Submit invalid email
#         email_data = {
#             "state": state,
#             "username": "invalid@example.com",
#             "js-available": "true",
#             "webauthn-available": "true",
#             "is-brave": "false", 
#             "webauthn-platform-available": "true",
#             "action": "default"
#         }

#         email_response = await api_context.post(
#             f"/u/login/identifier?state={state}",
#             form=email_data
#         )
        
#         # Should either get error response or continue to password step
#         assert email_response.status in [200, 302, 400, 401], f"Unexpected status: {email_response.status}"
        
#         print("✅ Invalid credentials test completed")

# # """
# # ===============================================================================
# # API Login Tests for Hudl Authentication Flow
# # ===============================================================================

# # This module contains API tests that verify the Hudl application's login flow
# # using direct HTTP requests instead of browser automation. Tests the Auth0
# # authentication endpoints used by the Hudl login system.

# # Features:
# #     ✓ Tests Auth0 authorization flow initiation
# #     ✓ Tests email/identifier submission
# #     ✓ Tests password authentication
# #     ✓ Validates session cookies and tokens
# #     ✓ Verifies successful authentication response

# # Usage Example:
# #     pytest tests/test_api_login.py

# # Author: PMAC
# # Date: [2025-07-27]
# # ===============================================================================
# # """

# # import pytest
# # import requests
# # import urllib.parse
# # from data.personas import PERSONAS
# # import re
# # import json

# # class TestAPILogin:
    
# #     def setup_method(self):
# #         """Setup for each test method - initialize session and headers."""
# #         self.session = requests.Session()
# #         self.base_headers = {
# #             'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
# #             'accept-language': 'en-US,en;q=0.9',
# #             'sec-ch-ua': '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
# #             'sec-ch-ua-mobile': '?0',
# #             'sec-ch-ua-platform': '"macOS"',
# #             'sec-fetch-dest': 'document',
# #             'sec-fetch-mode': 'navigate',
# #             'sec-fetch-site': 'cross-site',
# #             'sec-fetch-user': '?1',
# #             'upgrade-insecure-requests': '1',
# #             'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36'
# #         }
# #         self.session.headers.update(self.base_headers)

# #     def test_api_login_flow_complete(self):
# #         """
# #         Test the complete API login flow for Hudl authentication.
        
# #         Flow:
# #         1. Initiate Auth0 authorization request
# #         2. Submit email/identifier
# #         3. Submit password
# #         4. Verify successful authentication
# #         """
        
# #         # Step 1: Initiate Auth0 authorization flow
# #         auth_url = "https://identity.hudl.com/authorize"
# #         auth_params = {
# #             'state': 'eyJSZWRpcmVjdFVybCI6Ii9ob21lIiwiU2FsdCI6LTE5NjMwODEwMjEsIlJlcXVlc3RJZCI6ImRmNGU3YjE0MDY2MzAyZjBlNjVlNjE1MzlkNjRhMWZlIn0%3D',
# #             'client_id': 'n13RfkHzKozaNxWC5dZQobeWGf4WjSn5',
# #             'response_type': 'id_token',
# #             'redirect_uri': 'https://www.hudl.com/app/users/oidc/callback',
# #             'scope': 'openid profile email',
# #             'nonce': 'R0S1I6w7IYWc2c%2FIf6A07eHAtflz8%2F7oLMpA2dGhxHc%3D',
# #             'response_mode': 'form_post',
# #             'screen_hint': ''
# #         }
        
# #         # Make the authorization request
# #         auth_response = self.session.get(auth_url, params=auth_params)
# #         assert auth_response.status_code == 200, f"Authorization request failed: {auth_response.status_code}"
        
# #         # Extract the state parameter from the response for the next step
# #         state_match = re.search(r'state=([^&"]+)', auth_response.text)
# #         assert state_match, "Could not extract state parameter from authorization response"
# #         state = urllib.parse.unquote(state_match.group(1))
        
# #         # Step 2: Submit email identifier
# #         identifier_url = f"https://identity.hudl.com/u/login/identifier?state={state}"
        
# #         # Get the login form to extract CSRF token and other required fields
# #         identifier_response = self.session.get(identifier_url)
# #         assert identifier_response.status_code == 200, f"Identifier page request failed: {identifier_response.status_code}"
        
# #         # Extract CSRF token from the form
# #         csrf_match = re.search(r'name="_csrf" value="([^"]+)"', identifier_response.text)
# #         assert csrf_match, "Could not extract CSRF token from identifier form"
# #         csrf_token = csrf_match.group(1)
        
# #         # Submit email
# #         email_data = {
# #             'state': state,
# #             'username': PERSONAS["pm"]["email"],
# #             'js-available': 'true',
# #             'webauthn-available': 'true',
# #             'is-brave': 'false',
# #             'webauthn-platform-available': 'true',
# #             'action': 'default',
# #             '_csrf': csrf_token
# #         }
        
# #         email_response = self.session.post(identifier_url, data=email_data)
# #         assert email_response.status_code in [200, 302], f"Email submission failed: {email_response.status_code}"
        
# #         # Step 3: Submit password
# #         # Extract password form URL and required fields
# #         if email_response.status_code == 302:
# #             password_url = email_response.headers.get('Location')
# #         else:
# #             # Parse the response to find the password form action URL
# #             action_match = re.search(r'action="([^"]+)"', email_response.text)
# #             assert action_match, "Could not find password form action URL"
# #             password_url = action_match.group(1)
# #             if not password_url.startswith('http'):
# #                 password_url = f"https://identity.hudl.com{password_url}"
        
# #         # Get the password form
# #         password_form_response = self.session.get(password_url)
# #         assert password_form_response.status_code == 200, f"Password form request failed: {password_form_response.status_code}"
        
# #         # Extract new CSRF token from password form
# #         csrf_match = re.search(r'name="_csrf" value="([^"]+)"', password_form_response.text)
# #         assert csrf_match, "Could not extract CSRF token from password form"
# #         csrf_token = csrf_match.group(1)
        
# #         # Submit password
# #         password_data = {
# #             'state': state,
# #             'username': PERSONAS["pm"]["email"],
# #             'password': PERSONAS["pm"]["password"],
# #             'action': 'default',
# #             '_csrf': csrf_token
# #         }
        
# #         password_response = self.session.post(password_url, data=password_data)
        
# #         # Step 4: Verify successful authentication
# #         # Successful login should redirect or return success indicators
# #         assert password_response.status_code in [200, 302], f"Password submission failed: {password_response.status_code}"
        
# #         # Check for success indicators
# #         if password_response.status_code == 302:
# #             # Successful login typically redirects
# #             redirect_url = password_response.headers.get('Location', '')
# #             assert 'hudl.com' in redirect_url or 'callback' in redirect_url, f"Unexpected redirect URL: {redirect_url}"
# #         else:
# #             # Check response content for success indicators
# #             response_text = password_response.text.lower()
# #             # Should not contain error messages
# #             assert 'wrong email or password' not in response_text, "Login failed - wrong credentials"
# #             assert 'error' not in response_text or 'dashboard' in response_text, "Login may have failed"
        
# #         # Verify session cookies are set
# #         cookies = self.session.cookies
# #         assert len(cookies) > 0, "No session cookies were set after login"
        
# #         print(f"✓ API Login successful for {PERSONAS['pm']['email']}")
# #         print(f"✓ Session cookies: {[cookie.name for cookie in cookies]}")

# #     def test_api_login_invalid_credentials(self):
# #         """
# #         Test API login with invalid credentials to verify error handling.
# #         """
# #         # This test would follow the same flow but use invalid credentials
# #         # and verify that appropriate error responses are returned
        
# #         # Step 1: Get to password form (same as above, abbreviated)
# #         auth_url = "https://identity.hudl.com/authorize"
# #         auth_params = {
# #             'client_id': 'n13RfkHzKozaNxWC5dZQobeWGf4WjSn5',
# #             'response_type': 'id_token',
# #             'redirect_uri': 'https://www.hudl.com/app/users/oidc/callback',
# #             'scope': 'openid profile email'
# #         }
        
# #         auth_response = self.session.get(auth_url, params=auth_params)
# #         assert auth_response.status_code == 200
        
# #         # For brevity, assuming we can get to the password submission step
# #         # In a real test, you'd follow the full flow from the previous test
        
# #         # Submit invalid credentials
# #         password_data = {
# #             'username': 'invalid@email.com',
# #             'password': 'wrongpassword',
# #             'action': 'default'
# #         }
        
# #         # Note: You'd need the actual password URL and CSRF token from the flow
# #         # This is a simplified example showing the concept
        
# #         print("✓ Invalid credentials test structure created")

# #     def test_api_login_missing_parameters(self):
# #         """
# #         Test API login with missing required parameters.
# #         """
# #         # Test submitting login form without required fields
# #         identifier_url = "https://identity.hudl.com/u/login/identifier"
        
# #         # Submit without username
# #         incomplete_data = {
# #             'action': 'default'
# #         }
        
# #         response = self.session.post(identifier_url, data=incomplete_data)
        
# #         # Should return error or validation message
# #         assert response.status_code in [400, 422, 200], f"Unexpected status code: {response.status_code}"
        
# #         if response.status_code == 200:
# #             # Check for validation error in response
# #             assert 'required' in response.text.lower() or 'invalid' in response.text.lower()
        
# #         print("✓ Missing parameters validation test completed")

# #     def teardown_method(self):
# #         """Cleanup after each test method."""
# #         if hasattr(self, 'session'):
# #             self.session.close()

# import requests
# import re

# EMAIL = "pmcneely@gmail.com"
# PASSWORD = "Matrix93!"

# session = requests.Session()
# headers = {
#     "User-Agent": "Mozilla/5.0",
#     "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
# }

# # 1. GET the login page to extract the state value
# r1 = session.get("https://identity.hudl.com/login", headers=headers)
# assert r1.status_code == 200

# # Extract the state value from the hidden input
# state_match = re.search(r'name="state" value="([^"]+)"', r1.text)
# assert state_match, "Could not find state value"
# state = state_match.group(1)

# # 2. POST the email to /u/login/identifier
# data_email = {
#     "state": state,
#     "username": EMAIL,
#     "js-available": "true",
#     "webauthn-available": "true",
#     "is-brave": "false",
#     "webauthn-platform-available": "true",
#     "action": "default",
# }
# r2 = session.post(
#     "https://identity.hudl.com/u/login/identifier?state=" + state,
#     headers=headers,
#     data=data_email,
#     allow_redirects=True,
# )
# assert r2.status_code == 200

# # 3. Extract the new state value for the password step (may be the same)
# state_match2 = re.search(r'name="state" value="([^"]+)"', r2.text)
# assert state_match2, "Could not find state value for password step"
# state2 = state_match2.group(1)

# # 4. POST the password to /u/login/password
# data_pw = {
#     "state": state2,
#     "username": EMAIL,
#     "password": PASSWORD,
#     "action": "default",
# }
# r3 = session.post(
#     "https://identity.hudl.com/u/login/password?state=" + state2,
#     headers=headers,
#     data=data_pw,
#     allow_redirects=True,
# )
# print("Password POST status:", r3.status_code)
# print("Redirect location:", r3.headers.get("Location"))
# print("Cookies:", session.cookies.get_dict())
# print("Body:", r3.text[:500])

# # 5. Check for successful login (look for a redirect or dashboard keyword)
# if "dashboard" in r3.text or "Hudl" in r3.text:
#     print("Login may have succeeded!")
# else:
#     print("Login likely failed or needs more steps.")