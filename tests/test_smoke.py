"""Smoke test to verify framework running after Chromium broke"""
import pytest

@pytest.mark.only
@pytest.mark.asyncio
async def test_hudl_homepage(page):
    await page.goto("https://www.hudl.com/")
    assert "Hudl" in await page.title()