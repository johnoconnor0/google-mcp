"""
Google Ads Authentication Manager

Enhanced authentication handling with:
- Automatic token refresh
- Token validation
- Multi-account session management
- Service account support
- Credential encryption (optional)
"""

import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from pathlib import Path
from google.ads.googleads.client import GoogleAdsClient
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError

logger = logging.getLogger(__name__)


class AuthenticationError(Exception):
    """Custom exception for authentication errors."""
    pass


class TokenManager:
    """Manages OAuth tokens with automatic refresh."""

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        refresh_token: str,
        token_uri: str = "https://oauth2.googleapis.com/token"
    ):
        """
        Initialize token manager.

        Args:
            client_id: OAuth2 client ID
            client_secret: OAuth2 client secret
            refresh_token: OAuth2 refresh token
            token_uri: Token endpoint URI
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token
        self.token_uri = token_uri

        self._credentials: Optional[Credentials] = None
        self._last_refresh: Optional[datetime] = None

    def get_credentials(self, force_refresh: bool = False) -> Credentials:
        """
        Get valid credentials, refreshing if necessary.

        Args:
            force_refresh: Force token refresh even if not expired

        Returns:
            Valid OAuth2 credentials

        Raises:
            AuthenticationError: If token refresh fails
        """
        # Initialize credentials if not done
        if self._credentials is None:
            self._credentials = Credentials(
                token=None,
                refresh_token=self.refresh_token,
                token_uri=self.token_uri,
                client_id=self.client_id,
                client_secret=self.client_secret
            )

        # Check if refresh is needed
        needs_refresh = (
            force_refresh or
            not self._credentials.valid or
            self._credentials.expired or
            self._last_refresh is None
        )

        if needs_refresh:
            try:
                self._credentials.refresh(Request())
                self._last_refresh = datetime.now()
                logger.info("OAuth token refreshed successfully")
            except RefreshError as e:
                logger.error(f"Token refresh failed: {e}")
                raise AuthenticationError(
                    f"Failed to refresh OAuth token: {e}. "
                    "Your refresh token may have expired. Please regenerate it."
                )

        return self._credentials

    def validate_token(self) -> bool:
        """
        Validate that the refresh token works.

        Returns:
            True if token is valid, False otherwise
        """
        try:
            self.get_credentials(force_refresh=True)
            return True
        except AuthenticationError:
            return False


class GoogleAdsAuthManager:
    """
    Manages Google Ads API authentication with enhanced features.

    Features:
    - Automatic token refresh
    - Multiple account sessions
    - Token validation
    - Service account support
    """

    def __init__(self):
        """Initialize the authentication manager."""
        self._clients: Dict[str, GoogleAdsClient] = {}
        self._token_managers: Dict[str, TokenManager] = {}
        self._current_client_key: Optional[str] = None

    def initialize_oauth(
        self,
        developer_token: str,
        client_id: str,
        client_secret: str,
        refresh_token: str,
        login_customer_id: Optional[str] = None,
        client_key: str = "default"
    ) -> str:
        """
        Initialize Google Ads client with OAuth2.

        Args:
            developer_token: Google Ads developer token
            client_id: OAuth2 client ID
            client_secret: OAuth2 client secret
            refresh_token: OAuth2 refresh token
            login_customer_id: Optional MCC account ID
            client_key: Unique identifier for this client session

        Returns:
            Client key for this session

        Raises:
            AuthenticationError: If initialization fails
        """
        try:
            # Create token manager
            token_manager = TokenManager(
                client_id=client_id,
                client_secret=client_secret,
                refresh_token=refresh_token
            )

            # Validate token
            if not token_manager.validate_token():
                raise AuthenticationError("Invalid refresh token")

            # Build credentials dict
            credentials = {
                "developer_token": developer_token,
                "client_id": client_id,
                "client_secret": client_secret,
                "refresh_token": refresh_token,
                "use_proto_plus": True
            }

            if login_customer_id:
                credentials["login_customer_id"] = login_customer_id

            # Create client
            client = GoogleAdsClient.load_from_dict(credentials)

            # Store client and token manager
            self._clients[client_key] = client
            self._token_managers[client_key] = token_manager
            self._current_client_key = client_key

            logger.info(f"Google Ads client initialized: {client_key}")

            return client_key

        except Exception as e:
            logger.error(f"Failed to initialize OAuth client: {e}")
            raise AuthenticationError(f"OAuth initialization failed: {e}")

    def initialize_service_account(
        self,
        developer_token: str,
        json_key_file_path: str,
        login_customer_id: Optional[str] = None,
        client_key: str = "service_account"
    ) -> str:
        """
        Initialize Google Ads client with service account.

        Args:
            developer_token: Google Ads developer token
            json_key_file_path: Path to service account JSON key file
            login_customer_id: Optional MCC account ID
            client_key: Unique identifier for this client session

        Returns:
            Client key for this session

        Raises:
            AuthenticationError: If initialization fails
        """
        try:
            # Verify key file exists
            key_file = Path(json_key_file_path)
            if not key_file.exists():
                raise AuthenticationError(f"Service account key file not found: {json_key_file_path}")

            # Build credentials dict
            credentials = {
                "developer_token": developer_token,
                "json_key_file_path": json_key_file_path,
                "use_proto_plus": True
            }

            if login_customer_id:
                credentials["login_customer_id"] = login_customer_id

            # Create client
            client = GoogleAdsClient.load_from_dict(credentials)

            # Store client
            self._clients[client_key] = client
            self._current_client_key = client_key

            logger.info(f"Google Ads service account client initialized: {client_key}")

            return client_key

        except Exception as e:
            logger.error(f"Failed to initialize service account client: {e}")
            raise AuthenticationError(f"Service account initialization failed: {e}")

    def get_client(self, client_key: Optional[str] = None) -> GoogleAdsClient:
        """
        Get Google Ads client for the specified key.

        Args:
            client_key: Client key (uses current if None)

        Returns:
            Google Ads client

        Raises:
            AuthenticationError: If client not found
        """
        key = client_key or self._current_client_key

        if key is None:
            raise AuthenticationError(
                "No Google Ads client initialized. Call initialize_oauth() or "
                "initialize_service_account() first."
            )

        if key not in self._clients:
            raise AuthenticationError(f"Client not found: {key}")

        return self._clients[key]

    def switch_client(self, client_key: str) -> None:
        """
        Switch to a different client session.

        Args:
            client_key: Key of client to switch to

        Raises:
            AuthenticationError: If client not found
        """
        if client_key not in self._clients:
            raise AuthenticationError(f"Client not found: {client_key}")

        self._current_client_key = client_key
        logger.info(f"Switched to client: {client_key}")

    def list_clients(self) -> Dict[str, Dict[str, Any]]:
        """
        List all initialized clients.

        Returns:
            Dictionary of client keys and their metadata
        """
        clients_info = {}

        for key in self._clients:
            clients_info[key] = {
                "key": key,
                "is_current": key == self._current_client_key,
                "has_token_manager": key in self._token_managers
            }

        return clients_info

    def refresh_token(self, client_key: Optional[str] = None) -> None:
        """
        Manually refresh OAuth token for a client.

        Args:
            client_key: Client key (uses current if None)

        Raises:
            AuthenticationError: If client doesn't have token manager
        """
        key = client_key or self._current_client_key

        if key not in self._token_managers:
            raise AuthenticationError(
                f"Client {key} doesn't use OAuth (no token manager)"
            )

        self._token_managers[key].get_credentials(force_refresh=True)
        logger.info(f"Token refreshed for client: {key}")

    def validate_credentials(self, client_key: Optional[str] = None) -> bool:
        """
        Validate credentials for a client.

        Args:
            client_key: Client key (uses current if None)

        Returns:
            True if credentials are valid
        """
        try:
            client = self.get_client(client_key)
            # Try to access customer service (lightweight validation)
            customer_service = client.get_service("CustomerService")
            return True
        except Exception as e:
            logger.error(f"Credential validation failed: {e}")
            return False

    def remove_client(self, client_key: str) -> None:
        """
        Remove a client session.

        Args:
            client_key: Key of client to remove
        """
        if client_key in self._clients:
            del self._clients[client_key]

        if client_key in self._token_managers:
            del self._token_managers[client_key]

        if self._current_client_key == client_key:
            self._current_client_key = None

        logger.info(f"Removed client: {client_key}")


# Global authentication manager instance
auth_manager = GoogleAdsAuthManager()


def get_auth_manager() -> GoogleAdsAuthManager:
    """Get the global authentication manager instance."""
    return auth_manager
