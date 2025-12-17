"""
Google Ads MCP Server

A comprehensive Model Context Protocol server for Google Ads API integration.
Provides tools for account analysis, campaign management, and optimization.

Requirements:
- google-ads>=25.0.0
- mcp>=1.1.0
- httpx
- pydantic>=2.0.0
"""

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List, Dict, Any, Literal
from enum import Enum
from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException
import json
import asyncio
from datetime import datetime, timedelta

# Constants
CHARACTER_LIMIT = 25000
DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 100

# Initialize MCP server
mcp = FastMCP("google_ads_mcp")

# Global client - will be initialized with credentials
_google_ads_client = None


# ============================================================================
# Configuration & Initialization
# ============================================================================

def initialize_client(
    developer_token: str,
    client_id: str,
    client_secret: str,
    refresh_token: str,
    login_customer_id: Optional[str] = None
) -> None:
    """
    Initialize the Google Ads API client with OAuth credentials.
    
    Args:
        developer_token: Your Google Ads API developer token
        client_id: OAuth2 client ID
        client_secret: OAuth2 client secret
        refresh_token: OAuth2 refresh token
        login_customer_id: Optional MCC account ID (without hyphens)
    """
    global _google_ads_client
    
    credentials = {
        "developer_token": developer_token,
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
        "use_proto_plus": True
    }
    
    if login_customer_id:
        credentials["login_customer_id"] = login_customer_id
    
    _google_ads_client = GoogleAdsClient.load_from_dict(credentials)


def get_client() -> GoogleAdsClient:
    """Get the initialized Google Ads client."""
    if _google_ads_client is None:
        raise RuntimeError(
            "Google Ads client not initialized. Call initialize_client() first with your credentials."
        )
    return _google_ads_client


# ============================================================================
# Enums and Response Formats
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


def truncate_response(response: str, message: str = "Response truncated. Use filters to reduce data.") -> str:
    """Truncate response if it exceeds CHARACTER_LIMIT."""
    if len(response) > CHARACTER_LIMIT:
        return response[:CHARACTER_LIMIT] + f"\n\n... {message}"
    return response


async def execute_query(
    client: GoogleAdsClient,
    customer_id: str,
    query: str
) -> List[Any]:
    """
    Execute a GAQL query and return results.
    
    Args:
        client: Google Ads client
        customer_id: Customer ID (without hyphens)
        query: GAQL query string
        
    Returns:
        List of row results
    """
    ga_service = client.get_service("GoogleAdsService")
    
    try:
        response = ga_service.search(customer_id=customer_id, query=query)
        return list(response)
    except GoogleAdsException as ex:
        error_messages = []
        for error in ex.failure.errors:
            error_messages.append(
                f"Error: {error.message} "
                f"(Field: {error.location.field_path_elements[0].field_name if error.location.field_path_elements else 'unknown'})"
            )
        raise RuntimeError(f"Google Ads API error: {'; '.join(error_messages)}")


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
    
    return output


