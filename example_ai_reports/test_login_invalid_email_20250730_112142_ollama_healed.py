```python
async def test_login_invalid_email(app):
    await app.login_page.load_login_direct()
    await app.login_page.enter_email('dadfdf@gmail.com')
    await app.login_page.click_continue()
    # Assert error message for incorrect email is visible
    assert await app.login_page.error_message_email_incorrect.is_visible()
    # ... rest of the test code 
```