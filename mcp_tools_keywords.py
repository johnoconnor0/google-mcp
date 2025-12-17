"""
MCP Tools for Keyword Management

Keyword management tools for Google Ads MCP Server.
"""

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum
import json

from auth_manager import get_auth_manager
from error_handler import ErrorHandler
from logger import performance_logger, audit_logger, get_logger
from cache_manager import get_cache_manager, ResourceType
from keyword_manager import (
    KeywordManager, KeywordConfig, KeywordMatchType, KeywordStatus
)

logger = get_logger(__name__)


def register_keyword_tools(mcp: FastMCP):
    """Register keyword management tools with MCP server."""

    # ============================================================================
    # Keyword Addition
    # ============================================================================

    @mcp.tool()
    def google_ads_add_keywords(
        customer_id: str,
        ad_group_id: str,
        keywords: List[Dict[str, Any]],
        cpc_bid: Optional[float] = None
    ) -> str:
        """
        Add keywords to an ad group.

        Args:
            customer_id: Customer ID (without hyphens)
            ad_group_id: Ad group ID
            keywords: List of keyword dicts with 'text' and 'match_type' (EXACT, PHRASE, BROAD)
            cpc_bid: Optional default CPC bid for all keywords in currency units

        Returns:
            Success message with keyword count

        Example:
            keywords = [
                {"text": "running shoes", "match_type": "PHRASE"},
                {"text": "nike shoes", "match_type": "EXACT"},
                {"text": "athletic footwear", "match_type": "BROAD"}
            ]
        """
        with performance_logger.track_operation('add_keywords', customer_id=customer_id):
            try:
                client = get_auth_manager().get_client()
                keyword_manager = KeywordManager(client)

                # Convert to KeywordConfig objects
                cpc_bid_micros = int(cpc_bid * 1_000_000) if cpc_bid else None

                keyword_configs = [
                    KeywordConfig(
                        text=kw['text'],
                        match_type=KeywordMatchType[kw['match_type'].upper()],
                        ad_group_id=ad_group_id,
                        cpc_bid_micros=cpc_bid_micros,
                        status=KeywordStatus[kw.get('status', 'ENABLED').upper()]
                    )
                    for kw in keywords
                ]

                # Add keywords
                result = keyword_manager.add_keywords(customer_id, keyword_configs)

                # Audit log
                audit_logger.log_api_call(
                    customer_id=customer_id,
                    operation="add_keywords",
                    resource_type="keyword",
                    action="create",
                    result="success",
                    details={
                        'ad_group_id': ad_group_id,
                        'keyword_count': len(keywords),
                        'cpc_bid': cpc_bid
                    }
                )

                # Invalidate cache
                get_cache_manager().invalidate(customer_id, ResourceType.KEYWORD)

                output = f"✅ Keywords added successfully!\n\n"
                output += f"**Keywords Added**: {result['keywords_added']}\n"
                output += f"**Ad Group ID**: {ad_group_id}\n"

                if cpc_bid:
                    output += f"**Default CPC Bid**: ${cpc_bid:.2f}\n"

                output += "\n**Added Keywords**:\n"
                for kw in keywords[:10]:  # Show first 10
                    output += f"- {kw['text']} ({kw['match_type']})\n"

                if len(keywords) > 10:
                    output += f"... and {len(keywords) - 10} more\n"

                return output

            except Exception as e:
                error_msg = ErrorHandler.handle_error(e, context="add_keywords")
                return f"❌ Failed to add keywords: {error_msg}"

    @mcp.tool()
    def google_ads_add_negative_keywords(
        customer_id: str,
        ad_group_id: str,
        keywords: List[Dict[str, str]]
    ) -> str:
        """
        Add negative keywords to an ad group.

        Args:
            customer_id: Customer ID (without hyphens)
            ad_group_id: Ad group ID
            keywords: List of keyword dicts with 'text' and 'match_type'

        Returns:
            Success message

        Example:
            keywords = [
                {"text": "cheap", "match_type": "BROAD"},
                {"text": "free", "match_type": "BROAD"}
            ]
        """
        with performance_logger.track_operation('add_negative_keywords', customer_id=customer_id):
            try:
                client = get_auth_manager().get_client()
                keyword_manager = KeywordManager(client)

                result = keyword_manager.add_negative_keywords(
                    customer_id,
                    ad_group_id,
                    keywords
                )

                # Audit log
                audit_logger.log_api_call(
                    customer_id=customer_id,
                    operation="add_negative_keywords",
                    resource_type="keyword",
                    action="create",
                    result="success",
                    details={
                        'ad_group_id': ad_group_id,
                        'negative_keyword_count': len(keywords)
                    }
                )

                # Invalidate cache
                get_cache_manager().invalidate(customer_id, ResourceType.KEYWORD)

                output = f"✅ Negative keywords added successfully!\n\n"
                output += f"**Negative Keywords Added**: {result['negative_keywords_added']}\n\n"

                output += "**Added Negative Keywords**:\n"
                for kw in keywords[:10]:
                    output += f"- {kw['text']} ({kw['match_type']})\n"

                if len(keywords) > 10:
                    output += f"... and {len(keywords) - 10} more\n"

                output += "\nThese keywords will prevent your ads from showing when searched."

                return output

            except Exception as e:
                error_msg = ErrorHandler.handle_error(e, context="add_negative_keywords")
                return f"❌ Failed to add negative keywords: {error_msg}"

    # ============================================================================
    # Keyword Updates
    # ============================================================================

    @mcp.tool()
    def google_ads_update_keyword_bid(
        customer_id: str,
        ad_group_id: str,
        criterion_id: str,
        cpc_bid: float
    ) -> str:
        """
        Update keyword CPC bid.

        Args:
            customer_id: Customer ID (without hyphens)
            ad_group_id: Ad group ID
            criterion_id: Keyword criterion ID
            cpc_bid: New CPC bid in currency units (e.g., 1.50 for $1.50)

        Returns:
            Success message
        """
        with performance_logger.track_operation('update_keyword_bid', customer_id=customer_id):
            try:
                client = get_auth_manager().get_client()
                keyword_manager = KeywordManager(client)

                cpc_bid_micros = int(cpc_bid * 1_000_000)

                result = keyword_manager.update_keyword_bid(
                    customer_id,
                    ad_group_id,
                    criterion_id,
                    cpc_bid_micros
                )

                # Audit log
                audit_logger.log_api_call(
                    customer_id=customer_id,
                    operation="update_keyword_bid",
                    resource_type="keyword",
                    resource_id=criterion_id,
                    action="update",
                    result="success",
                    details={'new_cpc_bid': cpc_bid}
                )

                # Invalidate cache
                get_cache_manager().invalidate(customer_id, ResourceType.KEYWORD)

                return (
                    f"✅ Keyword bid updated successfully!\n\n"
                    f"**Criterion ID**: {criterion_id}\n"
                    f"**New CPC Bid**: ${result['new_cpc_bid']:.2f}\n\n"
                    f"The new bid will take effect immediately."
                )

            except Exception as e:
                error_msg = ErrorHandler.handle_error(e, context="update_keyword_bid")
                return f"❌ Failed to update keyword bid: {error_msg}"

    @mcp.tool()
    def google_ads_update_keyword_status(
        customer_id: str,
        ad_group_id: str,
        criterion_id: str,
        status: str
    ) -> str:
        """
        Update keyword status (enable, pause, or remove).

        Args:
            customer_id: Customer ID (without hyphens)
            ad_group_id: Ad group ID
            criterion_id: Keyword criterion ID
            status: New status (ENABLED, PAUSED, or REMOVED)

        Returns:
            Success message
        """
        with performance_logger.track_operation('update_keyword_status', customer_id=customer_id):
            try:
                client = get_auth_manager().get_client()
                keyword_manager = KeywordManager(client)

                status_upper = status.upper()
                result = keyword_manager.update_keyword_status(
                    customer_id,
                    ad_group_id,
                    criterion_id,
                    KeywordStatus[status_upper]
                )

                # Audit log
                audit_logger.log_api_call(
                    customer_id=customer_id,
                    operation="update_keyword_status",
                    resource_type="keyword",
                    resource_id=criterion_id,
                    action="update",
                    result="success",
                    details={'new_status': status_upper}
                )

                # Invalidate cache
                get_cache_manager().invalidate(customer_id, ResourceType.KEYWORD)

                status_messages = {
                    "ENABLED": "Keyword is now active and will trigger ads.",
                    "PAUSED": "Keyword is now paused and will not trigger ads.",
                    "REMOVED": "Keyword has been removed."
                }

                return (
                    f"✅ Keyword status updated to {status_upper}\n\n"
                    f"**Criterion ID**: {criterion_id}\n\n"
                    f"{status_messages.get(status_upper, 'Status updated successfully.')}"
                )

            except Exception as e:
                error_msg = ErrorHandler.handle_error(e, context="update_keyword_status")
                return f"❌ Failed to update keyword status: {error_msg}"

    # ============================================================================
    # Keyword Information
    # ============================================================================

    @mcp.tool()
    def google_ads_get_keyword_performance(
        customer_id: str,
        ad_group_id: Optional[str] = None,
        date_range: str = "LAST_30_DAYS"
    ) -> str:
        """
        Get keyword performance metrics.

        Args:
            customer_id: Customer ID (without hyphens)
            ad_group_id: Optional ad group ID to filter by
            date_range: Date range (TODAY, YESTERDAY, LAST_7_DAYS, LAST_30_DAYS, etc.)

        Returns:
            Keyword performance report
        """
        with performance_logger.track_operation('get_keyword_performance', customer_id=customer_id):
            try:
                client = get_auth_manager().get_client()
                keyword_manager = KeywordManager(client)

                keywords = keyword_manager.get_keyword_performance(
                    customer_id,
                    ad_group_id=ad_group_id,
                    date_range=date_range
                )

                if not keywords:
                    return "No keyword data found for the specified criteria."

                output = f"# Keyword Performance ({date_range})\n\n"
                output += f"**Total Keywords**: {len(keywords)}\n\n"

                # Show top 20 by cost
                for kw in keywords[:20]:
                    output += f"## {kw['keyword_text']} ({kw['match_type']})\n"
                    output += f"- **Status**: {kw['status']}\n"
                    output += f"- **Campaign**: {kw['campaign']['name']}\n"
                    output += f"- **Ad Group**: {kw['ad_group']['name']}\n"

                    if kw['cpc_bid']:
                        output += f"- **CPC Bid**: ${kw['cpc_bid']:.2f}\n"

                    if kw['quality_score']:
                        output += f"- **Quality Score**: {kw['quality_score']}/10\n"

                    metrics = kw['metrics']
                    output += f"- **Cost**: ${metrics['cost']:,.2f}\n"
                    output += f"- **Clicks**: {metrics['clicks']:,}\n"
                    output += f"- **Impressions**: {metrics['impressions']:,}\n"
                    output += f"- **CTR**: {metrics['ctr']:.2f}%\n"
                    output += f"- **Avg CPC**: ${metrics['average_cpc']:.2f}\n"
                    output += f"- **Conversions**: {metrics['conversions']:.2f}\n"

                    if metrics['cost_per_conversion'] > 0:
                        output += f"- **Cost/Conv**: ${metrics['cost_per_conversion']:.2f}\n"

                    output += "\n"

                if len(keywords) > 20:
                    output += f"... and {len(keywords) - 20} more keywords\n"

                return output

            except Exception as e:
                error_msg = ErrorHandler.handle_error(e, context="get_keyword_performance")
                return f"❌ Failed to get keyword performance: {error_msg}"

    @mcp.tool()
    def google_ads_list_keywords(
        customer_id: str,
        ad_group_id: str
    ) -> str:
        """
        List all keywords in an ad group.

        Args:
            customer_id: Customer ID (without hyphens)
            ad_group_id: Ad group ID

        Returns:
            List of keywords
        """
        with performance_logger.track_operation('list_keywords', customer_id=customer_id):
            try:
                client = get_auth_manager().get_client()
                keyword_manager = KeywordManager(client)

                keywords = keyword_manager.list_keywords(customer_id, ad_group_id)

                if not keywords:
                    return f"No keywords found in ad group {ad_group_id}"

                # Separate positive and negative keywords
                positive_kws = [kw for kw in keywords if not kw['negative']]
                negative_kws = [kw for kw in keywords if kw['negative']]

                output = f"# Keywords in Ad Group {ad_group_id}\n\n"

                if positive_kws:
                    output += f"## Positive Keywords ({len(positive_kws)})\n\n"
                    for kw in positive_kws:
                        output += f"- **{kw['keyword_text']}** ({kw['match_type']})\n"
                        output += f"  - Status: {kw['status']}\n"
                        if kw['cpc_bid']:
                            output += f"  - CPC Bid: ${kw['cpc_bid']:.2f}\n"
                        output += f"  - ID: {kw['criterion_id']}\n\n"

                if negative_kws:
                    output += f"## Negative Keywords ({len(negative_kws)})\n\n"
                    for kw in negative_kws:
                        output += f"- **{kw['keyword_text']}** ({kw['match_type']})\n"
                        output += f"  - ID: {kw['criterion_id']}\n\n"

                return output

            except Exception as e:
                error_msg = ErrorHandler.handle_error(e, context="list_keywords")
                return f"❌ Failed to list keywords: {error_msg}"

    @mcp.tool()
    def google_ads_get_keyword_quality_score(
        customer_id: str,
        ad_group_id: str,
        criterion_id: str
    ) -> str:
        """
        Get detailed quality score information for a keyword.

        Args:
            customer_id: Customer ID (without hyphens)
            ad_group_id: Ad group ID
            criterion_id: Keyword criterion ID

        Returns:
            Quality score details
        """
        with performance_logger.track_operation('get_keyword_quality_score', customer_id=customer_id):
            try:
                client = get_auth_manager().get_client()
                keyword_manager = KeywordManager(client)

                quality_data = keyword_manager.get_keyword_quality_score(
                    customer_id,
                    ad_group_id,
                    criterion_id
                )

                if not quality_data:
                    return f"❌ Keyword {criterion_id} not found"

                output = f"# Quality Score: {quality_data['keyword_text']}\n\n"
                output += f"**Match Type**: {quality_data['match_type']}\n\n"

                if quality_data['quality_score']:
                    output += f"## Overall Quality Score: {quality_data['quality_score']}/10\n\n"
                else:
                    output += "## Overall Quality Score: Not yet available\n\n"

                output += "## Quality Score Components\n\n"
                output += f"- **Expected CTR**: {quality_data['expected_ctr']}\n"
                output += f"- **Ad Relevance (Creative Quality)**: {quality_data['creative_quality']}\n"
                output += f"- **Landing Page Experience**: {quality_data['landing_page_experience']}\n\n"

                output += "### What This Means\n\n"
                output += "Quality Score is rated on a scale of 1-10:\n"
                output += "- 7-10: Above Average\n"
                output += "- 4-6: Average\n"
                output += "- 1-3: Below Average\n\n"

                output += "Each component is rated as:\n"
                output += "- ABOVE_AVERAGE: Better than most advertisers\n"
                output += "- AVERAGE: Similar to most advertisers\n"
                output += "- BELOW_AVERAGE: Lower than most advertisers\n"

                return output

            except Exception as e:
                error_msg = ErrorHandler.handle_error(e, context="get_keyword_quality_score")
                return f"❌ Failed to get quality score: {error_msg}"

    # ============================================================================
    # Search Terms
    # ============================================================================

    @mcp.tool()
    def google_ads_get_search_terms_for_keyword(
        customer_id: str,
        ad_group_id: str,
        criterion_id: Optional[str] = None,
        date_range: str = "LAST_30_DAYS"
    ) -> str:
        """
        Get search terms that triggered ads for keywords in an ad group.

        Args:
            customer_id: Customer ID (without hyphens)
            ad_group_id: Ad group ID
            criterion_id: Optional specific keyword criterion ID
            date_range: Date range (TODAY, YESTERDAY, LAST_7_DAYS, LAST_30_DAYS, etc.)

        Returns:
            Search terms report with performance data
        """
        with performance_logger.track_operation('get_search_terms', customer_id=customer_id):
            try:
                client = get_auth_manager().get_client()
                keyword_manager = KeywordManager(client)

                search_terms = keyword_manager.get_search_terms_for_keyword(
                    customer_id,
                    ad_group_id,
                    criterion_id=criterion_id,
                    date_range=date_range
                )

                if not search_terms:
                    return "No search term data found for the specified criteria."

                output = f"# Search Terms Report ({date_range})\n\n"
                output += f"**Total Search Terms**: {len(search_terms)}\n\n"

                # Show top 30 by impressions
                for st in search_terms[:30]:
                    output += f"## \"{st['search_term']}\"\n"
                    output += f"- **Triggered By Keyword**: {st['keyword_text']}\n"
                    output += f"- **Status**: {st['status']}\n"
                    output += f"- **Impressions**: {st['impressions']:,}\n"
                    output += f"- **Clicks**: {st['clicks']:,}\n"
                    output += f"- **CTR**: {st['ctr']:.2f}%\n"
                    output += f"- **Cost**: ${st['cost']:,.2f}\n"
                    output += f"- **Conversions**: {st['conversions']:.2f}\n\n"

                if len(search_terms) > 30:
                    output += f"... and {len(search_terms) - 30} more search terms\n\n"

                output += "**Tip**: Review search terms to identify:\n"
                output += "- New keyword opportunities (high-performing terms to add as keywords)\n"
                output += "- Negative keywords (irrelevant terms to exclude)\n"

                return output

            except Exception as e:
                error_msg = ErrorHandler.handle_error(e, context="get_search_terms")
                return f"❌ Failed to get search terms: {error_msg}"

    # ============================================================================
    # Bulk Operations
    # ============================================================================

    @mcp.tool()
    def google_ads_bulk_add_keywords(
        customer_id: str,
        ad_group_id: str,
        keyword_texts: List[str],
        match_type: str = "PHRASE",
        cpc_bid: Optional[float] = None
    ) -> str:
        """
        Bulk add multiple keywords with the same match type.

        Args:
            customer_id: Customer ID (without hyphens)
            ad_group_id: Ad group ID
            keyword_texts: List of keyword text strings
            match_type: Match type for all keywords (EXACT, PHRASE, or BROAD, default: PHRASE)
            cpc_bid: Optional CPC bid for all keywords in currency units

        Returns:
            Success message

        Example:
            keyword_texts = ["running shoes", "athletic shoes", "sport shoes"]
        """
        with performance_logger.track_operation('bulk_add_keywords', customer_id=customer_id):
            try:
                # Build keywords list
                keywords = [
                    {"text": text, "match_type": match_type}
                    for text in keyword_texts
                ]

                # Use existing add_keywords function
                client = get_auth_manager().get_client()
                keyword_manager = KeywordManager(client)

                cpc_bid_micros = int(cpc_bid * 1_000_000) if cpc_bid else None

                keyword_configs = [
                    KeywordConfig(
                        text=kw['text'],
                        match_type=KeywordMatchType[match_type.upper()],
                        ad_group_id=ad_group_id,
                        cpc_bid_micros=cpc_bid_micros
                    )
                    for kw in keywords
                ]

                result = keyword_manager.add_keywords(customer_id, keyword_configs)

                # Audit log
                audit_logger.log_api_call(
                    customer_id=customer_id,
                    operation="bulk_add_keywords",
                    resource_type="keyword",
                    action="create",
                    result="success",
                    details={
                        'ad_group_id': ad_group_id,
                        'keyword_count': len(keyword_texts),
                        'match_type': match_type,
                        'cpc_bid': cpc_bid
                    }
                )

                # Invalidate cache
                get_cache_manager().invalidate(customer_id, ResourceType.KEYWORD)

                output = f"✅ Bulk keywords added successfully!\n\n"
                output += f"**Keywords Added**: {result['keywords_added']}\n"
                output += f"**Match Type**: {match_type}\n"

                if cpc_bid:
                    output += f"**CPC Bid**: ${cpc_bid:.2f}\n"

                return output

            except Exception as e:
                error_msg = ErrorHandler.handle_error(e, context="bulk_add_keywords")
                return f"❌ Failed to bulk add keywords: {error_msg}"

    @mcp.tool()
    def google_ads_bulk_update_keyword_bids(
        customer_id: str,
        bid_updates: List[Dict[str, Any]]
    ) -> str:
        """
        Update bids for multiple keywords at once.

        Args:
            customer_id: Customer ID (without hyphens)
            bid_updates: List of dicts with 'ad_group_id', 'criterion_id', 'cpc_bid'

        Returns:
            Success message

        Example:
            bid_updates = [
                {"ad_group_id": "123", "criterion_id": "456", "cpc_bid": 2.50},
                {"ad_group_id": "123", "criterion_id": "789", "cpc_bid": 3.00}
            ]
        """
        with performance_logger.track_operation('bulk_update_keyword_bids', customer_id=customer_id):
            try:
                client = get_auth_manager().get_client()
                keyword_manager = KeywordManager(client)

                # Convert cpc_bid to micros
                updates_with_micros = [
                    {
                        'ad_group_id': update['ad_group_id'],
                        'criterion_id': update['criterion_id'],
                        'cpc_bid_micros': int(update['cpc_bid'] * 1_000_000)
                    }
                    for update in bid_updates
                ]

                result = keyword_manager.bulk_update_keyword_bids(
                    customer_id,
                    updates_with_micros
                )

                # Audit log
                audit_logger.log_api_call(
                    customer_id=customer_id,
                    operation="bulk_update_keyword_bids",
                    resource_type="keyword",
                    action="update",
                    result="success",
                    details={'keyword_count': len(bid_updates)}
                )

                # Invalidate cache
                get_cache_manager().invalidate(customer_id, ResourceType.KEYWORD)

                output = f"✅ Bulk bid update completed!\n\n"
                output += f"**Keywords Updated**: {result['keywords_updated']}\n\n"
                output += f"{result['message']}"

                return output

            except Exception as e:
                error_msg = ErrorHandler.handle_error(e, context="bulk_update_keyword_bids")
                return f"❌ Failed to bulk update keyword bids: {error_msg}"

    # ============================================================================
    # Traffic Estimation
    # ============================================================================

    @mcp.tool()
    def google_ads_estimate_keyword_traffic(
        customer_id: str,
        keywords: List[str],
        location_ids: Optional[List[str]] = None
    ) -> str:
        """
        Get traffic estimates for keywords.

        Args:
            customer_id: Customer ID (without hyphens)
            keywords: List of keyword texts to estimate
            location_ids: Optional location IDs for targeting (e.g., ["2840"] for United States)

        Returns:
            Traffic estimates

        Note: This is a placeholder. Full implementation requires Keyword Plan API setup.
        """
        with performance_logger.track_operation('estimate_keyword_traffic', customer_id=customer_id):
            try:
                client = get_auth_manager().get_client()
                keyword_manager = KeywordManager(client)

                result = keyword_manager.estimate_keyword_traffic(
                    customer_id,
                    keywords,
                    location_ids=location_ids
                )

                output = f"# Keyword Traffic Estimation\n\n"
                output += f"**Keywords Analyzed**: {result['keywords_analyzed']}\n\n"
                output += f"{result['message']}\n\n"
                output += f"**Note**: {result['note']}\n\n"
                output += "To enable full traffic estimation:\n"
                output += "1. Set up Keyword Planner in your Google Ads account\n"
                output += "2. Create a Keyword Plan via the API\n"
                output += "3. Use KeywordPlanIdeaService for detailed forecasts\n"

                return output

            except Exception as e:
                error_msg = ErrorHandler.handle_error(e, context="estimate_keyword_traffic")
                return f"❌ Failed to estimate keyword traffic: {error_msg}"

    @mcp.tool()
    def google_ads_keyword_ideas(
        customer_id: str,
        seed_keywords: str = "",
        page_url: str = "",
        location_ids: str = "2840",
        language_id: str = "1000",
        keyword_plan_network: str = "GOOGLE_SEARCH",
        response_format: str = "markdown"
    ) -> str:
        """Get keyword ideas from Google Ads Keyword Planner.

        Generate keyword suggestions based on seed keywords or a webpage URL.
        Includes search volume, competition level, and bid estimates.

        Args:
            customer_id: Google Ads customer ID (10 digits, no hyphens)
            seed_keywords: Comma-separated seed keywords (e.g., "running shoes,nike")
            page_url: Optional URL to extract keywords from
            location_ids: Comma-separated location criterion IDs (default: 2840 = US)
            language_id: Language criterion ID (default: 1000 = English)
            keyword_plan_network: Network - GOOGLE_SEARCH, GOOGLE_SEARCH_AND_PARTNERS, or YOUTUBE
            response_format: Output format (markdown or json)

        Returns:
            Keyword ideas with metrics (search volume, competition, bids)

        Example:
            google_ads_keyword_ideas(
                customer_id="1234567890",
                seed_keywords="running shoes,athletic footwear",
                location_ids="2840",  # US
                language_id="1000"  # English
            )

        Common Location IDs:
            - 2840: United States
            - 2826: United Kingdom
            - 2124: Canada
            - 2036: Australia

        Competition Levels:
            - LOW: Easy to rank for
            - MEDIUM: Moderate competition
            - HIGH: Very competitive
        """
        with performance_logger.track_operation('get_keyword_ideas', customer_id=customer_id):
            try:
                client = get_auth_manager().get_client()
                keyword_manager = KeywordManager(client)

                # Parse inputs
                seed_kws = [kw.strip() for kw in seed_keywords.split(",") if kw.strip()] if seed_keywords else None
                location_list = [loc.strip() for loc in location_ids.split(",") if loc.strip()]

                result = keyword_manager.get_keyword_ideas(
                    customer_id=customer_id,
                    seed_keywords=seed_kws,
                    page_url=page_url if page_url else None,
                    location_ids=location_list,
                    language_id=language_id,
                    keyword_plan_network=keyword_plan_network
                )

                audit_logger.log_api_call(
                    operation="get_keyword_ideas",
                    customer_id=customer_id,
                    details={
                        "seed_keywords": seed_kws,
                        "page_url": page_url,
                        "total_ideas": result['total_ideas']
                    },
                    response={"total_ideas": result['total_ideas']}
                )

                if response_format.lower() == "json":
                    return str(result)

                # Format markdown output
                output = f"# Keyword Ideas\n\n"
                output += f"**Total Ideas**: {result['total_ideas']}\n"
                if seed_kws:
                    output += f"**Seed Keywords**: {', '.join(seed_kws)}\n"
                if page_url:
                    output += f"**Page URL**: {page_url}\n"
                output += f"**Locations**: {', '.join(result['locations'])}\n"
                output += f"**Language**: {result['language']}\n"
                output += f"**Network**: {keyword_plan_network}\n\n"

                output += "## Top Keyword Ideas\n\n"
                output += "| Keyword | Avg Monthly Searches | Competition | Competition Index | Low Bid | High Bid |\n"
                output += "|---------|---------------------|-------------|------------------|---------|----------|\n"

                # Sort by search volume and show top 50
                sorted_ideas = sorted(
                    result['keyword_ideas'],
                    key=lambda x: x['avg_monthly_searches'],
                    reverse=True
                )[:50]

                for idea in sorted_ideas:
                    output += f"| {idea['keyword_text']} | "
                    output += f"{idea['avg_monthly_searches']:,} | "
                    output += f"{idea['competition']} | "
                    output += f"{idea['competition_index']}/100 | "
                    output += f"${idea['low_top_of_page_bid']:.2f} | "
                    output += f"${idea['high_top_of_page_bid']:.2f} |\n"

                if len(result['keyword_ideas']) > 50:
                    output += f"\n*Showing top 50 of {result['total_ideas']} total keyword ideas*\n"

                output += "\n## Competition Guide\n"
                output += "- **LOW**: Easy to rank for, less competitive\n"
                output += "- **MEDIUM**: Moderate competition\n"
                output += "- **HIGH**: Very competitive, higher bids needed\n"
                output += "- **Competition Index**: 0-100 scale (higher = more competitive)\n\n"

                output += "## Bid Estimates\n"
                output += "- **Low Bid**: Lower end of top-of-page bid range\n"
                output += "- **High Bid**: Upper end of top-of-page bid range\n"

                return output

            except Exception as e:
                error_msg = ErrorHandler.handle_error(e, context="get_keyword_ideas")
                return f"❌ Failed to get keyword ideas: {error_msg}"

    @mcp.tool()
    def google_ads_keyword_forecast(
        customer_id: str,
        keywords_json: str,
        location_ids: str = "2840",
        language_id: str = "1000",
        cpc_bid: float = 1.0,
        date_interval: str = "NEXT_MONTH",
        response_format: str = "markdown"
    ) -> str:
        """Forecast traffic metrics for specific keywords.

        Get projected impressions, clicks, and costs for keywords over a future time period.

        Args:
            customer_id: Google Ads customer ID (10 digits, no hyphens)
            keywords_json: JSON array of keywords with text and match_type
                Example: [{"text": "running shoes", "match_type": "BROAD"}]
            location_ids: Comma-separated location criterion IDs (default: 2840 = US)
            language_id: Language criterion ID (default: 1000 = English)
            cpc_bid: CPC bid amount for forecast (default: 1.0)
            date_interval: Forecast period - NEXT_WEEK, NEXT_MONTH, or NEXT_QUARTER
            response_format: Output format (markdown or json)

        Returns:
            Traffic forecast with projected metrics

        Example:
            google_ads_keyword_forecast(
                customer_id="1234567890",
                keywords_json='[{"text": "running shoes", "match_type": "BROAD"}, {"text": "nike shoes", "match_type": "PHRASE"}]',
                cpc_bid=2.5,
                date_interval="NEXT_MONTH"
            )

        Match Types:
            - BROAD: Matches variations and related searches
            - PHRASE: Matches phrase and close variants
            - EXACT: Matches exact keyword only

        Date Intervals:
            - NEXT_WEEK: 7-day forecast
            - NEXT_MONTH: 30-day forecast
            - NEXT_QUARTER: 90-day forecast
        """
        with performance_logger.track_operation('forecast_keyword_metrics', customer_id=customer_id):
            try:
                import json

                client = get_auth_manager().get_client()
                keyword_manager = KeywordManager(client)

                # Parse keywords JSON
                try:
                    keywords = json.loads(keywords_json)
                except json.JSONDecodeError as e:
                    return f"❌ Invalid JSON format for keywords: {str(e)}"

                # Parse locations
                location_list = [loc.strip() for loc in location_ids.split(",") if loc.strip()]

                # Convert CPC to micros
                cpc_bid_micros = int(cpc_bid * 1_000_000)

                result = keyword_manager.forecast_keyword_metrics(
                    customer_id=customer_id,
                    keywords=keywords,
                    location_ids=location_list,
                    language_id=language_id,
                    cpc_bid_micros=cpc_bid_micros,
                    date_interval=date_interval
                )

                audit_logger.log_api_call(
                    operation="forecast_keyword_metrics",
                    customer_id=customer_id,
                    details={
                        "keywords_count": len(keywords),
                        "cpc_bid": cpc_bid,
                        "date_interval": date_interval
                    },
                    response={"keywords_forecasted": result['keywords_forecasted']}
                )

                if response_format.lower() == "json":
                    return str(result)

                # Format markdown output
                output = f"# Keyword Traffic Forecast\n\n"
                output += f"**Keywords Forecasted**: {result['keywords_forecasted']}\n"
                output += f"**Forecast Period**: {result['forecast_period']}\n"
                if result['cpc_bid']:
                    output += f"**CPC Bid**: ${result['cpc_bid']:.2f}\n"
                output += f"**Locations**: {', '.join(location_list)}\n"
                output += f"**Language**: {language_id}\n\n"

                output += "## Keywords Being Forecasted\n\n"
                for i, kw in enumerate(keywords, 1):
                    output += f"{i}. **{kw['text']}** ({kw.get('match_type', 'BROAD')})\n"

                output += "\n## Forecast Metrics\n\n"
                output += f"**Note**: {result['note']}\n\n"

                output += "Expected metrics structure:\n"
                for metric, value in result['forecast_metrics'].items():
                    output += f"- **{metric.replace('_', ' ').title()}**: {value}\n"

                output += "\n## About Forecasts\n"
                output += "Keyword forecasts require creating a temporary keyword plan which:\n"
                output += "1. Creates a keyword plan structure\n"
                output += "2. Adds campaigns, ad groups, and keywords\n"
                output += "3. Generates traffic projections\n"
                output += "4. Cleans up temporary resources\n\n"

                output += "Forecast metrics include:\n"
                output += "- **Impressions**: Projected ad views\n"
                output += "- **Clicks**: Projected clicks\n"
                output += "- **Cost**: Projected spend\n"
                output += "- **CTR**: Click-through rate\n"
                output += "- **Average CPC**: Average cost per click\n"

                return output

            except Exception as e:
                error_msg = ErrorHandler.handle_error(e, context="forecast_keyword_metrics")
                return f"❌ Failed to forecast keyword metrics: {error_msg}"

    logger.info("Keyword management tools registered")
