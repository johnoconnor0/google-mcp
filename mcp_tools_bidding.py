"""
MCP Tools - Bidding Strategy Management

Provides 12 MCP tools for portfolio bidding strategies and bid adjustments:

Bidding Strategy Operations (4 tools):
1. google_ads_create_bidding_strategy - Create portfolio bid strategies
2. google_ads_update_bidding_strategy - Update strategy settings
3. google_ads_assign_bidding_strategy - Assign strategy to campaigns
4. google_ads_get_bidding_strategy_performance - Performance metrics

Bid Adjustments (5 tools):
5. google_ads_set_device_bid_adjustments - Mobile/desktop/tablet modifiers
6. google_ads_set_location_bid_adjustments - Geographic modifiers
7. google_ads_set_ad_schedule_bid_adjustments - Dayparting (time-based) modifiers
8. google_ads_list_bid_adjustments - View all bid adjustments for campaign

Smart Bidding Features (3 tools):
9. google_ads_get_bid_simulator - Bid simulation data
10. google_ads_get_bid_recommendations - AI-powered bid suggestions
11. google_ads_list_bidding_strategies - List all portfolio strategies
12. google_ads_get_bidding_strategy_details - Get full strategy configuration
"""

from typing import Optional, List, Dict, Any
from bidding_strategy_manager import (
    BiddingStrategyManager,
    BiddingStrategyConfig,
    BiddingStrategyType,
    ImpressionShareLocation,
    Device,
    DayOfWeek,
    AdScheduleConfig
)
from auth_manager import get_auth_manager
from error_handler import ErrorHandler
from logger import performance_logger, audit_logger
from cache_manager import get_cache_manager, ResourceType
import json


