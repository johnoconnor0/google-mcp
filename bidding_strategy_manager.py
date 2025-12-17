"""
Bidding Strategy Manager

Handles portfolio bidding strategies and bid adjustments across campaigns.
Supports all Google Ads Smart Bidding strategies:
- Target CPA
- Target ROAS
- Maximize Conversions
- Maximize Conversion Value
- Target Impression Share
- Manual CPC (Enhanced)

Includes bid adjustments for:
- Devices (mobile, desktop, tablet)
- Locations (geographic modifiers)
- Demographics (age, gender)
- Audiences (affinity, in-market, custom)
- Ad Schedule (dayparting)
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
from google.ads.googleads.client import GoogleAdsClient


class BiddingStrategyType(str, Enum):
    """Supported bidding strategy types."""
    TARGET_CPA = "TARGET_CPA"
    TARGET_ROAS = "TARGET_ROAS"
    MAXIMIZE_CONVERSIONS = "MAXIMIZE_CONVERSIONS"
    MAXIMIZE_CONVERSION_VALUE = "MAXIMIZE_CONVERSION_VALUE"
    TARGET_IMPRESSION_SHARE = "TARGET_IMPRESSION_SHARE"
    MANUAL_CPC = "MANUAL_CPC"


class ImpressionShareLocation(str, Enum):
    """Impression share location options."""
    ANYWHERE_ON_PAGE = "ANYWHERE_ON_PAGE"
    TOP_OF_PAGE = "TOP_OF_PAGE"
    ABSOLUTE_TOP_OF_PAGE = "ABSOLUTE_TOP_OF_PAGE"


class Device(str, Enum):
    """Device types for bid adjustments."""
    MOBILE = "MOBILE"
    DESKTOP = "DESKTOP"
    TABLET = "TABLET"


class DayOfWeek(str, Enum):
    """Days of week for ad scheduling."""
    MONDAY = "MONDAY"
    TUESDAY = "TUESDAY"
    WEDNESDAY = "WEDNESDAY"
    THURSDAY = "THURSDAY"
    FRIDAY = "FRIDAY"
    SATURDAY = "SATURDAY"
    SUNDAY = "SUNDAY"


@dataclass
class BiddingStrategyConfig:
    """Configuration for creating a portfolio bidding strategy."""
    name: str
    strategy_type: BiddingStrategyType
    target_cpa_micros: Optional[int] = None  # For TARGET_CPA
    target_roas: Optional[float] = None  # For TARGET_ROAS (e.g., 4.0 = 400%)
    target_impression_share: Optional[float] = None  # For TARGET_IMPRESSION_SHARE (0.0-1.0)
    location: Optional[ImpressionShareLocation] = None  # For TARGET_IMPRESSION_SHARE
    cpc_bid_ceiling_micros: Optional[int] = None  # Max CPC for impression share
    enhanced_cpc_enabled: Optional[bool] = None  # For MANUAL_CPC


@dataclass
class AdScheduleConfig:
    """Configuration for ad scheduling bid adjustment."""
    day_of_week: DayOfWeek
    start_hour: int  # 0-23
    start_minute: int  # 0, 15, 30, 45
    end_hour: int  # 0-24
    end_minute: int  # 0, 15, 30, 45
    bid_modifier: float  # 0.1 to 10.0 (1.0 = no change)


class BiddingStrategyManager:
    """Manager for portfolio bidding strategies and bid adjustments."""

    def __init__(self, client: GoogleAdsClient):
        """Initialize the bidding strategy manager.

        Args:
            client: Authenticated GoogleAdsClient instance
        """
        self.client = client

    def create_bidding_strategy(
        self,
        customer_id: str,
        config: BiddingStrategyConfig
    ) -> Dict[str, Any]:
        """Create a portfolio bidding strategy.

        Args:
            customer_id: Customer ID (without hyphens)
            config: Bidding strategy configuration

        Returns:
            Dictionary with strategy resource name and ID
        """
        bidding_strategy_service = self.client.get_service("BiddingStrategyService")
        bidding_strategy_operation = self.client.get_type("BiddingStrategyOperation")

        bidding_strategy = bidding_strategy_operation.create
        bidding_strategy.name = config.name

        # Set strategy type and parameters
        if config.strategy_type == BiddingStrategyType.TARGET_CPA:
            bidding_strategy.target_cpa.target_cpa_micros = config.target_cpa_micros

        elif config.strategy_type == BiddingStrategyType.TARGET_ROAS:
            bidding_strategy.target_roas.target_roas = config.target_roas

        elif config.strategy_type == BiddingStrategyType.MAXIMIZE_CONVERSIONS:
            # Maximize Conversions has no additional parameters
            bidding_strategy.maximize_conversions.SetInParent()

        elif config.strategy_type == BiddingStrategyType.MAXIMIZE_CONVERSION_VALUE:
            # Maximize Conversion Value has optional target ROAS
            if config.target_roas:
                bidding_strategy.maximize_conversion_value.target_roas = config.target_roas
            else:
                bidding_strategy.maximize_conversion_value.SetInParent()

        elif config.strategy_type == BiddingStrategyType.TARGET_IMPRESSION_SHARE:
            target_is = bidding_strategy.target_impression_share
            target_is.target_impression_share = config.target_impression_share

            if config.location:
                target_is.location = self.client.enums.TargetImpressionShareLocationEnum[
                    config.location.value
                ]

            if config.cpc_bid_ceiling_micros:
                target_is.cpc_bid_ceiling_micros = config.cpc_bid_ceiling_micros

        elif config.strategy_type == BiddingStrategyType.MANUAL_CPC:
            if config.enhanced_cpc_enabled:
                bidding_strategy.enhanced_cpc.SetInParent()

        # Create the bidding strategy
        response = bidding_strategy_service.mutate_bidding_strategies(
            customer_id=customer_id,
            operations=[bidding_strategy_operation]
        )

        resource_name = response.results[0].resource_name
        strategy_id = resource_name.split("/")[-1]

        return {
            'resource_name': resource_name,
            'bidding_strategy_id': strategy_id,
            'name': config.name,
            'type': config.strategy_type.value
        }

    def update_bidding_strategy(
        self,
        customer_id: str,
        bidding_strategy_id: str,
        config: BiddingStrategyConfig
    ) -> Dict[str, Any]:
        """Update an existing portfolio bidding strategy.

        Args:
            customer_id: Customer ID (without hyphens)
            bidding_strategy_id: Bidding strategy ID to update
            config: Updated bidding strategy configuration

        Returns:
            Dictionary with updated strategy details
        """
        bidding_strategy_service = self.client.get_service("BiddingStrategyService")
        bidding_strategy_operation = self.client.get_type("BiddingStrategyOperation")

        bidding_strategy = bidding_strategy_operation.update
        bidding_strategy.resource_name = bidding_strategy_service.bidding_strategy_path(
            customer_id, bidding_strategy_id
        )

        # Update strategy parameters based on type
        field_mask_paths = []

        if config.name:
            bidding_strategy.name = config.name
            field_mask_paths.append("name")

        if config.strategy_type == BiddingStrategyType.TARGET_CPA and config.target_cpa_micros:
            bidding_strategy.target_cpa.target_cpa_micros = config.target_cpa_micros
            field_mask_paths.append("target_cpa.target_cpa_micros")

        elif config.strategy_type == BiddingStrategyType.TARGET_ROAS and config.target_roas:
            bidding_strategy.target_roas.target_roas = config.target_roas
            field_mask_paths.append("target_roas.target_roas")

        elif config.strategy_type == BiddingStrategyType.TARGET_IMPRESSION_SHARE:
            if config.target_impression_share:
                bidding_strategy.target_impression_share.target_impression_share = config.target_impression_share
                field_mask_paths.append("target_impression_share.target_impression_share")

            if config.cpc_bid_ceiling_micros:
                bidding_strategy.target_impression_share.cpc_bid_ceiling_micros = config.cpc_bid_ceiling_micros
                field_mask_paths.append("target_impression_share.cpc_bid_ceiling_micros")

        # Set field mask
        self.client.copy_from(
            bidding_strategy_operation.update_mask,
            self.client.get_type("FieldMask", version="v17")(paths=field_mask_paths)
        )

        response = bidding_strategy_service.mutate_bidding_strategies(
            customer_id=customer_id,
            operations=[bidding_strategy_operation]
        )

        return {
            'resource_name': response.results[0].resource_name,
            'bidding_strategy_id': bidding_strategy_id,
            'updated_fields': field_mask_paths
        }

    def assign_bidding_strategy_to_campaign(
        self,
        customer_id: str,
        campaign_id: str,
        bidding_strategy_id: str
    ) -> Dict[str, Any]:
        """Assign a portfolio bidding strategy to a campaign.

        Args:
            customer_id: Customer ID (without hyphens)
            campaign_id: Campaign ID to update
            bidding_strategy_id: Bidding strategy ID to assign

        Returns:
            Dictionary with assignment details
        """
        campaign_service = self.client.get_service("CampaignService")
        bidding_strategy_service = self.client.get_service("BiddingStrategyService")
        campaign_operation = self.client.get_type("CampaignOperation")

        campaign = campaign_operation.update
        campaign.resource_name = campaign_service.campaign_path(customer_id, campaign_id)
        campaign.bidding_strategy = bidding_strategy_service.bidding_strategy_path(
            customer_id, bidding_strategy_id
        )

        self.client.copy_from(
            campaign_operation.update_mask,
            self.client.get_type("FieldMask", version="v17")(paths=["bidding_strategy"])
        )

        response = campaign_service.mutate_campaigns(
            customer_id=customer_id,
            operations=[campaign_operation]
        )

        return {
            'campaign_id': campaign_id,
            'bidding_strategy_id': bidding_strategy_id,
            'resource_name': response.results[0].resource_name
        }

    def get_bidding_strategy_performance(
        self,
        customer_id: str,
        bidding_strategy_id: str,
        date_range: str = "LAST_30_DAYS"
    ) -> Dict[str, Any]:
        """Get performance metrics for a portfolio bidding strategy.

        Args:
            customer_id: Customer ID (without hyphens)
            bidding_strategy_id: Bidding strategy ID
            date_range: Date range for metrics

        Returns:
            Dictionary with performance metrics
        """
        ga_service = self.client.get_service("GoogleAdsService")

        query = f"""
            SELECT
                bidding_strategy.id,
                bidding_strategy.name,
                bidding_strategy.type,
                bidding_strategy.campaign_count,
                metrics.impressions,
                metrics.clicks,
                metrics.ctr,
                metrics.average_cpc,
                metrics.cost_micros,
                metrics.conversions,
                metrics.conversions_value,
                metrics.cost_per_conversion
            FROM bidding_strategy
            WHERE bidding_strategy.id = {bidding_strategy_id}
            AND segments.date DURING {date_range}
        """

        response = ga_service.search(customer_id=customer_id, query=query)
        results = list(response)

        if not results:
            return {
                'bidding_strategy_id': bidding_strategy_id,
                'error': 'No data found for this bidding strategy'
            }

        row = results[0]

        return {
            'bidding_strategy_id': str(row.bidding_strategy.id),
            'name': row.bidding_strategy.name,
            'type': row.bidding_strategy.type.name,
            'campaign_count': row.bidding_strategy.campaign_count,
            'impressions': row.metrics.impressions,
            'clicks': row.metrics.clicks,
            'ctr': row.metrics.ctr,
            'average_cpc': row.metrics.average_cpc / 1_000_000,
            'cost': row.metrics.cost_micros / 1_000_000,
            'conversions': row.metrics.conversions,
            'conversions_value': row.metrics.conversions_value,
            'cost_per_conversion': row.metrics.cost_per_conversion if row.metrics.conversions > 0 else 0
        }

    def set_device_bid_adjustments(
        self,
        customer_id: str,
        campaign_id: str,
        device_adjustments: Dict[Device, float]
    ) -> Dict[str, Any]:
        """Set bid adjustments for different device types.

        Args:
            customer_id: Customer ID (without hyphens)
            campaign_id: Campaign ID
            device_adjustments: Dictionary mapping Device to bid modifier (0.1 to 10.0)

        Returns:
            Dictionary with adjustment results
        """
        campaign_criterion_service = self.client.get_service("CampaignCriterionService")
        operations = []

        for device, bid_modifier in device_adjustments.items():
            operation = self.client.get_type("CampaignCriterionOperation")
            criterion = operation.update

            # Build resource name
            device_id = self._get_device_criterion_id(device)
            criterion.resource_name = campaign_criterion_service.campaign_criterion_path(
                customer_id, campaign_id, device_id
            )

            criterion.bid_modifier = bid_modifier

            self.client.copy_from(
                operation.update_mask,
                self.client.get_type("FieldMask", version="v17")(paths=["bid_modifier"])
            )

            operations.append(operation)

        response = campaign_criterion_service.mutate_campaign_criteria(
            customer_id=customer_id,
            operations=operations
        )

        return {
            'campaign_id': campaign_id,
            'updated_devices': len(response.results),
            'adjustments': device_adjustments
        }

    def set_location_bid_adjustments(
        self,
        customer_id: str,
        campaign_id: str,
        location_adjustments: Dict[str, float]
    ) -> Dict[str, Any]:
        """Set bid adjustments for specific locations.

        Args:
            customer_id: Customer ID (without hyphens)
            campaign_id: Campaign ID
            location_adjustments: Dictionary mapping location criterion ID to bid modifier

        Returns:
            Dictionary with adjustment results
        """
        campaign_criterion_service = self.client.get_service("CampaignCriterionService")
        operations = []

        for location_id, bid_modifier in location_adjustments.items():
            operation = self.client.get_type("CampaignCriterionOperation")
            criterion = operation.update

            criterion.resource_name = campaign_criterion_service.campaign_criterion_path(
                customer_id, campaign_id, location_id
            )

            criterion.bid_modifier = bid_modifier

            self.client.copy_from(
                operation.update_mask,
                self.client.get_type("FieldMask", version="v17")(paths=["bid_modifier"])
            )

            operations.append(operation)

        response = campaign_criterion_service.mutate_campaign_criteria(
            customer_id=customer_id,
            operations=operations
        )

        return {
            'campaign_id': campaign_id,
            'updated_locations': len(response.results),
            'adjustments': location_adjustments
        }

    def set_ad_schedule_bid_adjustments(
        self,
        customer_id: str,
        campaign_id: str,
        schedules: List[AdScheduleConfig]
    ) -> Dict[str, Any]:
        """Set bid adjustments for ad scheduling (dayparting).

        Args:
            customer_id: Customer ID (without hyphens)
            campaign_id: Campaign ID
            schedules: List of ad schedule configurations with bid modifiers

        Returns:
            Dictionary with adjustment results
        """
        campaign_criterion_service = self.client.get_service("CampaignCriterionService")
        operations = []

        for schedule in schedules:
            operation = self.client.get_type("CampaignCriterionOperation")
            criterion = operation.create

            campaign_service = self.client.get_service("CampaignService")
            criterion.campaign = campaign_service.campaign_path(customer_id, campaign_id)

            # Set ad schedule
            ad_schedule = criterion.ad_schedule
            ad_schedule.day_of_week = self.client.enums.DayOfWeekEnum[schedule.day_of_week.value]
            ad_schedule.start_hour = schedule.start_hour
            ad_schedule.start_minute = self.client.enums.MinuteOfHourEnum(schedule.start_minute)
            ad_schedule.end_hour = schedule.end_hour
            ad_schedule.end_minute = self.client.enums.MinuteOfHourEnum(schedule.end_minute)

            criterion.bid_modifier = schedule.bid_modifier

            operations.append(operation)

        response = campaign_criterion_service.mutate_campaign_criteria(
            customer_id=customer_id,
            operations=operations
        )

        return {
            'campaign_id': campaign_id,
            'created_schedules': len(response.results),
            'schedules': [
                {
                    'day': s.day_of_week.value,
                    'time': f"{s.start_hour:02d}:{s.start_minute:02d}-{s.end_hour:02d}:{s.end_minute:02d}",
                    'bid_modifier': s.bid_modifier
                }
                for s in schedules
            ]
        }

    def get_bid_simulator_data(
        self,
        customer_id: str,
        campaign_id: str,
        criterion_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get bid simulation data showing potential performance at different bid levels.

        Args:
            customer_id: Customer ID (without hyphens)
            campaign_id: Campaign ID
            criterion_id: Optional keyword criterion ID for keyword-level simulation

        Returns:
            Dictionary with bid simulation data
        """
        ga_service = self.client.get_service("GoogleAdsService")

        if criterion_id:
            # Keyword-level bid simulation
            query = f"""
                SELECT
                    ad_group_criterion_simulation.criterion_id,
                    ad_group_criterion_simulation.type,
                    ad_group_criterion_simulation.simulation_type,
                    ad_group_criterion_simulation.start_date,
                    ad_group_criterion_simulation.end_date,
                    ad_group_criterion_simulation.cpc_bid_point_list.points
                FROM ad_group_criterion_simulation
                WHERE ad_group_criterion_simulation.criterion_id = {criterion_id}
            """
        else:
            # Campaign-level bid simulation
            query = f"""
                SELECT
                    campaign_simulation.campaign_id,
                    campaign_simulation.type,
                    campaign_simulation.start_date,
                    campaign_simulation.end_date,
                    campaign_simulation.cpc_bid_point_list.points
                FROM campaign_simulation
                WHERE campaign_simulation.campaign_id = {campaign_id}
                AND campaign_simulation.type = 'CPC_BID'
            """

        response = ga_service.search(customer_id=customer_id, query=query)
        results = list(response)

        if not results:
            return {
                'error': 'No bid simulation data available',
                'note': 'Simulations require at least 7 days of historical data'
            }

        row = results[0]

        # Parse simulation points
        if criterion_id:
            points = row.ad_group_criterion_simulation.cpc_bid_point_list.points
        else:
            points = row.campaign_simulation.cpc_bid_point_list.points

        simulation_data = []
        for point in points:
            simulation_data.append({
                'cpc_bid': point.cpc_bid_micros / 1_000_000,
                'impressions': point.impressions,
                'clicks': point.clicks,
                'cost': point.cost_micros / 1_000_000,
                'conversions': point.conversions,
                'conversions_value': point.conversions_value
            })

        return {
            'campaign_id': campaign_id,
            'criterion_id': criterion_id,
            'simulation_points': simulation_data,
            'total_scenarios': len(simulation_data)
        }

    def get_bid_recommendations(
        self,
        customer_id: str,
        campaign_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get AI-powered bid recommendations from Google Ads.

        Args:
            customer_id: Customer ID (without hyphens)
            campaign_id: Optional campaign ID to filter recommendations

        Returns:
            List of bid recommendations
        """
        ga_service = self.client.get_service("GoogleAdsService")

        query = """
            SELECT
                recommendation.type,
                recommendation.campaign,
                recommendation.keyword_recommendation.keyword,
                recommendation.keyword_recommendation.recommended_cpc_bid_micros,
                recommendation.campaign_budget_recommendation.current_budget_amount_micros,
                recommendation.campaign_budget_recommendation.recommended_budget_amount_micros,
                recommendation.impact.base_metrics.impressions,
                recommendation.impact.base_metrics.clicks,
                recommendation.impact.base_metrics.conversions
            FROM recommendation
            WHERE recommendation.type IN ('KEYWORD', 'CAMPAIGN_BUDGET')
        """

        if campaign_id:
            campaign_service = self.client.get_service("CampaignService")
            campaign_resource = campaign_service.campaign_path(customer_id, campaign_id)
            query += f" AND recommendation.campaign = '{campaign_resource}'"

        response = ga_service.search(customer_id=customer_id, query=query)

        recommendations = []
        for row in response:
            rec = row.recommendation

            rec_data = {
                'type': rec.type.name,
                'campaign': rec.campaign.split('/')[-1] if rec.campaign else None
            }

            # Parse based on recommendation type
            if rec.type.name == 'KEYWORD':
                rec_data['keyword'] = rec.keyword_recommendation.keyword.text
                rec_data['recommended_cpc_bid'] = rec.keyword_recommendation.recommended_cpc_bid_micros / 1_000_000
            elif rec.type.name == 'CAMPAIGN_BUDGET':
                rec_data['current_budget'] = rec.campaign_budget_recommendation.current_budget_amount_micros / 1_000_000
                rec_data['recommended_budget'] = rec.campaign_budget_recommendation.recommended_budget_amount_micros / 1_000_000

            # Impact metrics
            if rec.impact:
                rec_data['impact'] = {
                    'impressions': rec.impact.base_metrics.impressions,
                    'clicks': rec.impact.base_metrics.clicks,
                    'conversions': rec.impact.base_metrics.conversions
                }

            recommendations.append(rec_data)

        return recommendations

    def _get_device_criterion_id(self, device: Device) -> str:
        """Get criterion ID for device type.

        Args:
            device: Device enum value

        Returns:
            Criterion ID as string
        """
        device_map = {
            Device.MOBILE: "30001",
            Device.DESKTOP: "30000",
            Device.TABLET: "30002"
        }
        return device_map[device]
