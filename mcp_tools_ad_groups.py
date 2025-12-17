"""
MCP Tools for Ad Group Management

Ad group creation and management tools for Google Ads MCP Server.
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
from ad_group_manager import (
    AdGroupManager, AdGroupConfig, AdGroupStatus, AdGroupType
)

logger = get_logger(__name__)


def register_ad_group_tools(mcp: FastMCP):
    """Register ad group management tools with MCP server."""

    # ============================================================================
    # Ad Group Creation
    # ============================================================================

    @mcp.tool()
    def google_ads_create_ad_group(
        customer_id: str,
        campaign_id: str,
        ad_group_name: str,
        cpc_bid: Optional[float] = None,
        status: str = "PAUSED",
        ad_group_type: Optional[str] = None
    ) -> str:
        """
        Create a new ad group within a campaign.

        Args:
            customer_id: Customer ID (without hyphens)
            campaign_id: Campaign ID to create ad group in
            ad_group_name: Name for the ad group
            cpc_bid: Cost-per-click bid in currency units (e.g., 1.50 for $1.50)
            status: Initial status (ENABLED or PAUSED, default: PAUSED)
            ad_group_type: Optional ad group type (SEARCH_STANDARD, DISPLAY_STANDARD, etc.)

        Returns:
            Success message with ad group details

        Note: Ad groups are created PAUSED by default for safety.
        """
        with performance_logger.track_operation('create_ad_group', customer_id=customer_id):
            try:
                client = get_auth_manager().get_client()
                ad_group_manager = AdGroupManager(client)

                # Convert bid to micros
                cpc_bid_micros = int(cpc_bid * 1_000_000) if cpc_bid else None

                # Create config
                config = AdGroupConfig(
                    name=ad_group_name,
                    campaign_id=campaign_id,
                    status=AdGroupStatus[status.upper()],
                    cpc_bid_micros=cpc_bid_micros,
                    ad_group_type=AdGroupType[ad_group_type.upper()] if ad_group_type else None
                )

                # Create ad group
                result = ad_group_manager.create_ad_group(customer_id, config)

                # Audit log
                audit_logger.log_api_call(
                    customer_id=customer_id,
                    operation="create_ad_group",
                    resource_type="ad_group",
                    resource_id=result['ad_group_id'],
                    action="create",
                    result="success",
                    details={
                        'name': ad_group_name,
                        'campaign_id': campaign_id,
                        'cpc_bid': cpc_bid
                    }
                )

                # Invalidate cache
                get_cache_manager().invalidate(customer_id, ResourceType.AD_GROUP)

                output = f"✅ Ad group created successfully!\n\n"
                output += f"**Ad Group ID**: {result['ad_group_id']}\n"
                output += f"**Name**: {ad_group_name}\n"
                output += f"**Campaign ID**: {campaign_id}\n"
                output += f"**Status**: {status}\n"

                if cpc_bid:
                    output += f"**CPC Bid**: ${cpc_bid:.2f}\n"

                output += f"\n"
                output += f"Ad group is now {status.lower()}. "
                output += f"Next steps:\n"
                output += f"1. Add keywords to the ad group\n"
                output += f"2. Create ads\n"
                output += f"3. Enable the ad group when ready"

                return output

            except Exception as e:
                error_msg = ErrorHandler.handle_error(e, context="create_ad_group")
                return f"❌ Failed to create ad group: {error_msg}"

    # ============================================================================
    # Ad Group Updates
    # ============================================================================

    @mcp.tool()
    def google_ads_update_ad_group(
        customer_id: str,
        ad_group_id: str,
        ad_group_name: Optional[str] = None,
        status: Optional[str] = None,
        cpc_bid: Optional[float] = None
    ) -> str:
        """
        Update ad group settings.

        Args:
            customer_id: Customer ID (without hyphens)
            ad_group_id: Ad group ID to update
            ad_group_name: New ad group name (optional)
            status: New status (ENABLED, PAUSED, or REMOVED) (optional)
            cpc_bid: New CPC bid in currency units (optional)

        Returns:
            Success message with updated fields
        """
        with performance_logger.track_operation('update_ad_group', customer_id=customer_id):
            try:
                client = get_auth_manager().get_client()
                ad_group_manager = AdGroupManager(client)

                # Build updates dict
                updates = {}
                if ad_group_name:
                    updates['name'] = ad_group_name
                if status:
                    updates['status'] = status.upper()
                if cpc_bid is not None:
                    updates['cpc_bid_micros'] = int(cpc_bid * 1_000_000)

                if not updates:
                    return "⚠️ No updates specified. Provide at least one field to update."

                # Update ad group
                result = ad_group_manager.update_ad_group(customer_id, ad_group_id, updates)

                # Audit log
                audit_logger.log_api_call(
                    customer_id=customer_id,
                    operation="update_ad_group",
                    resource_type="ad_group",
                    resource_id=ad_group_id,
                    action="update",
                    result="success",
                    details={'updated_fields': result['updated_fields']}
                )

                # Invalidate cache
                get_cache_manager().invalidate(customer_id, ResourceType.AD_GROUP)

                output = f"✅ Ad group {ad_group_id} updated successfully!\n\n"
                output += f"**Updated Fields**: {', '.join(result['updated_fields'])}\n\n"

                if 'name' in updates:
                    output += f"**New Name**: {ad_group_name}\n"
                if 'status' in updates:
                    output += f"**New Status**: {status.upper()}\n"
                if 'cpc_bid_micros' in updates:
                    output += f"**New CPC Bid**: ${cpc_bid:.2f}\n"

                output += f"\nChanges have been applied to the ad group."

                return output

            except Exception as e:
                error_msg = ErrorHandler.handle_error(e, context="update_ad_group")
                return f"❌ Failed to update ad group: {error_msg}"

    @mcp.tool()
    def google_ads_update_ad_group_status(
        customer_id: str,
        ad_group_id: str,
        status: str
    ) -> str:
        """
        Update ad group status (enable, pause, or remove).

        Args:
            customer_id: Customer ID (without hyphens)
            ad_group_id: Ad group ID
            status: New status (ENABLED, PAUSED, or REMOVED)

        Returns:
            Success message
        """
        with performance_logger.track_operation('update_ad_group_status', customer_id=customer_id):
            try:
                client = get_auth_manager().get_client()
                ad_group_manager = AdGroupManager(client)

                status_upper = status.upper()
                result = ad_group_manager.update_ad_group_status(
                    customer_id,
                    ad_group_id,
                    AdGroupStatus[status_upper]
                )

                # Audit log
                audit_logger.log_api_call(
                    customer_id=customer_id,
                    operation="update_ad_group_status",
                    resource_type="ad_group",
                    resource_id=ad_group_id,
                    action="update",
                    result="success",
                    details={'new_status': status_upper}
                )

                # Invalidate cache
                get_cache_manager().invalidate(customer_id, ResourceType.AD_GROUP)

                status_messages = {
                    "ENABLED": "Ad group is now active and ads will start serving.",
                    "PAUSED": "Ad group is now paused. Ads have stopped serving.",
                    "REMOVED": "Ad group has been removed and cannot be re-enabled."
                }

                return (
                    f"✅ Ad group {ad_group_id} status updated to {status_upper}\n\n"
                    f"{status_messages.get(status_upper, 'Status updated successfully.')}"
                )

            except Exception as e:
                error_msg = ErrorHandler.handle_error(e, context="update_ad_group_status")
                return f"❌ Failed to update ad group status: {error_msg}"

    @mcp.tool()
    def google_ads_update_ad_group_bid(
        customer_id: str,
        ad_group_id: str,
        cpc_bid: float
    ) -> str:
        """
        Update ad group CPC bid.

        Args:
            customer_id: Customer ID (without hyphens)
            ad_group_id: Ad group ID
            cpc_bid: New CPC bid in currency units (e.g., 1.50 for $1.50)

        Returns:
            Success message with bid details
        """
        with performance_logger.track_operation('update_ad_group_bid', customer_id=customer_id):
            try:
                client = get_auth_manager().get_client()
                ad_group_manager = AdGroupManager(client)

                cpc_bid_micros = int(cpc_bid * 1_000_000)

                result = ad_group_manager.update_ad_group_cpc_bid(
                    customer_id,
                    ad_group_id,
                    cpc_bid_micros
                )

                # Audit log
                audit_logger.log_api_call(
                    customer_id=customer_id,
                    operation="update_ad_group_bid",
                    resource_type="ad_group",
                    resource_id=ad_group_id,
                    action="update",
                    result="success",
                    details={'new_cpc_bid': cpc_bid}
                )

                # Invalidate cache
                get_cache_manager().invalidate(customer_id, ResourceType.AD_GROUP)

                return (
                    f"✅ Ad group {ad_group_id} bid updated successfully!\n\n"
                    f"**New CPC Bid**: ${result['new_cpc_bid']:.2f}\n\n"
                    f"The new bid will take effect immediately. "
                    f"Monitor performance closely to see the impact on impressions and clicks."
                )

            except Exception as e:
                error_msg = ErrorHandler.handle_error(e, context="update_ad_group_bid")
                return f"❌ Failed to update ad group bid: {error_msg}"

    # ============================================================================
    # Ad Group Information
    # ============================================================================

    @mcp.tool()
    def google_ads_get_ad_group_details(
        customer_id: str,
        ad_group_id: str
    ) -> str:
        """
        Get detailed information about an ad group.

        Args:
            customer_id: Customer ID (without hyphens)
            ad_group_id: Ad group ID

        Returns:
            Detailed ad group information
        """
        with performance_logger.track_operation('get_ad_group_details', customer_id=customer_id):
            try:
                client = get_auth_manager().get_client()
                ad_group_manager = AdGroupManager(client)

                details = ad_group_manager.get_ad_group_details(customer_id, ad_group_id)

                if not details:
                    return f"❌ Ad group {ad_group_id} not found"

                output = f"# Ad Group Details: {details['name']}\n\n"
                output += f"**ID**: {details['id']}\n"
                output += f"**Status**: {details['status']}\n"
                output += f"**Type**: {details['type']}\n\n"

                output += "## Campaign\n"
                output += f"- **Campaign ID**: {details['campaign']['id']}\n"
                output += f"- **Campaign Name**: {details['campaign']['name']}\n\n"

                output += "## Bidding\n"
                if details['bids']['cpc_bid']:
                    output += f"- **CPC Bid**: ${details['bids']['cpc_bid']:.2f}\n"
                if details['bids']['cpm_bid']:
                    output += f"- **CPM Bid**: ${details['bids']['cpm_bid']:.2f}\n"
                if details['bids']['cpv_bid']:
                    output += f"- **CPV Bid**: ${details['bids']['cpv_bid']:.2f}\n"
                if details['bids']['target_cpa']:
                    output += f"- **Target CPA**: ${details['bids']['target_cpa']:.2f}\n"
                output += "\n"

                output += "## Performance Metrics\n"
                output += f"- **Cost**: ${details['metrics']['cost']:,.2f}\n"
                output += f"- **Clicks**: {details['metrics']['clicks']:,}\n"
                output += f"- **Impressions**: {details['metrics']['impressions']:,}\n"
                output += f"- **CTR**: {details['metrics']['ctr']:.2f}%\n"
                output += f"- **Avg CPC**: ${details['metrics']['average_cpc']:.2f}\n"
                output += f"- **Conversions**: {details['metrics']['conversions']}\n"

                return output

            except Exception as e:
                error_msg = ErrorHandler.handle_error(e, context="get_ad_group_details")
                return f"❌ Failed to get ad group details: {error_msg}"

    @mcp.tool()
    def google_ads_list_ad_groups(
        customer_id: str,
        campaign_id: Optional[str] = None,
        status: Optional[str] = None
    ) -> str:
        """
        List ad groups with optional filters.

        Args:
            customer_id: Customer ID (without hyphens)
            campaign_id: Optional campaign ID to filter by
            status: Optional status to filter by (ENABLED, PAUSED)

        Returns:
            List of ad groups with key metrics
        """
        with performance_logger.track_operation('list_ad_groups', customer_id=customer_id):
            try:
                client = get_auth_manager().get_client()
                ad_group_manager = AdGroupManager(client)

                status_filter = AdGroupStatus[status.upper()] if status else None

                ad_groups = ad_group_manager.list_ad_groups(
                    customer_id,
                    campaign_id=campaign_id,
                    status=status_filter
                )

                if not ad_groups:
                    return "No ad groups found matching the criteria."

                output = f"# Ad Groups ({len(ad_groups)} total)\n\n"

                for ag in ad_groups:
                    output += f"## {ag['name']}\n"
                    output += f"- **ID**: {ag['id']}\n"
                    output += f"- **Status**: {ag['status']}\n"
                    output += f"- **Campaign**: {ag['campaign_name']} (ID: {ag['campaign_id']})\n"

                    if ag['cpc_bid']:
                        output += f"- **CPC Bid**: ${ag['cpc_bid']:.2f}\n"

                    output += f"- **Impressions**: {ag['metrics']['impressions']:,}\n"
                    output += f"- **Clicks**: {ag['metrics']['clicks']:,}\n"
                    output += f"- **Cost**: ${ag['metrics']['cost']:,.2f}\n"
                    output += "\n"

                return output

            except Exception as e:
                error_msg = ErrorHandler.handle_error(e, context="list_ad_groups")
                return f"❌ Failed to list ad groups: {error_msg}"

    @mcp.tool()
    def google_ads_get_ad_group_performance(
        customer_id: str,
        ad_group_id: str,
        date_range: str = "LAST_30_DAYS"
    ) -> str:
        """
        Get performance metrics for an ad group over a date range.

        Args:
            customer_id: Customer ID (without hyphens)
            ad_group_id: Ad group ID
            date_range: Date range (TODAY, YESTERDAY, LAST_7_DAYS, LAST_30_DAYS, etc.)

        Returns:
            Performance metrics
        """
        with performance_logger.track_operation('get_ad_group_performance', customer_id=customer_id):
            try:
                client = get_auth_manager().get_client()
                ad_group_manager = AdGroupManager(client)

                result = ad_group_manager.get_ad_group_performance(
                    customer_id,
                    ad_group_id,
                    date_range
                )

                if 'error' in result:
                    return f"⚠️ {result['error']}"

                metrics = result['metrics']

                output = f"# Ad Group Performance: {result['name']}\n\n"
                output += f"**Campaign**: {result['campaign_name']}\n"
                output += f"**Date Range**: {date_range}\n\n"

                output += "## Key Metrics\n"
                output += f"- **Total Cost**: ${metrics['cost']:,.2f}\n"
                output += f"- **Clicks**: {metrics['clicks']:,}\n"
                output += f"- **Impressions**: {metrics['impressions']:,}\n"
                output += f"- **CTR**: {metrics['ctr']:.2f}%\n"
                output += f"- **Avg CPC**: ${metrics['average_cpc']:.2f}\n\n"

                output += "## Conversions\n"
                output += f"- **Conversions**: {metrics['conversions']:.2f}\n"
                output += f"- **Conversion Value**: ${metrics['conversions_value']:,.2f}\n"
                output += f"- **Cost per Conversion**: ${metrics['cost_per_conversion']:.2f}\n"
                output += f"- **Conversion Rate**: {metrics['conversion_rate']:.2f}%\n"
                output += f"- **All Conversions**: {metrics['all_conversions']:.2f}\n"
                output += f"- **View-Through Conversions**: {metrics['view_through_conversions']:.0f}\n"

                return output

            except Exception as e:
                error_msg = ErrorHandler.handle_error(e, context="get_ad_group_performance")
                return f"❌ Failed to get ad group performance: {error_msg}"

    # ============================================================================
    # Bulk Operations
    # ============================================================================

    @mcp.tool()
    def google_ads_bulk_update_ad_group_status(
        customer_id: str,
        ad_group_ids: List[str],
        status: str
    ) -> str:
        """
        Update status for multiple ad groups at once.

        Args:
            customer_id: Customer ID (without hyphens)
            ad_group_ids: List of ad group IDs to update
            status: New status for all ad groups (ENABLED, PAUSED, or REMOVED)

        Returns:
            Success message with count of updated ad groups

        Example:
            ad_group_ids = ["123456789", "987654321", "456789123"]
        """
        with performance_logger.track_operation('bulk_update_ad_group_status', customer_id=customer_id):
            try:
                client = get_auth_manager().get_client()
                ad_group_manager = AdGroupManager(client)

                if not ad_group_ids:
                    return "⚠️ No ad group IDs provided."

                status_upper = status.upper()
                result = ad_group_manager.bulk_update_ad_group_status(
                    customer_id,
                    ad_group_ids,
                    AdGroupStatus[status_upper]
                )

                # Audit log
                audit_logger.log_api_call(
                    customer_id=customer_id,
                    operation="bulk_update_ad_group_status",
                    resource_type="ad_group",
                    action="update",
                    result="success",
                    details={
                        'ad_group_count': len(ad_group_ids),
                        'new_status': status_upper
                    }
                )

                # Invalidate cache
                get_cache_manager().invalidate(customer_id, ResourceType.AD_GROUP)

                output = f"✅ Bulk status update completed!\n\n"
                output += f"**Ad Groups Updated**: {result['ad_groups_updated']}\n"
                output += f"**New Status**: {status_upper}\n\n"
                output += f"{result['message']}"

                return output

            except Exception as e:
                error_msg = ErrorHandler.handle_error(e, context="bulk_update_ad_group_status")
                return f"❌ Failed to bulk update ad group status: {error_msg}"

    logger.info("Ad group management tools registered")
