# tests/test_smoke.py
import pytest

@pytest.mark.only
@pytest.mark.asyncio
async def test_hudl_homepage(page):
    await page.goto("https://www.hudl.com/")
    assert "Hudl" in await page.title()