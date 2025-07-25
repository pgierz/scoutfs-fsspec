import os
from unittest.mock import MagicMock, patch

import pytest

# Set up test environment before importing the module
os.environ["SCOUTFS_USERNAME"] = "testuser"
os.environ["SCOUTFS_PASSWORD"] = "testpass"
os.environ["SCOUTFS_API_HOST"] = "test.host"
os.environ["SCOUTFS_API_PORT"] = "8080"
os.environ["SCOUTFS_API_VERSION"] = "1"

# Now import the module with the environment variables set
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
        monkeypatch.setenv("SCOUTFS_API_HOST", "test.host")
        monkeypatch.setenv("SCOUTFS_API_PORT", "8080")
        monkeypatch.setenv("SCOUTFS_API_VERSION", "1")

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
        "invalid_url", ["ftp://test.host", "test.host", ""]
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

        # Need to reload the module to pick up the new environment variables
        with patch.dict(
            "os.environ",
            {
                "SCOUTFS_API_HOST": "custom.host",
                "SCOUTFS_API_PORT": "9000",
                "SCOUTFS_API_VERSION": "2",
                "SCOUTFS_SSL_VERIFY": "true",
            },
        ):
            from importlib import reload

            from scoutfs import config

            reload(config)
            from scoutfs.config import ScoutFSConfig

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
        # First set up the defaults
        with patch.dict(
            "os.environ",
            {
                "SCOUTFS_USERNAME": "testuser",
                "SCOUTFS_PASSWORD": "testpass",
                "SCOUTFS_API_HOST": "test.host",
                "SCOUTFS_API_PORT": "8080",
                "SCOUTFS_API_VERSION": "1",
            },
        ):
            from importlib import reload

            from scoutfs import config

            reload(config)
            from scoutfs.config import ScoutFSConfig

            overrides = {
                "username": None,  # Should be ignored
                "password": "newpass",
                "new_key": None,  # Should vanish
            }
            config = ScoutFSConfig.load(overrides)

            # Username should keep its default value, not be set to None
            assert config["username"] == "testuser"
            assert config["password"] == "newpass"
            assert (
                "new_key" not in config
            )  # This has nothing to do with ScoutFSConfig, so it should vanish