def register_bidding_tools(mcp):
    """Register all bidding strategy management tools with the MCP server.

    Args:
        mcp: FastMCP server instance
    """

    # ============================================================================
    # Bidding Strategy Operations
    # ============================================================================

    @mcp.tool()
    def google_ads_create_bidding_strategy(
        customer_id: str,
        strategy_name: str,
        strategy_type: str,
        target_cpa: Optional[float] = None,
        target_roas: Optional[float] = None,
        target_impression_share: Optional[float] = None,
        impression_share_location: Optional[str] = None,
        max_cpc_bid: Optional[float] = None,
        enhanced_cpc: bool = False
    ) -> str:
        """
        Create a portfolio bidding strategy for shared use across campaigns.

        Portfolio bidding strategies allow you to apply the same automated bidding
        strategy across multiple campaigns, enabling Google's AI to optimize bids
        based on a larger pool of data.

        Strategy Types:
        - TARGET_CPA: Optimize for target cost per acquisition
        - TARGET_ROAS: Optimize for target return on ad spend
        - MAXIMIZE_CONVERSIONS: Get the most conversions within budget
        - MAXIMIZE_CONVERSION_VALUE: Maximize total conversion value
        - TARGET_IMPRESSION_SHARE: Target specific impression share percentage
        - MANUAL_CPC: Manual bidding with optional enhanced CPC

        Args:
            customer_id: Customer ID (without hyphens)
            strategy_name: Name for the bidding strategy (e.g., "High Value Customers")
            strategy_type: Strategy type (TARGET_CPA, TARGET_ROAS, MAXIMIZE_CONVERSIONS, etc.)
            target_cpa: Target cost per acquisition in currency units (required for TARGET_CPA)
            target_roas: Target return on ad spend as decimal (e.g., 4.0 = 400% ROAS) (for TARGET_ROAS)
            target_impression_share: Target impression share 0.0-1.0 (e.g., 0.75 = 75%) (for TARGET_IMPRESSION_SHARE)
            impression_share_location: Where to target impressions (ANYWHERE_ON_PAGE, TOP_OF_PAGE, ABSOLUTE_TOP_OF_PAGE)
            max_cpc_bid: Maximum CPC bid limit in currency units (optional for TARGET_IMPRESSION_SHARE)
            enhanced_cpc: Enable enhanced CPC for MANUAL_CPC strategy

        Returns:
            Success message with strategy ID and configuration details

        Example:
            google_ads_create_bidding_strategy(
                customer_id="1234567890",
                strategy_name="Target CPA - $25",
                strategy_type="TARGET_CPA",
                target_cpa=25.00
            )
        """
        with performance_logger.track_operation('create_bidding_strategy', customer_id=customer_id):
            try:
                client = get_auth_manager().get_client()
                bidding_manager = BiddingStrategyManager(client)

                # Validate strategy type
                try:
                    strategy_enum = BiddingStrategyType[strategy_type.upper()]
                except KeyError:
                    valid_types = [t.value for t in BiddingStrategyType]
                    return f"❌ Invalid strategy type '{strategy_type}'. Valid types: {', '.join(valid_types)}"

                # Validate required parameters
                if strategy_enum == BiddingStrategyType.TARGET_CPA and target_cpa is None:
                    return "❌ target_cpa is required for TARGET_CPA strategy"

                if strategy_enum == BiddingStrategyType.TARGET_ROAS and target_roas is None:
                    return "❌ target_roas is required for TARGET_ROAS strategy"

                if strategy_enum == BiddingStrategyType.TARGET_IMPRESSION_SHARE:
                    if target_impression_share is None:
                        return "❌ target_impression_share is required for TARGET_IMPRESSION_SHARE strategy"
                    if not (0.0 <= target_impression_share <= 1.0):
                        return "❌ target_impression_share must be between 0.0 and 1.0"

                # Build configuration
                config = BiddingStrategyConfig(
                    name=strategy_name,
                    strategy_type=strategy_enum,
                    target_cpa_micros=int(target_cpa * 1_000_000) if target_cpa else None,
                    target_roas=target_roas,
                    target_impression_share=target_impression_share,
                    location=ImpressionShareLocation[impression_share_location.upper()] if impression_share_location else None,
                    cpc_bid_ceiling_micros=int(max_cpc_bid * 1_000_000) if max_cpc_bid else None,
                    enhanced_cpc_enabled=enhanced_cpc if strategy_enum == BiddingStrategyType.MANUAL_CPC else None
                )

                # Create strategy
                result = bidding_manager.create_bidding_strategy(customer_id, config)

                # Audit log
                audit_logger.log_api_call(
                    customer_id=customer_id,
                    operation="create_bidding_strategy",
                    resource_type="bidding_strategy",
                    resource_id=result['bidding_strategy_id'],
                    action="create",
                    result="success",
                    details={'strategy_type': strategy_type, 'name': strategy_name}
                )

                # Invalidate cache
                get_cache_manager().invalidate(customer_id, ResourceType.CAMPAIGN)

                # Format response
                output = f"✅ Portfolio bidding strategy created successfully!\n\n"
                output += f"**Strategy ID**: {result['bidding_strategy_id']}\n"
                output += f"**Name**: {result['name']}\n"
                output += f"**Type**: {result['type']}\n\n"

                # Add strategy-specific details
                if strategy_enum == BiddingStrategyType.TARGET_CPA:
                    output += f"**Target CPA**: ${target_cpa:.2f}\n"
                elif strategy_enum == BiddingStrategyType.TARGET_ROAS:
                    output += f"**Target ROAS**: {target_roas:.2f}x ({target_roas * 100:.0f}%)\n"
                elif strategy_enum == BiddingStrategyType.TARGET_IMPRESSION_SHARE:
                    output += f"**Target Impression Share**: {target_impression_share * 100:.0f}%\n"
                    if impression_share_location:
                        output += f"**Location**: {impression_share_location}\n"
                    if max_cpc_bid:
                        output += f"**Max CPC Bid**: ${max_cpc_bid:.2f}\n"

                output += f"\n**Next Steps**:\n"
                output += f"1. Assign this strategy to campaigns using `google_ads_assign_bidding_strategy`\n"
                output += f"2. Monitor performance after 2-3 weeks for optimization\n"
                output += f"3. Adjust targets based on actual conversion data\n"

                return output

            except Exception as e:
                error_msg = ErrorHandler.handle_error(e, context="create_bidding_strategy")
                return f"❌ Failed to create bidding strategy: {error_msg}"

    @mcp.tool()
    def google_ads_update_bidding_strategy(
        customer_id: str,
        bidding_strategy_id: str,
        strategy_name: Optional[str] = None,
        target_cpa: Optional[float] = None,
        target_roas: Optional[float] = None,
        target_impression_share: Optional[float] = None,
        max_cpc_bid: Optional[float] = None
    ) -> str:
        """
        Update an existing portfolio bidding strategy's settings.

        Args:
            customer_id: Customer ID (without hyphens)
            bidding_strategy_id: Bidding strategy ID to update
            strategy_name: New name for the strategy (optional)
            target_cpa: New target CPA in currency units (for TARGET_CPA strategies)
            target_roas: New target ROAS as decimal (for TARGET_ROAS strategies)
            target_impression_share: New target impression share 0.0-1.0 (for TARGET_IMPRESSION_SHARE)
            max_cpc_bid: New maximum CPC bid limit (for TARGET_IMPRESSION_SHARE)

        Returns:
            Success message with updated configuration

        Example:
            google_ads_update_bidding_strategy(
                customer_id="1234567890",
                bidding_strategy_id="12345",
                target_cpa=30.00
            )
        """
        with performance_logger.track_operation('update_bidding_strategy', customer_id=customer_id):
            try:
                client = get_auth_manager().get_client()
                bidding_manager = BiddingStrategyManager(client)

                # Determine strategy type from existing strategy
                # We'll need to query it first to know which type to update
                ga_service = client.get_service("GoogleAdsService")
                query = f"""
                    SELECT
                        bidding_strategy.id,
                        bidding_strategy.name,
                        bidding_strategy.type
                    FROM bidding_strategy
                    WHERE bidding_strategy.id = {bidding_strategy_id}
                """

                response = ga_service.search(customer_id=customer_id, query=query)
                results = list(response)

                if not results:
                    return f"❌ Bidding strategy {bidding_strategy_id} not found"

                row = results[0]
                strategy_type_name = row.bidding_strategy.type.name
                strategy_enum = BiddingStrategyType[strategy_type_name]

                # Build update config
                config = BiddingStrategyConfig(
                    name=strategy_name or row.bidding_strategy.name,
                    strategy_type=strategy_enum,
                    target_cpa_micros=int(target_cpa * 1_000_000) if target_cpa else None,
                    target_roas=target_roas,
                    target_impression_share=target_impression_share,
                    cpc_bid_ceiling_micros=int(max_cpc_bid * 1_000_000) if max_cpc_bid else None
                )

                # Update strategy
                result = bidding_manager.update_bidding_strategy(customer_id, bidding_strategy_id, config)

                # Audit log
                audit_logger.log_api_call(
                    customer_id=customer_id,
                    operation="update_bidding_strategy",
                    resource_type="bidding_strategy",
                    resource_id=bidding_strategy_id,
                    action="update",
                    result="success",
                    details={'updated_fields': result['updated_fields']}
                )

                # Invalidate cache
                get_cache_manager().invalidate(customer_id, ResourceType.CAMPAIGN)

                output = f"✅ Bidding strategy updated successfully!\n\n"
                output += f"**Strategy ID**: {bidding_strategy_id}\n"
                output += f"**Updated Fields**: {', '.join(result['updated_fields'])}\n\n"

                if strategy_name:
                    output += f"**New Name**: {strategy_name}\n"
                if target_cpa:
                    output += f"**New Target CPA**: ${target_cpa:.2f}\n"
                if target_roas:
                    output += f"**New Target ROAS**: {target_roas:.2f}x\n"
                if target_impression_share:
                    output += f"**New Target Impression Share**: {target_impression_share * 100:.0f}%\n"

                output += f"\nChanges will take effect within 24 hours as the learning algorithm adjusts."

                return output

            except Exception as e:
                error_msg = ErrorHandler.handle_error(e, context="update_bidding_strategy")
                return f"❌ Failed to update bidding strategy: {error_msg}"

    @mcp.tool()
    def google_ads_assign_bidding_strategy(
        customer_id: str,
        campaign_id: str,
        bidding_strategy_id: str
    ) -> str:
        """
        Assign a portfolio bidding strategy to a campaign.

        This replaces the campaign's current bidding strategy with the specified
        portfolio strategy, allowing Google's AI to optimize bids across all
        campaigns using this strategy.

        Args:
            customer_id: Customer ID (without hyphens)
            campaign_id: Campaign ID to update
            bidding_strategy_id: Portfolio bidding strategy ID to assign

        Returns:
            Success message confirming assignment

        Example:
            google_ads_assign_bidding_strategy(
                customer_id="1234567890",
                campaign_id="111111111",
                bidding_strategy_id="12345"
            )
        """
        with performance_logger.track_operation('assign_bidding_strategy', customer_id=customer_id):
            try:
                client = get_auth_manager().get_client()
                bidding_manager = BiddingStrategyManager(client)

                result = bidding_manager.assign_bidding_strategy_to_campaign(
                    customer_id, campaign_id, bidding_strategy_id
                )

                # Audit log
                audit_logger.log_api_call(
                    customer_id=customer_id,
                    operation="assign_bidding_strategy",
                    resource_type="campaign",
                    resource_id=campaign_id,
                    action="update",
                    result="success",
                    details={'bidding_strategy_id': bidding_strategy_id}
                )

                # Invalidate cache
                get_cache_manager().invalidate(customer_id, ResourceType.CAMPAIGN)

                output = f"✅ Bidding strategy assigned successfully!\n\n"
                output += f"**Campaign ID**: {campaign_id}\n"
                output += f"**Bidding Strategy ID**: {bidding_strategy_id}\n\n"
                output += f"**Important Notes**:\n"
                output += f"- The campaign will enter a learning period (typically 7-14 days)\n"
                output += f"- Performance may fluctuate during this time\n"
                output += f"- Avoid making frequent changes to allow the algorithm to optimize\n"
                output += f"- Monitor performance closely in the first few weeks\n"

                return output

            except Exception as e:
                error_msg = ErrorHandler.handle_error(e, context="assign_bidding_strategy")
                return f"❌ Failed to assign bidding strategy: {error_msg}"

    @mcp.tool()
    def google_ads_get_bidding_strategy_performance(
        customer_id: str,
        bidding_strategy_id: str,
        date_range: str = "LAST_30_DAYS"
    ) -> str:
        """
        Get performance metrics for a portfolio bidding strategy.

        Shows aggregate performance across all campaigns using this strategy,
        including impressions, clicks, conversions, and cost metrics.

        Args:
            customer_id: Customer ID (without hyphens)
            bidding_strategy_id: Bidding strategy ID
            date_range: Date range (TODAY, YESTERDAY, LAST_7_DAYS, LAST_30_DAYS, etc.)

        Returns:
            Performance metrics in markdown format

        Example:
            google_ads_get_bidding_strategy_performance(
                customer_id="1234567890",
                bidding_strategy_id="12345",
                date_range="LAST_30_DAYS"
            )
        """
        with performance_logger.track_operation('get_bidding_strategy_performance', customer_id=customer_id):
            try:
                client = get_auth_manager().get_client()
                bidding_manager = BiddingStrategyManager(client)

                result = bidding_manager.get_bidding_strategy_performance(
                    customer_id, bidding_strategy_id, date_range
                )

                if 'error' in result:
                    return f"❌ {result['error']}"

                # Audit log
                audit_logger.log_api_call(
                    customer_id=customer_id,
                    operation="get_bidding_strategy_performance",
                    resource_type="bidding_strategy",
                    resource_id=bidding_strategy_id,
                    action="read",
                    result="success"
                )

                # Format response
                output = f"# Bidding Strategy Performance\n\n"
                output += f"**Strategy**: {result['name']}\n"
                output += f"**Type**: {result['type']}\n"
                output += f"**Date Range**: {date_range}\n"
                output += f"**Campaigns Using This Strategy**: {result['campaign_count']}\n\n"

                output += f"## Performance Metrics\n\n"
                output += f"- **Impressions**: {result['impressions']:,}\n"
                output += f"- **Clicks**: {result['clicks']:,}\n"
                output += f"- **CTR**: {result['ctr'] * 100:.2f}%\n"
                output += f"- **Average CPC**: ${result['average_cpc']:.2f}\n"
                output += f"- **Total Cost**: ${result['cost']:,.2f}\n\n"

                if result['conversions'] > 0:
                    output += f"## Conversion Metrics\n\n"
                    output += f"- **Conversions**: {result['conversions']:.1f}\n"
                    output += f"- **Conversion Value**: ${result['conversions_value']:,.2f}\n"
                    output += f"- **Cost per Conversion**: ${result['cost_per_conversion']:.2f}\n"

                    if result['type'] == 'TARGET_ROAS':
                        actual_roas = result['conversions_value'] / result['cost'] if result['cost'] > 0 else 0
                        output += f"- **Actual ROAS**: {actual_roas:.2f}x ({actual_roas * 100:.0f}%)\n"
                else:
                    output += f"\n*No conversions recorded in this period*\n"

                return output

            except Exception as e:
                error_msg = ErrorHandler.handle_error(e, context="get_bidding_strategy_performance")
                return f"❌ Failed to get bidding strategy performance: {error_msg}"

    # ============================================================================
    # Bid Adjustments
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
        Set bid adjustments for different device types.

        Bid modifiers allow you to increase or decrease bids based on the device
        used by the searcher. Values range from 0.1 (90% decrease) to 10.0 (900% increase).

        Common adjustments:
        - 1.0 = No change (default)
        - 1.5 = Increase bids by 50%
        - 0.7 = Decrease bids by 30%
        - 0.1 = Decrease bids by 90% (effectively pause)

        Args:
            customer_id: Customer ID (without hyphens)
            campaign_id: Campaign ID
            mobile_modifier: Bid modifier for mobile devices (0.1 to 10.0)
            desktop_modifier: Bid modifier for desktop devices (0.1 to 10.0)
            tablet_modifier: Bid modifier for tablet devices (0.1 to 10.0)

        Returns:
            Success message with applied adjustments

        Example:
            google_ads_set_device_bid_adjustments(
                customer_id="1234567890",
                campaign_id="111111111",
                mobile_modifier=1.3,  # Increase mobile bids by 30%
                desktop_modifier=1.0,  # No change for desktop
                tablet_modifier=0.8    # Decrease tablet bids by 20%
            )
        """
        with performance_logger.track_operation('set_device_bid_adjustments', customer_id=customer_id):
            try:
                client = get_auth_manager().get_client()
                bidding_manager = BiddingStrategyManager(client)

                # Build adjustments dictionary
                adjustments = {}
                if mobile_modifier is not None:
                    if not (0.1 <= mobile_modifier <= 10.0):
                        return "❌ mobile_modifier must be between 0.1 and 10.0"
                    adjustments[Device.MOBILE] = mobile_modifier

                if desktop_modifier is not None:
                    if not (0.1 <= desktop_modifier <= 10.0):
                        return "❌ desktop_modifier must be between 0.1 and 10.0"
                    adjustments[Device.DESKTOP] = desktop_modifier

                if tablet_modifier is not None:
                    if not (0.1 <= tablet_modifier <= 10.0):
                        return "❌ tablet_modifier must be between 0.1 and 10.0"
                    adjustments[Device.TABLET] = tablet_modifier

                if not adjustments:
                    return "❌ At least one device modifier must be specified"

                result = bidding_manager.set_device_bid_adjustments(
                    customer_id, campaign_id, adjustments
                )

                # Audit log
                audit_logger.log_api_call(
                    customer_id=customer_id,
                    operation="set_device_bid_adjustments",
                    resource_type="campaign",
                    resource_id=campaign_id,
                    action="update",
                    result="success",
                    details={'adjustments': {k.value: v for k, v in adjustments.items()}}
                )

                # Invalidate cache
                get_cache_manager().invalidate(customer_id, ResourceType.CAMPAIGN)

                output = f"✅ Device bid adjustments updated successfully!\n\n"
                output += f"**Campaign ID**: {campaign_id}\n"
                output += f"**Updated Devices**: {result['updated_devices']}\n\n"

                output += f"## Bid Adjustments\n\n"
                for device, modifier in adjustments.items():
                    change_pct = (modifier - 1.0) * 100
                    direction = "increase" if change_pct > 0 else "decrease"
                    output += f"- **{device.value.title()}**: {modifier:.2f}x ({abs(change_pct):.0f}% {direction})\n"

                output += f"\nThese adjustments will apply to all keywords and ad groups in this campaign."

                return output

            except Exception as e:
                error_msg = ErrorHandler.handle_error(e, context="set_device_bid_adjustments")
                return f"❌ Failed to set device bid adjustments: {error_msg}"

    @mcp.tool()
    def google_ads_set_ad_schedule_bid_adjustments(
        customer_id: str,
        campaign_id: str,
        schedules: List[Dict[str, Any]]
    ) -> str:
        """
        Set bid adjustments for ad scheduling (dayparting).

        Control when your ads show and adjust bids based on time of day and day of week.
        This is useful for targeting business hours, weekends, or other high-converting periods.

        Args:
            customer_id: Customer ID (without hyphens)
            campaign_id: Campaign ID
            schedules: List of schedule configurations, each containing:
                - day_of_week: Day (MONDAY, TUESDAY, etc.)
                - start_hour: Start hour (0-23)
                - start_minute: Start minute (0, 15, 30, 45)
                - end_hour: End hour (0-24)
                - end_minute: End minute (0, 15, 30, 45)
                - bid_modifier: Bid adjustment (0.1 to 10.0)

        Returns:
            Success message with created schedules

        Example:
            google_ads_set_ad_schedule_bid_adjustments(
                customer_id="1234567890",
                campaign_id="111111111",
                schedules=[
                    {
                        "day_of_week": "MONDAY",
                        "start_hour": 9,
                        "start_minute": 0,
                        "end_hour": 17,
                        "end_minute": 0,
                        "bid_modifier": 1.5  # Increase bids 50% during business hours
                    },
                    {
                        "day_of_week": "SATURDAY",
                        "start_hour": 0,
                        "start_minute": 0,
                        "end_hour": 24,
                        "end_minute": 0,
                        "bid_modifier": 0.7  # Decrease bids 30% on weekends
                    }
                ]
            )
        """
        with performance_logger.track_operation('set_ad_schedule_bid_adjustments', customer_id=customer_id):
            try:
                client = get_auth_manager().get_client()
                bidding_manager = BiddingStrategyManager(client)

                # Parse and validate schedules
                schedule_configs = []
                for sched in schedules:
                    try:
                        schedule_configs.append(AdScheduleConfig(
                            day_of_week=DayOfWeek[sched['day_of_week'].upper()],
                            start_hour=sched['start_hour'],
                            start_minute=sched['start_minute'],
                            end_hour=sched['end_hour'],
                            end_minute=sched['end_minute'],
                            bid_modifier=sched['bid_modifier']
                        ))
                    except KeyError as e:
                        return f"❌ Missing required field in schedule: {e}"
                    except ValueError as e:
                        return f"❌ Invalid schedule value: {e}"

                result = bidding_manager.set_ad_schedule_bid_adjustments(
                    customer_id, campaign_id, schedule_configs
                )

                # Audit log
                audit_logger.log_api_call(
                    customer_id=customer_id,
                    operation="set_ad_schedule_bid_adjustments",
                    resource_type="campaign",
                    resource_id=campaign_id,
                    action="create",
                    result="success",
                    details={'schedule_count': len(schedule_configs)}
                )

                # Invalidate cache
                get_cache_manager().invalidate(customer_id, ResourceType.CAMPAIGN)

                output = f"✅ Ad schedule bid adjustments created successfully!\n\n"
                output += f"**Campaign ID**: {campaign_id}\n"
                output += f"**Schedules Created**: {result['created_schedules']}\n\n"

                output += f"## Ad Schedule Adjustments\n\n"
                for sched in result['schedules']:
                    change_pct = (sched['bid_modifier'] - 1.0) * 100
                    direction = "increase" if change_pct > 0 else "decrease"
                    output += f"- **{sched['day']}** {sched['time']}: {abs(change_pct):.0f}% {direction}\n"

                output += f"\nAds will only show during these scheduled times with the specified bid adjustments."

                return output

            except Exception as e:
                error_msg = ErrorHandler.handle_error(e, context="set_ad_schedule_bid_adjustments")
                return f"❌ Failed to set ad schedule bid adjustments: {error_msg}"

    @mcp.tool()
    def google_ads_list_bid_adjustments(
        customer_id: str,
        campaign_id: str
    ) -> str:
        """
        List all bid adjustments for a campaign (devices, locations, demographics, ad schedule).

        Args:
            customer_id: Customer ID (without hyphens)
            campaign_id: Campaign ID

        Returns:
            All bid adjustments in markdown format

        Example:
            google_ads_list_bid_adjustments(
                customer_id="1234567890",
                campaign_id="111111111"
            )
        """
        with performance_logger.track_operation('list_bid_adjustments', customer_id=customer_id):
            try:
                client = get_auth_manager().get_client()
                ga_service = client.get_service("GoogleAdsService")

                query = f"""
                    SELECT
                        campaign_criterion.criterion_id,
                        campaign_criterion.type,
                        campaign_criterion.bid_modifier,
                        campaign_criterion.device.type,
                        campaign_criterion.location.geo_target_constant,
                        campaign_criterion.ad_schedule.day_of_week,
                        campaign_criterion.ad_schedule.start_hour,
                        campaign_criterion.ad_schedule.start_minute,
                        campaign_criterion.ad_schedule.end_hour,
                        campaign_criterion.ad_schedule.end_minute
                    FROM campaign_criterion
                    WHERE campaign.id = {campaign_id}
                    AND campaign_criterion.bid_modifier IS NOT NULL
                """

                response = ga_service.search(customer_id=customer_id, query=query)

                device_adjustments = []
                location_adjustments = []
                schedule_adjustments = []

                for row in response:
                    criterion = row.campaign_criterion

                    if criterion.type.name == 'DEVICE':
                        device_adjustments.append({
                            'type': criterion.device.type.name,
                            'modifier': criterion.bid_modifier
                        })
                    elif criterion.type.name == 'LOCATION':
                        location_adjustments.append({
                            'location': criterion.location.geo_target_constant.split('/')[-1],
                            'modifier': criterion.bid_modifier
                        })
                    elif criterion.type.name == 'AD_SCHEDULE':
                        schedule = criterion.ad_schedule
                        schedule_adjustments.append({
                            'day': schedule.day_of_week.name,
                            'start': f"{schedule.start_hour:02d}:{schedule.start_minute.name}",
                            'end': f"{schedule.end_hour:02d}:{schedule.end_minute.name}",
                            'modifier': criterion.bid_modifier
                        })

                # Audit log
                audit_logger.log_api_call(
                    customer_id=customer_id,
                    operation="list_bid_adjustments",
                    resource_type="campaign",
                    resource_id=campaign_id,
                    action="read",
                    result="success"
                )

                # Format response
                output = f"# Bid Adjustments - Campaign {campaign_id}\n\n"

                if device_adjustments:
                    output += f"## Device Adjustments\n\n"
                    for adj in device_adjustments:
                        change_pct = (adj['modifier'] - 1.0) * 100
                        output += f"- **{adj['type']}**: {adj['modifier']:.2f}x ({change_pct:+.0f}%)\n"
                    output += "\n"

                if location_adjustments:
                    output += f"## Location Adjustments\n\n"
                    for adj in location_adjustments:
                        change_pct = (adj['modifier'] - 1.0) * 100
                        output += f"- **Location {adj['location']}**: {adj['modifier']:.2f}x ({change_pct:+.0f}%)\n"
                    output += "\n"

                if schedule_adjustments:
                    output += f"## Ad Schedule Adjustments\n\n"
                    for adj in schedule_adjustments:
                        change_pct = (adj['modifier'] - 1.0) * 100
                        output += f"- **{adj['day']}** {adj['start']}-{adj['end']}: {adj['modifier']:.2f}x ({change_pct:+.0f}%)\n"
                    output += "\n"

                if not (device_adjustments or location_adjustments or schedule_adjustments):
                    output += "No bid adjustments configured for this campaign.\n"

                return output

            except Exception as e:
                error_msg = ErrorHandler.handle_error(e, context="list_bid_adjustments")
                return f"❌ Failed to list bid adjustments: {error_msg}"

    # ============================================================================
    # Smart Bidding Features
    # ============================================================================

    @mcp.tool()
    def google_ads_get_bid_simulator(
        customer_id: str,
        campaign_id: str,
        criterion_id: Optional[str] = None
    ) -> str:
        """
        Get bid simulation data showing potential performance at different bid levels.

        Bid simulators use historical data to project how different bid amounts would
        have affected impressions, clicks, cost, and conversions. This helps you find
        the optimal bid level for your goals.

        Note: Simulations require at least 7 days of historical data.

        Args:
            customer_id: Customer ID (without hyphens)
            campaign_id: Campaign ID for campaign-level simulation
            criterion_id: Optional keyword criterion ID for keyword-level simulation

        Returns:
            Bid simulation data with projected performance at different bid levels

        Example:
            google_ads_get_bid_simulator(
                customer_id="1234567890",
                campaign_id="111111111"
            )
        """
        with performance_logger.track_operation('get_bid_simulator', customer_id=customer_id):
            try:
                client = get_auth_manager().get_client()
                bidding_manager = BiddingStrategyManager(client)

                result = bidding_manager.get_bid_simulator_data(
                    customer_id, campaign_id, criterion_id
                )

                if 'error' in result:
                    return f"❌ {result['error']}\n\n{result.get('note', '')}"

                # Audit log
                audit_logger.log_api_call(
                    customer_id=customer_id,
                    operation="get_bid_simulator",
                    resource_type="campaign",
                    resource_id=campaign_id,
                    action="read",
                    result="success"
                )

                # Format response
                output = f"# Bid Simulator Results\n\n"
                output += f"**Campaign ID**: {result['campaign_id']}\n"
                if criterion_id:
                    output += f"**Keyword ID**: {result['criterion_id']}\n"
                output += f"**Total Scenarios**: {result['total_scenarios']}\n\n"

                output += f"## Projected Performance\n\n"
                output += f"| CPC Bid | Impressions | Clicks | Cost | Conversions | Conv. Value |\n"
                output += f"|---------|-------------|--------|------|-------------|-------------|\n"

                for point in result['simulation_points']:
                    output += f"| ${point['cpc_bid']:.2f} | {point['impressions']:,} | {point['clicks']:,} | "
                    output += f"${point['cost']:,.2f} | {point['conversions']:.1f} | ${point['conversions_value']:,.2f} |\n"

                output += f"\n**Interpretation**:\n"
                output += f"- Higher bids = More impressions and clicks (but higher cost)\n"
                output += f"- Look for the bid level with optimal cost per conversion\n"
                output += f"- Consider your target CPA/ROAS when selecting bid level\n"

                return output

            except Exception as e:
                error_msg = ErrorHandler.handle_error(e, context="get_bid_simulator")
                return f"❌ Failed to get bid simulator data: {error_msg}"

    @mcp.tool()
    def google_ads_get_bid_recommendations(
        customer_id: str,
        campaign_id: Optional[str] = None
    ) -> str:
        """
        Get AI-powered bid recommendations from Google Ads.

        Google's recommendation engine analyzes your account performance and suggests
        specific bid changes to improve results. Recommendations may include:
        - Keyword bid adjustments
        - Campaign budget increases
        - Bidding strategy changes

        Args:
            customer_id: Customer ID (without hyphens)
            campaign_id: Optional campaign ID to filter recommendations

        Returns:
            List of bid recommendations with projected impact

        Example:
            google_ads_get_bid_recommendations(
                customer_id="1234567890",
                campaign_id="111111111"
            )
        """
        with performance_logger.track_operation('get_bid_recommendations', customer_id=customer_id):
            try:
                client = get_auth_manager().get_client()
                bidding_manager = BiddingStrategyManager(client)

                recommendations = bidding_manager.get_bid_recommendations(customer_id, campaign_id)

                if not recommendations:
                    return "No bid recommendations available at this time."

                # Audit log
                audit_logger.log_api_call(
                    customer_id=customer_id,
                    operation="get_bid_recommendations",
                    resource_type="recommendation",
                    action="read",
                    result="success",
                    details={'recommendation_count': len(recommendations)}
                )

                # Format response
                output = f"# Bid Recommendations\n\n"
                output += f"**Total Recommendations**: {len(recommendations)}\n\n"

                for i, rec in enumerate(recommendations, 1):
                    output += f"## Recommendation {i}: {rec['type']}\n\n"

                    if rec.get('campaign'):
                        output += f"**Campaign ID**: {rec['campaign']}\n"

                    if rec['type'] == 'KEYWORD':
                        output += f"**Keyword**: {rec['keyword']}\n"
                        output += f"**Recommended CPC Bid**: ${rec['recommended_cpc_bid']:.2f}\n"

                    elif rec['type'] == 'CAMPAIGN_BUDGET':
                        output += f"**Current Budget**: ${rec['current_budget']:.2f}/day\n"
                        output += f"**Recommended Budget**: ${rec['recommended_budget']:.2f}/day\n"
                        increase = rec['recommended_budget'] - rec['current_budget']
                        output += f"**Increase**: ${increase:.2f}/day ({increase / rec['current_budget'] * 100:.0f}%)\n"

                    if rec.get('impact'):
                        output += f"\n**Projected Impact**:\n"
                        output += f"- Impressions: {rec['impact']['impressions']:,}\n"
                        output += f"- Clicks: {rec['impact']['clicks']:,}\n"
                        output += f"- Conversions: {rec['impact']['conversions']:.1f}\n"

                    output += "\n"

                output += f"**Note**: These are Google's AI-generated recommendations. Review carefully before applying."

                return output

            except Exception as e:
                error_msg = ErrorHandler.handle_error(e, context="get_bid_recommendations")
                return f"❌ Failed to get bid recommendations: {error_msg}"

    @mcp.tool()
    def google_ads_list_bidding_strategies(
        customer_id: str
    ) -> str:
        """
        List all portfolio bidding strategies in the account.

        Args:
            customer_id: Customer ID (without hyphens)

        Returns:
            List of all portfolio bidding strategies with basic info

        Example:
            google_ads_list_bidding_strategies(
                customer_id="1234567890"
            )
        """
        with performance_logger.track_operation('list_bidding_strategies', customer_id=customer_id):
            try:
                client = get_auth_manager().get_client()
                ga_service = client.get_service("GoogleAdsService")

                query = """
                    SELECT
                        bidding_strategy.id,
                        bidding_strategy.name,
                        bidding_strategy.type,
                        bidding_strategy.campaign_count,
                        bidding_strategy.target_cpa.target_cpa_micros,
                        bidding_strategy.target_roas.target_roas,
                        bidding_strategy.target_impression_share.target_impression_share
                    FROM bidding_strategy
                """

                response = ga_service.search(customer_id=customer_id, query=query)

                strategies = []
                for row in response:
                    strategy = row.bidding_strategy
                    strategies.append({
                        'id': str(strategy.id),
                        'name': strategy.name,
                        'type': strategy.type.name,
                        'campaign_count': strategy.campaign_count
                    })

                # Audit log
                audit_logger.log_api_call(
                    customer_id=customer_id,
                    operation="list_bidding_strategies",
                    resource_type="bidding_strategy",
                    action="read",
                    result="success",
                    details={'strategy_count': len(strategies)}
                )

                if not strategies:
                    return "No portfolio bidding strategies found. Create one with `google_ads_create_bidding_strategy`."

                # Format response
                output = f"# Portfolio Bidding Strategies\n\n"
                output += f"**Total Strategies**: {len(strategies)}\n\n"

                for strategy in strategies:
                    output += f"## {strategy['name']}\n"
                    output += f"- **ID**: {strategy['id']}\n"
                    output += f"- **Type**: {strategy['type']}\n"
                    output += f"- **Campaigns Using**: {strategy['campaign_count']}\n\n"

                return output

            except Exception as e:
                error_msg = ErrorHandler.handle_error(e, context="list_bidding_strategies")
                return f"❌ Failed to list bidding strategies: {error_msg}"

    @mcp.tool()
    def google_ads_get_bidding_strategy_details(
        customer_id: str,
        bidding_strategy_id: str
    ) -> str:
        """
        Get full configuration details for a portfolio bidding strategy.

        Args:
            customer_id: Customer ID (without hyphens)
            bidding_strategy_id: Bidding strategy ID

        Returns:
            Complete strategy configuration and settings

        Example:
            google_ads_get_bidding_strategy_details(
                customer_id="1234567890",
                bidding_strategy_id="12345"
            )
        """
        with performance_logger.track_operation('get_bidding_strategy_details', customer_id=customer_id):
            try:
                client = get_auth_manager().get_client()
                ga_service = client.get_service("GoogleAdsService")

                query = f"""
                    SELECT
                        bidding_strategy.id,
                        bidding_strategy.name,
                        bidding_strategy.type,
                        bidding_strategy.campaign_count,
                        bidding_strategy.target_cpa.target_cpa_micros,
                        bidding_strategy.target_roas.target_roas,
                        bidding_strategy.target_impression_share.target_impression_share,
                        bidding_strategy.target_impression_share.location,
                        bidding_strategy.target_impression_share.cpc_bid_ceiling_micros,
                        bidding_strategy.enhanced_cpc
                    FROM bidding_strategy
                    WHERE bidding_strategy.id = {bidding_strategy_id}
                """

                response = ga_service.search(customer_id=customer_id, query=query)
                results = list(response)

                if not results:
                    return f"❌ Bidding strategy {bidding_strategy_id} not found"

                row = results[0]
                strategy = row.bidding_strategy

                # Audit log
                audit_logger.log_api_call(
                    customer_id=customer_id,
                    operation="get_bidding_strategy_details",
                    resource_type="bidding_strategy",
                    resource_id=bidding_strategy_id,
                    action="read",
                    result="success"
                )

                # Format response
                output = f"# Bidding Strategy Details\n\n"
                output += f"**Name**: {strategy.name}\n"
                output += f"**ID**: {strategy.id}\n"
                output += f"**Type**: {strategy.type.name}\n"
                output += f"**Campaigns Using**: {strategy.campaign_count}\n\n"

                output += f"## Configuration\n\n"

                if strategy.type.name == 'TARGET_CPA':
                    output += f"**Target CPA**: ${strategy.target_cpa.target_cpa_micros / 1_000_000:.2f}\n"

                elif strategy.type.name == 'TARGET_ROAS':
                    output += f"**Target ROAS**: {strategy.target_roas.target_roas:.2f}x ({strategy.target_roas.target_roas * 100:.0f}%)\n"

                elif strategy.type.name == 'TARGET_IMPRESSION_SHARE':
                    output += f"**Target Impression Share**: {strategy.target_impression_share.target_impression_share * 100:.0f}%\n"
                    output += f"**Location**: {strategy.target_impression_share.location.name}\n"
                    if strategy.target_impression_share.cpc_bid_ceiling_micros:
                        output += f"**Max CPC Bid**: ${strategy.target_impression_share.cpc_bid_ceiling_micros / 1_000_000:.2f}\n"

                elif strategy.type.name == 'MANUAL_CPC':
                    output += f"**Enhanced CPC**: {'Enabled' if strategy.enhanced_cpc else 'Disabled'}\n"

                return output

            except Exception as e:
                error_msg = ErrorHandler.handle_error(e, context="get_bidding_strategy_details")
                return f"❌ Failed to get bidding strategy details: {error_msg}"
