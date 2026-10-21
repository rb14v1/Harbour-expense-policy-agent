"""
Tests for Teams Service Configuration

Tests configuration loading and validation.
"""
import os
import pytest
from teams_service.config import Config


def test_config_requires_client_id(monkeypatch):
    """Test that CLIENT_ID is required."""
    monkeypatch.delenv("CLIENT_ID", raising=False)
    monkeypatch.setenv("CLIENT_SECRET", "test-secret")
    monkeypatch.setenv("TENANT_ID", "test-tenant")

    with pytest.raises(ValueError, match="CLIENT_ID"):
        Config()


def test_config_requires_client_secret(monkeypatch):
    """Test that CLIENT_SECRET is required."""
    monkeypatch.setenv("CLIENT_ID", "test-id")
    monkeypatch.delenv("CLIENT_SECRET", raising=False)
    monkeypatch.setenv("TENANT_ID", "test-tenant")

    with pytest.raises(ValueError, match="CLIENT_SECRET"):
        Config()


def test_config_requires_tenant_id(monkeypatch):
    """Test that TENANT_ID is required."""
    monkeypatch.setenv("CLIENT_ID", "test-id")
    monkeypatch.setenv("CLIENT_SECRET", "test-secret")
    monkeypatch.delenv("TENANT_ID", raising=False)

    with pytest.raises(ValueError, match="TENANT_ID"):
        Config()


def test_config_loads_from_env(monkeypatch):
    """Test configuration loads from environment variables."""
    monkeypatch.setenv("CLIENT_ID", "test-client-id")
    monkeypatch.setenv("CLIENT_SECRET", "test-client-secret")
    monkeypatch.setenv("TENANT_ID", "test-tenant-id")

    config = Config()

    assert config.TEAMS_APP_ID == "test-client-id"
    assert config.TEAMS_APP_PASSWORD == "test-client-secret"
    assert config.TEAMS_TENANT_ID == "test-tenant-id"


def test_config_defaults(monkeypatch):
    """Test configuration defaults."""
    monkeypatch.setenv("CLIENT_ID", "test-id")
    monkeypatch.setenv("CLIENT_SECRET", "test-secret")
    monkeypatch.setenv("TENANT_ID", "test-tenant")

    config = Config()

    assert config.TEAMS_SERVICE_HOST == "0.0.0.0"
    assert config.TEAMS_SERVICE_PORT == 8001
    assert config.DJANGO_API_URL == "http://localhost:8000/api/v1"
    assert config.DJANGO_FINANCE_API_URL == "http://localhost:8000/finance/api"


def test_config_custom_service_port(monkeypatch):
    """Test custom Teams service port."""
    monkeypatch.setenv("CLIENT_ID", "test-id")
    monkeypatch.setenv("CLIENT_SECRET", "test-secret")
    monkeypatch.setenv("TENANT_ID", "test-tenant")
    monkeypatch.setenv("TEAMS_SERVICE_PORT", "9001")

    config = Config()

    assert config.TEAMS_SERVICE_PORT == 9001


def test_config_get_teams_options(monkeypatch):
    """Test Teams options dictionary."""
    monkeypatch.setenv("CLIENT_ID", "test-id")
    monkeypatch.setenv("CLIENT_SECRET", "test-secret")
    monkeypatch.setenv("TENANT_ID", "test-tenant")

    config = Config()
    options = config.get_teams_options()

    assert options["client_id"] == "test-id"
    assert options["client_secret"] == "test-secret"
    assert options["tenant_id"] == "test-tenant"
