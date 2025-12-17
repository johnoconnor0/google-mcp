"""
Google Ads MCP Server v2.0

Enhanced MCP server with:
- Automatic token refresh
- Intelligent caching
- Error handling with retry logic
- Performance tracking
- Audit logging
- Query optimization
- Response streaming

Requirements:
- google-ads>=25.0.0
- mcp>=1.1.0
- httpx>=0.27.0
- pydantic>=2.0.0
- google-auth-oauthlib>=1.0.0
- PyYAML>=6.0.0
- cachetools>=5.3.0
- redis>=5.0.0 (optional)
"""

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any, Literal
from enum import Enum
import json
import asyncio

# Import our new modules
from auth_manager import get_auth_manager, AuthenticationError
from error_handler import with_retry, with_rate_limit_handling, ErrorHandler, safe_execute
from config_manager import get_config_manager, get_config
from cache_manager import get_cache_manager, cached, ResourceType, initialize_cache
from logger import main_logger, performance_logger, audit_logger, get_logger
from query_optimizer import get_query_optimizer, validate_query, optimize_query
from response_handler import ResponseFormatter, stream_large_query, paginate_results

# Initialize logger for this module
logger = get_logger(__name__)

# Initialize MCP server
mcp = FastMCP("google_ads_mcp_v2")

# Initialize configuration (loads from config.yaml or environment variables)
try:
    config = get_config_manager()
    logger.info("Configuration loaded successfully")
except Exception as e:
    logger.warning(f"Failed to load configuration, using defaults: {e}")
    config = get_config_manager()  # Will use defaults

# Initialize auth manager
auth_manager = get_auth_manager()

# Initialize cache manager
cache_backend = config.config.performance.cache.backend
if cache_backend.value == "redis" and config.config.performance.cache.redis_url:
    cache_manager = initialize_cache(
        backend=cache_backend,
        redis_url=config.config.performance.cache.redis_url,
        default_ttl=config.config.performance.cache.ttl
    )
else:
    cache_manager = initialize_cache(
        backend=cache_backend,
        max_size=config.config.performance.cache.max_size,
        default_ttl=config.config.performance.cache.ttl
    )

logger.info(f"Cache initialized with backend: {cache_backend.value}")

# Constants
CHARACTER_LIMIT = config.config.character_limit
DEFAULT_PAGE_SIZE = config.config.default_page_size
MAX_PAGE_SIZE = config.config.max_page_size


# ============================================================================
# Enums
# ============================================================================

class ResponseFormat(str, Enum):
    """Output format for tool responses."""
    MARKDOWN = "markdown"
    JSON = "json"


class DateRange(str, Enum):
    """Predefined date ranges for queries."""
    TODAY = "TODAY"
    YESTERDAY = "YESTERDAY"
    LAST_7_DAYS = "LAST_7_DAYS"
    LAST_14_DAYS = "LAST_14_DAYS"
    LAST_30_DAYS = "LAST_30_DAYS"
    THIS_MONTH = "THIS_MONTH"
    LAST_MONTH = "LAST_MONTH"
    LAST_90_DAYS = "LAST_90_DAYS"


class CampaignStatus(str, Enum):
    """Campaign status options."""
    ENABLED = "ENABLED"
    PAUSED = "PAUSED"
    REMOVED = "REMOVED"


# ============================================================================
# Helper Functions
# ============================================================================

def format_micros(micros: int) -> float:
    """Convert micros to standard currency units."""
    return micros / 1_000_000


def format_percentage(value: float) -> str:
    """Format a decimal as a percentage."""
    return f"{value * 100:.2f}%"


@with_retry(max_attempts=3, backoff_base=2.0)
async def execute_query(
    customer_id: str,
    query: str,
    use_cache: bool = True
) -> List[Any]:
    """
    Execute a GAQL query with caching and retry logic.

    Args:
        customer_id: Customer ID (without hyphens)
        query: GAQL query string
        use_cache: Whether to use caching

    Returns:
        List of row results
    """
    with performance_logger.track_operation('execute_query', customer_id=customer_id):
        # Get client
        client = auth_manager.get_client()
        ga_service = client.get_service("GoogleAdsService")

        try:
            # Validate and optimize query
            query_analysis = validate_query(query)

            if not query_analysis.is_valid:
                error_msg = "Query validation failed:\n" + "\n".join(query_analysis.errors)
                logger.error(error_msg)
                raise ValueError(error_msg)

            # Log warnings
            for warning in query_analysis.warnings:
                logger.warning(f"Query warning: {warning}")

            # Execute query
            response = ga_service.search(customer_id=customer_id, query=query)
            results = list(response)

            logger.info(f"Query returned {len(results)} results for customer {customer_id}")

            return results

        except Exception as e:
            error_msg = ErrorHandler.handle_error(e, context="execute_query")
            logger.error(error_msg)
            raise


