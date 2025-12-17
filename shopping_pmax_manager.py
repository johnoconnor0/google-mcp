"""
Shopping & Performance Max Manager

Handles Shopping campaigns and Performance Max campaigns.

Shopping Campaigns:
- Product shopping campaigns
- Product partition management (product groups)
- Shopping feed status monitoring
- Shopping-specific performance metrics

Performance Max Campaigns:
- Performance Max campaign creation
- Asset group management
- Asset uploads (images, videos, text)
- Audience signals configuration
- Performance Max insights and reporting
"""

from typing import Dict, Any, List, Optional
from google.ads.googleads.client import GoogleAdsClient
from dataclasses import dataclass
from enum import Enum


class ShoppingCampaignPriority(str, Enum):
    """Shopping campaign priority levels."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class AssetType(str, Enum):
    """Asset types for Performance Max."""
    IMAGE = "IMAGE"
    VIDEO = "VIDEO"
    TEXT = "TEXT"
    HEADLINE = "HEADLINE"
    DESCRIPTION = "DESCRIPTION"


@dataclass
class ShoppingCampaignConfig:
    """Configuration for shopping campaign creation."""
    name: str
    merchant_center_id: str
    budget_amount: float
    priority: ShoppingCampaignPriority = ShoppingCampaignPriority.LOW
    target_roas: Optional[float] = None
    enable_local: bool = False


@dataclass
class PerformanceMaxCampaignConfig:
    """Configuration for Performance Max campaign creation."""
    name: str
    budget_amount: float
    conversion_goals: List[str]
    target_roas: Optional[float] = None
    target_cpa: Optional[float] = None


class ShoppingPMaxManager:
    """Manager for Shopping and Performance Max campaigns."""

    def __init__(self, client: GoogleAdsClient):
        """Initialize the shopping/PMax manager.

        Args:
            client: Authenticated GoogleAdsClient instance
        """
        self.client = client

    def create_shopping_campaign(
        self,
        customer_id: str,
        config: ShoppingCampaignConfig
    ) -> Dict[str, Any]:
        """Create a Shopping campaign.

        Args:
            customer_id: Customer ID (without hyphens)
            config: Shopping campaign configuration

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

        # Create shopping campaign
        campaign_operation = self.client.get_type("CampaignOperation")
        campaign = campaign_operation.create

        campaign.name = config.name
        campaign.advertising_channel_type = self.client.enums.AdvertisingChannelTypeEnum.SHOPPING
        campaign.status = self.client.enums.CampaignStatusEnum.PAUSED
        campaign.campaign_budget = budget_resource_name

        # Shopping settings
        campaign.shopping_setting.merchant_id = int(config.merchant_center_id)
        campaign.shopping_setting.sales_country = "US"
        campaign.shopping_setting.campaign_priority = {
            "LOW": 0,
            "MEDIUM": 1,
            "HIGH": 2
        }[config.priority.value]
        campaign.shopping_setting.enable_local = config.enable_local

        # Bidding strategy
        if config.target_roas:
            campaign.target_roas.target_roas = config.target_roas
        else:
            campaign.maximize_conversion_value.target_roas = 0

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
            'merchant_center_id': config.merchant_center_id,
            'priority': config.priority.value,
            'budget': config.budget_amount
        }

    def create_product_group(
        self,
        customer_id: str,
        ad_group_id: str,
        product_condition: Optional[str] = None,
        product_type: Optional[str] = None,
        is_subdivision: bool = False
    ) -> Dict[str, Any]:
        """Create a product group (product partition) in a shopping ad group.

        Args:
            customer_id: Customer ID (without hyphens)
            ad_group_id: Shopping ad group ID
            product_condition: Product condition filter (NEW, USED, REFURBISHED)
            product_type: Product type filter
            is_subdivision: Whether this is a subdivision or unit

        Returns:
            Created product group details
        """
        ad_group_criterion_service = self.client.get_service("AdGroupCriterionService")

        criterion_operation = self.client.get_type("AdGroupCriterionOperation")
        criterion = criterion_operation.create

        criterion.ad_group = self.client.get_service("AdGroupService").ad_group_path(
            customer_id, ad_group_id
        )
        criterion.status = self.client.enums.AdGroupCriterionStatusEnum.ENABLED

        # Configure listing group
        criterion.listing_group.type_ = (
            self.client.enums.ListingGroupTypeEnum.SUBDIVISION if is_subdivision
            else self.client.enums.ListingGroupTypeEnum.UNIT
        )

        # Apply product dimensions
        if product_condition:
            dimension = self.client.get_type("ListingDimensionInfo")
            dimension.product_condition.condition = self.client.enums.ProductConditionEnum[product_condition]
            criterion.listing_group.case_value.product_condition.CopyFrom(dimension.product_condition)

        if product_type:
            dimension = self.client.get_type("ListingDimensionInfo")
            dimension.product_type.value = product_type
            criterion.listing_group.case_value.product_type.CopyFrom(dimension.product_type)

        # Set CPC bid for units (not subdivisions)
        if not is_subdivision:
            criterion.cpc_bid_micros = 1_000_000  # $1.00 default

        response = ad_group_criterion_service.mutate_ad_group_criteria(
            customer_id=customer_id,
            operations=[criterion_operation]
        )

        return {
            'resource_name': response.results[0].resource_name,
            'criterion_id': response.results[0].resource_name.split('~')[-1],
            'ad_group_id': ad_group_id,
            'type': 'subdivision' if is_subdivision else 'unit'
        }

    def get_shopping_feed_status(
        self,
        customer_id: str,
        merchant_center_id: str
    ) -> Dict[str, Any]:
        """Check Merchant Center feed status.

        Args:
            customer_id: Customer ID (without hyphens)
            merchant_center_id: Merchant Center ID

        Returns:
            Feed status information
        """
        ga_service = self.client.get_service("GoogleAdsService")

        query = f"""
            SELECT
                merchant_center_link.id,
                merchant_center_link.merchant_center_id,
                merchant_center_link.status
            FROM merchant_center_link
            WHERE merchant_center_link.merchant_center_id = {merchant_center_id}
        """

        response = ga_service.search(customer_id=customer_id, query=query)
        results = list(response)

        if not results:
            return {
                'status': 'NOT_LINKED',
                'message': 'Merchant Center account not linked',
                'merchant_center_id': merchant_center_id
            }

        link = results[0].merchant_center_link

        return {
            'status': link.status.name,
            'merchant_center_id': str(link.merchant_center_id),
            'link_id': str(link.id),
            'message': f'Merchant Center account is {link.status.name}'
        }

    def get_shopping_performance(
        self,
        customer_id: str,
        campaign_id: Optional[str] = None,
        date_range: str = "LAST_30_DAYS"
    ) -> Dict[str, Any]:
        """Get Shopping campaign performance metrics.

        Args:
            customer_id: Customer ID (without hyphens)
            campaign_id: Optional campaign ID filter
            date_range: Date range for metrics

        Returns:
            Shopping performance data
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
                metrics.cost_per_conversion,
                shopping_performance_view.click_type
            FROM shopping_performance_view
            WHERE segments.date DURING {date_range}
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
                'cost_per_conversion': row.metrics.cost_per_conversion,
                'roas': (row.metrics.conversions_value / (row.metrics.cost_micros / 1_000_000))
                        if row.metrics.cost_micros > 0 else 0
            })

        return {
            'campaigns': campaigns,
            'total_campaigns': len(campaigns)
        }

    def create_performance_max_campaign(
        self,
        customer_id: str,
        config: PerformanceMaxCampaignConfig
    ) -> Dict[str, Any]:
        """Create a Performance Max campaign.

        Args:
            customer_id: Customer ID (without hyphens)
            config: Performance Max campaign configuration

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

        # Create Performance Max campaign
        campaign_operation = self.client.get_type("CampaignOperation")
        campaign = campaign_operation.create

        campaign.name = config.name
        campaign.advertising_channel_type = self.client.enums.AdvertisingChannelTypeEnum.PERFORMANCE_MAX
        campaign.status = self.client.enums.CampaignStatusEnum.PAUSED
        campaign.campaign_budget = budget_resource_name

        # Bidding strategy
        if config.target_roas:
            campaign.maximize_conversion_value.target_roas = config.target_roas
        elif config.target_cpa:
            campaign.maximize_conversions.target_cpa_micros = int(config.target_cpa * 1_000_000)
        else:
            campaign.maximize_conversions.target_cpa_micros = 0

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
            'bidding_strategy': 'TARGET_ROAS' if config.target_roas else 'MAXIMIZE_CONVERSIONS'
        }

    def create_asset_group(
        self,
        customer_id: str,
        campaign_id: str,
        asset_group_name: str,
        final_urls: List[str]
    ) -> Dict[str, Any]:
        """Create an asset group for Performance Max campaign.

        Args:
            customer_id: Customer ID (without hyphens)
            campaign_id: Performance Max campaign ID
            asset_group_name: Name for the asset group
            final_urls: List of final URLs

        Returns:
            Created asset group details
        """
        asset_group_service = self.client.get_service("AssetGroupService")

        asset_group_operation = self.client.get_type("AssetGroupOperation")
        asset_group = asset_group_operation.create

        asset_group.name = asset_group_name
        asset_group.campaign = self.client.get_service("CampaignService").campaign_path(
            customer_id, campaign_id
        )
        asset_group.status = self.client.enums.AssetGroupStatusEnum.PAUSED

        # Set final URLs
        asset_group.final_urls.extend(final_urls)

        response = asset_group_service.mutate_asset_groups(
            customer_id=customer_id,
            operations=[asset_group_operation]
        )

        asset_group_id = response.results[0].resource_name.split('/')[-1]

        return {
            'asset_group_id': asset_group_id,
            'asset_group_name': asset_group_name,
            'campaign_id': campaign_id,
            'resource_name': response.results[0].resource_name,
            'final_urls': final_urls
        }

    def upload_pmax_text_asset(
        self,
        customer_id: str,
        asset_group_id: str,
        headlines: List[str],
        descriptions: List[str],
        long_headline: str
    ) -> Dict[str, Any]:
        """Upload text assets to a Performance Max asset group.

        Args:
            customer_id: Customer ID (without hyphens)
            asset_group_id: Asset group ID
            headlines: List of headlines (3-15)
            descriptions: List of descriptions (2-5)
            long_headline: Single long headline

        Returns:
            Upload result
        """
        asset_service = self.client.get_service("AssetService")
        asset_group_asset_service = self.client.get_service("AssetGroupAssetService")

        operations = []
        created_assets = []

        # Create headline assets
        for headline in headlines[:15]:  # Max 15 headlines
            asset_operation = self.client.get_type("AssetOperation")
            asset = asset_operation.create
            asset.text_asset.text = headline
            asset.type_ = self.client.enums.AssetTypeEnum.TEXT

            asset_response = asset_service.mutate_assets(
                customer_id=customer_id,
                operations=[asset_operation]
            )
            asset_resource_name = asset_response.results[0].resource_name

            # Link asset to asset group
            aga_operation = self.client.get_type("AssetGroupAssetOperation")
            aga = aga_operation.create
            aga.asset = asset_resource_name
            aga.asset_group = self.client.get_service("AssetGroupService").asset_group_path(
                customer_id, asset_group_id
            )
            aga.field_type = self.client.enums.AssetFieldTypeEnum.HEADLINE

            operations.append(aga_operation)
            created_assets.append({'type': 'HEADLINE', 'text': headline})

        # Create description assets
        for description in descriptions[:5]:  # Max 5 descriptions
            asset_operation = self.client.get_type("AssetOperation")
            asset = asset_operation.create
            asset.text_asset.text = description
            asset.type_ = self.client.enums.AssetTypeEnum.TEXT

            asset_response = asset_service.mutate_assets(
                customer_id=customer_id,
                operations=[asset_operation]
            )
            asset_resource_name = asset_response.results[0].resource_name

            # Link asset to asset group
            aga_operation = self.client.get_type("AssetGroupAssetOperation")
            aga = aga_operation.create
            aga.asset = asset_resource_name
            aga.asset_group = self.client.get_service("AssetGroupService").asset_group_path(
                customer_id, asset_group_id
            )
            aga.field_type = self.client.enums.AssetFieldTypeEnum.DESCRIPTION

            operations.append(aga_operation)
            created_assets.append({'type': 'DESCRIPTION', 'text': description})

        # Create long headline asset
        asset_operation = self.client.get_type("AssetOperation")
        asset = asset_operation.create
        asset.text_asset.text = long_headline
        asset.type_ = self.client.enums.AssetTypeEnum.TEXT

        asset_response = asset_service.mutate_assets(
            customer_id=customer_id,
            operations=[asset_operation]
        )
        asset_resource_name = asset_response.results[0].resource_name

        aga_operation = self.client.get_type("AssetGroupAssetOperation")
        aga = aga_operation.create
        aga.asset = asset_resource_name
        aga.asset_group = self.client.get_service("AssetGroupService").asset_group_path(
            customer_id, asset_group_id
        )
        aga.field_type = self.client.enums.AssetFieldTypeEnum.LONG_HEADLINE

        operations.append(aga_operation)
        created_assets.append({'type': 'LONG_HEADLINE', 'text': long_headline})

        # Link all assets to asset group
        response = asset_group_asset_service.mutate_asset_group_assets(
            customer_id=customer_id,
            operations=operations
        )

        return {
            'asset_group_id': asset_group_id,
            'total_assets': len(created_assets),
            'headlines': len(headlines),
            'descriptions': len(descriptions),
            'assets': created_assets
        }

    def set_audience_signals(
        self,
        customer_id: str,
        asset_group_id: str,
        audience_segments: List[str]
    ) -> Dict[str, Any]:
        """Configure audience signals for a Performance Max asset group.

        Args:
            customer_id: Customer ID (without hyphens)
            asset_group_id: Asset group ID
            audience_segments: List of audience segment resource names

        Returns:
            Configuration result
        """
        asset_group_signal_service = self.client.get_service("AssetGroupSignalService")

        operations = []

        for segment_resource_name in audience_segments:
            signal_operation = self.client.get_type("AssetGroupSignalOperation")
            signal = signal_operation.create

            signal.asset_group = self.client.get_service("AssetGroupService").asset_group_path(
                customer_id, asset_group_id
            )
            signal.audience.audience = segment_resource_name

            operations.append(signal_operation)

        response = asset_group_signal_service.mutate_asset_group_signals(
            customer_id=customer_id,
            operations=operations
        )

        return {
            'asset_group_id': asset_group_id,
            'audience_signals_added': len(audience_segments),
            'resource_names': [r.resource_name for r in response.results]
        }

    def get_pmax_insights(
        self,
        customer_id: str,
        campaign_id: str,
        date_range: str = "LAST_30_DAYS"
    ) -> Dict[str, Any]:
        """Get Performance Max campaign insights.

        Args:
            customer_id: Customer ID (without hyphens)
            campaign_id: Performance Max campaign ID
            date_range: Date range for metrics

        Returns:
            Performance Max insights
        """
        ga_service = self.client.get_service("GoogleAdsService")

        # Get campaign performance
        campaign_query = f"""
            SELECT
                campaign.id,
                campaign.name,
                metrics.impressions,
                metrics.clicks,
                metrics.ctr,
                metrics.cost_micros,
                metrics.conversions,
                metrics.conversions_value,
                metrics.all_conversions,
                metrics.all_conversions_value
            FROM campaign
            WHERE campaign.id = {campaign_id}
              AND segments.date DURING {date_range}
        """

        campaign_response = ga_service.search(customer_id=customer_id, query=campaign_query)
        campaign_results = list(campaign_response)

        if not campaign_results:
            return {'error': 'Campaign not found or no data available'}

        row = campaign_results[0]

        # Get asset group performance
        asset_group_query = f"""
            SELECT
                asset_group.id,
                asset_group.name,
                asset_group.status,
                metrics.impressions,
                metrics.clicks,
                metrics.conversions
            FROM asset_group
            WHERE campaign.id = {campaign_id}
              AND segments.date DURING {date_range}
        """

        asset_group_response = ga_service.search(customer_id=customer_id, query=asset_group_query)

        asset_groups = []
        for ag_row in asset_group_response:
            asset_groups.append({
                'asset_group_id': str(ag_row.asset_group.id),
                'asset_group_name': ag_row.asset_group.name,
                'status': ag_row.asset_group.status.name,
                'impressions': ag_row.metrics.impressions,
                'clicks': ag_row.metrics.clicks,
                'conversions': ag_row.metrics.conversions
            })

        cost = row.metrics.cost_micros / 1_000_000
        roas = (row.metrics.conversions_value / cost) if cost > 0 else 0

        return {
            'campaign_id': str(row.campaign.id),
            'campaign_name': row.campaign.name,
            'metrics': {
                'impressions': row.metrics.impressions,
                'clicks': row.metrics.clicks,
                'ctr': row.metrics.ctr,
                'cost': cost,
                'conversions': row.metrics.conversions,
                'conversion_value': row.metrics.conversions_value,
                'all_conversions': row.metrics.all_conversions,
                'all_conversions_value': row.metrics.all_conversions_value,
                'roas': roas
            },
            'asset_groups': asset_groups,
            'total_asset_groups': len(asset_groups)
        }
