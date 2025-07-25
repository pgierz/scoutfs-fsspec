import os
from typing import Dict, Any, Optional, Union


class ScoutFSConfig:
    """Configuration helper for ScoutFS connections.

    This class handles loading and managing configuration for ScoutFS connections,
    with support for environment variables and programmatic overrides.

    Attributes
    ----------
    DEFAULT_CONFIG : dict
        Dictionary containing default configuration values loaded from environment variables.
        Includes API settings, authentication, SSL/TLS, timeouts, and retry logic.
    """

    # Default configuration values
    DEFAULT_CONFIG = {
        # Base URL for the ScoutFS API
        "api_url": os.environ.get(
            "SCOUTFS_API_URL",
            f"https://{os.environ.get('SCOUTFS_API_HOST', 'hsm.dmawi.de')}:"
            f"{os.environ.get('SCOUTFS_API_PORT', '8080')}/"
            f"v{os.environ.get('SCOUTFS_API_VERSION', '1')}",
        ),
        # Authentication
        "username": os.environ.get("SCOUTFS_USERNAME"),
        "password": os.environ.get("SCOUTFS_PASSWORD"),
        # SSL/TLS settings
        "ssl_verify": os.environ.get("SCOUTFS_SSL_VERIFY", "False").lower() == "true",
        "ssl_cert": os.environ.get("SCOUTFS_SSL_CERT"),
        # Timeout settings (in seconds)
        "connect_timeout": float(os.environ.get("SCOUTFS_CONNECT_TIMEOUT", "30.0")),
        "request_timeout": float(os.environ.get("SCOUTFS_REQUEST_TIMEOUT", "300.0")),
        # Retry settings
        "max_retries": int(os.environ.get("SCOUTFS_MAX_RETRIES", "3")),
        "retry_delay": float(os.environ.get("SCOUTFS_RETRY_DELAY", "1.0")),
        # Caching
        "token_cache_ttl": int(
            os.environ.get("SCOUTFS_TOKEN_CACHE_TTL", "300")
        ),  # 5 minutes
    }

    @classmethod
    def load(
        cls, config: Optional[Union[Dict[str, Any], str]] = None
    ) -> Dict[str, Any]:
        """Load ScoutFS configuration with optional overrides.

        Parameters
        ----------
        config : dict or str or None, optional
            Configuration overrides. Can be:
            - A dictionary of configuration values
            - A path to a configuration file (not yet implemented)
            - None to use environment variables and defaults

        Returns
        -------
        dict
            Dictionary containing the merged configuration

        Examples
        --------
        >>> # Basic usage with environment variables
        >>> config = ScoutFSConfig.load()
        >>>
        >>> # With programmatic overrides
        >>> config = ScoutFSConfig.load({"username": "user", "password": "pass"})
        """
        result = cls.DEFAULT_CONFIG.copy()

        if config is None:
            return result

        if isinstance(config, str):
            # TODO: Implement loading from config file
            # For now, we'll just return the defaults
            return result

        if isinstance(config, dict):
            # Update with provided config, filtering out None values
            result.update({k: v for k, v in config.items() if v is not None})

        return result

    @classmethod
    def validate(cls, config: Dict[str, Any]) -> None:
        """Validate the configuration.

        Parameters
        ----------
        config : dict
            The configuration dictionary to validate

        Raises
        ------
        ValueError
            If the configuration is missing required fields or is invalid
        """
        if not config.get("username") or not config.get("password"):
            raise ValueError(
                "Both username and password must be provided for authentication"
            )

        if not config["api_url"].startswith(("http://", "https://")):
            raise ValueError("API URL must start with http:// or https://")


def get_scoutfs_config(**overrides) -> Dict[str, Any]:
    """Get ScoutFS configuration with optional overrides.

    This is a convenience function that wraps ScoutFSConfig.load() and validate().

    Parameters
    ----------
    **overrides : dict, optional
        Configuration overrides as keyword arguments

    Returns
    -------
    dict
        Dictionary containing the merged and validated configuration

    Examples
    --------
    >>> # Basic usage with environment variables
    >>> config = get_scoutfs_config()
    >>>
    >>> # With overrides
    >>> config = get_scoutfs_config(username="user", password="pass")
    """
    config = ScoutFSConfig.load(overrides)
    ScoutFSConfig.validate(config)
    return config
