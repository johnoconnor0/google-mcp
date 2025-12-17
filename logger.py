"""
Google Ads MCP Logging Module

Structured logging with:
- Multiple log handlers
- JSON formatting
- Context-aware logging
- Performance tracking
- Audit logging
"""

import logging
import logging.handlers
import json
import time
from typing import Optional, Dict, Any
from datetime import datetime
from pathlib import Path
from contextlib import contextmanager

# ANSI color codes for console output
class Colors:
    """ANSI color codes."""
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'

    # Foreground colors
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'

    # Background colors
    BG_BLACK = '\033[40m'
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'
    BG_BLUE = '\033[44m'


class JSONFormatter(logging.Formatter):
    """
    JSON log formatter for structured logging.
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
        }

        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)

        # Add extra fields
        if hasattr(record, 'customer_id'):
            log_data['customer_id'] = record.customer_id

        if hasattr(record, 'operation'):
            log_data['operation'] = record.operation

        if hasattr(record, 'duration'):
            log_data['duration_ms'] = record.duration

        if hasattr(record, 'extra'):
            log_data['extra'] = record.extra

        return json.dumps(log_data)


class ColoredFormatter(logging.Formatter):
    """
    Colored console formatter for better readability.
    """

    LEVEL_COLORS = {
        'DEBUG': Colors.CYAN,
        'INFO': Colors.GREEN,
        'WARNING': Colors.YELLOW,
        'ERROR': Colors.RED,
        'CRITICAL': Colors.BG_RED + Colors.WHITE + Colors.BOLD,
    }

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors."""
        # Color the level name
        level_color = self.LEVEL_COLORS.get(record.levelname, Colors.RESET)
        colored_level = f"{level_color}{record.levelname:8s}{Colors.RESET}"

        # Create colored format string
        record.levelname = colored_level

        # Format the message
        formatted = super().format(record)

        return formatted


class PerformanceLogger:
    """Helper for logging performance metrics."""

    def __init__(self, logger: logging.Logger):
        """
        Initialize performance logger.

        Args:
            logger: Base logger to use
        """
        self.logger = logger

    @contextmanager
    def track_operation(
        self,
        operation: str,
        customer_id: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None
    ):
        """
        Context manager to track operation performance.

        Args:
            operation: Operation name
            customer_id: Optional customer ID
            extra: Extra metadata to log

        Example:
            with performance_logger.track_operation('campaign_query', customer_id='123'):
                # Your code here
                pass
        """
        start_time = time.time()

        try:
            yield

            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000

            # Log successful operation
            extra_dict = extra or {}
            extra_dict.update({
                'operation': operation,
                'duration_ms': duration_ms,
                'success': True
            })

            if customer_id:
                extra_dict['customer_id'] = customer_id

            self.logger.info(
                f"Operation '{operation}' completed in {duration_ms:.2f}ms",
                extra=extra_dict
            )

        except Exception as e:
            # Calculate duration even for failed operations
            duration_ms = (time.time() - start_time) * 1000

            # Log failed operation
            extra_dict = extra or {}
            extra_dict.update({
                'operation': operation,
                'duration_ms': duration_ms,
                'success': False,
                'error': str(e)
            })

            if customer_id:
                extra_dict['customer_id'] = customer_id

            self.logger.error(
                f"Operation '{operation}' failed after {duration_ms:.2f}ms: {e}",
                extra=extra_dict,
                exc_info=True
            )

            # Re-raise the exception
            raise


class AuditLogger:
    """Logger for audit trail of API operations."""

    def __init__(self, logger_name: str = "google_ads_mcp.audit"):
        """
        Initialize audit logger.

        Args:
            logger_name: Name for the audit logger
        """
        self.logger = logging.getLogger(logger_name)

    def log_api_call(
        self,
        customer_id: str,
        operation: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        action: str = "read",
        user: Optional[str] = None,
        result: str = "success",
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Log an API call for audit purposes.

        Args:
            customer_id: Google Ads customer ID
            operation: Operation name
            resource_type: Type of resource (campaign, ad_group, etc.)
            resource_id: Optional resource ID
            action: Action performed (read, create, update, delete)
            user: Optional user identifier
            result: Result status (success, failure)
            details: Additional details
        """
        audit_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'customer_id': customer_id,
            'operation': operation,
            'resource_type': resource_type,
            'action': action,
            'result': result
        }

        if resource_id:
            audit_data['resource_id'] = resource_id

        if user:
            audit_data['user'] = user

        if details:
            audit_data['details'] = details

        # Log as INFO for successful operations, WARNING for failures
        if result == "success":
            self.logger.info(f"Audit: {action} {resource_type}", extra=audit_data)
        else:
            self.logger.warning(f"Audit: Failed {action} {resource_type}", extra=audit_data)


def setup_logger(
    name: str,
    level: str = "INFO",
    log_file: Optional[str] = None,
    json_format: bool = False,
    colored_console: bool = True
) -> logging.Logger:
    """
    Set up a logger with appropriate handlers.

    Args:
        name: Logger name
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional file path for file logging
        json_format: Use JSON formatting
        colored_console: Use colored console output

    Returns:
        Configured logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))

    # Remove existing handlers
    logger.handlers = []

    # Create formatter
    if json_format:
        formatter = JSONFormatter()
    elif colored_console:
        formatter = ColoredFormatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (if specified)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        # Use rotating file handler to prevent huge log files
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10 MB
            backupCount=5
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger by name.

    Args:
        name: Logger name

    Returns:
        Logger instance
    """
    return logging.getLogger(name)


# Create default loggers
main_logger = setup_logger("google_ads_mcp")
performance_logger = PerformanceLogger(setup_logger("google_ads_mcp.performance"))
audit_logger = AuditLogger()
