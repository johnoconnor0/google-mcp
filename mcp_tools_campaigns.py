"""
MCP Tools for Campaign Management

Campaign creation and management tools for Google Ads MCP Server.
"""

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from enum import Enum
import json

from auth_manager import get_auth_manager
from error_handler import ErrorHandler
from logger import performance_logger, audit_logger, get_logger
from cache_manager import get_cache_manager, ResourceType
from campaign_manager import (
    CampaignManager, CampaignConfig, CampaignType, CampaignStatus,
    BiddingStrategyType, LocationTarget, LanguageTarget
)

logger = get_logger(__name__)


def register_campaign_tools(mcp: FastMCP):
    """Register campaign management tools with MCP server."""

    # ============================================================================
    # Campaign Creation
    # ============================================================================

    @mcp.tool()
    def google_ads_create_campaign(
        customer_id: str,
        campaign_name: str,
        campaign_type: str,
        daily_budget: float,
        bidding_strategy: str = "MANUAL_CPC",
        status: str = "PAUSED",
        enable_search_network: bool = True,
        enable_search_partners: bool = False,
        enable_display_network: bool = False,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        target_cpa: Optional[float] = None,
        target_roas: Optional[float] = None
    ) -> str:
        """
        Create a new Google Ads campaign.

        Args:
            customer_id: Customer ID (without hyphens)
            campaign_name: Name for the campaign
            campaign_type: Type of campaign (SEARCH, DISPLAY, SHOPPING, VIDEO, PERFORMANCE_MAX, APP, LOCAL)
            daily_budget: Daily budget in currency units (e.g., 50.00 for $50/day)
            bidding_strategy: Bidding strategy (MANUAL_CPC, MAXIMIZE_CONVERSIONS, TARGET_CPA, TARGET_ROAS, etc.)
            status: Initial status (ENABLED or PAUSED, default: PAUSED for safety)
            enable_search_network: Target Google search network (default: True)
            enable_search_partners: Target search partner sites (default: False)
            enable_display_network: Target display network (default: False)
            start_date: Campaign start date in YYYY-MM-DD format (optional)
            end_date: Campaign end date in YYYY-MM-DD format (optional)
            target_cpa: Target CPA in currency units (required for TARGET_CPA strategy)
            target_roas: Target ROAS as decimal (required for TARGET_ROAS strategy)

        Returns:
            Success message with campaign details
        """
        with performance_logger.track_operation('create_campaign', customer_id=customer_id):
            try:
                # Get auth client
                client = get_auth_manager().get_client()

                # Convert budget to micros
                daily_budget_micros = int(daily_budget * 1_000_000)
                target_cpa_micros = int(target_cpa * 1_000_000) if target_cpa else None

                # Create campaign config
                config = CampaignConfig(
                    name=campaign_name,
                    campaign_type=CampaignType[campaign_type.upper()],
                    status=CampaignStatus[status.upper()],
                    daily_budget_micros=daily_budget_micros,
                    bidding_strategy_type=BiddingStrategyType[bidding_strategy.upper()],
                    target_cpa_micros=target_cpa_micros,
                    target_roas=target_roas,
                    enable_search_network=enable_search_network,
                    enable_search_partners=enable_search_partners,
                    enable_content_network=enable_display_network,
                    start_date=start_date,
                    end_date=end_date
                )

                # Create campaign manager
                campaign_manager = CampaignManager(client)

                # Create campaign
                result = campaign_manager.create_campaign(customer_id, config)

                # Audit log
                audit_logger.log_api_call(
                    customer_id=customer_id,
                    operation="create_campaign",
                    resource_type="campaign",
                    resource_id=result['campaign_id'],
                    action="create",
                    result="success",
                    details={
                        'name': campaign_name,
                        'type': campaign_type,
                        'budget': daily_budget
                    }
                )

                # Invalidate campaign cache
                cache_manager = get_cache_manager()
                cache_manager.invalidate(customer_id, ResourceType.CAMPAIGN)

                return (
                    f"✅ Campaign created successfully!\n\n"
                    f"**Campaign ID**: {result['campaign_id']}\n"
                    f"**Name**: {campaign_name}\n"
                    f"**Type**: {campaign_type}\n"
                    f"**Status**: {status}\n"
                    f"**Daily Budget**: ${daily_budget:,.2f}\n"
                    f"**Bidding Strategy**: {bidding_strategy}\n\n"
                    f"Campaign is now {status.lower()}. "
                    f"{'Enable it when ready to start running ads.' if status == 'PAUSED' else 'Ads will start serving soon.'}\n\n"
                    f"Next steps:\n"
                    f"1. Create ad groups\n"
                    f"2. Add keywords\n"
                    f"3. Create ads"
                )

            except Exception as e:
                error_msg = ErrorHandler.handle_error(e, context="create_campaign")
                audit_logger.log_api_call(
                    customer_id=customer_id,
                    operation="create_campaign",
                    resource_type="campaign",
                    action="create",
                    result="failure",
                    details={'error': str(e)}
                )
                return f"❌ Failed to create campaign: {error_msg}"

    # ============================================================================
    # Campaign Updates
    # ============================================================================

    @mcp.tool()
    def google_ads_update_campaign(
        customer_id: str,
        campaign_id: str,
        campaign_name: Optional[str] = None,
        status: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> str:
        """
        Update campaign settings.

        Args:
            customer_id: Customer ID (without hyphens)
            campaign_id: Campaign ID to update
            campaign_name: New campaign name (optional)
            status: New status (ENABLED, PAUSED, or REMOVED) (optional)
            start_date: New start date in YYYY-MM-DD format (optional)
            end_date: New end date in YYYY-MM-DD format (optional)

        Returns:
            Success message with updated fields
        """
        with performance_logger.track_operation('update_campaign', customer_id=customer_id):
            try:
                client = get_auth_manager().get_client()
                campaign_manager = CampaignManager(client)

                # Build updates dict
                updates = {}
                if campaign_name:
                    updates['name'] = campaign_name
                if status:
                    updates['status'] = status.upper()
                if start_date:
                    updates['start_date'] = start_date
                if end_date:
                    updates['end_date'] = end_date

                if not updates:
                    return "⚠️ No updates specified. Provide at least one field to update."

                # Update campaign
                result = campaign_manager.update_campaign(customer_id, campaign_id, updates)

                # Audit log
                audit_logger.log_api_call(
                    customer_id=customer_id,
                    operation="update_campaign",
                    resource_type="campaign",
                    resource_id=campaign_id,
                    action="update",
                    result="success",
                    details={'updated_fields': result['updated_fields']}
                )

                # Invalidate cache
                get_cache_manager().invalidate(customer_id, ResourceType.CAMPAIGN)

                return (
                    f"✅ Campaign {campaign_id} updated successfully!\n\n"
                    f"**Updated Fields**: {', '.join(result['updated_fields'])}\n\n"
                    f"Changes have been applied to the campaign."
                )

            except Exception as e:
                error_msg = ErrorHandler.handle_error(e, context="update_campaign")
                return f"❌ Failed to update campaign: {error_msg}"

    @mcp.tool()
    def google_ads_update_campaign_status_v2(
        customer_id: str,
        campaign_id: str,
        status: str
    ) -> str:
        """
        Update campaign status (enable, pause, or remove).

        Args:
            customer_id: Customer ID (without hyphens)
            campaign_id: Campaign ID
            status: New status (ENABLED, PAUSED, or REMOVED)

        Returns:
            Success message
        """
        with performance_logger.track_operation('update_campaign_status', customer_id=customer_id):
            try:
                client = get_auth_manager().get_client()
                campaign_manager = CampaignManager(client)

                status_upper = status.upper()
                result = campaign_manager.update_campaign_status(
                    customer_id,
                    campaign_id,
                    CampaignStatus[status_upper]
                )

                # Audit log
                audit_logger.log_api_call(
                    customer_id=customer_id,
                    operation="update_campaign_status",
                    resource_type="campaign",
                    resource_id=campaign_id,
                    action="update",
                    result="success",
                    details={'new_status': status_upper}
                )

                # Invalidate cache
                get_cache_manager().invalidate(customer_id, ResourceType.CAMPAIGN)

                status_messages = {
                    "ENABLED": "Campaign is now active and ads will start serving.",
                    "PAUSED": "Campaign is now paused. Ads have stopped serving.",
                    "REMOVED": "Campaign has been removed and cannot be re-enabled."
                }

                return (
                    f"✅ Campaign {campaign_id} status updated to {status_upper}\n\n"
                    f"{status_messages.get(status_upper, 'Status updated successfully.')}"
                )

            except Exception as e:
                error_msg = ErrorHandler.handle_error(e, context="update_campaign_status")
                return f"❌ Failed to update campaign status: {error_msg}"

    @mcp.tool()
    def google_ads_update_campaign_budget_v2(
        customer_id: str,
        campaign_id: str,
        daily_budget: float
    ) -> str:
        """
        Update campaign daily budget.

        Args:
            customer_id: Customer ID (without hyphens)
            campaign_id: Campaign ID
            daily_budget: New daily budget in currency units (e.g., 100.00 for $100/day)

        Returns:
            Success message with budget details
        """
        with performance_logger.track_operation('update_campaign_budget', customer_id=customer_id):
            try:
                client = get_auth_manager().get_client()
                campaign_manager = CampaignManager(client)

                daily_budget_micros = int(daily_budget * 1_000_000)

                result = campaign_manager.update_campaign_budget(
                    customer_id,
                    campaign_id,
                    daily_budget_micros
                )

                # Audit log
                audit_logger.log_api_call(
                    customer_id=customer_id,
                    operation="update_campaign_budget",
                    resource_type="campaign",
                    resource_id=campaign_id,
                    action="update",
                    result="success",
                    details={'new_budget': daily_budget}
                )

                # Invalidate cache
                get_cache_manager().invalidate(customer_id, ResourceType.CAMPAIGN)

                return (
                    f"✅ Campaign {campaign_id} budget updated successfully!\n\n"
                    f"**New Daily Budget**: ${result['new_budget_amount']:,.2f}\n\n"
                    f"The new budget will take effect within a few hours. "
                    f"Monitor performance closely over the next few days to see the impact."
                )

            except Exception as e:
                error_msg = ErrorHandler.handle_error(e, context="update_campaign_budget")
                return f"❌ Failed to update campaign budget: {error_msg}"

    # ============================================================================
    # Campaign Targeting
    # ============================================================================

    @mcp.tool()
    def google_ads_set_campaign_locations(
        customer_id: str,
        campaign_id: str,
        location_ids: List[str],
        negative_location_ids: Optional[List[str]] = None
    ) -> str:
        """
        Set location targeting for a campaign.

        Args:
            customer_id: Customer ID (without hyphens)
            campaign_id: Campaign ID
            location_ids: List of geo target constant IDs to target
            negative_location_ids: List of geo target constant IDs to exclude (optional)

        Returns:
            Success message

        Note: Common location IDs:
        - 2840: United States
        - 2826: United Kingdom
        - 2124: Canada
        - 2036: Australia
        Use Google Ads location targeting tool to find specific IDs
        """
        with performance_logger.track_operation('set_campaign_locations', customer_id=customer_id):
            try:
                client = get_auth_manager().get_client()
                campaign_manager = CampaignManager(client)

                # Build location targets
                locations = [
                    LocationTarget(location_id=loc_id, is_negative=False)
                    for loc_id in location_ids
                ]

                if negative_location_ids:
                    locations.extend([
                        LocationTarget(location_id=loc_id, is_negative=True)
                        for loc_id in negative_location_ids
                    ])

                result = campaign_manager.set_location_targets(
                    customer_id,
                    campaign_id,
                    locations
                )

                # Audit log
                audit_logger.log_api_call(
                    customer_id=customer_id,
                    operation="set_campaign_locations",
                    resource_type="campaign",
                    resource_id=campaign_id,
                    action="update",
                    result="success",
                    details={
                        'positive_locations': len(location_ids),
                        'negative_locations': len(negative_location_ids or [])
                    }
                )

                return (
                    f"✅ Location targeting set for campaign {campaign_id}\n\n"
                    f"**Targeted Locations**: {len(location_ids)}\n"
                    f"**Excluded Locations**: {len(negative_location_ids or [])}\n\n"
                    f"Campaign will now show ads in the specified locations."
                )

            except Exception as e:
                error_msg = ErrorHandler.handle_error(e, context="set_campaign_locations")
                return f"❌ Failed to set location targeting: {error_msg}"

    @mcp.tool()
    def google_ads_set_campaign_languages(
        customer_id: str,
        campaign_id: str,
        language_codes: List[str]
    ) -> str:
        """
        Set language targeting for a campaign.

        Args:
            customer_id: Customer ID (without hyphens)
            campaign_id: Campaign ID
            language_codes: List of language constant IDs

        Returns:
            Success message

        Note: Common language IDs:
        - 1000: English
        - 1003: Spanish
        - 1002: French
        - 1001: German
        - 1005: Chinese (Simplified)
        """
        with performance_logger.track_operation('set_campaign_languages', customer_id=customer_id):
            try:
                client = get_auth_manager().get_client()
                campaign_manager = CampaignManager(client)

                # Build language targets
                languages = [
                    LanguageTarget(language_constant_id=lang_id)
                    for lang_id in language_codes
                ]

                result = campaign_manager.set_language_targets(
                    customer_id,
                    campaign_id,
                    languages
                )

                # Audit log
                audit_logger.log_api_call(
                    customer_id=customer_id,
                    operation="set_campaign_languages",
                    resource_type="campaign",
                    resource_id=campaign_id,
                    action="update",
                    result="success",
                    details={'language_count': len(language_codes)}
                )

                return (
                    f"✅ Language targeting set for campaign {campaign_id}\n\n"
                    f"**Languages Added**: {len(language_codes)}\n\n"
                    f"Campaign will now show ads to users who speak these languages."
                )

            except Exception as e:
                error_msg = ErrorHandler.handle_error(e, context="set_campaign_languages")
                return f"❌ Failed to set language targeting: {error_msg}"

    # ============================================================================
    # Campaign Information
    # ============================================================================

    @mcp.tool()
    def google_ads_get_campaign_details(
        customer_id: str,
        campaign_id: str
    ) -> str:
        """
        Get detailed information about a campaign.

        Args:
            customer_id: Customer ID (without hyphens)
            campaign_id: Campaign ID

        Returns:
            Detailed campaign information
        """
        with performance_logger.track_operation('get_campaign_details', customer_id=customer_id):
            try:
                client = get_auth_manager().get_client()
                campaign_manager = CampaignManager(client)

                details = campaign_manager.get_campaign_details(customer_id, campaign_id)

                if not details:
                    return f"❌ Campaign {campaign_id} not found"

                output = f"# Campaign Details: {details['name']}\n\n"
                output += f"**ID**: {details['id']}\n"
                output += f"**Type**: {details['type']}\n"
                output += f"**Status**: {details['status']}\n"
                output += f"**Bidding Strategy**: {details['bidding_strategy']}\n\n"

                output += "## Dates\n"
                output += f"- **Start Date**: {details['start_date'] or 'Not set'}\n"
                output += f"- **End Date**: {details['end_date'] or 'No end date'}\n\n"

                output += "## Network Settings\n"
                output += f"- **Google Search**: {details['network_settings']['google_search']}\n"
                output += f"- **Search Network**: {details['network_settings']['search_network']}\n"
                output += f"- **Display Network**: {details['network_settings']['content_network']}\n\n"

                if details['metrics']:
                    output += "## Performance Metrics\n"
                    output += f"- **Cost**: ${details['metrics']['cost']:,.2f}\n"
                    output += f"- **Clicks**: {details['metrics']['clicks']:,}\n"
                    output += f"- **Impressions**: {details['metrics']['impressions']:,}\n"
                    output += f"- **Conversions**: {details['metrics']['conversions']}\n"

                return output

            except Exception as e:
                error_msg = ErrorHandler.handle_error(e, context="get_campaign_details")
                return f"❌ Failed to get campaign details: {error_msg}"

    # ============================================================================
    # Device Bid Adjustments
    # ============================================================================

    @mcp.tool()
    def google_ads_set_device_bid_adjustments(
        customer_id: str,
        campaign_id: str,
        mobile_modifier: Optional[float] = None,
        desktop_modifier: Optional[float] = None,
        tablet_modifier: Optional[float] = None
    ) -> str:
        """
        Set device bid adjustments for a campaign.

        Args:
            customer_id: Customer ID (without hyphens)
            campaign_id: Campaign ID
            mobile_modifier: Bid modifier for mobile devices (1.2 = +20%, 0.8 = -20%, None = no change)
            desktop_modifier: Bid modifier for desktop devices (1.2 = +20%, 0.8 = -20%, None = no change)
            tablet_modifier: Bid modifier for tablet devices (1.2 = +20%, 0.8 = -20%, None = no change)

        Returns:
            Success message with applied modifiers

        Note:
        - 1.0 = 0% adjustment (no change)
        - 1.2 = +20% bid adjustment
        - 0.8 = -20% bid adjustment
        - 0.0 = -100% adjustment (effectively disabled)
        """
        with performance_logger.track_operation('set_device_bid_adjustments', customer_id=customer_id):
            try:
                client = get_auth_manager().get_client()
                campaign_manager = CampaignManager(client)

                if mobile_modifier is None and desktop_modifier is None and tablet_modifier is None:
                    return "⚠️ No device modifiers specified. Provide at least one device modifier."

                result = campaign_manager.set_device_bid_adjustments(
                    customer_id,
                    campaign_id,
                    mobile_modifier,
                    desktop_modifier,
                    tablet_modifier
                )

                # Audit log
                audit_logger.log_api_call(
                    customer_id=customer_id,
                    operation="set_device_bid_adjustments",
                    resource_type="campaign",
                    resource_id=campaign_id,
                    action="update",
                    result="success",
                    details={
                        'mobile': mobile_modifier,
                        'desktop': desktop_modifier,
                        'tablet': tablet_modifier
                    }
                )

                # Invalidate cache
                get_cache_manager().invalidate(customer_id, ResourceType.CAMPAIGN)

                output = f"✅ Device bid adjustments set for campaign {campaign_id}\n\n"

                if mobile_modifier is not None:
                    pct = (mobile_modifier - 1.0) * 100
                    output += f"**Mobile**: {mobile_modifier:.2f} ({pct:+.0f}%)\n"
                if desktop_modifier is not None:
                    pct = (desktop_modifier - 1.0) * 100
                    output += f"**Desktop**: {desktop_modifier:.2f} ({pct:+.0f}%)\n"
                if tablet_modifier is not None:
                    pct = (tablet_modifier - 1.0) * 100
                    output += f"**Tablet**: {tablet_modifier:.2f} ({pct:+.0f}%)\n"

                output += f"\n{result['message']}"

                return output

            except Exception as e:
                error_msg = ErrorHandler.handle_error(e, context="set_device_bid_adjustments")
                return f"❌ Failed to set device bid adjustments: {error_msg}"

    # ============================================================================
    # Ad Scheduling
    # ============================================================================

    @mcp.tool()
    def google_ads_set_campaign_schedule(
        customer_id: str,
        campaign_id: str,
        schedules: List[Dict[str, Any]]
    ) -> str:
        """
        Set ad scheduling (dayparting) for a campaign.

        Args:
            customer_id: Customer ID (without hyphens)
            campaign_id: Campaign ID
            schedules: List of schedule dictionaries with:
                - day_of_week: Day name (MONDAY, TUESDAY, etc.) or numeric (0=Sunday, 6=Saturday)
                - start_hour: Hour to start (0-23)
                - start_minute: Minute to start (0, 15, 30, 45)
                - end_hour: Hour to end (0-24)
                - end_minute: Minute to end (0, 15, 30, 45)
                - bid_modifier: Optional bid adjustment (1.2 = +20%, 0.8 = -20%)

        Returns:
            Success message with schedule summary

        Example:
            schedules = [
                {
                    "day_of_week": "MONDAY",
                    "start_hour": 9,
                    "start_minute": 0,
                    "end_hour": 17,
                    "end_minute": 0,
                    "bid_modifier": 1.2
                }
            ]
        """
        with performance_logger.track_operation('set_campaign_schedule', customer_id=customer_id):
            try:
                client = get_auth_manager().get_client()
                campaign_manager = CampaignManager(client)

                if not schedules:
                    return "⚠️ No schedules provided. Provide at least one schedule."

                result = campaign_manager.set_ad_schedule(
                    customer_id,
                    campaign_id,
                    schedules
                )

                # Audit log
                audit_logger.log_api_call(
                    customer_id=customer_id,
                    operation="set_campaign_schedule",
                    resource_type="campaign",
                    resource_id=campaign_id,
                    action="update",
                    result="success",
                    details={'schedule_count': len(schedules)}
                )

                # Invalidate cache
                get_cache_manager().invalidate(customer_id, ResourceType.CAMPAIGN)

                output = f"✅ Ad schedule set for campaign {campaign_id}\n\n"
                output += f"**Schedules Added**: {len(schedules)}\n\n"

                for schedule in schedules[:5]:  # Show first 5
                    day = schedule.get('day_of_week', 'Unknown')
                    start_h = schedule.get('start_hour', 0)
                    start_m = schedule.get('start_minute', 0)
                    end_h = schedule.get('end_hour', 24)
                    end_m = schedule.get('end_minute', 0)
                    modifier = schedule.get('bid_modifier', 1.0)

                    output += f"- {day}: {start_h:02d}:{start_m:02d} - {end_h:02d}:{end_m:02d}"
                    if modifier != 1.0:
                        pct = (modifier - 1.0) * 100
                        output += f" (Bid: {pct:+.0f}%)"
                    output += "\n"

                if len(schedules) > 5:
                    output += f"... and {len(schedules) - 5} more\n"

                output += f"\n{result['message']}"

                return output

            except Exception as e:
                error_msg = ErrorHandler.handle_error(e, context="set_campaign_schedule")
                return f"❌ Failed to set campaign schedule: {error_msg}"

    # ============================================================================
    # Campaign Duplication
    # ============================================================================

    @mcp.tool()
    def google_ads_duplicate_campaign(
        customer_id: str,
        campaign_id: str,
        new_name: str,
        include_ad_groups: bool = False
    ) -> str:
        """
        Duplicate an existing campaign with all settings.

        Args:
            customer_id: Customer ID (without hyphens)
            campaign_id: Campaign ID to duplicate
            new_name: Name for the new campaign
            include_ad_groups: Whether to copy ad groups and their content (default: False)

        Returns:
            Success message with new campaign details

        Note: The new campaign will be created in PAUSED status for safety.
        """
        with performance_logger.track_operation('duplicate_campaign', customer_id=customer_id):
            try:
                client = get_auth_manager().get_client()
                campaign_manager = CampaignManager(client)

                result = campaign_manager.duplicate_campaign(
                    customer_id,
                    campaign_id,
                    new_name,
                    include_ad_groups
                )

                # Audit log
                audit_logger.log_api_call(
                    customer_id=customer_id,
                    operation="duplicate_campaign",
                    resource_type="campaign",
                    resource_id=campaign_id,
                    action="create",
                    result="success",
                    details={
                        'new_campaign_id': result['new_campaign_id'],
                        'new_name': new_name,
                        'include_ad_groups': include_ad_groups
                    }
                )

                # Invalidate cache
                get_cache_manager().invalidate(customer_id, ResourceType.CAMPAIGN)

                output = f"✅ Campaign duplicated successfully!\n\n"
                output += f"**Original Campaign**: {campaign_id}\n"
                output += f"**New Campaign ID**: {result['new_campaign_id']}\n"
                output += f"**New Name**: {new_name}\n"
                output += f"**Status**: PAUSED (for safety)\n"

                if include_ad_groups:
                    output += f"**Ad Groups Copied**: Yes\n"
                else:
                    output += f"**Ad Groups Copied**: No\n"

                output += f"\n{result['message']}\n\n"
                output += "The new campaign is paused. Enable it when you're ready to start serving ads."

                return output

            except Exception as e:
                error_msg = ErrorHandler.handle_error(e, context="duplicate_campaign")
                return f"❌ Failed to duplicate campaign: {error_msg}"

    # ============================================================================
    # Shared Budgets
    # ============================================================================

    @mcp.tool()
    def google_ads_create_shared_budget(
        customer_id: str,
        budget_name: str,
        daily_amount: float,
        delivery_method: str = "STANDARD"
    ) -> str:
        """
        Create a shared budget that can be used across multiple campaigns.

        Args:
            customer_id: Customer ID (without hyphens)
            budget_name: Name for the shared budget
            daily_amount: Daily budget amount in currency units (e.g., 100.00 for $100/day)
            delivery_method: Budget delivery method (STANDARD or ACCELERATED, default: STANDARD)

        Returns:
            Success message with budget resource name

        Note: After creating a shared budget, use google_ads_assign_shared_budget to assign it to campaigns.
        """
        with performance_logger.track_operation('create_shared_budget', customer_id=customer_id):
            try:
                client = get_auth_manager().get_client()
                campaign_manager = CampaignManager(client)

                daily_amount_micros = int(daily_amount * 1_000_000)

                result = campaign_manager.create_shared_budget(
                    customer_id,
                    budget_name,
                    daily_amount_micros,
                    delivery_method.upper()
                )

                # Audit log
                audit_logger.log_api_call(
                    customer_id=customer_id,
                    operation="create_shared_budget",
                    resource_type="campaign_budget",
                    resource_id=result['budget_id'],
                    action="create",
                    result="success",
                    details={
                        'name': budget_name,
                        'amount': daily_amount,
                        'delivery_method': delivery_method
                    }
                )

                # Invalidate cache
                get_cache_manager().invalidate(customer_id, ResourceType.CAMPAIGN)

                output = f"✅ Shared budget created successfully!\n\n"
                output += f"**Budget ID**: {result['budget_id']}\n"
                output += f"**Name**: {budget_name}\n"
                output += f"**Daily Amount**: ${daily_amount:,.2f}\n"
                output += f"**Delivery Method**: {delivery_method}\n"
                output += f"**Resource Name**: `{result['resource_name']}`\n\n"
                output += "Use the resource name to assign this budget to campaigns with google_ads_assign_shared_budget.\n\n"
                output += "Example campaigns that can share this budget:\n"
                output += "- Multiple campaigns targeting the same product\n"
                output += "- Campaigns targeting different locations with a shared total budget\n"
                output += "- Campaign variants for A/B testing"

                return output

            except Exception as e:
                error_msg = ErrorHandler.handle_error(e, context="create_shared_budget")
                return f"❌ Failed to create shared budget: {error_msg}"

    @mcp.tool()
    def google_ads_assign_shared_budget(
        customer_id: str,
        campaign_id: str,
        budget_resource_name: str
    ) -> str:
        """
        Assign a shared budget to a campaign.

        Args:
            customer_id: Customer ID (without hyphens)
            campaign_id: Campaign ID to update
            budget_resource_name: Resource name of the shared budget (from google_ads_create_shared_budget)

        Returns:
            Success message

        Note: The campaign will switch from its individual budget to the shared budget.
        """
        with performance_logger.track_operation('assign_shared_budget', customer_id=customer_id):
            try:
                client = get_auth_manager().get_client()
                campaign_manager = CampaignManager(client)

                result = campaign_manager.assign_shared_budget(
                    customer_id,
                    campaign_id,
                    budget_resource_name
                )

                # Audit log
                audit_logger.log_api_call(
                    customer_id=customer_id,
                    operation="assign_shared_budget",
                    resource_type="campaign",
                    resource_id=campaign_id,
                    action="update",
                    result="success",
                    details={'budget_resource_name': budget_resource_name}
                )

                # Invalidate cache
                get_cache_manager().invalidate(customer_id, ResourceType.CAMPAIGN)

                output = f"✅ Shared budget assigned to campaign {campaign_id}\n\n"
                output += f"**Budget Resource**: {budget_resource_name}\n\n"
                output += f"{result['message']}\n\n"
                output += "The campaign now shares its budget with other campaigns using the same budget."

                return output

            except Exception as e:
                error_msg = ErrorHandler.handle_error(e, context="assign_shared_budget")
                return f"❌ Failed to assign shared budget: {error_msg}"

    # ============================================================================
    # Campaign Exclusions
    # ============================================================================

    @mcp.tool()
    def google_ads_add_campaign_exclusions(
        customer_id: str,
        campaign_id: str,
        placement_exclusions: Optional[List[str]] = None,
        ip_exclusions: Optional[List[str]] = None
    ) -> str:
        """
        Add placement and IP exclusions to a campaign.

        Args:
            customer_id: Customer ID (without hyphens)
            campaign_id: Campaign ID
            placement_exclusions: List of URLs/apps to exclude (e.g., ["example.com", "youtube.com/channel/ABC"])
            ip_exclusions: List of IP addresses to exclude (e.g., ["192.168.1.1", "10.0.0.0/24"])

        Returns:
            Success message with exclusion summary

        Note:
        - Placement exclusions prevent ads from showing on specific websites, YouTube channels, or apps
        - IP exclusions prevent ads from showing to specific IP addresses (useful for excluding office IPs)
        - CIDR notation supported for IP ranges (e.g., "10.0.0.0/24")
        """
        with performance_logger.track_operation('add_campaign_exclusions', customer_id=customer_id):
            try:
                client = get_auth_manager().get_client()
                campaign_manager = CampaignManager(client)

                if not placement_exclusions and not ip_exclusions:
                    return "⚠️ No exclusions specified. Provide placement_exclusions or ip_exclusions."

                result = campaign_manager.add_campaign_exclusions(
                    customer_id,
                    campaign_id,
                    placement_exclusions,
                    ip_exclusions
                )

                # Audit log
                audit_logger.log_api_call(
                    customer_id=customer_id,
                    operation="add_campaign_exclusions",
                    resource_type="campaign",
                    resource_id=campaign_id,
                    action="update",
                    result="success",
                    details={
                        'placement_count': len(placement_exclusions or []),
                        'ip_count': len(ip_exclusions or [])
                    }
                )

                # Invalidate cache
                get_cache_manager().invalidate(customer_id, ResourceType.CAMPAIGN)

                output = f"✅ Exclusions added to campaign {campaign_id}\n\n"

                if placement_exclusions:
                    output += f"**Placement Exclusions**: {len(placement_exclusions)}\n"
                    for placement in placement_exclusions[:5]:  # Show first 5
                        output += f"  - {placement}\n"
                    if len(placement_exclusions) > 5:
                        output += f"  ... and {len(placement_exclusions) - 5} more\n"
                    output += "\n"

                if ip_exclusions:
                    output += f"**IP Exclusions**: {len(ip_exclusions)}\n"
                    for ip in ip_exclusions[:5]:  # Show first 5
                        output += f"  - {ip}\n"
                    if len(ip_exclusions) > 5:
                        output += f"  ... and {len(ip_exclusions) - 5} more\n"
                    output += "\n"

                output += f"{result['message']}"

                return output

            except Exception as e:
                error_msg = ErrorHandler.handle_error(e, context="add_campaign_exclusions")
                return f"❌ Failed to add campaign exclusions: {error_msg}"

    logger.info("Campaign management tools registered")
