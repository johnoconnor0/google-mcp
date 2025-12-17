"""
Local & App Campaigns Manager

Handles Local campaigns and App campaigns (Universal App Campaigns).

Local Campaigns:
- Promote physical business locations
- Drive store visits and foot traffic
- Optimize for local actions (calls, directions, visits)
- Google My Business integration

App Campaigns:
- Promote mobile app installs
- Drive app engagement
- Automated across Google properties
- App store optimization
"""

from typing import Dict, Any, List, Optional
from google.ads.googleads.client import GoogleAdsClient
from dataclasses import dataclass
from enum import Enum


class AppCampaignAppStore(str, Enum):
    """App store types."""
    APPLE_APP_STORE = "APPLE_APP_STORE"
    GOOGLE_APP_STORE = "GOOGLE_APP_STORE"


class AppCampaignBiddingStrategyGoalType(str, Enum):
    """App campaign bidding goals."""
    OPTIMIZE_INSTALLS_TARGET_INSTALL_COST = "OPTIMIZE_INSTALLS_TARGET_INSTALL_COST"
    OPTIMIZE_IN_APP_CONVERSIONS_TARGET_INSTALL_COST = "OPTIMIZE_IN_APP_CONVERSIONS_TARGET_INSTALL_COST"
    OPTIMIZE_IN_APP_CONVERSIONS_TARGET_CONVERSION_COST = "OPTIMIZE_IN_APP_CONVERSIONS_TARGET_CONVERSION_COST"
    OPTIMIZE_RETURN_ON_ADVERTISING_SPEND = "OPTIMIZE_RETURN_ON_ADVERTISING_SPEND"
    OPTIMIZE_PRE_REGISTRATION_CONVERSION_VOLUME = "OPTIMIZE_PRE_REGISTRATION_CONVERSION_VOLUME"


@dataclass
class LocalCampaignConfig:
    """Configuration for local campaign creation."""
    name: str
    budget_amount: float
    location_ids: List[str]  # Google My Business location IDs
    optimization_goal: str = "STORE_VISITS"  # STORE_VISITS, STORE_SALES


@dataclass
class AppCampaignConfig:
    """Configuration for app campaign creation."""
    name: str
    app_id: str  # App store ID
    app_store: AppCampaignAppStore
    budget_amount: float
    bidding_strategy_goal_type: AppCampaignBiddingStrategyGoalType
    target_cpa: Optional[float] = None


