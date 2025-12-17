"""
Google Ads Campaign Manager

Campaign creation and management with:
- All 9 campaign types support
- Campaign CRUD operations
- Budget management
- Targeting (location, language, devices)
- Campaign scheduling
- Network settings
- Bidding strategy configuration
"""

import logging
from typing import Optional, List, Dict, Any, Literal
from enum import Enum
from dataclasses import dataclass
from google.ads.googleads.client import GoogleAdsClient

logger = logging.getLogger(__name__)


class CampaignType(str, Enum):
    """Campaign types in Google Ads."""
    SEARCH = "SEARCH"
    DISPLAY = "DISPLAY"
    SHOPPING = "SHOPPING"
    VIDEO = "VIDEO"
    PERFORMANCE_MAX = "PERFORMANCE_MAX"
    APP = "APP"
    LOCAL = "LOCAL"
    SMART = "SMART"
    DEMAND_GEN = "DEMAND_GEN"


class CampaignStatus(str, Enum):
    """Campaign status values."""
    ENABLED = "ENABLED"
    PAUSED = "PAUSED"
    REMOVED = "REMOVED"


class BiddingStrategyType(str, Enum):
    """Bidding strategy types."""
    MANUAL_CPC = "MANUAL_CPC"
    MANUAL_CPM = "MANUAL_CPM"
    MANUAL_CPV = "MANUAL_CPV"
    MAXIMIZE_CONVERSIONS = "MAXIMIZE_CONVERSIONS"
    MAXIMIZE_CONVERSION_VALUE = "MAXIMIZE_CONVERSION_VALUE"
    TARGET_CPA = "TARGET_CPA"
    TARGET_ROAS = "TARGET_ROAS"
    TARGET_SPEND = "TARGET_SPEND"
    TARGET_IMPRESSION_SHARE = "TARGET_IMPRESSION_SHARE"
    PERCENT_CPC = "PERCENT_CPC"


class NetworkSetting(str, Enum):
    """Network settings for campaigns."""
    SEARCH = "SEARCH"
    SEARCH_NETWORK = "SEARCH_NETWORK"
    CONTENT_NETWORK = "CONTENT_NETWORK"  # Display Network
    PARTNER_SEARCH_NETWORK = "PARTNER_SEARCH_NETWORK"


class AdRotationMode(str, Enum):
    """Ad rotation modes."""
    OPTIMIZE = "OPTIMIZE"
    ROTATE_INDEFINITELY = "ROTATE_INDEFINITELY"


@dataclass
class CampaignConfig:
    """Campaign configuration."""
    name: str
    campaign_type: CampaignType
    status: CampaignStatus = CampaignStatus.PAUSED
    daily_budget_micros: Optional[int] = None
    bidding_strategy_type: BiddingStrategyType = BiddingStrategyType.MANUAL_CPC
    target_cpa_micros: Optional[int] = None
    target_roas: Optional[float] = None
    enable_search_network: bool = True
    enable_search_partners: bool = False
    enable_content_network: bool = False
    start_date: Optional[str] = None  # YYYY-MM-DD
    end_date: Optional[str] = None    # YYYY-MM-DD


@dataclass
class LocationTarget:
    """Location targeting."""
    location_id: str  # Geo target constant ID
    is_negative: bool = False


@dataclass
class LanguageTarget:
    """Language targeting."""
    language_constant_id: str  # Language constant ID