# ============================================================================
# MCP Tools - Authentication
# ============================================================================

@mcp.tool()
def google_ads_initialize(
    developer_token: str,
    client_id: str,
    client_secret: str,
    refresh_token: str,
    login_customer_id: Optional[str] = None,
    client_key: str = "default"
) -> str:
    """
    Initialize Google Ads API with OAuth credentials (v2 with auto token refresh).

    Args:
        developer_token: Google Ads developer token
        client_id: OAuth2 client ID
        client_secret: OAuth2 client secret
        refresh_token: OAuth2 refresh token (auto-refreshes when expired)
        login_customer_id: Optional MCC account ID (without hyphens)
        client_key: Unique identifier for this session (default: "default")

    Returns:
        Success message with session information
    """
    try:
        # Initialize OAuth with auth manager
        session_key = auth_manager.initialize_oauth(
            developer_token=developer_token,
            client_id=client_id,
            client_secret=client_secret,
            refresh_token=refresh_token,
            login_customer_id=login_customer_id,
            client_key=client_key
        )

        # Validate credentials
        is_valid = auth_manager.validate_credentials(client_key)

        if not is_valid:
            return "❌ Initialization failed: Could not validate credentials"

        logger.info(f"Google Ads client initialized successfully: {client_key}")

        return (
            f"✅ Google Ads API initialized successfully!\n\n"
            f"Session Key: {session_key}\n"
            f"MCC Account: {login_customer_id or 'Not specified'}\n"
            f"Token Refresh: Automatic (enabled)\n"
            f"Multi-Account Support: Yes\n\n"
            f"You can now use other Google Ads tools to query and manage campaigns."
        )

    except AuthenticationError as e:
        error_msg = str(e)
        logger.error(f"Authentication failed: {error_msg}")
        return f"❌ Authentication Error: {error_msg}"
    except Exception as e:
        error_msg = ErrorHandler.handle_error(e, context="google_ads_initialize")
        return f"❌ Initialization Error: {error_msg}"


@mcp.tool()
def google_ads_service_account_init(
    developer_token: str,
    json_key_file_path: str,
    login_customer_id: Optional[str] = None,
    client_key: str = "service_account"
) -> str:
    """
    Initialize Google Ads API with service account (for automated processes).

    Args:
        developer_token: Google Ads developer token
        json_key_file_path: Path to service account JSON key file
        login_customer_id: Optional MCC account ID (without hyphens)
        client_key: Unique identifier for this session

    Returns:
        Success message with session information
    """
    try:
        session_key = auth_manager.initialize_service_account(
            developer_token=developer_token,
            json_key_file_path=json_key_file_path,
            login_customer_id=login_customer_id,
            client_key=client_key
        )

        logger.info(f"Service account initialized: {client_key}")

        return (
            f"✅ Service Account initialized successfully!\n\n"
            f"Session Key: {session_key}\n"
            f"Key File: {json_key_file_path}\n"
            f"MCC Account: {login_customer_id or 'Not specified'}\n\n"
            f"Service account authentication is ideal for automated scripts and scheduled tasks."
        )

    except AuthenticationError as e:
        return f"❌ Service Account Error: {str(e)}"
    except Exception as e:
        error_msg = ErrorHandler.handle_error(e, context="service_account_init")
        return f"❌ Initialization Error: {error_msg}"


@mcp.tool()
def google_ads_list_auth_sessions() -> str:
    """
    List all authenticated Google Ads sessions.

    Returns:
        List of active sessions with metadata
    """
    try:
        clients = auth_manager.list_clients()

        if not clients:
            return "No authenticated sessions found. Use google_ads_initialize first."

        output = "# Authenticated Google Ads Sessions\n\n"

        for key, info in clients.items():
            current_marker = " (CURRENT)" if info['is_current'] else ""
            auth_type = "OAuth2" if info['has_token_manager'] else "Service Account"

            output += f"## {key}{current_marker}\n"
            output += f"- **Auth Type**: {auth_type}\n"
            output += f"- **Status**: Active\n\n"

        output += f"\n**Total Sessions**: {len(clients)}\n"
        output += "\nUse `google_ads_switch_session` to switch between sessions."

        return output

    except Exception as e:
        error_msg = ErrorHandler.handle_error(e, context="list_auth_sessions")
        return f"❌ Error: {error_msg}"