class LocalAppManager:
    """Manager for Local and App campaigns."""

    def __init__(self, client: GoogleAdsClient):
        """Initialize the local/app manager.

        Args:
            client: Authenticated GoogleAdsClient instance
        """
        self.client = client

    def create_local_campaign(
        self,
        customer_id: str,
        config: LocalCampaignConfig
    ) -> Dict[str, Any]:
        """Create a Local campaign.

        Args:
            customer_id: Customer ID (without hyphens)
            config: Local campaign configuration

        Returns:
            Created campaign details
        """
        campaign_service = self.client.get_service("CampaignService")
        campaign_budget_service = self.client.get_service("CampaignBudgetService")

        # Create campaign budget
        budget_operation = self.client.get_type("CampaignBudgetOperation")
        budget = budget_operation.create
        budget.name = f"{config.name} Budget"
        budget.amount_micros = int(config.budget_amount * 1_000_000)
        budget.delivery_method = self.client.enums.BudgetDeliveryMethodEnum.STANDARD

        budget_response = campaign_budget_service.mutate_campaign_budgets(
            customer_id=customer_id,
            operations=[budget_operation]
        )
        budget_resource_name = budget_response.results[0].resource_name

        # Create local campaign
        campaign_operation = self.client.get_type("CampaignOperation")
        campaign = campaign_operation.create

        campaign.name = config.name
        campaign.advertising_channel_type = self.client.enums.AdvertisingChannelTypeEnum.LOCAL
        campaign.status = self.client.enums.CampaignStatusEnum.PAUSED
        campaign.campaign_budget = budget_resource_name

        # Local campaign settings
        campaign.local_campaign_setting.location_source_type = (
            self.client.enums.LocationSourceTypeEnum.GOOGLE_MY_BUSINESS
        )

        # Bidding strategy - maximize conversions for local actions
        campaign.maximize_conversions.CopyFrom(self.client.get_type("MaximizeConversions"))

        # Create campaign
        response = campaign_service.mutate_campaigns(
            customer_id=customer_id,
            operations=[campaign_operation]
        )

        campaign_id = response.results[0].resource_name.split('/')[-1]

        return {
            'campaign_id': campaign_id,
            'campaign_name': config.name,
            'resource_name': response.results[0].resource_name,
            'budget': config.budget_amount,
            'location_count': len(config.location_ids),
            'optimization_goal': config.optimization_goal
        }

    def get_local_performance(
        self,
        customer_id: str,
        campaign_id: Optional[str] = None,
        date_range: str = "LAST_30_DAYS"
    ) -> Dict[str, Any]:
        """Get Local campaign performance metrics.

        Args:
            customer_id: Customer ID (without hyphens)
            campaign_id: Optional campaign ID filter
            date_range: Date range for metrics

        Returns:
            Local campaign performance data
        """
        ga_service = self.client.get_service("GoogleAdsService")

        query = f"""
            SELECT
                campaign.id,
                campaign.name,
                metrics.impressions,
                metrics.clicks,
                metrics.ctr,
                metrics.cost_micros,
                metrics.conversions,
                metrics.conversions_value,
                metrics.view_through_conversions
            FROM campaign
            WHERE campaign.advertising_channel_type = 'LOCAL'
              AND segments.date DURING {date_range}
        """

        if campaign_id:
            query += f" AND campaign.id = {campaign_id}"

        query += " ORDER BY metrics.impressions DESC"

        response = ga_service.search(customer_id=customer_id, query=query)

        campaigns = []
        for row in response:
            campaigns.append({
                'campaign_id': str(row.campaign.id),
                'campaign_name': row.campaign.name,
                'impressions': row.metrics.impressions,
                'clicks': row.metrics.clicks,
                'ctr': row.metrics.ctr,
                'cost': row.metrics.cost_micros / 1_000_000,
                'conversions': row.metrics.conversions,
                'conversion_value': row.metrics.conversions_value,
                'view_through_conversions': row.metrics.view_through_conversions
            })

        return {
            'campaigns': campaigns,
            'total_campaigns': len(campaigns)
        }

    def get_store_visits(
        self,
        customer_id: str,
        campaign_id: Optional[str] = None,
        date_range: str = "LAST_30_DAYS"
    ) -> Dict[str, Any]:
        """Get store visit conversion data.

        Args:
            customer_id: Customer ID (without hyphens)
            campaign_id: Optional campaign ID filter
            date_range: Date range for metrics

        Returns:
            Store visit conversion data
        """
        ga_service = self.client.get_service("GoogleAdsService")

        # Note: Store visits require Google My Business integration
        # and may take 4-6 weeks to accumulate data
        query = f"""
            SELECT
                campaign.id,
                campaign.name,
                metrics.conversions,
                metrics.conversions_value,
                segments.conversion_action_name
            FROM campaign
            WHERE campaign.advertising_channel_type = 'LOCAL'
              AND segments.date DURING {date_range}
              AND segments.conversion_action_name LIKE '%store visit%'
        """

        if campaign_id:
            query += f" AND campaign.id = {campaign_id}"

        response = ga_service.search(customer_id=customer_id, query=query)

        store_visits = []
        total_visits = 0
        total_value = 0

        for row in response:
            visits = row.metrics.conversions
            value = row.metrics.conversions_value

            store_visits.append({
                'campaign_id': str(row.campaign.id),
                'campaign_name': row.campaign.name,
                'conversion_action': row.segments.conversion_action_name,
                'store_visits': visits,
                'value': value
            })

            total_visits += visits
            total_value += value

        return {
            'campaigns': store_visits,
            'total_store_visits': total_visits,
            'total_value': total_value,
            'has_data': len(store_visits) > 0
        }

    def create_app_campaign(
        self,
        customer_id: str,
        config: AppCampaignConfig
    ) -> Dict[str, Any]:
        """Create an App campaign (Universal App Campaign).

        Args:
            customer_id: Customer ID (without hyphens)
            config: App campaign configuration

        Returns:
            Created campaign details
        """
        campaign_service = self.client.get_service("CampaignService")
        campaign_budget_service = self.client.get_service("CampaignBudgetService")

        # Create campaign budget
        budget_operation = self.client.get_type("CampaignBudgetOperation")
        budget = budget_operation.create
        budget.name = f"{config.name} Budget"
        budget.amount_micros = int(config.budget_amount * 1_000_000)
        budget.delivery_method = self.client.enums.BudgetDeliveryMethodEnum.STANDARD

        budget_response = campaign_budget_service.mutate_campaign_budgets(
            customer_id=customer_id,
            operations=[budget_operation]
        )
        budget_resource_name = budget_response.results[0].resource_name

        # Create app campaign
        campaign_operation = self.client.get_type("CampaignOperation")
        campaign = campaign_operation.create

        campaign.name = config.name
        campaign.advertising_channel_type = self.client.enums.AdvertisingChannelTypeEnum.MULTI_CHANNEL
        campaign.advertising_channel_sub_type = self.client.enums.AdvertisingChannelSubTypeEnum.APP_CAMPAIGN
        campaign.status = self.client.enums.CampaignStatusEnum.PAUSED
        campaign.campaign_budget = budget_resource_name

        # App campaign settings
        campaign.app_campaign_setting.app_id = config.app_id
        campaign.app_campaign_setting.app_store = self.client.enums.AppCampaignAppStoreEnum[
            config.app_store.value
        ]
        campaign.app_campaign_setting.bidding_strategy_goal_type = (
            self.client.enums.AppCampaignBiddingStrategyGoalTypeEnum[
                config.bidding_strategy_goal_type.value
            ]
        )

        # Set bidding strategy based on goal type
        if config.bidding_strategy_goal_type.value.startswith("OPTIMIZE_INSTALLS"):
            if config.target_cpa:
                campaign.target_cpa.target_cpa_micros = int(config.target_cpa * 1_000_000)
            else:
                campaign.maximize_conversions.CopyFrom(self.client.get_type("MaximizeConversions"))
        elif "TARGET_CONVERSION_COST" in config.bidding_strategy_goal_type.value:
            if config.target_cpa:
                campaign.target_cpa.target_cpa_micros = int(config.target_cpa * 1_000_000)
            else:
                campaign.maximize_conversions.CopyFrom(self.client.get_type("MaximizeConversions"))
        elif config.bidding_strategy_goal_type.value == "OPTIMIZE_RETURN_ON_ADVERTISING_SPEND":
            campaign.maximize_conversion_value.CopyFrom(self.client.get_type("MaximizeConversionValue"))
        else:
            campaign.maximize_conversions.CopyFrom(self.client.get_type("MaximizeConversions"))

        # Create campaign
        response = campaign_service.mutate_campaigns(
            customer_id=customer_id,
            operations=[campaign_operation]
        )

        campaign_id = response.results[0].resource_name.split('/')[-1]

        return {
            'campaign_id': campaign_id,
            'campaign_name': config.name,
            'resource_name': response.results[0].resource_name,
            'app_id': config.app_id,
            'app_store': config.app_store.value,
            'budget': config.budget_amount,
            'bidding_goal': config.bidding_strategy_goal_type.value
        }

    def get_app_performance(
        self,
        customer_id: str,
        campaign_id: Optional[str] = None,
        date_range: str = "LAST_30_DAYS"
    ) -> Dict[str, Any]:
        """Get App campaign performance metrics.

        Args:
            customer_id: Customer ID (without hyphens)
            campaign_id: Optional campaign ID filter
            date_range: Date range for metrics

        Returns:
            App campaign performance data
        """
        ga_service = self.client.get_service("GoogleAdsService")

        query = f"""
            SELECT
                campaign.id,
                campaign.name,
                campaign.app_campaign_setting.app_id,
                campaign.app_campaign_setting.app_store,
                metrics.impressions,
                metrics.clicks,
                metrics.ctr,
                metrics.cost_micros,
                metrics.conversions,
                metrics.conversions_value,
                metrics.cost_per_conversion
            FROM campaign
            WHERE campaign.advertising_channel_sub_type = 'APP_CAMPAIGN'
              AND segments.date DURING {date_range}
        """

        if campaign_id:
            query += f" AND campaign.id = {campaign_id}"

        query += " ORDER BY metrics.impressions DESC"

        response = ga_service.search(customer_id=customer_id, query=query)

        campaigns = []
        for row in response:
            campaigns.append({
                'campaign_id': str(row.campaign.id),
                'campaign_name': row.campaign.name,
                'app_id': row.campaign.app_campaign_setting.app_id,
                'app_store': row.campaign.app_campaign_setting.app_store.name,
                'impressions': row.metrics.impressions,
                'clicks': row.metrics.clicks,
                'ctr': row.metrics.ctr,
                'cost': row.metrics.cost_micros / 1_000_000,
                'conversions': row.metrics.conversions,
                'conversion_value': row.metrics.conversions_value,
                'cost_per_conversion': row.metrics.cost_per_conversion
            })

        return {
            'campaigns': campaigns,
            'total_campaigns': len(campaigns)
        }

    def get_app_conversions(
        self,
        customer_id: str,
        campaign_id: Optional[str] = None,
        date_range: str = "LAST_30_DAYS"
    ) -> Dict[str, Any]:
        """Get app install and engagement conversion data.

        Args:
            customer_id: Customer ID (without hyphens)
            campaign_id: Optional campaign ID filter
            date_range: Date range for metrics

        Returns:
            App conversion data by type
        """
        ga_service = self.client.get_service("GoogleAdsService")

        query = f"""
            SELECT
                campaign.id,
                campaign.name,
                segments.conversion_action_name,
                segments.conversion_action_category,
                metrics.conversions,
                metrics.conversions_value
            FROM campaign
            WHERE campaign.advertising_channel_sub_type = 'APP_CAMPAIGN'
              AND segments.date DURING {date_range}
        """

        if campaign_id:
            query += f" AND campaign.id = {campaign_id}"

        query += " ORDER BY metrics.conversions DESC"

        response = ga_service.search(customer_id=customer_id, query=query)

        conversions_by_type = {}
        campaigns_data = {}

        for row in response:
            campaign_id_str = str(row.campaign.id)
            conversion_category = row.segments.conversion_action_category.name
            conversion_name = row.segments.conversion_action_name

            # Track by campaign
            if campaign_id_str not in campaigns_data:
                campaigns_data[campaign_id_str] = {
                    'campaign_name': row.campaign.name,
                    'conversions': {}
                }

            campaigns_data[campaign_id_str]['conversions'][conversion_name] = {
                'category': conversion_category,
                'conversions': row.metrics.conversions,
                'value': row.metrics.conversions_value
            }

            # Track by type
            if conversion_category not in conversions_by_type:
                conversions_by_type[conversion_category] = {
                    'total_conversions': 0,
                    'total_value': 0
                }

            conversions_by_type[conversion_category]['total_conversions'] += row.metrics.conversions
            conversions_by_type[conversion_category]['total_value'] += row.metrics.conversions_value

        return {
            'campaigns': campaigns_data,
            'by_type': conversions_by_type,
            'total_campaigns': len(campaigns_data)
        }
