"""
Google Ads MCP Configuration Manager

Centralized configuration management with:
- Environment variable support
- Configuration file loading (YAML/JSON)
- Per-customer configuration profiles
- Feature flags
- Validation
"""

import os
import json
import yaml
import logging
from typing import Optional, Dict, Any, List
from pathlib import Path
from pydantic import BaseModel, Field, field_validator
from enum import Enum

logger = logging.getLogger(__name__)


class CacheBackend(str, Enum):
    """Cache backend options."""
    MEMORY = "memory"
    REDIS = "redis"
    NONE = "none"


class LogLevel(str, Enum):
    """Log level options."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogFormat(str, Enum):
    """Log format options."""
    JSON = "json"
    TEXT = "text"


class AuthConfig(BaseModel):
    """Authentication configuration."""
    method: str = Field(default="oauth2", description="Authentication method (oauth2 or service_account)")
    developer_token: Optional[str] = Field(default=None, description="Google Ads developer token")
    client_id: Optional[str] = Field(default=None, description="OAuth2 client ID")
    client_secret: Optional[str] = Field(default=None, description="OAuth2 client secret")
    refresh_token: Optional[str] = Field(default=None, description="OAuth2 refresh token")
    service_account_key_file: Optional[str] = Field(default=None, description="Service account JSON key file path")
    login_customer_id: Optional[str] = Field(default=None, description="MCC account ID")

    @field_validator('login_customer_id')
    @classmethod
    def validate_customer_id(cls, v):
        """Validate customer ID format."""
        if v and '-' in v:
            raise ValueError("Customer ID must not contain hyphens")
        return v


class CacheConfig(BaseModel):
    """Cache configuration."""
    enabled: bool = Field(default=True, description="Enable caching")
    backend: CacheBackend = Field(default=CacheBackend.MEMORY, description="Cache backend")
    ttl: int = Field(default=3600, description="Cache TTL in seconds")
    redis_url: Optional[str] = Field(default=None, description="Redis connection URL")
    max_size: int = Field(default=1000, description="Maximum cache size (for memory backend)")


class ConnectionPoolConfig(BaseModel):
    """Connection pool configuration."""
    size: int = Field(default=10, description="Connection pool size")
    timeout: int = Field(default=30, description="Connection timeout in seconds")


class RateLimitConfig(BaseModel):
    """Rate limiting configuration."""
    enabled: bool = Field(default=True, description="Enable rate limiting")
    requests_per_minute: int = Field(default=100, description="Maximum requests per minute")
    burst_size: int = Field(default=10, description="Burst size for rate limiter")


class PerformanceConfig(BaseModel):
    """Performance configuration."""
    cache: CacheConfig = Field(default_factory=CacheConfig)
    connection_pool: ConnectionPoolConfig = Field(default_factory=ConnectionPoolConfig)
    rate_limiting: RateLimitConfig = Field(default_factory=RateLimitConfig)


class RetryConfig(BaseModel):
    """Retry configuration."""
    enabled: bool = Field(default=True, description="Enable automatic retries")
    max_attempts: int = Field(default=3, description="Maximum retry attempts")
    backoff: str = Field(default="exponential", description="Backoff strategy (exponential or linear)")
    initial_delay: float = Field(default=1.0, description="Initial delay in seconds")
    max_delay: float = Field(default=60.0, description="Maximum delay in seconds")


class AlertsConfig(BaseModel):
    """Alerts configuration."""
    enabled: bool = Field(default=False, description="Enable alerts")
    webhook_url: Optional[str] = Field(default=None, description="Webhook URL for alerts")
    email: Optional[str] = Field(default=None, description="Email for alerts")


class ErrorHandlingConfig(BaseModel):
    """Error handling configuration."""
    retry: RetryConfig = Field(default_factory=RetryConfig)
    alerts: AlertsConfig = Field(default_factory=AlertsConfig)
    log_errors: bool = Field(default=True, description="Log errors")


class LoggingConfig(BaseModel):
    """Logging configuration."""
    level: LogLevel = Field(default=LogLevel.INFO, description="Log level")
    format: LogFormat = Field(default=LogFormat.TEXT, description="Log format")
    file: Optional[str] = Field(default=None, description="Log file path")
    console: bool = Field(default=True, description="Log to console")


class FeaturesConfig(BaseModel):
    """Feature flags configuration."""
    batch_operations: bool = Field(default=True, description="Enable batch operations")
    auto_recommendations: bool = Field(default=False, description="Auto-apply recommendations")
    advanced_reporting: bool = Field(default=True, description="Enable advanced reporting")
    conversion_tracking: bool = Field(default=True, description="Enable conversion tracking")
    audience_management: bool = Field(default=True, description="Enable audience management")


class GoogleAdsMCPConfig(BaseModel):
    """Main configuration model."""
    authentication: AuthConfig = Field(default_factory=AuthConfig)
    performance: PerformanceConfig = Field(default_factory=PerformanceConfig)
    error_handling: ErrorHandlingConfig = Field(default_factory=ErrorHandlingConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    features: FeaturesConfig = Field(default_factory=FeaturesConfig)

    # API settings
    api_version: str = Field(default="v22", description="Google Ads API version")
    use_proto_plus: bool = Field(default=True, description="Use proto-plus for API responses")

    # Response settings
    default_page_size: int = Field(default=50, description="Default page size for queries")
    max_page_size: int = Field(default=100, description="Maximum page size for queries")
    character_limit: int = Field(default=25000, description="Response character limit")


class ConfigManager:
    """Manages application configuration."""

    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize configuration manager.

        Args:
            config_file: Optional path to configuration file (YAML or JSON)
        """
        self.config: GoogleAdsMCPConfig = self._load_config(config_file)
        self._configure_logging()

    def _load_config(self, config_file: Optional[str]) -> GoogleAdsMCPConfig:
        """
        Load configuration from file and environment variables.

        Args:
            config_file: Path to configuration file

        Returns:
            Loaded configuration
        """
        config_dict = {}

        # Load from file if provided
        if config_file:
            config_path = Path(config_file)
            if config_path.exists():
                try:
                    with open(config_path, 'r') as f:
                        if config_path.suffix in ['.yml', '.yaml']:
                            config_dict = yaml.safe_load(f) or {}
                        elif config_path.suffix == '.json':
                            config_dict = json.load(f)
                    logger.info(f"Loaded configuration from {config_file}")
                except Exception as e:
                    logger.warning(f"Failed to load config file {config_file}: {e}")
            else:
                logger.warning(f"Config file not found: {config_file}")

        # Override with environment variables
        env_config = self._load_from_env()
        config_dict = self._merge_dicts(config_dict, env_config)

        # Create and validate configuration
        try:
            return GoogleAdsMCPConfig(**config_dict)
        except Exception as e:
            logger.error(f"Configuration validation failed: {e}")
            # Return default configuration
            return GoogleAdsMCPConfig()

    def _load_from_env(self) -> Dict[str, Any]:
        """
        Load configuration from environment variables.

        Returns:
            Configuration dictionary from environment
        """
        config = {
            "authentication": {}
        }

        # Authentication settings
        if os.getenv("GOOGLE_ADS_DEVELOPER_TOKEN"):
            config["authentication"]["developer_token"] = os.getenv("GOOGLE_ADS_DEVELOPER_TOKEN")

        if os.getenv("GOOGLE_ADS_CLIENT_ID"):
            config["authentication"]["client_id"] = os.getenv("GOOGLE_ADS_CLIENT_ID")

        if os.getenv("GOOGLE_ADS_CLIENT_SECRET"):
            config["authentication"]["client_secret"] = os.getenv("GOOGLE_ADS_CLIENT_SECRET")

        if os.getenv("GOOGLE_ADS_REFRESH_TOKEN"):
            config["authentication"]["refresh_token"] = os.getenv("GOOGLE_ADS_REFRESH_TOKEN")

        if os.getenv("GOOGLE_ADS_LOGIN_CUSTOMER_ID"):
            config["authentication"]["login_customer_id"] = os.getenv("GOOGLE_ADS_LOGIN_CUSTOMER_ID")

        if os.getenv("GOOGLE_ADS_SERVICE_ACCOUNT_KEY_FILE"):
            config["authentication"]["service_account_key_file"] = os.getenv("GOOGLE_ADS_SERVICE_ACCOUNT_KEY_FILE")
            config["authentication"]["method"] = "service_account"

        # Logging settings
        if os.getenv("LOG_LEVEL"):
            config["logging"] = {"level": os.getenv("LOG_LEVEL")}

        # Cache settings
        if os.getenv("CACHE_ENABLED"):
            config["performance"] = {
                "cache": {"enabled": os.getenv("CACHE_ENABLED").lower() == "true"}
            }

        if os.getenv("CACHE_BACKEND"):
            if "performance" not in config:
                config["performance"] = {}
            if "cache" not in config["performance"]:
                config["performance"]["cache"] = {}
            config["performance"]["cache"]["backend"] = os.getenv("CACHE_BACKEND")

        if os.getenv("REDIS_URL"):
            if "performance" not in config:
                config["performance"] = {}
            if "cache" not in config["performance"]:
                config["performance"]["cache"] = {}
            config["performance"]["cache"]["redis_url"] = os.getenv("REDIS_URL")

        return config

    def _merge_dicts(self, base: Dict, override: Dict) -> Dict:
        """
        Recursively merge two dictionaries.

        Args:
            base: Base dictionary
            override: Override dictionary

        Returns:
            Merged dictionary
        """
        result = base.copy()

        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_dicts(result[key], value)
            else:
                result[key] = value

        return result

    def _configure_logging(self):
        """Configure logging based on config."""
        log_config = self.config.logging

        # Set log level
        numeric_level = getattr(logging, log_config.level.value)
        logging.basicConfig(level=numeric_level)

        # Configure format
        if log_config.format == LogFormat.JSON:
            formatter = logging.Formatter(
                '{"time": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}'
            )
        else:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )

        # Configure handlers
        handlers: List[logging.Handler] = []

        if log_config.console:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            handlers.append(console_handler)

        if log_config.file:
            file_handler = logging.FileHandler(log_config.file)
            file_handler.setFormatter(formatter)
            handlers.append(file_handler)

        # Apply to root logger
        root_logger = logging.getLogger()
        root_logger.handlers = handlers

    def get_auth_config(self) -> AuthConfig:
        """Get authentication configuration."""
        return self.config.authentication

    def get_cache_config(self) -> CacheConfig:
        """Get cache configuration."""
        return self.config.performance.cache

    def get_retry_config(self) -> RetryConfig:
        """Get retry configuration."""
        return self.config.error_handling.retry

    def is_feature_enabled(self, feature: str) -> bool:
        """
        Check if a feature is enabled.

        Args:
            feature: Feature name

        Returns:
            True if feature is enabled
        """
        return getattr(self.config.features, feature, False)

    def save_config(self, file_path: str, format: str = "yaml"):
        """
        Save current configuration to file.

        Args:
            file_path: Path to save configuration
            format: File format (yaml or json)
        """
        config_dict = self.config.model_dump()

        try:
            with open(file_path, 'w') as f:
                if format == "yaml":
                    yaml.dump(config_dict, f, default_flow_style=False, sort_keys=False)
                else:
                    json.dump(config_dict, f, indent=2)

            logger.info(f"Configuration saved to {file_path}")
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            raise

    def validate(self) -> tuple[bool, List[str]]:
        """
        Validate current configuration.

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []

        # Validate authentication
        auth = self.config.authentication
        if auth.method == "oauth2":
            required_fields = ["developer_token", "client_id", "client_secret", "refresh_token"]
            for field in required_fields:
                if not getattr(auth, field):
                    errors.append(f"Missing required OAuth2 field: {field}")
        elif auth.method == "service_account":
            if not auth.service_account_key_file:
                errors.append("Missing service_account_key_file for service account authentication")
            elif not Path(auth.service_account_key_file).exists():
                errors.append(f"Service account key file not found: {auth.service_account_key_file}")

        # Validate cache backend
        if self.config.performance.cache.enabled:
            if self.config.performance.cache.backend == CacheBackend.REDIS:
                if not self.config.performance.cache.redis_url:
                    errors.append("Redis backend enabled but redis_url not provided")

        return len(errors) == 0, errors


# Global configuration manager instance
_config_manager: Optional[ConfigManager] = None


def get_config_manager(config_file: Optional[str] = None) -> ConfigManager:
    """
    Get or create the global configuration manager.

    Args:
        config_file: Optional configuration file path

    Returns:
        Configuration manager instance
    """
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager(config_file)
    return _config_manager


def get_config() -> GoogleAdsMCPConfig:
    """Get current configuration."""
    return get_config_manager().config