def format_campaign_performance_markdown(campaigns: List[Dict]) -> str:
    """Format campaign performance data as markdown."""
    if not campaigns:
        return "No campaigns found matching the criteria."
    
    output = "# Campaign Performance Report\n\n"
    
    # Summary statistics
    total_cost = sum(c.get('cost', 0) for c in campaigns)
    total_clicks = sum(c.get('clicks', 0) for c in campaigns)
    total_impressions = sum(c.get('impressions', 0) for c in campaigns)
    total_conversions = sum(c.get('conversions', 0) for c in campaigns)
    
    output += "## Summary\n"
    output += f"- **Total Campaigns**: {len(campaigns)}\n"
    output += f"- **Total Cost**: ${total_cost:,.2f}\n"
    output += f"- **Total Clicks**: {total_clicks:,}\n"
    output += f"- **Total Impressions**: {total_impressions:,}\n"
    output += f"- **Total Conversions**: {total_conversions:.2f}\n"
    if total_cost > 0:
        output += f"- **Average CPC**: ${total_cost / total_clicks:.2f}\n" if total_clicks > 0 else ""
        output += f"- **Cost per Conversion**: ${total_cost / total_conversions:.2f}\n" if total_conversions > 0 else ""
    output += "\n## Campaign Details\n\n"
    
    for campaign in campaigns:
        output += f"### {campaign['name']} (ID: {campaign['id']})\n"
        output += f"- **Status**: {campaign['status']}\n"
        output += f"- **Cost**: ${campaign.get('cost', 0):,.2f}\n"
        output += f"- **Clicks**: {campaign.get('clicks', 0):,}\n"
        output += f"- **Impressions**: {campaign.get('impressions', 0):,}\n"
        output += f"- **CTR**: {format_percentage(campaign.get('ctr', 0))}\n"
        output += f"- **Avg CPC**: ${campaign.get('average_cpc', 0):.2f}\n"
        output += f"- **Conversions**: {campaign.get('conversions', 0):.2f}\n"
        output += f"- **Conversion Rate**: {format_percentage(campaign.get('conversion_rate', 0))}\n"
        if campaign.get('cost', 0) > 0 and campaign.get('conversions', 0) > 0:
            output += f"- **Cost per Conversion**: ${campaign['cost'] / campaign['conversions']:.2f}\n"
        output += "\n"
    
    return output


# ============================================================================
# Input Models
# ============================================================================

class InitializeInput(BaseModel):
    """Input for initializing Google Ads client."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    developer_token: str = Field(..., description="Your Google Ads API developer token", min_length=1)
    client_id: str = Field(..., description="OAuth2 client ID", min_length=1)
    client_secret: str = Field(..., description="OAuth2 client secret", min_length=1)
    refresh_token: str = Field(..., description="OAuth2 refresh token", min_length=1)
    login_customer_id: Optional[str] = Field(
        default=None,
        description="MCC account ID (without hyphens) if accessing client accounts. Example: '1234567890'"
    )


class ListAccountsInput(BaseModel):
    """Input for listing accessible accounts."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' for readable or 'json' for structured data"
    )


class CampaignPerformanceInput(BaseModel):
    """Input for getting campaign performance data."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    customer_id: str = Field(
        ...,
        description="Customer ID without hyphens (e.g., '1234567890')",
        min_length=1,
        pattern=r'^\d+$'
    )
    date_range: Optional[DateRange] = Field(
        default=DateRange.LAST_30_DAYS,
        description="Predefined date range for the report"
    )
    campaign_status: Optional[List[CampaignStatus]] = Field(
        default=None,
        description="Filter by campaign status (e.g., ['ENABLED', 'PAUSED']). If not specified, returns all statuses."
    )
    min_cost: Optional[float] = Field(
        default=None,
        description="Minimum cost threshold (filters campaigns with cost >= this value)",
        ge=0
    )
    limit: Optional[int] = Field(
        default=DEFAULT_PAGE_SIZE,
        description="Maximum number of campaigns to return",
        ge=1,
        le=MAX_PAGE_SIZE
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' for human-readable or 'json' for structured data"
    )


class KeywordPerformanceInput(BaseModel):
    """Input for getting keyword performance data."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    customer_id: str = Field(
        ...,
        description="Customer ID without hyphens",
        pattern=r'^\d+$'
    )
    campaign_id: Optional[str] = Field(
        default=None,
        description="Optional campaign ID to filter keywords"
    )
    date_range: Optional[DateRange] = Field(
        default=DateRange.LAST_30_DAYS,
        description="Date range for keyword data"
    )
    min_impressions: Optional[int] = Field(
        default=None,
        description="Filter keywords with impressions >= this value",
        ge=0
    )
    limit: Optional[int] = Field(
        default=DEFAULT_PAGE_SIZE,
        ge=1,
        le=MAX_PAGE_SIZE
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format"
    )


