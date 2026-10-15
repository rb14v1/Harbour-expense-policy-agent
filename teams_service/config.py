"""
Teams Service Configuration

Loads Teams SDK and Django API configuration from environment variables.
"""
import os
from typing import Optional


class Config:
    """Configuration for Teams SDK and Django communication."""

    # Teams / Azure Entra ID
    TEAMS_APP_ID: str = os.getenv("CLIENT_ID", "")
    TEAMS_APP_PASSWORD: str = os.getenv("CLIENT_SECRET", "")
    TEAMS_TENANT_ID: str = os.getenv("TENANT_ID", "")

    # Teams Service
    TEAMS_SERVICE_HOST: str = os.getenv("TEAMS_SERVICE_HOST", "0.0.0.0")
    TEAMS_SERVICE_PORT: int = int(os.getenv("TEAMS_SERVICE_PORT", "8001"))

    # Django Backend
    DJANGO_API_URL: str = os.getenv("DJANGO_API_URL", "http://localhost:8000/api/v1")
    DJANGO_PUBLIC_API_URL: str = os.getenv(
        "DJANGO_PUBLIC_API_URL", "http://localhost:8000/api/v1"
    )
    DJANGO_FINANCE_API_URL: str = os.getenv(
        "DJANGO_FINANCE_API_URL", "http://localhost:8000/finance/api"
    )

    # User Manual
    PUBLIC_FRONTEND_URL: str = os.getenv(
        "PUBLIC_FRONTEND_URL", "http://localhost:5173"
    )

    # Feature Flags
    SKIP_TEAMS_AUTH: bool = os.getenv("SKIP_TEAMS_AUTH", "False").lower() == "true"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"

    def __init__(self):
        """Validate required configuration."""
        if not self.TEAMS_APP_ID:
            raise ValueError("CLIENT_ID environment variable not set")
        if not self.TEAMS_APP_PASSWORD:
            raise ValueError("CLIENT_SECRET environment variable not set")
        if not self.TEAMS_TENANT_ID:
            raise ValueError("TENANT_ID environment variable not set")

    def get_teams_options(self) -> dict:
        """Get Teams SDK App options."""
        return {
            "client_id": self.TEAMS_APP_ID,
            "client_secret": self.TEAMS_APP_PASSWORD,
            "tenant_id": self.TEAMS_TENANT_ID,
        }

    @staticmethod
    def log_config_summary():
        """Log configuration summary (without exposing secrets)."""
        print("="*60)
        print("Teams Service Configuration")
        print("="*60)
        print(f"  Teams Service: {Config.TEAMS_SERVICE_HOST}:{Config.TEAMS_SERVICE_PORT}")
        print(f"  Django API: {Config.DJANGO_API_URL}")
        print(f"  Teams App ID: {Config.TEAMS_APP_ID[:8]}...")
        print(f"  Teams Tenant ID: {Config.TEAMS_TENANT_ID[:8]}...")
        print(f"  Auth Enabled: {not Config.SKIP_TEAMS_AUTH}")
        print(f"  Debug Mode: {Config.DEBUG}")
        print("="*60)
        print()


# Create global config instance
try:
    config = Config()
except ValueError as e:
    print(f"❌ Configuration Error: {e}")
    print("   Ensure .env file has: CLIENT_ID, CLIENT_SECRET, TENANT_ID")
    raise