@mcp.tool()
def google_ads_switch_session(client_key: str) -> str:
    """
    Switch to a different authenticated session.

    Args:
        client_key: Session key to switch to

    Returns:
        Success message
    """
    try:
        auth_manager.switch_client(client_key)
        logger.info(f"Switched to session: {client_key}")

        return f"✅ Switched to session: {client_key}\n\nAll subsequent operations will use this session."

    except AuthenticationError as e:
        return f"❌ Error: {str(e)}"
    except Exception as e:
        error_msg = ErrorHandler.handle_error(e, context="switch_session")
        return f"❌ Error: {error_msg}"


@mcp.tool()
def google_ads_get_cache_stats() -> str:
    """
    Get cache statistics and performance metrics.

    Returns:
        Cache statistics in markdown format
    """
    try:
        stats = cache_manager.get_stats()

        output = "# Cache Statistics\n\n"
        output += f"**Backend**: {stats.get('backend', 'unknown').upper()}\n"
        output += f"**Hit Rate**: {stats.get('hit_rate', '0%')}\n"
        output += f"**Total Requests**: {stats.get('total_requests', 0)}\n"
        output += f"**Cache Hits**: {stats.get('hits', 0)}\n"
        output += f"**Cache Misses**: {stats.get('misses', 0)}\n"
        output += f"**Cache Sets**: {stats.get('sets', 0)}\n"
        output += f"**Errors**: {stats.get('errors', 0)}\n\n"

        if 'size' in stats:
            output += f"**Current Size**: {stats['size']} items\n"
            output += f"**Max Size**: {stats.get('max_size', 'N/A')}\n\n"

        if stats.get('backend') == 'redis':
            output += f"**Connected Clients**: {stats.get('connected_clients', 0)}\n"
            output += f"**Memory Used**: {stats.get('used_memory_human', 'unknown')}\n"
            output += f"**Total Keys**: {stats.get('total_keys', 0)}\n\n"

        output += "Cache is automatically used for read operations to improve performance."

        return output

    except Exception as e:
        error_msg = ErrorHandler.handle_error(e, context="get_cache_stats")
        return f"❌ Error: {error_msg}"


# ============================================================================
# MCP Tools - Account Management
# ============================================================================

@mcp.tool()
async def google_ads_list_accounts(
    response_format: ResponseFormat = ResponseFormat.MARKDOWN
) -> str:
    """
    List all accessible Google Ads accounts.

    Args:
        response_format: Output format (markdown or json)

    Returns:
        List of accounts with details
    """
    with performance_logger.track_operation('list_accounts'):
        try:
            client = auth_manager.get_client()
            customer_service = client.get_service("CustomerService")

            # Get accessible customers
            accessible_customers = customer_service.list_accessible_customers()
            resource_names = accessible_customers.resource_names

            accounts = []

            for resource_name in resource_names:
                customer_id = resource_name.split("/")[1]

                # Get customer details
                query = f"""
                    SELECT
                        customer.id,
                        customer.descriptive_name,
                        customer.currency_code,
                        customer.time_zone,
                        customer.manager,
                        customer.status
                    FROM customer
                    WHERE customer.id = {customer_id}
                """

                results = await execute_query(customer_id, query, use_cache=True)

                if results:
                    row = results[0]
                    accounts.append({
                        'id': str(row.customer.id),
                        'name': row.customer.descriptive_name or 'Unnamed Account',
                        'currency_code': row.customer.currency_code,
                        'time_zone': row.customer.time_zone,
                        'manager': row.customer.manager,
                        'status': row.customer.status.name
                    })

            # Audit log
            audit_logger.log_api_call(
                customer_id="all",
                operation="list_accounts",
                resource_type="customer",
                action="read",
                result="success",
                details={'account_count': len(accounts)}
            )

            # Format response
            if response_format == ResponseFormat.JSON:
                return json.dumps(accounts, indent=2)
            else:
                return format_account_list_markdown(accounts)

        except Exception as e:
            error_msg = ErrorHandler.handle_error(e, context="list_accounts")
            return f"❌ Error listing accounts: {error_msg}"


def format_account_list_markdown(accounts: List[Dict]) -> str:
    """Format account list as markdown."""
    if not accounts:
        return "No accounts found."

    output = "# Google Ads Accounts\n\n"
    for account in accounts:
        output += f"## {account['name']}\n"
        output += f"- **Customer ID**: {account['id']}\n"
        output += f"- **Currency**: {account['currency_code']}\n"
        output += f"- **Timezone**: {account['time_zone']}\n"
        output += f"- **Status**: {account['status']}\n"
        if account.get('manager'):
            output += f"- **Manager Account**: Yes\n"
        output += "\n"

    output += f"**Total Accounts**: {len(accounts)}\n"

    return output


