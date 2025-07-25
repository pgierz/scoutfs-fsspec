import os
from unittest.mock import patch, MagicMock

import pytest

from scoutfs.config import ScoutFSConfig, get_scoutfs_config


class TestScoutFSConfig:
    """Test suite for ScoutFSConfig class."""

    @pytest.fixture(autouse=True)
    def setup_env(self, monkeypatch):
        """Set up test environment with default values."""
        # Clear any existing environment variables that might affect tests
        for key in os.environ:
            if key.startswith("SCOUTFS_"):
                monkeypatch.delenv(key, raising=False)

        # Set default test values
        monkeypatch.setenv("SCOUTFS_USERNAME", "testuser")
        monkeypatch.setenv("SCOUTFS_PASSWORD", "testpass")
        monkeypatch.setenv("SCOUTFS_API_URL", "https://test.host:8080/v1")

    def test_load_defaults(self):
        """Test loading configuration with default values."""
        config = ScoutFSConfig.load()

        assert config["username"] == "testuser"
        assert config["password"] == "testpass"
        assert config["api_url"] == "https://test.host:8080/v1"
        assert config["ssl_verify"] is False
        assert config["connect_timeout"] == 30.0
        assert config["request_timeout"] == 300.0
        assert config["max_retries"] == 3
        assert config["retry_delay"] == 1.0
        assert config["token_cache_ttl"] == 300

    def test_load_with_overrides(self):
        """Test loading configuration with overrides."""
        overrides = {
            "username": "override_user",
            "password": "override_pass",
            "max_retries": 5,
            "ssl_verify": True,
        }
        config = ScoutFSConfig.load(overrides)

        assert config["username"] == "override_user"
        assert config["password"] == "override_pass"
        assert config["max_retries"] == 5
        assert config["ssl_verify"] is True
        # Other values should remain as defaults
        assert config["api_url"] == "https://test.host:8080/v1"

    def test_validate_success(self):
        """Test successful validation of configuration."""
        config = {
            "username": "testuser",
            "password": "testpass",
            "api_url": "https://test.host:8080/v1",
        }
        # Should not raise
        ScoutFSConfig.validate(config)

    @pytest.mark.parametrize("missing_field", ["username", "password"])
    def test_validate_missing_required_fields(self, missing_field):
        """Test validation fails when required fields are missing."""
        config = {
            "username": "testuser",
            "password": "testpass",
            "api_url": "https://test.host:8080/v1",
        }
        config.pop(missing_field)

        with pytest.raises(ValueError) as excinfo:
            ScoutFSConfig.validate(config)
        assert "must be provided" in str(excinfo.value)

    @pytest.mark.parametrize(
        "invalid_url", ["ftp://test.host", "test.host", "https://", ""]
    )
    def test_validate_invalid_url(self, invalid_url):
        """Test validation fails with invalid API URL."""
        config = {
            "username": "testuser",
            "password": "testpass",
            "api_url": invalid_url,
        }

        with pytest.raises(ValueError) as excinfo:
            ScoutFSConfig.validate(config)
        assert "must start with http:// or https://" in str(excinfo.value)

    def test_environment_variables(self, monkeypatch):
        """Test loading configuration from environment variables."""
        monkeypatch.setenv("SCOUTFS_API_HOST", "custom.host")
        monkeypatch.setenv("SCOUTFS_API_PORT", "9000")
        monkeypatch.setenv("SCOUTFS_API_VERSION", "2")
        monkeypatch.setenv("SCOUTFS_SSL_VERIFY", "true")

        config = ScoutFSConfig.load()

        assert config["api_url"] == "https://custom.host:9000/v2"
        assert config["ssl_verify"] is True

    def test_get_scoutfs_config_helper(self):
        """Test the get_scoutfs_config helper function."""
        config = get_scoutfs_config(
            username="helper_user", password="helper_pass", ssl_verify=True
        )

        assert config["username"] == "helper_user"
        assert config["password"] == "helper_pass"
        assert config["ssl_verify"] is True

    def test_none_values_in_overrides(self):
        """Test that None values in overrides don't override existing values."""
        overrides = {
            "username": None,  # Should be ignored
            "password": "newpass",
            "new_key": None,  # Should still be set to None
        }
        config = ScoutFSConfig.load(overrides)

        # Username should keep its default value, not be set to None
        assert config["username"] == "testuser"
        assert config["password"] == "newpass"
        assert "new_key" in config
        assert config["new_key"] is None