class SearchTermsInput(BaseModel):
    """Input for search terms report."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    customer_id: str = Field(..., description="Customer ID without hyphens", pattern=r'^\d+$')
    campaign_id: Optional[str] = Field(default=None, description="Optional campaign ID filter")
    date_range: DateRange = Field(default=DateRange.LAST_30_DAYS)
    min_impressions: Optional[int] = Field(default=10, ge=0)
    limit: int = Field(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE)
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN)


class AdGroupPerformanceInput(BaseModel):
    """Input for ad group performance."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    customer_id: str = Field(..., pattern=r'^\d+$')
    campaign_id: Optional[str] = Field(default=None)
    date_range: DateRange = Field(default=DateRange.LAST_30_DAYS)
    limit: int = Field(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE)
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN)


class RecommendationsInput(BaseModel):
    """Input for optimization recommendations."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    customer_id: str = Field(..., pattern=r'^\d+$')
    recommendation_types: Optional[List[str]] = Field(
        default=None,
        description="Filter by recommendation types (e.g., ['KEYWORD', 'TARGET_CPA_OPT'])"
    )
    limit: int = Field(default=20, ge=1, le=100)
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN)


class UpdateCampaignBudgetInput(BaseModel):
    """Input for updating campaign budget."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    customer_id: str = Field(..., pattern=r'^\d+$')
    campaign_id: str = Field(..., description="Campaign ID to update")
    budget_amount_micros: int = Field(
        ...,
        description="New budget amount in micros (e.g., 50000000 for $50)",
        ge=10000  # Minimum 0.01
    )


class UpdateCampaignStatusInput(BaseModel):
    """Input for pausing/enabling campaigns."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    customer_id: str = Field(..., pattern=r'^\d+$')
    campaign_id: str = Field(...)
    status: Literal["ENABLED", "PAUSED"] = Field(...)


class CustomQueryInput(BaseModel):
    """Input for custom GAQL queries."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    customer_id: str = Field(..., pattern=r'^\d+$')
    query: str = Field(
        ...,
        description="GAQL query (use Google Ads Query Builder: https://developers.google.com/google-ads/api/fields/latest/overview_query_builder)",
        min_length=1
    )
    response_format: ResponseFormat = Field(default=ResponseFormat.JSON)


# ============================================================================
# MCP Tools
# ============================================================================