# ============================================================================
# Register Additional Tool Modules
# ============================================================================

# Import and register campaign management tools
try:
    from mcp_tools_campaigns import register_campaign_tools
    register_campaign_tools(mcp)
    logger.info("Campaign management tools registered (15 tools)")
except Exception as e:
    logger.warning(f"Failed to register campaign tools: {e}")

# Import and register ad group management tools
try:
    from mcp_tools_ad_groups import register_ad_group_tools
    register_ad_group_tools(mcp)
    logger.info("Ad group management tools registered (8 tools)")
except Exception as e:
    logger.warning(f"Failed to register ad group tools: {e}")

# Import and register keyword management tools
try:
    from mcp_tools_keywords import register_keyword_tools
    register_keyword_tools(mcp)
    logger.info("Keyword management tools registered (12 tools)")
except Exception as e:
    logger.warning(f"Failed to register keyword tools: {e}")

# Import and register ad management tools
try:
    from mcp_tools_ads import register_ad_tools
    register_ad_tools(mcp)
    logger.info("Ad management tools registered (8 tools)")
except Exception as e:
    logger.warning(f"Failed to register ad tools: {e}")

# Import and register bidding strategy management tools
try:
    from mcp_tools_bidding import register_bidding_tools
    register_bidding_tools(mcp)
    logger.info("Bidding strategy management tools registered (12 tools)")
except Exception as e:
    logger.warning(f"Failed to register bidding tools: {e}")

# Import and register automation and optimization tools
try:
    from mcp_tools_automation import register_automation_tools
    register_automation_tools(mcp)
    logger.info("Automation and optimization tools registered (10 tools)")
except Exception as e:
    logger.warning(f"Failed to register automation tools: {e}")

# Import and register audience and remarketing tools
try:
    from mcp_tools_audiences import register_audience_tools
    register_audience_tools(mcp)
    logger.info("Audience and remarketing tools registered (10 tools)")
except Exception as e:
    logger.warning(f"Failed to register audience tools: {e}")

# Import and register conversion tracking tools
try:
    from mcp_tools_conversions import register_conversion_tools
    register_conversion_tools(mcp)
    logger.info("Conversion tracking tools registered (10 tools)")
except Exception as e:
    logger.warning(f"Failed to register conversion tools: {e}")

# Import and register reporting and analytics tools
try:
    from mcp_tools_reporting import register_reporting_tools
    register_reporting_tools(mcp)
    logger.info("Reporting and analytics tools registered (6 tools)")
except Exception as e:
    logger.warning(f"Failed to register reporting tools: {e}")

# Import and register insights and recommendations tools
try:
    from mcp_tools_insights import register_insights_tools
    register_insights_tools(mcp)
    logger.info("Insights and recommendations tools registered (8 tools)")
except Exception as e:
    logger.warning(f"Failed to register insights tools: {e}")

# Import and register batch operation tools
try:
    from mcp_tools_batch import register_batch_tools
    register_batch_tools(mcp)
    logger.info("Batch operation tools registered (11 tools)")
except Exception as e:
    logger.warning(f"Failed to register batch tools: {e}")

# Import and register Shopping and Performance Max tools
try:
    from mcp_tools_shopping_pmax import register_shopping_pmax_tools
    register_shopping_pmax_tools(mcp)
    logger.info("Shopping and Performance Max tools registered (9 tools)")
except Exception as e:
    logger.warning(f"Failed to register shopping/PMax tools: {e}")

# Import and register ad extension tools
try:
    from mcp_tools_extensions import register_extension_tools
    register_extension_tools(mcp)
    logger.info("Ad extension tools registered (7 tools)")
except Exception as e:
    logger.warning(f"Failed to register extension tools: {e}")

# Import and register local/app campaign tools
try:
    from mcp_tools_local_app import register_local_app_tools
    register_local_app_tools(mcp)
    logger.info("Local and App campaign tools registered (6 tools)")
except Exception as e:
    logger.warning(f"Failed to register local/app tools: {e}")


# ============================================================================
# Entry Point
# ============================================================================

if __name__ == "__main__":
    logger.info("Starting Google Ads MCP Server v2.0")
    logger.info(f"Cache backend: {cache_backend.value}")
    logger.info(f"Features enabled: {config.config.features.model_dump()}")

    # Run the MCP server
    mcp.run()