class CampaignManager:
    """
    Manages Google Ads campaigns.
    """

    def __init__(self, client: GoogleAdsClient):
        """
        Initialize campaign manager.

        Args:
            client: Google Ads client
        """
        self.client = client

    def create_campaign(
        self,
        customer_id: str,
        config: CampaignConfig
    ) -> Dict[str, Any]:
        """
        Create a new campaign.

        Args:
            customer_id: Customer ID
            config: Campaign configuration

        Returns:
            Created campaign details
        """
        campaign_service = self.client.get_service("CampaignService")
        campaign_budget_service = self.client.get_service("CampaignBudgetService")

        # Create budget first (if specified)
        budget_resource_name = None
        if config.daily_budget_micros:
            budget_operation = self.client.get_type("CampaignBudgetOperation")
            budget = budget_operation.create

            budget.name = f"{config.name} Budget"
            budget.amount_micros = config.daily_budget_micros
            budget.delivery_method = self.client.enums.BudgetDeliveryMethodEnum.STANDARD

            # Create budget
            budget_response = campaign_budget_service.mutate_campaign_budgets(
                customer_id=customer_id,
                operations=[budget_operation]
            )

            budget_resource_name = budget_response.results[0].resource_name
            logger.info(f"Created budget: {budget_resource_name}")

        # Create campaign
        campaign_operation = self.client.get_type("CampaignOperation")
        campaign = campaign_operation.create

        campaign.name = config.name
        campaign.status = self.client.enums.CampaignStatusEnum[config.status.value]

        # Set campaign type
        if config.campaign_type == CampaignType.SEARCH:
            campaign.advertising_channel_type = (
                self.client.enums.AdvertisingChannelTypeEnum.SEARCH
            )
        elif config.campaign_type == CampaignType.DISPLAY:
            campaign.advertising_channel_type = (
                self.client.enums.AdvertisingChannelTypeEnum.DISPLAY
            )
        elif config.campaign_type == CampaignType.SHOPPING:
            campaign.advertising_channel_type = (
                self.client.enums.AdvertisingChannelTypeEnum.SHOPPING
            )
        elif config.campaign_type == CampaignType.VIDEO:
            campaign.advertising_channel_type = (
                self.client.enums.AdvertisingChannelTypeEnum.VIDEO
            )
        elif config.campaign_type == CampaignType.PERFORMANCE_MAX:
            campaign.advertising_channel_type = (
                self.client.enums.AdvertisingChannelTypeEnum.PERFORMANCE_MAX
            )
        elif config.campaign_type == CampaignType.APP:
            campaign.advertising_channel_type = (
                self.client.enums.AdvertisingChannelTypeEnum.MULTI_CHANNEL
            )
            campaign.advertising_channel_sub_type = (
                self.client.enums.AdvertisingChannelSubTypeEnum.APP_CAMPAIGN
            )
        elif config.campaign_type == CampaignType.LOCAL:
            campaign.advertising_channel_type = (
                self.client.enums.AdvertisingChannelTypeEnum.LOCAL
            )

        # Assign budget
        if budget_resource_name:
            campaign.campaign_budget = budget_resource_name

        # Network settings (for Search campaigns)
        if config.campaign_type == CampaignType.SEARCH:
            campaign.network_settings.target_google_search = True
            campaign.network_settings.target_search_network = config.enable_search_partners
            campaign.network_settings.target_content_network = config.enable_content_network
            campaign.network_settings.target_partner_search_network = config.enable_search_partners

        # Bidding strategy
        self._set_bidding_strategy(campaign, config)

        # Start and end dates
        if config.start_date:
            campaign.start_date = config.start_date
        if config.end_date:
            campaign.end_date = config.end_date

        # Create campaign
        response = campaign_service.mutate_campaigns(
            customer_id=customer_id,
            operations=[campaign_operation]
        )

        campaign_resource_name = response.results[0].resource_name
        campaign_id = campaign_resource_name.split("/")[-1]

        logger.info(f"Created campaign: {campaign_id}")

        return {
            "campaign_id": campaign_id,
            "resource_name": campaign_resource_name,
            "budget_resource_name": budget_resource_name,
            "name": config.name,
            "type": config.campaign_type.value,
            "status": config.status.value
        }

    def _set_bidding_strategy(self, campaign, config: CampaignConfig):
        """Set bidding strategy on campaign."""
        if config.bidding_strategy_type == BiddingStrategyType.MANUAL_CPC:
            campaign.manual_cpc.enhanced_cpc_enabled = True

        elif config.bidding_strategy_type == BiddingStrategyType.MANUAL_CPM:
            campaign.manual_cpm = self.client.get_type("ManualCpm")

        elif config.bidding_strategy_type == BiddingStrategyType.MANUAL_CPV:
            campaign.manual_cpv = self.client.get_type("ManualCpv")

        elif config.bidding_strategy_type == BiddingStrategyType.MAXIMIZE_CONVERSIONS:
            campaign.maximize_conversions = self.client.get_type("MaximizeConversions")
            if config.target_cpa_micros:
                campaign.maximize_conversions.target_cpa_micros = config.target_cpa_micros

        elif config.bidding_strategy_type == BiddingStrategyType.MAXIMIZE_CONVERSION_VALUE:
            campaign.maximize_conversion_value = self.client.get_type("MaximizeConversionValue")
            if config.target_roas:
                campaign.maximize_conversion_value.target_roas = config.target_roas

        elif config.bidding_strategy_type == BiddingStrategyType.TARGET_CPA:
            campaign.target_cpa.target_cpa_micros = config.target_cpa_micros or 10000000

        elif config.bidding_strategy_type == BiddingStrategyType.TARGET_ROAS:
            campaign.target_roas.target_roas = config.target_roas or 1.0

        elif config.bidding_strategy_type == BiddingStrategyType.TARGET_SPEND:
            campaign.target_spend = self.client.get_type("TargetSpend")

    def update_campaign(
        self,
        customer_id: str,
        campaign_id: str,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update campaign settings.

        Args:
            customer_id: Customer ID
            campaign_id: Campaign ID
            updates: Dictionary of fields to update

        Returns:
            Updated campaign details
        """
        campaign_service = self.client.get_service("CampaignService")

        campaign_operation = self.client.get_type("CampaignOperation")
        campaign = campaign_operation.update

        campaign.resource_name = campaign_service.campaign_path(customer_id, campaign_id)

        # Update fields
        field_mask = []

        if "name" in updates:
            campaign.name = updates["name"]
            field_mask.append("name")

        if "status" in updates:
            campaign.status = self.client.enums.CampaignStatusEnum[updates["status"]]
            field_mask.append("status")

        if "start_date" in updates:
            campaign.start_date = updates["start_date"]
            field_mask.append("start_date")

        if "end_date" in updates:
            campaign.end_date = updates["end_date"]
            field_mask.append("end_date")

        # Set field mask
        self.client.copy_from(
            campaign_operation.update_mask,
            self.client.get_type("FieldMask", version="v17")(paths=field_mask)
        )

        # Update campaign
        response = campaign_service.mutate_campaigns(
            customer_id=customer_id,
            operations=[campaign_operation]
        )

        logger.info(f"Updated campaign: {campaign_id}")

        return {
            "campaign_id": campaign_id,
            "resource_name": response.results[0].resource_name,
            "updated_fields": field_mask
        }

    def update_campaign_status(
        self,
        customer_id: str,
        campaign_id: str,
        status: CampaignStatus
    ) -> Dict[str, Any]:
        """
        Update campaign status (enable/pause/remove).

        Args:
            customer_id: Customer ID
            campaign_id: Campaign ID
            status: New status

        Returns:
            Update result
        """
        return self.update_campaign(
            customer_id=customer_id,
            campaign_id=campaign_id,
            updates={"status": status.value}
        )

    def update_campaign_budget(
        self,
        customer_id: str,
        campaign_id: str,
        daily_budget_micros: int
    ) -> Dict[str, Any]:
        """
        Update campaign daily budget.

        Args:
            customer_id: Customer ID
            campaign_id: Campaign ID
            daily_budget_micros: New daily budget in micros

        Returns:
            Update result
        """
        # First, get the campaign's budget resource name
        query = f"""
            SELECT campaign.campaign_budget
            FROM campaign
            WHERE campaign.id = {campaign_id}
        """

        ga_service = self.client.get_service("GoogleAdsService")
        response = ga_service.search(customer_id=customer_id, query=query)

        budget_resource_name = None
        for row in response:
            budget_resource_name = row.campaign.campaign_budget
            break

        if not budget_resource_name:
            raise ValueError(f"Campaign {campaign_id} has no budget assigned")

        # Update the budget
        campaign_budget_service = self.client.get_service("CampaignBudgetService")

        budget_operation = self.client.get_type("CampaignBudgetOperation")
        budget = budget_operation.update

        budget.resource_name = budget_resource_name
        budget.amount_micros = daily_budget_micros

        # Set field mask
        self.client.copy_from(
            budget_operation.update_mask,
            self.client.get_type("FieldMask", version="v17")(paths=["amount_micros"])
        )

        # Update budget
        budget_response = campaign_budget_service.mutate_campaign_budgets(
            customer_id=customer_id,
            operations=[budget_operation]
        )

        logger.info(f"Updated budget for campaign {campaign_id} to {daily_budget_micros} micros")

        return {
            "campaign_id": campaign_id,
            "budget_resource_name": budget_response.results[0].resource_name,
            "new_budget_micros": daily_budget_micros,
            "new_budget_amount": daily_budget_micros / 1_000_000
        }

    def remove_campaign(
        self,
        customer_id: str,
        campaign_id: str
    ) -> Dict[str, Any]:
        """
        Remove (delete) a campaign.

        Args:
            customer_id: Customer ID
            campaign_id: Campaign ID to remove

        Returns:
            Removal result
        """
        campaign_service = self.client.get_service("CampaignService")

        campaign_operation = self.client.get_type("CampaignOperation")
        campaign_operation.remove = campaign_service.campaign_path(customer_id, campaign_id)

        # Remove campaign
        response = campaign_service.mutate_campaigns(
            customer_id=customer_id,
            operations=[campaign_operation]
        )

        logger.info(f"Removed campaign: {campaign_id}")

        return {
            "campaign_id": campaign_id,
            "resource_name": response.results[0].resource_name,
            "status": "removed"
        }

    def set_location_targets(
        self,
        customer_id: str,
        campaign_id: str,
        locations: List[LocationTarget]
    ) -> Dict[str, Any]:
        """
        Set location targeting for a campaign.

        Args:
            customer_id: Customer ID
            campaign_id: Campaign ID
            locations: List of location targets

        Returns:
            Operation result
        """
        campaign_criterion_service = self.client.get_service("CampaignCriterionService")

        operations = []

        for location in locations:
            operation = self.client.get_type("CampaignCriterionOperation")
            criterion = operation.create

            criterion.campaign = campaign_criterion_service.campaign_path(
                customer_id, campaign_id
            )

            criterion.location.geo_target_constant = (
                f"geoTargetConstants/{location.location_id}"
            )

            criterion.negative = location.is_negative

            operations.append(operation)

        # Add criteria
        response = campaign_criterion_service.mutate_campaign_criteria(
            customer_id=customer_id,
            operations=operations
        )

        logger.info(f"Added {len(operations)} location targets to campaign {campaign_id}")

        return {
            "campaign_id": campaign_id,
            "locations_added": len(operations),
            "resource_names": [result.resource_name for result in response.results]
        }

    def set_language_targets(
        self,
        customer_id: str,
        campaign_id: str,
        languages: List[LanguageTarget]
    ) -> Dict[str, Any]:
        """
        Set language targeting for a campaign.

        Args:
            customer_id: Customer ID
            campaign_id: Campaign ID
            languages: List of language targets

        Returns:
            Operation result
        """
        campaign_criterion_service = self.client.get_service("CampaignCriterionService")

        operations = []

        for language in languages:
            operation = self.client.get_type("CampaignCriterionOperation")
            criterion = operation.create

            criterion.campaign = campaign_criterion_service.campaign_path(
                customer_id, campaign_id
            )

            criterion.language.language_constant = (
                f"languageConstants/{language.language_constant_id}"
            )

            operations.append(operation)

        # Add criteria
        response = campaign_criterion_service.mutate_campaign_criteria(
            customer_id=customer_id,
            operations=operations
        )

        logger.info(f"Added {len(operations)} language targets to campaign {campaign_id}")

        return {
            "campaign_id": campaign_id,
            "languages_added": len(operations),
            "resource_names": [result.resource_name for result in response.results]
        }

    def get_campaign_details(
        self,
        customer_id: str,
        campaign_id: str
    ) -> Dict[str, Any]:
        """
        Get detailed campaign information.

        Args:
            customer_id: Customer ID
            campaign_id: Campaign ID

        Returns:
            Campaign details
        """
        query = f"""
            SELECT
                campaign.id,
                campaign.name,
                campaign.status,
                campaign.advertising_channel_type,
                campaign.campaign_budget,
                campaign.start_date,
                campaign.end_date,
                campaign.bidding_strategy_type,
                campaign.network_settings.target_google_search,
                campaign.network_settings.target_search_network,
                campaign.network_settings.target_content_network,
                campaign.target_cpa.target_cpa_micros,
                campaign.target_roas.target_roas,
                metrics.cost_micros,
                metrics.clicks,
                metrics.impressions,
                metrics.conversions
            FROM campaign
            WHERE campaign.id = {campaign_id}
        """

        ga_service = self.client.get_service("GoogleAdsService")
        response = ga_service.search(customer_id=customer_id, query=query)

        for row in response:
            return {
                "id": str(row.campaign.id),
                "name": row.campaign.name,
                "status": row.campaign.status.name,
                "type": row.campaign.advertising_channel_type.name,
                "budget": row.campaign.campaign_budget,
                "start_date": row.campaign.start_date,
                "end_date": row.campaign.end_date,
                "bidding_strategy": row.campaign.bidding_strategy_type.name,
                "network_settings": {
                    "google_search": row.campaign.network_settings.target_google_search,
                    "search_network": row.campaign.network_settings.target_search_network,
                    "content_network": row.campaign.network_settings.target_content_network
                },
                "metrics": {
                    "cost": row.metrics.cost_micros / 1_000_000,
                    "clicks": row.metrics.clicks,
                    "impressions": row.metrics.impressions,
                    "conversions": row.metrics.conversions
                }
            }

        return None

    def set_device_bid_adjustments(
        self,
        customer_id: str,
        campaign_id: str,
        mobile_modifier: Optional[float] = None,
        desktop_modifier: Optional[float] = None,
        tablet_modifier: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Set device bid adjustments for a campaign.

        Args:
            customer_id: Customer ID
            campaign_id: Campaign ID
            mobile_modifier: Mobile bid modifier (e.g., 1.2 for +20%, 0.8 for -20%)
            desktop_modifier: Desktop bid modifier
            tablet_modifier: Tablet bid modifier

        Returns:
            Operation result
        """
        campaign_criterion_service = self.client.get_service("CampaignCriterionService")

        operations = []
        device_modifiers = {}

        # Map device types to their constants
        device_map = {
            'mobile': (self.client.enums.DeviceEnum.MOBILE, mobile_modifier),
            'desktop': (self.client.enums.DeviceEnum.DESKTOP, desktop_modifier),
            'tablet': (self.client.enums.DeviceEnum.TABLET, tablet_modifier)
        }

        for device_name, (device_type, modifier) in device_map.items():
            if modifier is not None:
                operation = self.client.get_type("CampaignCriterionOperation")
                criterion = operation.create

                criterion.campaign = campaign_criterion_service.campaign_path(
                    customer_id, campaign_id
                )
                criterion.device.type_ = device_type

                # Bid modifier: 1.0 = no change, 1.2 = +20%, 0.8 = -20%
                criterion.bid_modifier = modifier

                operations.append(operation)
                device_modifiers[device_name] = modifier

        if not operations:
            raise ValueError("At least one device modifier must be specified")

        # Add criteria
        response = campaign_criterion_service.mutate_campaign_criteria(
            customer_id=customer_id,
            operations=operations
        )

        logger.info(f"Set device bid adjustments for campaign {campaign_id}")

        return {
            "campaign_id": campaign_id,
            "device_modifiers": device_modifiers,
            "criteria_added": len(operations)
        }

    def set_ad_schedule(
        self,
        customer_id: str,
        campaign_id: str,
        schedules: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Set ad scheduling (dayparting) for a campaign.

        Args:
            customer_id: Customer ID
            campaign_id: Campaign ID
            schedules: List of schedule dicts with:
                - day_of_week: Day name (MONDAY, TUESDAY, etc.)
                - start_hour: Start hour (0-23)
                - start_minute: Start minute (0, 15, 30, 45)
                - end_hour: End hour (0-24)
                - end_minute: End minute (0, 15, 30, 45)
                - bid_modifier: Optional bid adjustment (default 1.0)

        Returns:
            Operation result
        """
        campaign_criterion_service = self.client.get_service("CampaignCriterionService")

        operations = []

        for schedule in schedules:
            operation = self.client.get_type("CampaignCriterionOperation")
            criterion = operation.create

            criterion.campaign = campaign_criterion_service.campaign_path(
                customer_id, campaign_id
            )

            # Set ad schedule
            ad_schedule = criterion.ad_schedule
            ad_schedule.day_of_week = self.client.enums.DayOfWeekEnum[
                schedule['day_of_week'].upper()
            ]
            ad_schedule.start_hour = schedule['start_hour']
            ad_schedule.start_minute = self.client.enums.MinuteOfHourEnum[
                f"MINUTE_{schedule.get('start_minute', 0)}"
            ]
            ad_schedule.end_hour = schedule['end_hour']
            ad_schedule.end_minute = self.client.enums.MinuteOfHourEnum[
                f"MINUTE_{schedule.get('end_minute', 0)}"
            ]

            # Set bid modifier if provided
            if 'bid_modifier' in schedule:
                criterion.bid_modifier = schedule['bid_modifier']

            operations.append(operation)

        # Add criteria
        response = campaign_criterion_service.mutate_campaign_criteria(
            customer_id=customer_id,
            operations=operations
        )

        logger.info(f"Set {len(operations)} ad schedules for campaign {campaign_id}")

        return {
            "campaign_id": campaign_id,
            "schedules_added": len(operations),
            "resource_names": [result.resource_name for result in response.results]
        }

    def duplicate_campaign(
        self,
        customer_id: str,
        campaign_id: str,
        new_name: str,
        include_ad_groups: bool = False
    ) -> Dict[str, Any]:
        """
        Duplicate an existing campaign.

        Args:
            customer_id: Customer ID
            campaign_id: Campaign ID to duplicate
            new_name: Name for the new campaign
            include_ad_groups: Whether to also copy ad groups (default: False)

        Returns:
            New campaign details
        """
        # Get campaign details
        original = self.get_campaign_details(customer_id, campaign_id)

        if not original:
            raise ValueError(f"Campaign {campaign_id} not found")

        # Get full campaign info including budget
        query = f"""
            SELECT
                campaign.id,
                campaign.name,
                campaign.status,
                campaign.advertising_channel_type,
                campaign.bidding_strategy_type,
                campaign.network_settings.target_google_search,
                campaign.network_settings.target_search_network,
                campaign.network_settings.target_content_network,
                campaign.target_cpa.target_cpa_micros,
                campaign.target_roas.target_roas,
                campaign_budget.amount_micros
            FROM campaign
            WHERE campaign.id = {campaign_id}
        """

        ga_service = self.client.get_service("GoogleAdsService")
        response = ga_service.search(customer_id=customer_id, query=query)

        campaign_data = None
        for row in response:
            campaign_data = row
            break

        if not campaign_data:
            raise ValueError(f"Could not retrieve campaign {campaign_id} data")

        # Create config for new campaign
        config = CampaignConfig(
            name=new_name,
            campaign_type=CampaignType[campaign_data.campaign.advertising_channel_type.name],
            status=CampaignStatus.PAUSED,  # Always start paused for safety
            daily_budget_micros=campaign_data.campaign_budget.amount_micros if hasattr(campaign_data, 'campaign_budget') else None,
            bidding_strategy_type=BiddingStrategyType[campaign_data.campaign.bidding_strategy_type.name],
            target_cpa_micros=campaign_data.campaign.target_cpa.target_cpa_micros if hasattr(campaign_data.campaign, 'target_cpa') else None,
            target_roas=campaign_data.campaign.target_roas.target_roas if hasattr(campaign_data.campaign, 'target_roas') else None,
            enable_search_network=campaign_data.campaign.network_settings.target_google_search,
            enable_search_partners=campaign_data.campaign.network_settings.target_search_network,
            enable_content_network=campaign_data.campaign.network_settings.target_content_network
        )

        # Create new campaign
        result = self.create_campaign(customer_id, config)

        logger.info(f"Duplicated campaign {campaign_id} to {result['campaign_id']}")

        # TODO: Copy targeting settings, ad groups, etc. if requested
        # This would require additional queries and operations

        return {
            "original_campaign_id": campaign_id,
            "new_campaign_id": result['campaign_id'],
            "new_campaign_name": new_name,
            "status": "PAUSED",
            "note": "Campaign duplicated successfully. Ad groups not copied (not yet implemented)."
        }

    def create_shared_budget(
        self,
        customer_id: str,
        budget_name: str,
        amount_micros: int,
        delivery_method: str = "STANDARD"
    ) -> Dict[str, Any]:
        """
        Create a shared budget that can be used across multiple campaigns.

        Args:
            customer_id: Customer ID
            budget_name: Name for the budget
            amount_micros: Daily budget amount in micros
            delivery_method: STANDARD or ACCELERATED

        Returns:
            Created budget details
        """
        campaign_budget_service = self.client.get_service("CampaignBudgetService")

        budget_operation = self.client.get_type("CampaignBudgetOperation")
        budget = budget_operation.create

        budget.name = budget_name
        budget.amount_micros = amount_micros
        budget.delivery_method = self.client.enums.BudgetDeliveryMethodEnum[delivery_method]
        budget.explicitly_shared = True  # Mark as shared

        # Create budget
        response = campaign_budget_service.mutate_campaign_budgets(
            customer_id=customer_id,
            operations=[budget_operation]
        )

        budget_resource_name = response.results[0].resource_name
        budget_id = budget_resource_name.split("/")[-1]

        logger.info(f"Created shared budget: {budget_id}")

        return {
            "budget_id": budget_id,
            "resource_name": budget_resource_name,
            "name": budget_name,
            "amount_micros": amount_micros,
            "amount": amount_micros / 1_000_000,
            "delivery_method": delivery_method,
            "shared": True
        }

    def assign_shared_budget(
        self,
        customer_id: str,
        campaign_id: str,
        budget_resource_name: str
    ) -> Dict[str, Any]:
        """
        Assign a shared budget to a campaign.

        Args:
            customer_id: Customer ID
            campaign_id: Campaign ID
            budget_resource_name: Resource name of the shared budget

        Returns:
            Operation result
        """
        campaign_service = self.client.get_service("CampaignService")

        campaign_operation = self.client.get_type("CampaignOperation")
        campaign = campaign_operation.update

        campaign.resource_name = campaign_service.campaign_path(customer_id, campaign_id)
        campaign.campaign_budget = budget_resource_name

        # Set field mask
        self.client.copy_from(
            campaign_operation.update_mask,
            self.client.get_type("FieldMask", version="v17")(paths=["campaign_budget"])
        )

        # Update campaign
        response = campaign_service.mutate_campaigns(
            customer_id=customer_id,
            operations=[campaign_operation]
        )

        logger.info(f"Assigned shared budget to campaign {campaign_id}")

        return {
            "campaign_id": campaign_id,
            "budget_resource_name": budget_resource_name
        }

    def add_campaign_exclusions(
        self,
        customer_id: str,
        campaign_id: str,
        placement_exclusions: Optional[List[str]] = None,
        ip_exclusions: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Add exclusions to a campaign.

        Args:
            customer_id: Customer ID
            campaign_id: Campaign ID
            placement_exclusions: List of placement URLs to exclude
            ip_exclusions: List of IP addresses to exclude

        Returns:
            Operation result
        """
        campaign_criterion_service = self.client.get_service("CampaignCriterionService")

        operations = []
        exclusion_counts = {}

        # Add placement exclusions
        if placement_exclusions:
            for url in placement_exclusions:
                operation = self.client.get_type("CampaignCriterionOperation")
                criterion = operation.create

                criterion.campaign = campaign_criterion_service.campaign_path(
                    customer_id, campaign_id
                )
                criterion.placement.url = url
                criterion.negative = True

                operations.append(operation)

            exclusion_counts['placements'] = len(placement_exclusions)

        # Add IP exclusions
        if ip_exclusions:
            for ip_address in ip_exclusions:
                operation = self.client.get_type("CampaignCriterionOperation")
                criterion = operation.create

                criterion.campaign = campaign_criterion_service.campaign_path(
                    customer_id, campaign_id
                )
                criterion.ip_block.ip_address = ip_address
                criterion.negative = True

                operations.append(operation)

            exclusion_counts['ip_addresses'] = len(ip_exclusions)

        if not operations:
            raise ValueError("At least one exclusion type must be specified")

        # Add criteria
        response = campaign_criterion_service.mutate_campaign_criteria(
            customer_id=customer_id,
            operations=operations
        )

        logger.info(f"Added {len(operations)} exclusions to campaign {campaign_id}")

        return {
            "campaign_id": campaign_id,
            "exclusions": exclusion_counts,
            "total_exclusions": len(operations)
        }


def create_campaign_manager(client: GoogleAdsClient) -> CampaignManager:
    """
    Create a campaign manager instance.

    Args:
        client: Google Ads client

    Returns:
        Campaign manager
    """
    return CampaignManager(client)
