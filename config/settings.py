"""
Configuration settings for the test framework.
Loads environment variables and provides default values.
"""
import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings:
    """Application settings loaded from environment variables."""
    
    # Base Configuration
    BASE_URL: str = os.getenv("BASE_URL", "https://www.hudl.com/")
    TEST_EMAIL: str = os.getenv("TEST_EMAIL", "")
    TEST_PASSWORD: str = os.getenv("TEST_PASSWORD", "")
    
    # Browser Configuration
    BROWSER: str = os.getenv("BROWSER", "chromium")
    HEADLESS: bool = os.getenv("HEADLESS", "false").lower() == "true"
    SLOW_MO: int = int(os.getenv("SLOW_MO", "100"))
    TIMEOUT: int = int(os.getenv("TIMEOUT", "30000"))
    
    # Test Configuration
    RETRY_COUNT: int = int(os.getenv("RETRY_COUNT", "3"))
    RETRY_DELAY: int = int(os.getenv("RETRY_DELAY", "1000"))
    SCREENSHOT_ON_FAILURE: bool = os.getenv("SCREENSHOT_ON_FAILURE", "true").lower() == "true"
    VIDEO_ON_FAILURE: bool = os.getenv("VIDEO_ON_FAILURE", "true").lower() == "true"
    
    # Allure Configuration
    ALLURE_RESULTS_DIR: str = os.getenv("ALLURE_RESULTS_DIR", "allure-results")
    
    @classmethod
    def validate_required_settings(cls) -> None:
        """Validate that required settings are present."""
        required_settings = ["TEST_EMAIL", "TEST_PASSWORD"]
        missing_settings = []
        
        for setting in required_settings:
            if not getattr(cls, setting):
                missing_settings.append(setting)
        
        if missing_settings:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_settings)}")
    
    @classmethod
    def get_browser_options(cls) -> dict:
        """Get browser launch options."""
        return {
            "headless": cls.HEADLESS,
            "slow_mo": cls.SLOW_MO,
            "args": [
                "--disable-blink-features=AutomationControlled",
                "--disable-extensions",
                "--no-sandbox",
                "--disable-dev-shm-usage"
            ]
        }

# Create a global settings instance
settings = Settings()
