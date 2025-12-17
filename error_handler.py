"""
Google Ads MCP Error Handler

Comprehensive error handling with:
- Error categorization
- Retry logic with exponential backoff
- Rate limit detection
- User-friendly error messages
- Error logging and tracking
"""

import logging
import time
from typing import Callable, Any, Optional, TypeVar, List
from functools import wraps
from google.ads.googleads.errors import GoogleAdsException
from google.api_core.exceptions import ResourceExhausted, DeadlineExceeded, ServiceUnavailable

logger = logging.getLogger(__name__)

T = TypeVar('T')


class ErrorCategory:
    """Error category constants."""
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    VALIDATION = "validation"
    RATE_LIMIT = "rate_limit"
    NOT_FOUND = "not_found"
    QUOTA_EXCEEDED = "quota_exceeded"
    NETWORK = "network"
    TIMEOUT = "timeout"
    SERVER_ERROR = "server_error"
    UNKNOWN = "unknown"


class GoogleAdsError:
    """Structured Google Ads error information."""

    def __init__(
        self,
        category: str,
        message: str,
        original_error: Optional[Exception] = None,
        field_path: Optional[str] = None,
        retryable: bool = False,
        user_action: Optional[str] = None
    ):
        """
        Initialize error information.

        Args:
            category: Error category
            message: Error message
            original_error: Original exception
            field_path: Field path that caused the error
            retryable: Whether the error is retryable
            user_action: Suggested user action
        """
        self.category = category
        self.message = message
        self.original_error = original_error
        self.field_path = field_path
        self.retryable = retryable
        self.user_action = user_action

    def to_user_message(self) -> str:
        """
        Convert to user-friendly error message.

        Returns:
            Formatted error message for users
        """
        parts = []

        # Category-specific prefix
        prefixes = {
            ErrorCategory.AUTHENTICATION: "🔐 Authentication Error",
            ErrorCategory.AUTHORIZATION: "🚫 Permission Denied",
            ErrorCategory.VALIDATION: "⚠️ Validation Error",
            ErrorCategory.RATE_LIMIT: "⏱️ Rate Limit Exceeded",
            ErrorCategory.NOT_FOUND: "🔍 Not Found",
            ErrorCategory.QUOTA_EXCEEDED: "📊 Quota Exceeded",
            ErrorCategory.NETWORK: "🌐 Network Error",
            ErrorCategory.TIMEOUT: "⏰ Request Timeout",
            ErrorCategory.SERVER_ERROR: "🔧 Server Error",
        }

        prefix = prefixes.get(self.category, "❌ Error")
        parts.append(f"{prefix}: {self.message}")

        # Add field path if available
        if self.field_path:
            parts.append(f"\nField: {self.field_path}")

        # Add user action if available
        if self.user_action:
            parts.append(f"\n\n💡 Suggested Action: {self.user_action}")

        # Add retry hint
        if self.retryable:
            parts.append("\n\n🔄 This error is retryable. The operation will be attempted again automatically.")

        return "".join(parts)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "category": self.category,
            "message": self.message,
            "field_path": self.field_path,
            "retryable": self.retryable,
            "user_action": self.user_action
        }


