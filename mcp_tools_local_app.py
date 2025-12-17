"""
MCP Tools for Local & App Campaigns

Provides MCP tool wrappers for Local campaigns (Google My Business integration)
and App campaigns (Universal App Campaigns for mobile app promotion).

Local Campaigns:
- Create local campaigns to drive store visits
- Track local performance metrics
- Monitor store visit conversions

App Campaigns:
- Create Universal App Campaigns
- Track app install and engagement metrics
- Monitor conversion actions by type
"""

from typing import TYPE_CHECKING, Dict, Any, Optional, List
from local_app_manager import (
    LocalAppManager,
    LocalCampaignConfig,
    AppCampaignConfig,
    AppCampaignAppStore,
    AppCampaignBiddingStrategyGoalType
)
from auth_manager import get_auth_manager
from error_handler import ErrorHandler
from logger import get_logger, get_performance_logger, get_audit_logger

if TYPE_CHECKING:
    from mcp.server import Server

logger = get_logger(__name__)
performance_logger = get_performance_logger()
audit_logger = get_audit_logger()


def register_local_app_tools(mcp: "Server") -> None:
    """Register all local and app campaign MCP tools.

    Args:
        mcp: The MCP server instance
    """

    @mcp.tool()
    async def google_ads_create_local_campaign(
        customer_id: str,
        campaign_name: str,
        budget_amount: float,
        location_ids: List[str],
        optimization_goal: str = "STORE_VISITS"
    ) -> Dict[str, Any]:
        """Create a Local campaign to drive store visits and foot traffic.

        Local campaigns promote physical business locations through Google properties
        including Search, Maps, Display, and YouTube. They require Google My Business
        integration and optimize for local actions (store visits, calls, directions).

        Args:
            customer_id: Google Ads customer ID (10 digits, no hyphens)
            campaign_name: Name for the local campaign
            budget_amount: Daily budget in account currency
            location_ids: List of Google My Business location IDs
            optimization_goal: Optimization goal - "STORE_VISITS" or "STORE_SALES"

        Returns:
            Dictionary with campaign creation results including:
            - campaign_id: Created campaign ID
            - campaign_name: Campaign name
            - resource_name: Full resource name
            - budget: Daily budget amount
            - location_count: Number of locations
            - optimization_goal: Selected optimization goal

        Example:
            Create a local campaign for 3 store locations:
            ```
            google_ads_create_local_campaign(
                customer_id="1234567890",
                campaign_name="Summer Store Promotions",
                budget_amount=50.0,
                location_ids=["loc_123", "loc_456", "loc_789"],
                optimization_goal="STORE_VISITS"
            )
            ```

        Notes:
            - Requires Google My Business account linking
            - Campaigns start in PAUSED status
            - Store visit data may take 4-6 weeks to accumulate
            - Automatically optimizes ad placement across Google properties
        """
        try:
            with performance_logger.track_operation("create_local_campaign"):
                # Get client and initialize manager
                client = get_auth_manager().get_client()
                local_app_manager = LocalAppManager(client)

                # Validate customer ID format
                customer_id = customer_id.replace('-', '')
                if not customer_id.isdigit() or len(customer_id) != 10:
                    raise ValueError("Customer ID must be 10 digits")

                # Validate budget
                if budget_amount <= 0:
                    raise ValueError("Budget amount must be positive")

                # Validate location IDs
                if not location_ids:
                    raise ValueError("At least one location ID is required")

                # Validate optimization goal
                valid_goals = ["STORE_VISITS", "STORE_SALES"]
                if optimization_goal not in valid_goals:
                    raise ValueError(f"Optimization goal must be one of: {', '.join(valid_goals)}")

                # Create configuration
                config = LocalCampaignConfig(
                    name=campaign_name,
                    budget_amount=budget_amount,
                    location_ids=location_ids,
                    optimization_goal=optimization_goal
                )

                # Create campaign
                result = local_app_manager.create_local_campaign(
                    customer_id=customer_id,
                    config=config
                )

                # Log audit trail
                audit_logger.log_api_call(
                    operation="create_local_campaign",
                    customer_id=customer_id,
                    details={
                        'campaign_name': campaign_name,
                        'budget': budget_amount,
                        'locations': len(location_ids),
                        'goal': optimization_goal
                    },
                    response=result
                )

                # Format response
                response = f"""
## Local Campaign Created Successfully

**Campaign Details:**
- Campaign ID: `{result['campaign_id']}`
- Campaign Name: {result['campaign_name']}
- Resource Name: `{result['resource_name']}`

**Configuration:**
- Daily Budget: ${result['budget']:.2f}
- Locations: {result['location_count']} Google My Business location(s)
- Optimization Goal: {result['optimization_goal']}

**Status:** Campaign created in PAUSED status

**Next Steps:**
1. Enable the campaign when ready to start
2. Monitor store visit conversions (may take 4-6 weeks for data)
3. Review local performance metrics regularly
4. Adjust budget based on store visit volume

**Note:** Ensure your Google My Business locations are properly configured and verified.
"""

                return {
                    "content": [{"type": "text", "text": response.strip()}],
                    "metadata": result
                }

        except Exception as e:
            error_msg = ErrorHandler.handle_error(e, {
                'operation': 'create_local_campaign',
                'customer_id': customer_id,
                'campaign_name': campaign_name
            })
            return {"content": [{"type": "text", "text": error_msg}], "isError": True}


    @mcp.tool()
    async def google_ads_local_performance(
        customer_id: str,
        campaign_id: Optional[str] = None,
        date_range: str = "LAST_30_DAYS"
    ) -> Dict[str, Any]:
        """Get performance metrics for Local campaigns.

        Retrieves key performance indicators for local campaigns including
        impressions, clicks, conversions, and cost data.

        Args:
            customer_id: Google Ads customer ID (10 digits, no hyphens)
            campaign_id: Optional campaign ID to filter (returns all if not specified)
            date_range: Date range - LAST_7_DAYS, LAST_30_DAYS, LAST_90_DAYS, etc.

        Returns:
            Dictionary with local campaign performance data including:
            - campaigns: List of campaign metrics
            - total_campaigns: Number of local campaigns

        Example:
            Get performance for all local campaigns in the last 30 days:
            ```
            google_ads_local_performance(
                customer_id="1234567890",
                date_range="LAST_30_DAYS"
            )
            ```

        Metrics Included:
            - Impressions: Ad views
            - Clicks: User clicks
            - CTR: Click-through rate
            - Cost: Total spend
            - Conversions: Local actions (visits, calls, directions)
            - Conversion Value: Value of conversions
            - View-Through Conversions: Conversions after viewing (no click)
        """
        try:
            with performance_logger.track_operation("get_local_performance"):
                # Get client and initialize manager
                client = get_auth_manager().get_client()
                local_app_manager = LocalAppManager(client)

                # Validate customer ID
                customer_id = customer_id.replace('-', '')
                if not customer_id.isdigit() or len(customer_id) != 10:
                    raise ValueError("Customer ID must be 10 digits")

                # Get performance data
                result = local_app_manager.get_local_performance(
                    customer_id=customer_id,
                    campaign_id=campaign_id,
                    date_range=date_range
                )

                # Log audit trail
                audit_logger.log_api_call(
                    operation="get_local_performance",
                    customer_id=customer_id,
                    details={
                        'campaign_id': campaign_id,
                        'date_range': date_range,
                        'campaigns_returned': result['total_campaigns']
                    },
                    response={'total_campaigns': result['total_campaigns']}
                )

                # Format response
                if result['total_campaigns'] == 0:
                    response = f"""
## No Local Campaigns Found

No local campaigns found for customer ID `{customer_id}` in the {date_range} period.

**Possible Reasons:**
- No local campaigns have been created yet
- All local campaigns are outside the date range
- Campaigns haven't accumulated data yet
"""
                else:
                    campaign_lines = []
                    for camp in result['campaigns']:
                        campaign_lines.append(f"""
### {camp['campaign_name']} (ID: {camp['campaign_id']})

**Performance Metrics:**
- Impressions: {camp['impressions']:,}
- Clicks: {camp['clicks']:,}
- CTR: {camp['ctr']:.2%}
- Cost: ${camp['cost']:.2f}
- Conversions: {camp['conversions']:.1f}
- Conversion Value: ${camp['conversion_value']:.2f}
- View-Through Conversions: {camp['view_through_conversions']:.1f}
""")

                    response = f"""
## Local Campaign Performance

**Period:** {date_range}
**Total Campaigns:** {result['total_campaigns']}

{chr(10).join(campaign_lines)}

**Note:** Store visit data may take 4-6 weeks to fully accumulate.
"""

                return {
                    "content": [{"type": "text", "text": response.strip()}],
                    "metadata": result
                }

        except Exception as e:
            error_msg = ErrorHandler.handle_error(e, {
                'operation': 'get_local_performance',
                'customer_id': customer_id,
                'campaign_id': campaign_id
            })
            return {"content": [{"type": "text", "text": error_msg}], "isError": True}


    @mcp.tool()
    async def google_ads_store_visits(
        customer_id: str,
        campaign_id: Optional[str] = None,
        date_range: str = "LAST_30_DAYS"
    ) -> Dict[str, Any]:
        """Get store visit conversion data for Local campaigns.

        Retrieves detailed store visit conversion metrics. Store visits are tracked
        when users who saw or clicked an ad subsequently visit a physical location.

        Args:
            customer_id: Google Ads customer ID (10 digits, no hyphens)
            campaign_id: Optional campaign ID to filter (returns all if not specified)
            date_range: Date range - LAST_7_DAYS, LAST_30_DAYS, LAST_90_DAYS, etc.

        Returns:
            Dictionary with store visit data including:
            - campaigns: List of campaigns with store visit conversions
            - total_store_visits: Total store visits across all campaigns
            - total_value: Total value of store visits
            - has_data: Whether any store visit data is available

        Example:
            Get store visit conversions for all local campaigns:
            ```
            google_ads_store_visits(
                customer_id="1234567890",
                date_range="LAST_30_DAYS"
            )
            ```

        Important Notes:
            - Requires Google My Business integration
            - Store visit data takes 4-6 weeks to accumulate
            - Uses probabilistic modeling based on location services
            - Aggregated and anonymized data for privacy
        """
        try:
            with performance_logger.track_operation("get_store_visits"):
                # Get client and initialize manager
                client = get_auth_manager().get_client()
                local_app_manager = LocalAppManager(client)

                # Validate customer ID
                customer_id = customer_id.replace('-', '')
                if not customer_id.isdigit() or len(customer_id) != 10:
                    raise ValueError("Customer ID must be 10 digits")

                # Get store visit data
                result = local_app_manager.get_store_visits(
                    customer_id=customer_id,
                    campaign_id=campaign_id,
                    date_range=date_range
                )

                # Log audit trail
                audit_logger.log_api_call(
                    operation="get_store_visits",
                    customer_id=customer_id,
                    details={
                        'campaign_id': campaign_id,
                        'date_range': date_range,
                        'has_data': result['has_data']
                    },
                    response={
                        'total_visits': result['total_store_visits'],
                        'total_value': result['total_value']
                    }
                )

                # Format response
                if not result['has_data']:
                    response = f"""
## No Store Visit Data Available

No store visit conversions found for customer ID `{customer_id}` in the {date_range} period.

**Common Reasons:**
- Store visit tracking requires 4-6 weeks to accumulate data
- Google My Business integration not properly configured
- Campaigns are new and haven't generated visits yet
- Location services data insufficient for modeling

**Setup Requirements:**
1. Link Google My Business account to Google Ads
2. Verify all business locations in Google My Business
3. Enable location assets in campaigns
4. Wait 4-6 weeks for data to accumulate
"""
                else:
                    campaign_lines = []
                    for camp in result['campaigns']:
                        campaign_lines.append(f"""
### {camp['campaign_name']} (ID: {camp['campaign_id']})

**Conversion Action:** {camp['conversion_action']}
- Store Visits: {camp['store_visits']:.1f}
- Value: ${camp['value']:.2f}
""")

                    response = f"""
## Store Visit Conversions

**Period:** {date_range}
**Total Store Visits:** {result['total_store_visits']:.1f}
**Total Value:** ${result['total_value']:.2f}

{chr(10).join(campaign_lines)}

**About Store Visit Tracking:**
Store visits are measured using aggregated, anonymized data from users who have
enabled location services. The data is modeled to estimate in-store visits from
users who saw or clicked your ads.
"""

                return {
                    "content": [{"type": "text", "text": response.strip()}],
                    "metadata": result
                }

        except Exception as e:
            error_msg = ErrorHandler.handle_error(e, {
                'operation': 'get_store_visits',
                'customer_id': customer_id,
                'campaign_id': campaign_id
            })
            return {"content": [{"type": "text", "text": error_msg}], "isError": True}


    @mcp.tool()
    async def google_ads_create_app_campaign(
        customer_id: str,
        campaign_name: str,
        app_id: str,
        app_store: str,
        budget_amount: float,
        bidding_strategy_goal_type: str,
        target_cpa: Optional[float] = None
    ) -> Dict[str, Any]:
        """Create a Universal App Campaign (UAC) to promote mobile app installs and engagement.

        App campaigns automatically optimize ad creative and placement across Google Search,
        Display Network, YouTube, and Google Play to drive app installs and in-app actions.

        Args:
            customer_id: Google Ads customer ID (10 digits, no hyphens)
            campaign_name: Name for the app campaign
            app_id: App store identifier (bundle ID for iOS, package name for Android)
            app_store: "APPLE_APP_STORE" or "GOOGLE_APP_STORE"
            budget_amount: Daily budget in account currency
            bidding_strategy_goal_type: Bidding goal - one of:
                - OPTIMIZE_INSTALLS_TARGET_INSTALL_COST (target CPA for installs)
                - OPTIMIZE_IN_APP_CONVERSIONS_TARGET_INSTALL_COST (target CPA for installs + conversions)
                - OPTIMIZE_IN_APP_CONVERSIONS_TARGET_CONVERSION_COST (target CPA for conversions)
                - OPTIMIZE_RETURN_ON_ADVERTISING_SPEND (target ROAS)
                - OPTIMIZE_PRE_REGISTRATION_CONVERSION_VOLUME (pre-registration campaigns)
            target_cpa: Optional target cost per action (for CPA-based strategies)

        Returns:
            Dictionary with campaign creation results including:
            - campaign_id: Created campaign ID
            - campaign_name: Campaign name
            - resource_name: Full resource name
            - app_id: App store identifier
            - app_store: App store type
            - budget: Daily budget amount
            - bidding_goal: Selected bidding strategy goal

        Example:
            Create an iOS app campaign optimizing for installs:
            ```
            google_ads_create_app_campaign(
                customer_id="1234567890",
                campaign_name="iOS App Install Campaign",
                app_id="com.example.myapp",
                app_store="APPLE_APP_STORE",
                budget_amount=100.0,
                bidding_strategy_goal_type="OPTIMIZE_INSTALLS_TARGET_INSTALL_COST",
                target_cpa=5.0
            )
            ```

        Notes:
            - Campaigns start in PAUSED status
            - Requires app store listing to be live
            - Automatic ad creation from app store assets
            - Can add text, image, video, and HTML5 assets for better performance
        """
        try:
            with performance_logger.track_operation("create_app_campaign"):
                # Get client and initialize manager
                client = get_auth_manager().get_client()
                local_app_manager = LocalAppManager(client)

                # Validate customer ID
                customer_id = customer_id.replace('-', '')
                if not customer_id.isdigit() or len(customer_id) != 10:
                    raise ValueError("Customer ID must be 10 digits")

                # Validate budget
                if budget_amount <= 0:
                    raise ValueError("Budget amount must be positive")

                # Validate app store
                try:
                    app_store_enum = AppCampaignAppStore(app_store)
                except ValueError:
                    raise ValueError(f"Invalid app store. Must be: APPLE_APP_STORE or GOOGLE_APP_STORE")

                # Validate bidding strategy
                try:
                    bidding_goal_enum = AppCampaignBiddingStrategyGoalType(bidding_strategy_goal_type)
                except ValueError:
                    valid_goals = [goal.value for goal in AppCampaignBiddingStrategyGoalType]
                    raise ValueError(f"Invalid bidding goal. Must be one of: {', '.join(valid_goals)}")

                # Validate target CPA if provided
                if target_cpa is not None and target_cpa <= 0:
                    raise ValueError("Target CPA must be positive")

                # Create configuration
                config = AppCampaignConfig(
                    name=campaign_name,
                    app_id=app_id,
                    app_store=app_store_enum,
                    budget_amount=budget_amount,
                    bidding_strategy_goal_type=bidding_goal_enum,
                    target_cpa=target_cpa
                )

                # Create campaign
                result = local_app_manager.create_app_campaign(
                    customer_id=customer_id,
                    config=config
                )

                # Log audit trail
                audit_logger.log_api_call(
                    operation="create_app_campaign",
                    customer_id=customer_id,
                    details={
                        'campaign_name': campaign_name,
                        'app_id': app_id,
                        'app_store': app_store,
                        'budget': budget_amount,
                        'bidding_goal': bidding_strategy_goal_type,
                        'target_cpa': target_cpa
                    },
                    response=result
                )

                # Format response
                response = f"""
## App Campaign Created Successfully

**Campaign Details:**
- Campaign ID: `{result['campaign_id']}`
- Campaign Name: {result['campaign_name']}
- Resource Name: `{result['resource_name']}`

**App Configuration:**
- App ID: {result['app_id']}
- App Store: {result['app_store']}

**Budget & Bidding:**
- Daily Budget: ${result['budget']:.2f}
- Bidding Goal: {result['bidding_goal']}
{f"- Target CPA: ${target_cpa:.2f}" if target_cpa else "- Bidding: Maximize Conversions (no target)"}

**Status:** Campaign created in PAUSED status

**Next Steps:**
1. Add text assets (up to 5 headlines, 5 descriptions)
2. Add image assets (recommended: 1200x628, 1200x1200, 320x50)
3. Add video assets (YouTube videos)
4. Add HTML5 assets if available
5. Enable the campaign when ready to start

**Optimization:**
App campaigns automatically optimize ad placement across:
- Google Search
- Google Display Network
- YouTube
- Google Play
- Google Discover

The campaign will use machine learning to find the best audiences and creatives
for your app promotion goals.
"""

                return {
                    "content": [{"type": "text", "text": response.strip()}],
                    "metadata": result
                }

        except Exception as e:
            error_msg = ErrorHandler.handle_error(e, {
                'operation': 'create_app_campaign',
                'customer_id': customer_id,
                'campaign_name': campaign_name
            })
            return {"content": [{"type": "text", "text": error_msg}], "isError": True}


    @mcp.tool()
    async def google_ads_app_performance(
        customer_id: str,
        campaign_id: Optional[str] = None,
        date_range: str = "LAST_30_DAYS"
    ) -> Dict[str, Any]:
        """Get performance metrics for App campaigns.

        Retrieves key performance indicators for app campaigns including
        impressions, clicks, conversions (installs), and cost data.

        Args:
            customer_id: Google Ads customer ID (10 digits, no hyphens)
            campaign_id: Optional campaign ID to filter (returns all if not specified)
            date_range: Date range - LAST_7_DAYS, LAST_30_DAYS, LAST_90_DAYS, etc.

        Returns:
            Dictionary with app campaign performance data including:
            - campaigns: List of campaign metrics
            - total_campaigns: Number of app campaigns

        Example:
            Get performance for all app campaigns in the last 30 days:
            ```
            google_ads_app_performance(
                customer_id="1234567890",
                date_range="LAST_30_DAYS"
            )
            ```

        Metrics Included:
            - Impressions: Ad views across all networks
            - Clicks: User clicks
            - CTR: Click-through rate
            - Cost: Total spend
            - Conversions: App installs or in-app actions
            - Conversion Value: Value of conversions
            - Cost per Conversion: Average cost for each conversion
        """
        try:
            with performance_logger.track_operation("get_app_performance"):
                # Get client and initialize manager
                client = get_auth_manager().get_client()
                local_app_manager = LocalAppManager(client)

                # Validate customer ID
                customer_id = customer_id.replace('-', '')
                if not customer_id.isdigit() or len(customer_id) != 10:
                    raise ValueError("Customer ID must be 10 digits")

                # Get performance data
                result = local_app_manager.get_app_performance(
                    customer_id=customer_id,
                    campaign_id=campaign_id,
                    date_range=date_range
                )

                # Log audit trail
                audit_logger.log_api_call(
                    operation="get_app_performance",
                    customer_id=customer_id,
                    details={
                        'campaign_id': campaign_id,
                        'date_range': date_range,
                        'campaigns_returned': result['total_campaigns']
                    },
                    response={'total_campaigns': result['total_campaigns']}
                )

                # Format response
                if result['total_campaigns'] == 0:
                    response = f"""
## No App Campaigns Found

No app campaigns found for customer ID `{customer_id}` in the {date_range} period.

**Possible Reasons:**
- No app campaigns have been created yet
- All app campaigns are outside the date range
- Campaigns haven't accumulated data yet
"""
                else:
                    campaign_lines = []
                    for camp in result['campaigns']:
                        campaign_lines.append(f"""
### {camp['campaign_name']} (ID: {camp['campaign_id']})

**App Details:**
- App ID: {camp['app_id']}
- App Store: {camp['app_store']}

**Performance Metrics:**
- Impressions: {camp['impressions']:,}
- Clicks: {camp['clicks']:,}
- CTR: {camp['ctr']:.2%}
- Cost: ${camp['cost']:.2f}
- Conversions: {camp['conversions']:.1f}
- Conversion Value: ${camp['conversion_value']:.2f}
- Cost per Conversion: ${camp['cost_per_conversion']:.2f}
""")

                    response = f"""
## App Campaign Performance

**Period:** {date_range}
**Total Campaigns:** {result['total_campaigns']}

{chr(10).join(campaign_lines)}

**Networks:** Performance across Google Search, Display, YouTube, and Google Play.
"""

                return {
                    "content": [{"type": "text", "text": response.strip()}],
                    "metadata": result
                }

        except Exception as e:
            error_msg = ErrorHandler.handle_error(e, {
                'operation': 'get_app_performance',
                'customer_id': customer_id,
                'campaign_id': campaign_id
            })
            return {"content": [{"type": "text", "text": error_msg}], "isError": True}


    @mcp.tool()
    async def google_ads_app_conversions(
        customer_id: str,
        campaign_id: Optional[str] = None,
        date_range: str = "LAST_30_DAYS"
    ) -> Dict[str, Any]:
        """Get detailed app conversion data by conversion type.

        Retrieves app install and in-app engagement conversions broken down by
        conversion action and category. Useful for understanding which conversion
        events are driving campaign performance.

        Args:
            customer_id: Google Ads customer ID (10 digits, no hyphens)
            campaign_id: Optional campaign ID to filter (returns all if not specified)
            date_range: Date range - LAST_7_DAYS, LAST_30_DAYS, LAST_90_DAYS, etc.

        Returns:
            Dictionary with app conversion data including:
            - campaigns: Campaign-level conversion breakdown
            - by_type: Aggregated conversions by category
            - total_campaigns: Number of campaigns with conversion data

        Example:
            Get conversion breakdown for all app campaigns:
            ```
            google_ads_app_conversions(
                customer_id="1234567890",
                date_range="LAST_30_DAYS"
            )
            ```

        Conversion Categories:
            - App Installs: First-time app installations
            - In-App Purchases: Purchases made within the app
            - In-App Actions: Custom conversion events (level completed, item viewed, etc.)
            - App Engagement: Session starts, time in app, etc.

        Notes:
            - Requires Firebase or third-party SDK integration for in-app tracking
            - Install conversions are automatically tracked
            - In-app conversions require SDK implementation
        """
        try:
            with performance_logger.track_operation("get_app_conversions"):
                # Get client and initialize manager
                client = get_auth_manager().get_client()
                local_app_manager = LocalAppManager(client)

                # Validate customer ID
                customer_id = customer_id.replace('-', '')
                if not customer_id.isdigit() or len(customer_id) != 10:
                    raise ValueError("Customer ID must be 10 digits")

                # Get conversion data
                result = local_app_manager.get_app_conversions(
                    customer_id=customer_id,
                    campaign_id=campaign_id,
                    date_range=date_range
                )

                # Log audit trail
                audit_logger.log_api_call(
                    operation="get_app_conversions",
                    customer_id=customer_id,
                    details={
                        'campaign_id': campaign_id,
                        'date_range': date_range,
                        'campaigns_returned': result['total_campaigns']
                    },
                    response={
                        'total_campaigns': result['total_campaigns'],
                        'conversion_types': len(result['by_type'])
                    }
                )

                # Format response
                if result['total_campaigns'] == 0:
                    response = f"""
## No App Conversion Data Found

No app conversion data found for customer ID `{customer_id}` in the {date_range} period.

**Possible Reasons:**
- No app campaigns have been created yet
- Campaigns haven't generated conversions yet
- Conversion tracking not properly configured

**Setup Requirements:**
1. Create app campaigns
2. Ensure app install tracking is enabled (automatic)
3. For in-app conversions: integrate Firebase or third-party SDK
4. Configure conversion actions in Google Ads
"""
                else:
                    # Format by-type summary
                    type_lines = []
                    for conv_type, data in result['by_type'].items():
                        type_lines.append(f"""
### {conv_type}
- Total Conversions: {data['total_conversions']:.1f}
- Total Value: ${data['total_value']:.2f}
""")

                    # Format campaign details
                    campaign_lines = []
                    for camp_id, camp_data in result['campaigns'].items():
                        conv_lines = []
                        for conv_name, conv_data in camp_data['conversions'].items():
                            conv_lines.append(f"  - {conv_name} ({conv_data['category']}): {conv_data['conversions']:.1f} conversions, ${conv_data['value']:.2f} value")

                        campaign_lines.append(f"""
#### {camp_data['campaign_name']} (ID: {camp_id})
{chr(10).join(conv_lines)}
""")

                    response = f"""
## App Conversion Data

**Period:** {date_range}
**Total Campaigns:** {result['total_campaigns']}

## Conversion Summary by Type
{chr(10).join(type_lines)}

## Campaign-Level Breakdown
{chr(10).join(campaign_lines)}

**Tracking:**
- App installs are tracked automatically
- In-app conversions require Firebase or third-party SDK integration
- Configure conversion values to track revenue and ROI
"""

                return {
                    "content": [{"type": "text", "text": response.strip()}],
                    "metadata": result
                }

        except Exception as e:
            error_msg = ErrorHandler.handle_error(e, {
                'operation': 'get_app_conversions',
                'customer_id': customer_id,
                'campaign_id': campaign_id
            })
            return {"content": [{"type": "text", "text": error_msg}], "isError": True}
