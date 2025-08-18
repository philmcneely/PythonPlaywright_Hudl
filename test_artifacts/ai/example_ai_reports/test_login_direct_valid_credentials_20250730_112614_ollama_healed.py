```python
@pytest.mark.login
@pytest.mark.asyncio
async def test_login_direct_valid_credentials(app):
    # ... (rest of the test code)
    await app.login_page.enter_passwordx(PERSONAS['user']['password']) 
    # ... (rest of the test code)
```