class ErrorHandler:
    """Handles Google Ads API errors with categorization and retry logic."""

    # Retryable error codes
    RETRYABLE_ERROR_CODES = {
        "INTERNAL_ERROR",
        "TRANSIENT_ERROR",
        "DEADLINE_EXCEEDED",
        "RESOURCE_EXHAUSTED",
        "UNAVAILABLE"
    }

    # Rate limit error codes
    RATE_LIMIT_CODES = {
        "RATE_LIMIT_ERROR",
        "RESOURCE_EXHAUSTED",
        "RATE_EXCEEDED"
    }

    @staticmethod
    def categorize_error(error: Exception) -> GoogleAdsError:
        """
        Categorize and structure an error.

        Args:
            error: Exception to categorize

        Returns:
            Structured Google Ads error
        """
        if isinstance(error, GoogleAdsException):
            return ErrorHandler._categorize_google_ads_exception(error)
        elif isinstance(error, ResourceExhausted):
            return GoogleAdsError(
                category=ErrorCategory.RATE_LIMIT,
                message="API rate limit exceeded. Please wait before retrying.",
                original_error=error,
                retryable=True,
                user_action="Reduce request frequency or use caching to minimize API calls."
            )
        elif isinstance(error, DeadlineExceeded):
            return GoogleAdsError(
                category=ErrorCategory.TIMEOUT,
                message="Request timed out. The server took too long to respond.",
                original_error=error,
                retryable=True,
                user_action="Try again with a smaller date range or more restrictive filters."
            )
        elif isinstance(error, ServiceUnavailable):
            return GoogleAdsError(
                category=ErrorCategory.SERVER_ERROR,
                message="Google Ads API is temporarily unavailable.",
                original_error=error,
                retryable=True,
                user_action="Wait a few minutes and try again."
            )
        else:
            return GoogleAdsError(
                category=ErrorCategory.UNKNOWN,
                message=str(error),
                original_error=error,
                retryable=False,
                user_action="Check your request parameters and try again."
            )

    @staticmethod
    def _categorize_google_ads_exception(error: GoogleAdsException) -> GoogleAdsError:
        """Categorize a GoogleAdsException."""
        if not error.failure or not error.failure.errors:
            return GoogleAdsError(
                category=ErrorCategory.UNKNOWN,
                message="Unknown Google Ads API error",
                original_error=error
            )

        # Get first error (usually the root cause)
        first_error = error.failure.errors[0]
        error_code = first_error.error_code
        error_message = first_error.message

        # Extract field path
        field_path = None
        if first_error.location and first_error.location.field_path_elements:
            field_path = ".".join(
                elem.field_name for elem in first_error.location.field_path_elements
            )

        # Categorize based on error code
        category = ErrorCategory.UNKNOWN
        retryable = False
        user_action = None

        # Check authentication errors
        if any(code in str(error_code) for code in ["AUTHENTICATION", "INVALID_CUSTOMER"]):
            category = ErrorCategory.AUTHENTICATION
            user_action = "Check your credentials and ensure they are valid and not expired."

        # Check authorization errors
        elif any(code in str(error_code) for code in ["AUTHORIZATION", "PERMISSION"]):
            category = ErrorCategory.AUTHORIZATION
            user_action = "Verify that you have permission to access this resource."

        # Check validation errors
        elif any(code in str(error_code) for code in ["INVALID", "REQUIRED", "MALFORMED"]):
            category = ErrorCategory.VALIDATION
            user_action = "Review your input parameters and ensure they meet API requirements."

        # Check rate limit errors
        elif any(code in str(error_code) for code in ErrorHandler.RATE_LIMIT_CODES):
            category = ErrorCategory.RATE_LIMIT
            retryable = True
            user_action = "Wait before making more requests or reduce request frequency."

        # Check quota errors
        elif "QUOTA" in str(error_code):
            category = ErrorCategory.QUOTA_EXCEEDED
            user_action = "You've reached your API quota limit. Wait until it resets or request an increase."

        # Check not found errors
        elif any(code in str(error_code) for code in ["NOT_FOUND", "DOES_NOT_EXIST"]):
            category = ErrorCategory.NOT_FOUND
            user_action = "Verify that the resource ID is correct and exists in your account."

        # Check retryable errors
        elif any(code in str(error_code) for code in ErrorHandler.RETRYABLE_ERROR_CODES):
            category = ErrorCategory.SERVER_ERROR
            retryable = True
            user_action = "This is a temporary error. Try again in a few moments."

        return GoogleAdsError(
            category=category,
            message=error_message,
            original_error=error,
            field_path=field_path,
            retryable=retryable,
            user_action=user_action
        )

    @staticmethod
    def handle_error(error: Exception, context: str = "") -> str:
        """
        Handle an error and return user-friendly message.

        Args:
            error: Exception to handle
            context: Additional context about the operation

        Returns:
            User-friendly error message
        """
        structured_error = ErrorHandler.categorize_error(error)

        # Log the error
        logger.error(
            f"Error in {context}: {structured_error.category} - {structured_error.message}",
            exc_info=error
        )

        # Return user-friendly message
        return structured_error.to_user_message()


def with_retry(
    max_attempts: int = 3,
    backoff_base: float = 2.0,
    max_backoff: float = 60.0,
    retryable_errors: Optional[List[str]] = None
):
    """
    Decorator to add retry logic with exponential backoff.

    Args:
        max_attempts: Maximum number of retry attempts
        backoff_base: Base for exponential backoff calculation
        max_backoff: Maximum backoff time in seconds
        retryable_errors: List of error categories to retry (None = all retryable)

    Returns:
        Decorated function with retry logic
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            attempt = 0
            last_error = None

            while attempt < max_attempts:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    structured_error = ErrorHandler.categorize_error(e)

                    # Check if error is retryable
                    if not structured_error.retryable:
                        raise

                    # Check if error category is in retryable list
                    if retryable_errors and structured_error.category not in retryable_errors:
                        raise

                    # Calculate backoff time
                    attempt += 1
                    if attempt >= max_attempts:
                        logger.error(f"Max retry attempts ({max_attempts}) reached for {func.__name__}")
                        raise

                    backoff = min(backoff_base ** attempt, max_backoff)
                    logger.warning(
                        f"Retrying {func.__name__} (attempt {attempt}/{max_attempts}) "
                        f"after {backoff:.1f}s due to: {structured_error.message}"
                    )

                    time.sleep(backoff)

            # This shouldn't be reached, but just in case
            if last_error:
                raise last_error

        return wrapper
    return decorator


def with_rate_limit_handling(
    max_retries: int = 5,
    initial_backoff: float = 1.0
):
    """
    Decorator specifically for handling rate limits.

    Args:
        max_retries: Maximum number of retries
        initial_backoff: Initial backoff time in seconds

    Returns:
        Decorated function with rate limit handling
    """
    return with_retry(
        max_attempts=max_retries,
        backoff_base=2.0,
        max_backoff=300.0,  # 5 minutes max
        retryable_errors=[ErrorCategory.RATE_LIMIT]
    )


def safe_execute(func: Callable[..., T], *args, **kwargs) -> tuple[Optional[T], Optional[str]]:
    """
    Safely execute a function and return result or error message.

    Args:
        func: Function to execute
        *args: Positional arguments
        **kwargs: Keyword arguments

    Returns:
        Tuple of (result, error_message). One will be None.
    """
    try:
        result = func(*args, **kwargs)
        return result, None
    except Exception as e:
        error_msg = ErrorHandler.handle_error(e, context=func.__name__)
        return None, error_msg
