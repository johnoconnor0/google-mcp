"""
MCP Tools for Ad Management

Ad creation and management tools for Google Ads MCP Server.
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
from ad_manager import (
    AdManager, ResponsiveSearchAdConfig, AdStatus
)

logger = get_logger(__name__)


def register_ad_tools(mcp: FastMCP):
    """Register ad management tools with MCP server."""

    # ============================================================================
    # Responsive Search Ad Creation
    # ============================================================================

    @mcp.tool()
    def google_ads_create_responsive_search_ad(
        customer_id: str,
        ad_group_id: str,
        headlines: List[str],
        descriptions: List[str],
        final_urls: List[str],
        path1: Optional[str] = None,
        path2: Optional[str] = None,
        status: str = "PAUSED"
    ) -> str:
        """
        Create a Responsive Search Ad (RSA).

        Args:
            customer_id: Customer ID (without hyphens)
            ad_group_id: Ad group ID
            headlines: List of 3-15 headline texts (max 30 chars each)
            descriptions: List of 2-4 description texts (max 90 chars each)
            final_urls: List of final URLs (landing pages)
            path1: Optional display path 1 (max 15 chars)
            path2: Optional display path 2 (max 15 chars)
            status: Initial status (ENABLED or PAUSED, default: PAUSED)

        Returns:
            Success message with ad details

        Example:
            headlines = [
                "Premium Running Shoes",
                "Free Shipping Today",
                "Shop Nike & Adidas"
            ]
            descriptions = [
                "Browse our selection of top running shoes",
                "30-day money back guarantee"
            ]
            final_urls = ["https://example.com/shoes"]
        """
        with performance_logger.track_operation('create_responsive_search_ad', customer_id=customer_id):
            try:
                client = get_auth_manager().get_client()
                ad_manager = AdManager(client)

                # Validate headlines and descriptions
                if len(headlines) < 3 or len(headlines) > 15:
                    return "❌ Must provide 3-15 headlines"

                if len(descriptions) < 2 or len(descriptions) > 4:
                    return "❌ Must provide 2-4 descriptions"

                # Create config
                config = ResponsiveSearchAdConfig(
                    ad_group_id=ad_group_id,
                    headlines=headlines,
                    descriptions=descriptions,
                    path1=path1,
                    path2=path2,
                    final_urls=final_urls,
                    status=AdStatus[status.upper()]
                )

                # Create ad
                result = ad_manager.create_responsive_search_ad(customer_id, config)

                # Audit log
                audit_logger.log_api_call(
                    customer_id=customer_id,
                    operation="create_responsive_search_ad",
                    resource_type="ad",
                    resource_id=result['ad_id'],
                    action="create",
                    result="success",
                    details={
                        'ad_group_id': ad_group_id,
                        'headline_count': len(headlines),
                        'description_count': len(descriptions)
                    }
                )

                # Invalidate cache
                get_cache_manager().invalidate(customer_id, ResourceType.AD)

                output = f"✅ Responsive Search Ad created successfully!\n\n"
                output += f"**Ad ID**: {result['ad_id']}\n"
                output += f"**Ad Group ID**: {ad_group_id}\n"
                output += f"**Status**: {status}\n"
                output += f"**Headlines**: {result['headline_count']}\n"
                output += f"**Descriptions**: {result['description_count']}\n\n"

                output += "**Headlines**:\n"
                for i, h in enumerate(headlines[:5], 1):
                    output += f"{i}. {h}\n"
                if len(headlines) > 5:
                    output += f"... and {len(headlines) - 5} more\n"

                output += "\n**Descriptions**:\n"
                for i, d in enumerate(descriptions, 1):
                    output += f"{i}. {d}\n"

                output += f"\n**Final URL**: {final_urls[0]}\n"

                if status == "PAUSED":
                    output += "\nℹ️ Ad is paused. Enable it when ready to start serving."

                return output

            except Exception as e:
                error_msg = ErrorHandler.handle_error(e, context="create_responsive_search_ad")
                return f"❌ Failed to create ad: {error_msg}"

    # ============================================================================
    # Ad Status Updates
    # ============================================================================

    @mcp.tool()
    def google_ads_update_ad_status(
        customer_id: str,
        ad_group_id: str,
        ad_id: str,
        status: str
    ) -> str:
        """
        Update ad status (enable, pause, or remove).

        Args:
            customer_id: Customer ID (without hyphens)
            ad_group_id: Ad group ID
            ad_id: Ad ID
            status: New status (ENABLED, PAUSED, or REMOVED)

        Returns:
            Success message
        """
        with performance_logger.track_operation('update_ad_status', customer_id=customer_id):
            try:
                client = get_auth_manager().get_client()
                ad_manager = AdManager(client)

                status_upper = status.upper()
                result = ad_manager.update_ad_status(
                    customer_id,
                    ad_group_id,
                    ad_id,
                    AdStatus[status_upper]
                )

                # Audit log
                audit_logger.log_api_call(
                    customer_id=customer_id,
                    operation="update_ad_status",
                    resource_type="ad",
                    resource_id=ad_id,
                    action="update",
                    result="success",
                    details={'new_status': status_upper}
                )

                # Invalidate cache
                get_cache_manager().invalidate(customer_id, ResourceType.AD)

                status_messages = {
                    "ENABLED": "Ad is now active and will start serving.",
                    "PAUSED": "Ad is now paused and will not serve.",
                    "REMOVED": "Ad has been removed."
                }

                return (
                    f"✅ Ad status updated to {status_upper}\n\n"
                    f"**Ad ID**: {ad_id}\n\n"
                    f"{status_messages.get(status_upper, 'Status updated successfully.')}"
                )

            except Exception as e:
                error_msg = ErrorHandler.handle_error(e, context="update_ad_status")
                return f"❌ Failed to update ad status: {error_msg}"

    # ============================================================================
    # Ad Information
    # ============================================================================

    @mcp.tool()
    def google_ads_list_ads(
        customer_id: str,
        ad_group_id: str
    ) -> str:
        """
        List all ads in an ad group.

        Args:
            customer_id: Customer ID (without hyphens)
            ad_group_id: Ad group ID

        Returns:
            List of ads with details
        """
        with performance_logger.track_operation('list_ads', customer_id=customer_id):
            try:
                client = get_auth_manager().get_client()
                ad_manager = AdManager(client)

                ads = ad_manager.list_ads(customer_id, ad_group_id)

                if not ads:
                    return f"No ads found in ad group {ad_group_id}"

                output = f"# Ads in Ad Group {ad_group_id}\n\n"
                output += f"**Total Ads**: {len(ads)}\n\n"

                for ad in ads:
                    output += f"## Ad ID: {ad['ad_id']}\n"
                    output += f"- **Type**: {ad['ad_type']}\n"
                    output += f"- **Status**: {ad['status']}\n"
                    output += f"- **Approval**: {ad['approval_status']}\n"

                    if ad.get('ad_strength'):
                        output += f"- **Ad Strength**: {ad['ad_strength']}\n"

                    if ad['ad_type'] == "RESPONSIVE_SEARCH_AD":
                        output += f"- **Headlines**: {len(ad['headlines'])}\n"
                        output += f"- **Descriptions**: {len(ad['descriptions'])}\n"

                        # Show first 3 headlines
                        output += "\n  **Headlines**:\n"
                        for h in ad['headlines'][:3]:
                            output += f"  - {h}\n"
                        if len(ad['headlines']) > 3:
                            output += f"  ... and {len(ad['headlines']) - 3} more\n"

                    if ad['final_urls']:
                        output += f"- **Final URL**: {ad['final_urls'][0]}\n"

                    output += "\n"

                return output

            except Exception as e:
                error_msg = ErrorHandler.handle_error(e, context="list_ads")
                return f"❌ Failed to list ads: {error_msg}"

    @mcp.tool()
    def google_ads_get_ad_details(
        customer_id: str,
        ad_group_id: str,
        ad_id: str
    ) -> str:
        """
        Get detailed information about an ad.

        Args:
            customer_id: Customer ID (without hyphens)
            ad_group_id: Ad group ID
            ad_id: Ad ID

        Returns:
            Detailed ad information
        """
        with performance_logger.track_operation('get_ad_details', customer_id=customer_id):
            try:
                client = get_auth_manager().get_client()
                ad_manager = AdManager(client)

                details = ad_manager.get_ad_details(customer_id, ad_group_id, ad_id)

                if not details:
                    return f"❌ Ad {ad_id} not found"

                output = f"# Ad Details: {ad_id}\n\n"
                output += f"**Type**: {details['ad_type']}\n"
                output += f"**Status**: {details['status']}\n"
                output += f"**Approval Status**: {details['approval_status']}\n"
                output += f"**Review Status**: {details['review_status']}\n"

                if details.get('ad_strength'):
                    output += f"**Ad Strength**: {details['ad_strength']}\n"

                output += "\n"

                if details['ad_type'] == "RESPONSIVE_SEARCH_AD":
                    output += "## Headlines\n"
                    for i, h in enumerate(details['headlines'], 1):
                        output += f"{i}. {h}\n"

                    output += "\n## Descriptions\n"
                    for i, d in enumerate(details['descriptions'], 1):
                        output += f"{i}. {d}\n"

                    if details.get('path1') or details.get('path2'):
                        output += "\n## Display Paths\n"
                        if details.get('path1'):
                            output += f"- Path 1: {details['path1']}\n"
                        if details.get('path2'):
                            output += f"- Path 2: {details['path2']}\n"

                output += "\n## Final URLs\n"
                for url in details['final_urls']:
                    output += f"- {url}\n"

                output += "\n## Performance Metrics\n"
                output += f"- **Impressions**: {details['metrics']['impressions']:,}\n"
                output += f"- **Clicks**: {details['metrics']['clicks']:,}\n"
                output += f"- **Cost**: ${details['metrics']['cost']:,.2f}\n"
                output += f"- **Conversions**: {details['metrics']['conversions']:.2f}\n"

                return output

            except Exception as e:
                error_msg = ErrorHandler.handle_error(e, context="get_ad_details")
                return f"❌ Failed to get ad details: {error_msg}"

    @mcp.tool()
    def google_ads_get_ad_performance(
        customer_id: str,
        ad_group_id: Optional[str] = None,
        date_range: str = "LAST_30_DAYS"
    ) -> str:
        """
        Get ad performance metrics.

        Args:
            customer_id: Customer ID (without hyphens)
            ad_group_id: Optional ad group ID to filter
            date_range: Date range (TODAY, YESTERDAY, LAST_7_DAYS, LAST_30_DAYS, etc.)

        Returns:
            Ad performance report
        """
        with performance_logger.track_operation('get_ad_performance', customer_id=customer_id):
            try:
                client = get_auth_manager().get_client()
                ad_manager = AdManager(client)

                ads = ad_manager.get_ad_performance(
                    customer_id,
                    ad_group_id=ad_group_id,
                    date_range=date_range
                )

                if not ads:
                    return "No ad performance data found"

                output = f"# Ad Performance ({date_range})\n\n"
                output += f"**Total Ads**: {len(ads)}\n\n"

                # Show top 20 by cost
                for ad in ads[:20]:
                    output += f"## Ad ID: {ad['ad_id']}\n"
                    output += f"- **Type**: {ad['ad_type']}\n"
                    output += f"- **Status**: {ad['status']}\n"
                    output += f"- **Campaign**: {ad['campaign']['name']}\n"
                    output += f"- **Ad Group**: {ad['ad_group']['name']}\n"

                    metrics = ad['metrics']
                    output += f"- **Cost**: ${metrics['cost']:,.2f}\n"
                    output += f"- **Clicks**: {metrics['clicks']:,}\n"
                    output += f"- **Impressions**: {metrics['impressions']:,}\n"
                    output += f"- **CTR**: {metrics['ctr']:.2f}%\n"
                    output += f"- **Avg CPC**: ${metrics['average_cpc']:.2f}\n"
                    output += f"- **Conversions**: {metrics['conversions']:.2f}\n"
                    output += f"- **Conv Value**: ${metrics['conversions_value']:,.2f}\n\n"

                if len(ads) > 20:
                    output += f"... and {len(ads) - 20} more ads\n"

                return output

            except Exception as e:
                error_msg = ErrorHandler.handle_error(e, context="get_ad_performance")
                return f"❌ Failed to get ad performance: {error_msg}"

    # ============================================================================
    # Ad Approval and Policy
    # ============================================================================

    @mcp.tool()
    def google_ads_check_ad_approval_status(
        customer_id: str,
        ad_group_id: str,
        ad_id: str
    ) -> str:
        """
        Check ad approval and policy status.

        Args:
            customer_id: Customer ID (without hyphens)
            ad_group_id: Ad group ID
            ad_id: Ad ID

        Returns:
            Approval status details
        """
        with performance_logger.track_operation('check_ad_approval_status', customer_id=customer_id):
            try:
                client = get_auth_manager().get_client()
                ad_manager = AdManager(client)

                status = ad_manager.check_ad_approval_status(
                    customer_id,
                    ad_group_id,
                    ad_id
                )

                if not status:
                    return f"❌ Ad {ad_id} not found"

                output = f"# Ad Approval Status: {ad_id}\n\n"
                output += f"**Approval Status**: {status['approval_status']}\n"
                output += f"**Review Status**: {status['review_status']}\n\n"

                if status['policy_topics']:
                    output += "## Policy Issues\n"
                    for topic in status['policy_topics']:
                        output += f"- **{topic['topic']}**: {topic['type']}\n"
                else:
                    output += "✅ No policy issues found\n"

                output += "\n### Approval Statuses\n"
                output += "- **APPROVED**: Ad can serve\n"
                output += "- **APPROVED_LIMITED**: Ad serving with limitations\n"
                output += "- **DISAPPROVED**: Ad cannot serve\n"
                output += "- **UNDER_REVIEW**: Currently being reviewed\n"

                return output

            except Exception as e:
                error_msg = ErrorHandler.handle_error(e, context="check_ad_approval_status")
                return f"❌ Failed to check approval status: {error_msg}"

    # ============================================================================
    # Bulk Operations
    # ============================================================================

    @mcp.tool()
    def google_ads_bulk_update_ad_status(
        customer_id: str,
        status_updates: List[Dict[str, str]],
        status: str
    ) -> str:
        """
        Update status for multiple ads at once.

        Args:
            customer_id: Customer ID (without hyphens)
            status_updates: List of dicts with 'ad_group_id' and 'ad_id'
            status: New status for all ads (ENABLED, PAUSED, or REMOVED)

        Returns:
            Success message

        Example:
            status_updates = [
                {"ad_group_id": "123", "ad_id": "456"},
                {"ad_group_id": "123", "ad_id": "789"}
            ]
        """
        with performance_logger.track_operation('bulk_update_ad_status', customer_id=customer_id):
            try:
                client = get_auth_manager().get_client()
                ad_manager = AdManager(client)

                if not status_updates:
                    return "⚠️ No ads specified for update"

                status_upper = status.upper()
                result = ad_manager.bulk_update_ad_status(
                    customer_id,
                    status_updates,
                    AdStatus[status_upper]
                )

                # Audit log
                audit_logger.log_api_call(
                    customer_id=customer_id,
                    operation="bulk_update_ad_status",
                    resource_type="ad",
                    action="update",
                    result="success",
                    details={
                        'ad_count': len(status_updates),
                        'new_status': status_upper
                    }
                )

                # Invalidate cache
                get_cache_manager().invalidate(customer_id, ResourceType.AD)

                output = f"✅ Bulk ad status update completed!\n\n"
                output += f"**Ads Updated**: {result['ads_updated']}\n"
                output += f"**New Status**: {status_upper}\n\n"
                output += f"{result['message']}"

                return output

            except Exception as e:
                error_msg = ErrorHandler.handle_error(e, context="bulk_update_ad_status")
                return f"❌ Failed to bulk update ad status: {error_msg}"

    # ============================================================================
    # Ad Copy Testing
    # ============================================================================

    @mcp.tool()
    def google_ads_compare_ad_performance(
        customer_id: str,
        ad_id_1: str,
        ad_id_2: str,
        date_range: str = "LAST_30_DAYS"
    ) -> str:
        """
        Compare performance between two ads (A/B testing).

        Args:
            customer_id: Customer ID (without hyphens)
            ad_id_1: First ad ID
            ad_id_2: Second ad ID
            date_range: Date range for comparison

        Returns:
            Comparison report
        """
        with performance_logger.track_operation('compare_ad_performance', customer_id=customer_id):
            try:
                # Get all ad performance
                client = get_auth_manager().get_client()
                ad_manager = AdManager(client)

                all_ads = ad_manager.get_ad_performance(customer_id, date_range=date_range)

                # Find the two ads
                ad1 = next((a for a in all_ads if a['ad_id'] == ad_id_1), None)
                ad2 = next((a for a in all_ads if a['ad_id'] == ad_id_2), None)

                if not ad1 or not ad2:
                    return "❌ One or both ads not found"

                output = f"# Ad Performance Comparison ({date_range})\n\n"

                # Ad 1
                output += f"## Ad A (ID: {ad_id_1})\n"
                metrics1 = ad1['metrics']
                output += f"- **Impressions**: {metrics1['impressions']:,}\n"
                output += f"- **Clicks**: {metrics1['clicks']:,}\n"
                output += f"- **CTR**: {metrics1['ctr']:.2f}%\n"
                output += f"- **Avg CPC**: ${metrics1['average_cpc']:.2f}\n"
                output += f"- **Cost**: ${metrics1['cost']:,.2f}\n"
                output += f"- **Conversions**: {metrics1['conversions']:.2f}\n"
                conv_rate_1 = (metrics1['conversions'] / metrics1['clicks'] * 100) if metrics1['clicks'] > 0 else 0
                output += f"- **Conv Rate**: {conv_rate_1:.2f}%\n\n"

                # Ad 2
                output += f"## Ad B (ID: {ad_id_2})\n"
                metrics2 = ad2['metrics']
                output += f"- **Impressions**: {metrics2['impressions']:,}\n"
                output += f"- **Clicks**: {metrics2['clicks']:,}\n"
                output += f"- **CTR**: {metrics2['ctr']:.2f}%\n"
                output += f"- **Avg CPC**: ${metrics2['average_cpc']:.2f}\n"
                output += f"- **Cost**: ${metrics2['cost']:,.2f}\n"
                output += f"- **Conversions**: {metrics2['conversions']:.2f}\n"
                conv_rate_2 = (metrics2['conversions'] / metrics2['clicks'] * 100) if metrics2['clicks'] > 0 else 0
                output += f"- **Conv Rate**: {conv_rate_2:.2f}%\n\n"

                # Winner determination
                output += "## Analysis\n"
                if metrics1['ctr'] > metrics2['ctr']:
                    output += f"🏆 Ad A has better CTR ({metrics1['ctr']:.2f}% vs {metrics2['ctr']:.2f}%)\n"
                else:
                    output += f"🏆 Ad B has better CTR ({metrics2['ctr']:.2f}% vs {metrics1['ctr']:.2f}%)\n"

                if conv_rate_1 > conv_rate_2:
                    output += f"🏆 Ad A has better conversion rate ({conv_rate_1:.2f}% vs {conv_rate_2:.2f}%)\n"
                else:
                    output += f"🏆 Ad B has better conversion rate ({conv_rate_2:.2f}% vs {conv_rate_1:.2f}%)\n"

                return output

            except Exception as e:
                error_msg = ErrorHandler.handle_error(e, context="compare_ad_performance")
                return f"❌ Failed to compare ads: {error_msg}"

    logger.info("Ad management tools registered")