@mcp.tool(
    name="google_ads_initialize",
    annotations={
        "title": "Initialize Google Ads Connection",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def google_ads_initialize(params: InitializeInput) -> str:
    """
    Initialize the Google Ads API connection with OAuth credentials.
    
    This must be called before using any other Google Ads tools. Provide your
    developer token, OAuth2 credentials, and optionally an MCC login customer ID
    if you're accessing client accounts.
    
    Args:
        params: Configuration containing:
            - developer_token: API developer token
            - client_id: OAuth2 client ID
            - client_secret: OAuth2 client secret
            - refresh_token: OAuth2 refresh token
            - login_customer_id: Optional MCC account ID
    
    Returns:
        Confirmation message with initialization status
    """
    try:
        initialize_client(
            developer_token=params.developer_token,
            client_id=params.client_id,
            client_secret=params.client_secret,
            refresh_token=params.refresh_token,
            login_customer_id=params.login_customer_id
        )
        
        message = "✓ Google Ads API client initialized successfully."
        if params.login_customer_id:
            message += f"\n✓ Using MCC account: {params.login_customer_id}"
        message += "\n\nYou can now use other Google Ads tools to access your account data."
        
        return message
    except Exception as e:
        return f"✗ Failed to initialize: {str(e)}\n\nPlease verify your credentials and try again."


@mcp.tool(
    name="google_ads_list_accounts",
    annotations={
        "title": "List Accessible Google Ads Accounts",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def google_ads_list_accounts(params: ListAccountsInput) -> str:
    """
    List all Google Ads accounts accessible with current credentials.
    
    Returns details about all accounts you have access to, including customer IDs,
    names, currency codes, and whether they are manager accounts.
    
    Args:
        params: Query parameters containing response format preference
    
    Returns:
        List of accessible accounts with their details
    """
    try:
        client = get_client()
        customer_service = client.get_service("CustomerService")
        
        # Get accessible customers
        accessible_customers = customer_service.list_accessible_customers()
        customer_ids = accessible_customers.resource_names
        
        accounts = []
        for resource_name in customer_ids:
            customer_id = resource_name.split('/')[-1]
            
            query = """
                SELECT
                    customer.id,
                    customer.descriptive_name,
                    customer.currency_code,
                    customer.time_zone,
                    customer.manager,
                    customer.status
                FROM customer
                WHERE customer.id = {customer_id}
            """.replace("{customer_id}", customer_id)
            
            try:
                rows = await execute_query(client, customer_id, query)
                if rows:
                    customer = rows[0].customer
                    accounts.append({
                        'id': str(customer.id),
                        'name': customer.descriptive_name,
                        'currency_code': customer.currency_code,
                        'time_zone': customer.time_zone,
                        'manager': customer.manager,
                        'status': customer.status.name
                    })
            except Exception as e:
                # Skip accounts we don't have access to
                continue
        
        if params.response_format == ResponseFormat.JSON:
            return json.dumps({"accounts": accounts, "count": len(accounts)}, indent=2)
        else:
            return format_account_list_markdown(accounts)
            
    except Exception as e:
        return f"Error listing accounts: {str(e)}"


@mcp.tool(
    name="google_ads_campaign_performance",
    annotations={
        "title": "Get Campaign Performance Metrics",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def google_ads_campaign_performance(params: CampaignPerformanceInput) -> str:
    """
    Get comprehensive performance metrics for campaigns.
    
    Retrieves key performance indicators including cost, clicks, impressions, CTR,
    conversions, and more for campaigns in the specified date range. Supports
    filtering by status and cost thresholds.
    
    Args:
        params: Query parameters including:
            - customer_id: Account to query
            - date_range: Time period (default: LAST_30_DAYS)
            - campaign_status: Filter by status (optional)
            - min_cost: Minimum cost filter (optional)
            - limit: Max results to return
            - response_format: Output format
    
    Returns:
        Campaign performance data with metrics and analysis
    """
    try:
        client = get_client()
        
        # Build GAQL query
        query = f"""
            SELECT
                campaign.id,
                campaign.name,
                campaign.status,
                metrics.cost_micros,
                metrics.clicks,
                metrics.impressions,
                metrics.ctr,
                metrics.average_cpc,
                metrics.conversions,
                metrics.conversions_value,
                metrics.cost_per_conversion,
                metrics.conversion_rate
            FROM campaign
            WHERE segments.date DURING {params.date_range.value}
        """
        
        # Add status filter if specified
        if params.campaign_status:
            status_filter = " OR ".join([f"campaign.status = '{s.value}'" for s in params.campaign_status])
            query += f" AND ({status_filter})"
        
        query += f" ORDER BY metrics.cost_micros DESC LIMIT {params.limit}"
        
        rows = await execute_query(client, params.customer_id, query)
        
        campaigns = []
        for row in rows:
            cost = format_micros(row.metrics.cost_micros)
            
            # Apply min_cost filter
            if params.min_cost is not None and cost < params.min_cost:
                continue
            
            campaigns.append({
                'id': str(row.campaign.id),
                'name': row.campaign.name,
                'status': row.campaign.status.name,
                'cost': cost,
                'clicks': row.metrics.clicks,
                'impressions': row.metrics.impressions,
                'ctr': row.metrics.ctr,
                'average_cpc': format_micros(row.metrics.average_cpc),
                'conversions': row.metrics.conversions,
                'conversions_value': row.metrics.conversions_value,
                'conversion_rate': row.metrics.conversion_rate,
                'cost_per_conversion': format_micros(row.metrics.cost_per_conversion) if row.metrics.conversions > 0 else 0
            })
        
        if params.response_format == ResponseFormat.JSON:
            result = {
                'campaigns': campaigns,
                'count': len(campaigns),
                'date_range': params.date_range.value,
                'customer_id': params.customer_id
            }
            return json.dumps(result, indent=2)
        else:
            return truncate_response(format_campaign_performance_markdown(campaigns))
            
    except Exception as e:
        return f"Error retrieving campaign performance: {str(e)}"


@mcp.tool(
    name="google_ads_keyword_performance",
    annotations={
        "title": "Get Keyword Performance Analysis",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def google_ads_keyword_performance(params: KeywordPerformanceInput) -> str:
    """
    Analyze keyword-level performance metrics.
    
    Get detailed performance data for keywords including quality scores, average
    positions, costs, and conversion metrics. Helps identify high and low performers.
    
    Args:
        params: Query parameters for keyword analysis
    
    Returns:
        Keyword performance metrics with quality and position data
    """
    try:
        client = get_client()
        
        query = f"""
            SELECT
                campaign.id,
                campaign.name,
                ad_group.id,
                ad_group.name,
                ad_group_criterion.keyword.text,
                ad_group_criterion.keyword.match_type,
                ad_group_criterion.quality_info.quality_score,
                metrics.cost_micros,
                metrics.clicks,
                metrics.impressions,
                metrics.ctr,
                metrics.average_cpc,
                metrics.conversions,
                metrics.cost_per_conversion,
                metrics.average_position
            FROM keyword_view
            WHERE segments.date DURING {params.date_range.value}
        """
        
        if params.campaign_id:
            query += f" AND campaign.id = {params.campaign_id}"
        
        if params.min_impressions:
            query += f" AND metrics.impressions >= {params.min_impressions}"
        
        query += f" ORDER BY metrics.cost_micros DESC LIMIT {params.limit}"
        
        rows = await execute_query(client, params.customer_id, query)
        
        keywords = []
        for row in rows:
            keywords.append({
                'campaign_name': row.campaign.name,
                'ad_group_name': row.ad_group.name,
                'keyword': row.ad_group_criterion.keyword.text,
                'match_type': row.ad_group_criterion.keyword.match_type.name,
                'quality_score': row.ad_group_criterion.quality_info.quality_score,
                'cost': format_micros(row.metrics.cost_micros),
                'clicks': row.metrics.clicks,
                'impressions': row.metrics.impressions,
                'ctr': row.metrics.ctr,
                'average_cpc': format_micros(row.metrics.average_cpc),
                'conversions': row.metrics.conversions,
                'average_position': row.metrics.average_position
            })
        
        if params.response_format == ResponseFormat.JSON:
            return json.dumps({'keywords': keywords, 'count': len(keywords)}, indent=2)
        else:
            output = "# Keyword Performance Report\n\n"
            output += f"**Total Keywords**: {len(keywords)}\n\n"
            
            for kw in keywords:
                output += f"## {kw['keyword']} ({kw['match_type']})\n"
                output += f"- Campaign: {kw['campaign_name']}\n"
                output += f"- Ad Group: {kw['ad_group_name']}\n"
                output += f"- Quality Score: {kw['quality_score']}/10\n"
                output += f"- Cost: ${kw['cost']:,.2f}\n"
                output += f"- Clicks: {kw['clicks']:,} | Impressions: {kw['impressions']:,}\n"
                output += f"- CTR: {format_percentage(kw['ctr'])}\n"
                output += f"- Avg CPC: ${kw['average_cpc']:.2f}\n"
                output += f"- Conversions: {kw['conversions']:.2f}\n"
                output += f"- Avg Position: {kw['average_position']:.2f}\n\n"
            
            return truncate_response(output)
            
    except Exception as e:
        return f"Error retrieving keyword performance: {str(e)}"


@mcp.tool(
    name="google_ads_search_terms",
    annotations={
        "title": "Get Search Terms Report",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def google_ads_search_terms(params: SearchTermsInput) -> str:
    """
    Get search terms that triggered your ads.
    
    Discover actual search queries that matched your keywords. Essential for finding
    new keyword opportunities and negative keywords to exclude.
    
    Args:
        params: Search terms query parameters
    
    Returns:
        Search terms with performance metrics and matched keywords
    """
    try:
        client = get_client()
        
        query = f"""
            SELECT
                campaign.name,
                ad_group.name,
                segments.search_term_match_type,
                search_term_view.search_term,
                ad_group_criterion.keyword.text,
                metrics.impressions,
                metrics.clicks,
                metrics.ctr,
                metrics.cost_micros,
                metrics.conversions
            FROM search_term_view
            WHERE segments.date DURING {params.date_range.value}
              AND metrics.impressions >= {params.min_impressions or 0}
        """
        
        if params.campaign_id:
            query += f" AND campaign.id = {params.campaign_id}"
        
        query += f" ORDER BY metrics.impressions DESC LIMIT {params.limit}"
        
        rows = await execute_query(client, params.customer_id, query)
        
        search_terms = []
        for row in rows:
            search_terms.append({
                'search_term': row.search_term_view.search_term,
                'matched_keyword': row.ad_group_criterion.keyword.text,
                'match_type': row.segments.search_term_match_type.name,
                'campaign': row.campaign.name,
                'ad_group': row.ad_group.name,
                'impressions': row.metrics.impressions,
                'clicks': row.metrics.clicks,
                'ctr': row.metrics.ctr,
                'cost': format_micros(row.metrics.cost_micros),
                'conversions': row.metrics.conversions
            })
        
        if params.response_format == ResponseFormat.JSON:
            return json.dumps({'search_terms': search_terms, 'count': len(search_terms)}, indent=2)
        else:
            output = "# Search Terms Report\n\n"
            output += f"**Total Search Terms**: {len(search_terms)}\n\n"
            output += "These are actual queries that triggered your ads. Look for:\n"
            output += "- High-performing terms to add as exact match keywords\n"
            output += "- Irrelevant terms to add as negative keywords\n\n"
            
            for term in search_terms[:30]:  # Limit display
                output += f"## \"{term['search_term']}\"\n"
                output += f"- **Matched Keyword**: {term['matched_keyword']} ({term['match_type']})\n"
                output += f"- **Campaign**: {term['campaign']}\n"
                output += f"- **Impressions**: {term['impressions']:,} | **Clicks**: {term['clicks']}\n"
                output += f"- **CTR**: {format_percentage(term['ctr'])} | **Cost**: ${term['cost']:.2f}\n"
                output += f"- **Conversions**: {term['conversions']:.2f}\n\n"
            
            if len(search_terms) > 30:
                output += f"\n... and {len(search_terms) - 30} more search terms. Use JSON format or filters for full data.\n"
            
            return truncate_response(output)
            
    except Exception as e:
        return f"Error retrieving search terms: {str(e)}"


@mcp.tool(
    name="google_ads_ad_group_performance",
    annotations={
        "title": "Get Ad Group Performance",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def google_ads_ad_group_performance(params: AdGroupPerformanceInput) -> str:
    """
    Analyze performance at the ad group level.
    
    Get metrics for ad groups to identify which groups are performing well and
    which need optimization.
    
    Args:
        params: Ad group query parameters
    
    Returns:
        Ad group performance metrics
    """
    try:
        client = get_client()
        
        query = f"""
            SELECT
                campaign.name,
                ad_group.id,
                ad_group.name,
                ad_group.status,
                metrics.cost_micros,
                metrics.clicks,
                metrics.impressions,
                metrics.ctr,
                metrics.average_cpc,
                metrics.conversions,
                metrics.conversion_rate
            FROM ad_group
            WHERE segments.date DURING {params.date_range.value}
        """
        
        if params.campaign_id:
            query += f" AND campaign.id = {params.campaign_id}"
        
        query += f" ORDER BY metrics.cost_micros DESC LIMIT {params.limit}"
        
        rows = await execute_query(client, params.customer_id, query)
        
        ad_groups = []
        for row in rows:
            ad_groups.append({
                'campaign': row.campaign.name,
                'id': str(row.ad_group.id),
                'name': row.ad_group.name,
                'status': row.ad_group.status.name,
                'cost': format_micros(row.metrics.cost_micros),
                'clicks': row.metrics.clicks,
                'impressions': row.metrics.impressions,
                'ctr': row.metrics.ctr,
                'average_cpc': format_micros(row.metrics.average_cpc),
                'conversions': row.metrics.conversions,
                'conversion_rate': row.metrics.conversion_rate
            })
        
        if params.response_format == ResponseFormat.JSON:
            return json.dumps({'ad_groups': ad_groups, 'count': len(ad_groups)}, indent=2)
        else:
            output = "# Ad Group Performance\n\n"
            for ag in ad_groups:
                output += f"## {ag['name']} ({ag['status']})\n"
                output += f"- Campaign: {ag['campaign']}\n"
                output += f"- Cost: ${ag['cost']:,.2f}\n"
                output += f"- Clicks: {ag['clicks']:,} | Impressions: {ag['impressions']:,}\n"
                output += f"- CTR: {format_percentage(ag['ctr'])}\n"
                output += f"- Avg CPC: ${ag['average_cpc']:.2f}\n"
                output += f"- Conversions: {ag['conversions']:.2f} ({format_percentage(ag['conversion_rate'])})\n\n"
            
            return truncate_response(output)
            
    except Exception as e:
        return f"Error retrieving ad group performance: {str(e)}"


@mcp.tool(
    name="google_ads_recommendations",
    annotations={
        "title": "Get Google Ads Optimization Recommendations",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def google_ads_recommendations(params: RecommendationsInput) -> str:
    """
    Get AI-powered optimization recommendations from Google.
    
    Retrieve Google's automated recommendations for improving campaign performance,
    including keyword suggestions, bid adjustments, and budget recommendations.
    
    Args:
        params: Recommendations query parameters
    
    Returns:
        List of actionable optimization recommendations
    """
    try:
        client = get_client()
        
        query = """
            SELECT
                recommendation.type,
                recommendation.campaign,
                recommendation.ad_group,
                recommendation.resource_name,
                recommendation.impact
            FROM recommendation
        """
        
        if params.recommendation_types:
            type_filter = " OR ".join([f"recommendation.type = '{t}'" for t in params.recommendation_types])
            query += f" WHERE ({type_filter})"
        
        query += f" LIMIT {params.limit}"
        
        rows = await execute_query(client, params.customer_id, query)
        
        recommendations = []
        for row in rows:
            rec = row.recommendation
            recommendations.append({
                'type': rec.type_.name if hasattr(rec.type_, 'name') else str(rec.type_),
                'resource_name': rec.resource_name,
                'impact': str(rec.impact) if hasattr(rec, 'impact') else 'N/A'
            })
        
        if params.response_format == ResponseFormat.JSON:
            return json.dumps({'recommendations': recommendations, 'count': len(recommendations)}, indent=2)
        else:
            output = "# Google Ads Recommendations\n\n"
            output += f"**Total Recommendations**: {len(recommendations)}\n\n"
            
            if not recommendations:
                output += "No recommendations available at this time.\n"
            else:
                for i, rec in enumerate(recommendations, 1):
                    output += f"{i}. **{rec['type']}**\n"
                    output += f"   - Impact: {rec['impact']}\n"
                    output += f"   - Resource: {rec['resource_name']}\n\n"
            
            return output
            
    except Exception as e:
        return f"Error retrieving recommendations: {str(e)}"


@mcp.tool(
    name="google_ads_update_campaign_budget",
    annotations={
        "title": "Update Campaign Budget",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True
    }
)
async def google_ads_update_campaign_budget(params: UpdateCampaignBudgetInput) -> str:
    """
    Update the daily budget for a campaign.
    
    Modify campaign budget allocation. Budget is specified in micros (multiply
    your dollar amount by 1,000,000).
    
    Args:
        params: Budget update parameters including campaign ID and new amount
    
    Returns:
        Confirmation of budget update
    """
    try:
        client = get_client()
        campaign_service = client.get_service("CampaignService")
        campaign_budget_service = client.get_service("CampaignBudgetService")
        
        # First get the campaign to find its budget
        query = f"""
            SELECT campaign.id, campaign.name, campaign.campaign_budget
            FROM campaign
            WHERE campaign.id = {params.campaign_id}
        """
        
        rows = await execute_query(client, params.customer_id, query)
        if not rows:
            return f"Campaign {params.campaign_id} not found."
        
        budget_resource = rows[0].campaign.campaign_budget
        
        # Update the budget
        budget_operation = client.get_type("CampaignBudgetOperation")
        budget = budget_operation.update
        budget.resource_name = budget_resource
        budget.amount_micros = params.budget_amount_micros
        
        budget_operation.update_mask = client.get_type("FieldMask")
        budget_operation.update_mask.paths.append("amount_micros")
        
        response = campaign_budget_service.mutate_campaign_budgets(
            customer_id=params.customer_id,
            operations=[budget_operation]
        )
        
        budget_amount = format_micros(params.budget_amount_micros)
        return f"✓ Successfully updated budget for campaign {params.campaign_id} to ${budget_amount:.2f}/day"
        
    except Exception as e:
        return f"Error updating campaign budget: {str(e)}"


@mcp.tool(
    name="google_ads_update_campaign_status",
    annotations={
        "title": "Pause or Enable Campaign",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def google_ads_update_campaign_status(params: UpdateCampaignStatusInput) -> str:
    """
    Pause or enable a campaign.
    
    Change campaign status to control when ads are shown.
    
    Args:
        params: Status update parameters
    
    Returns:
        Confirmation of status change
    """
    try:
        client = get_client()
        campaign_service = client.get_service("CampaignService")
        
        campaign_operation = client.get_type("CampaignOperation")
        campaign = campaign_operation.update
        campaign.resource_name = campaign_service.campaign_path(params.customer_id, params.campaign_id)
        
        # Set status
        if params.status == "ENABLED":
            campaign.status = client.enums.CampaignStatusEnum.ENABLED
        else:
            campaign.status = client.enums.CampaignStatusEnum.PAUSED
        
        campaign_operation.update_mask = client.get_type("FieldMask")
        campaign_operation.update_mask.paths.append("status")
        
        response = campaign_service.mutate_campaigns(
            customer_id=params.customer_id,
            operations=[campaign_operation]
        )
        
        return f"✓ Successfully {params.status.lower()} campaign {params.campaign_id}"
        
    except Exception as e:
        return f"Error updating campaign status: {str(e)}"


@mcp.tool(
    name="google_ads_custom_query",
    annotations={
        "title": "Execute Custom GAQL Query",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def google_ads_custom_query(params: CustomQueryInput) -> str:
    """
    Execute a custom Google Ads Query Language (GAQL) query.
    
    For advanced users who want to write their own GAQL queries. Use the
    Google Ads Query Builder to construct queries:
    https://developers.google.com/google-ads/api/fields/latest/overview_query_builder
    
    Args:
        params: Custom query parameters including GAQL query string
    
    Returns:
        Query results in specified format
    """
    try:
        client = get_client()
        rows = await execute_query(client, params.customer_id, params.query)
        
        # Convert rows to list of dicts
        results = []
        for row in rows:
            row_dict = {}
            for field in row._pb:
                if field:
                    row_dict[field] = str(getattr(row, field))
            results.append(row_dict)
        
        if params.response_format == ResponseFormat.JSON:
            return json.dumps({'results': results, 'count': len(results)}, indent=2)
        else:
            output = "# Custom Query Results\n\n"
            output += f"**Query**: {params.query}\n\n"
            output += f"**Result Count**: {len(results)}\n\n"
            output += json.dumps(results, indent=2)
            return truncate_response(output)
            
    except Exception as e:
        return f"Error executing custom query: {str(e)}\n\nTip: Use the Query Builder to validate your GAQL syntax."


# ============================================================================
# Server Entry Point
# ============================================================================

if __name__ == "__main__":
    # Run the MCP server
    mcp.run()
