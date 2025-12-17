"""
Ad Group Manager for Google Ads MCP Server

Provides complete ad group lifecycle management including:
- Ad group creation and configuration
- Status and bid management
- Ad group targeting
- Performance retrieval
"""

from google.ads.googleads.client import GoogleAdsClient
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from enum import Enum
from logger import get_logger

logger = get_logger(__name__)


# ============================================================================
# Enums and Data Classes
# ============================================================================

class AdGroupStatus(str, Enum):
    """Ad group status options."""
    ENABLED = "ENABLED"
    PAUSED = "PAUSED"
    REMOVED = "REMOVED"


class AdGroupType(str, Enum):
    """Ad group type options."""
    SEARCH_STANDARD = "SEARCH_STANDARD"
    DISPLAY_STANDARD = "DISPLAY_STANDARD"
    SHOPPING_PRODUCT_ADS = "SHOPPING_PRODUCT_ADS"
    VIDEO_BUMPER = "VIDEO_BUMPER"
    VIDEO_TRUE_VIEW_IN_STREAM = "VIDEO_TRUE_VIEW_IN_STREAM"
    VIDEO_TRUE_VIEW_IN_DISPLAY = "VIDEO_TRUE_VIEW_IN_DISPLAY"
    VIDEO_NON_SKIPPABLE_IN_STREAM = "VIDEO_NON_SKIPPABLE_IN_STREAM"
    VIDEO_OUTSTREAM = "VIDEO_OUTSTREAM"


@dataclass
class AdGroupConfig:
    """Configuration for creating an ad group."""
    name: str
    campaign_id: str
    status: AdGroupStatus = AdGroupStatus.PAUSED
    cpc_bid_micros: Optional[int] = None  # Manual CPC bid
    cpm_bid_micros: Optional[int] = None  # CPM bid (display)
    cpv_bid_micros: Optional[int] = None  # CPV bid (video)
    target_cpa_micros: Optional[int] = None  # Target CPA
    percent_cpc_bid_micros: Optional[int] = None  # Enhanced CPC
    ad_group_type: Optional[AdGroupType] = None


# ============================================================================
# Ad Group Manager
# ============================================================================

class AdGroupManager:
    """Manages Google Ads ad groups."""

    def __init__(self, client: GoogleAdsClient):
        """
        Initialize the ad group manager.

        Args:
            client: Authenticated Google Ads client
        """
        self.client = client

    # ========================================================================
    # Ad Group Creation
    # ========================================================================

    def create_ad_group(
        self,
        customer_id: str,
        config: AdGroupConfig
    ) -> Dict[str, Any]:
        """
        Create a new ad group.

        Args:
            customer_id: Customer ID
            config: Ad group configuration

        Returns:
            Created ad group details
        """
        ad_group_service = self.client.get_service("AdGroupService")
        campaign_service = self.client.get_service("CampaignService")

        # Create operation
        ad_group_operation = self.client.get_type("AdGroupOperation")
        ad_group = ad_group_operation.create

        # Set basic fields
        ad_group.name = config.name
        ad_group.campaign = campaign_service.campaign_path(
            customer_id, config.campaign_id
        )
        ad_group.status = self.client.enums.AdGroupStatusEnum[config.status.value]

        # Set ad group type if specified
        if config.ad_group_type:
            ad_group.type_ = self.client.enums.AdGroupTypeEnum[config.ad_group_type.value]

        # Set bidding (only set the relevant bid type)
        if config.cpc_bid_micros is not None:
            ad_group.cpc_bid_micros = config.cpc_bid_micros
        elif config.cpm_bid_micros is not None:
            ad_group.cpm_bid_micros = config.cpm_bid_micros
        elif config.cpv_bid_micros is not None:
            ad_group.cpv_bid_micros = config.cpv_bid_micros
        elif config.target_cpa_micros is not None:
            ad_group.target_cpa_micros = config.target_cpa_micros
        elif config.percent_cpc_bid_micros is not None:
            ad_group.percent_cpc_bid_micros = config.percent_cpc_bid_micros

        # Create ad group
        response = ad_group_service.mutate_ad_groups(
            customer_id=customer_id,
            operations=[ad_group_operation]
        )

        ad_group_resource_name = response.results[0].resource_name
        ad_group_id = ad_group_resource_name.split("/")[-1]

        logger.info(f"Created ad group: {ad_group_id} in campaign {config.campaign_id}")

        return {
            "ad_group_id": ad_group_id,
            "resource_name": ad_group_resource_name,
            "name": config.name,
            "campaign_id": config.campaign_id,
            "status": config.status.value
        }

    # ========================================================================
    # Ad Group Updates
    # ========================================================================

    def update_ad_group(
        self,
        customer_id: str,
        ad_group_id: str,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update ad group settings.

        Args:
            customer_id: Customer ID
            ad_group_id: Ad group ID
            updates: Dictionary of fields to update (name, status, cpc_bid_micros, etc.)

        Returns:
            Operation result
        """
        ad_group_service = self.client.get_service("AdGroupService")

        ad_group_operation = self.client.get_type("AdGroupOperation")
        ad_group = ad_group_operation.update

        ad_group.resource_name = ad_group_service.ad_group_path(customer_id, ad_group_id)

        # Track updated fields for field mask
        update_mask_paths = []

        # Update name
        if "name" in updates:
            ad_group.name = updates["name"]
            update_mask_paths.append("name")

        # Update status
        if "status" in updates:
            ad_group.status = self.client.enums.AdGroupStatusEnum[updates["status"]]
            update_mask_paths.append("status")

        # Update CPC bid
        if "cpc_bid_micros" in updates:
            ad_group.cpc_bid_micros = updates["cpc_bid_micros"]
            update_mask_paths.append("cpc_bid_micros")

        # Update CPM bid
        if "cpm_bid_micros" in updates:
            ad_group.cpm_bid_micros = updates["cpm_bid_micros"]
            update_mask_paths.append("cpm_bid_micros")

        # Update CPV bid
        if "cpv_bid_micros" in updates:
            ad_group.cpv_bid_micros = updates["cpv_bid_micros"]
            update_mask_paths.append("cpv_bid_micros")

        # Set field mask
        self.client.copy_from(
            ad_group_operation.update_mask,
            self.client.get_type("FieldMask", version="v17")(paths=update_mask_paths)
        )

        # Update ad group
        response = ad_group_service.mutate_ad_groups(
            customer_id=customer_id,
            operations=[ad_group_operation]
        )

        logger.info(f"Updated ad group {ad_group_id}: {', '.join(update_mask_paths)}")

        return {
            "ad_group_id": ad_group_id,
            "updated_fields": update_mask_paths,
            "message": f"Ad group updated successfully"
        }

    def update_ad_group_status(
        self,
        customer_id: str,
        ad_group_id: str,
        status: AdGroupStatus
    ) -> Dict[str, Any]:
        """
        Update ad group status.

        Args:
            customer_id: Customer ID
            ad_group_id: Ad group ID
            status: New status

        Returns:
            Operation result
        """
        return self.update_ad_group(
            customer_id,
            ad_group_id,
            {"status": status.value}
        )

    def update_ad_group_cpc_bid(
        self,
        customer_id: str,
        ad_group_id: str,
        cpc_bid_micros: int
    ) -> Dict[str, Any]:
        """
        Update ad group CPC bid.

        Args:
            customer_id: Customer ID
            ad_group_id: Ad group ID
            cpc_bid_micros: New CPC bid in micros

        Returns:
            Operation result with bid amount
        """
        result = self.update_ad_group(
            customer_id,
            ad_group_id,
            {"cpc_bid_micros": cpc_bid_micros}
        )

        result["new_cpc_bid"] = cpc_bid_micros / 1_000_000

        return result

    # ========================================================================
    # Ad Group Information
    # ========================================================================

    def get_ad_group_details(
        self,
        customer_id: str,
        ad_group_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about an ad group.

        Args:
            customer_id: Customer ID
            ad_group_id: Ad group ID

        Returns:
            Ad group details or None if not found
        """
        query = f"""
            SELECT
                ad_group.id,
                ad_group.name,
                ad_group.status,
                ad_group.type,
                ad_group.cpc_bid_micros,
                ad_group.cpm_bid_micros,
                ad_group.cpv_bid_micros,
                ad_group.target_cpa_micros,
                campaign.id,
                campaign.name,
                metrics.impressions,
                metrics.clicks,
                metrics.cost_micros,
                metrics.conversions,
                metrics.ctr,
                metrics.average_cpc
            FROM ad_group
            WHERE ad_group.id = {ad_group_id}
        """

        ga_service = self.client.get_service("GoogleAdsService")
        response = ga_service.search(customer_id=customer_id, query=query)

        for row in response:
            return {
                "id": str(row.ad_group.id),
                "name": row.ad_group.name,
                "status": row.ad_group.status.name,
                "type": row.ad_group.type_.name if row.ad_group.type_ else "UNSPECIFIED",
                "campaign": {
                    "id": str(row.campaign.id),
                    "name": row.campaign.name
                },
                "bids": {
                    "cpc_bid": row.ad_group.cpc_bid_micros / 1_000_000 if row.ad_group.cpc_bid_micros else None,
                    "cpm_bid": row.ad_group.cpm_bid_micros / 1_000_000 if row.ad_group.cpm_bid_micros else None,
                    "cpv_bid": row.ad_group.cpv_bid_micros / 1_000_000 if row.ad_group.cpv_bid_micros else None,
                    "target_cpa": row.ad_group.target_cpa_micros / 1_000_000 if row.ad_group.target_cpa_micros else None
                },
                "metrics": {
                    "impressions": row.metrics.impressions,
                    "clicks": row.metrics.clicks,
                    "cost": row.metrics.cost_micros / 1_000_000,
                    "conversions": row.metrics.conversions,
                    "ctr": row.metrics.ctr,
                    "average_cpc": row.metrics.average_cpc / 1_000_000 if row.metrics.average_cpc else 0
                }
            }

        return None

    def list_ad_groups(
        self,
        customer_id: str,
        campaign_id: Optional[str] = None,
        status: Optional[AdGroupStatus] = None
    ) -> List[Dict[str, Any]]:
        """
        List ad groups with optional filters.

        Args:
            customer_id: Customer ID
            campaign_id: Optional campaign ID to filter by
            status: Optional status to filter by

        Returns:
            List of ad groups
        """
        query = """
            SELECT
                ad_group.id,
                ad_group.name,
                ad_group.status,
                ad_group.type,
                ad_group.cpc_bid_micros,
                campaign.id,
                campaign.name,
                metrics.impressions,
                metrics.clicks,
                metrics.cost_micros
            FROM ad_group
            WHERE ad_group.status != 'REMOVED'
        """

        # Add filters
        if campaign_id:
            query += f" AND campaign.id = {campaign_id}"

        if status:
            query += f" AND ad_group.status = {status.value}"

        query += " ORDER BY ad_group.name"

        ga_service = self.client.get_service("GoogleAdsService")
        response = ga_service.search(customer_id=customer_id, query=query)

        ad_groups = []
        for row in response:
            ad_groups.append({
                "id": str(row.ad_group.id),
                "name": row.ad_group.name,
                "status": row.ad_group.status.name,
                "type": row.ad_group.type_.name if row.ad_group.type_ else "UNSPECIFIED",
                "campaign_id": str(row.campaign.id),
                "campaign_name": row.campaign.name,
                "cpc_bid": row.ad_group.cpc_bid_micros / 1_000_000 if row.ad_group.cpc_bid_micros else None,
                "metrics": {
                    "impressions": row.metrics.impressions,
                    "clicks": row.metrics.clicks,
                    "cost": row.metrics.cost_micros / 1_000_000
                }
            })

        logger.info(f"Retrieved {len(ad_groups)} ad groups")

        return ad_groups

    # ========================================================================
    # Ad Group Performance
    # ========================================================================

    def get_ad_group_performance(
        self,
        customer_id: str,
        ad_group_id: str,
        date_range: str = "LAST_30_DAYS"
    ) -> Dict[str, Any]:
        """
        Get performance metrics for an ad group.

        Args:
            customer_id: Customer ID
            ad_group_id: Ad group ID
            date_range: Date range for metrics (e.g., LAST_30_DAYS, LAST_7_DAYS)

        Returns:
            Performance metrics
        """
        query = f"""
            SELECT
                ad_group.id,
                ad_group.name,
                campaign.name,
                metrics.impressions,
                metrics.clicks,
                metrics.ctr,
                metrics.average_cpc,
                metrics.cost_micros,
                metrics.conversions,
                metrics.conversions_value,
                metrics.cost_per_conversion,
                metrics.conversion_rate,
                metrics.all_conversions,
                metrics.view_through_conversions
            FROM ad_group
            WHERE ad_group.id = {ad_group_id}
            AND segments.date DURING {date_range}
        """

        ga_service = self.client.get_service("GoogleAdsService")
        response = ga_service.search(customer_id=customer_id, query=query)

        # Aggregate metrics
        total_metrics = {
            "impressions": 0,
            "clicks": 0,
            "cost": 0,
            "conversions": 0,
            "conversions_value": 0,
            "all_conversions": 0,
            "view_through_conversions": 0
        }

        ad_group_info = None

        for row in response:
            if not ad_group_info:
                ad_group_info = {
                    "id": str(row.ad_group.id),
                    "name": row.ad_group.name,
                    "campaign_name": row.campaign.name
                }

            total_metrics["impressions"] += row.metrics.impressions
            total_metrics["clicks"] += row.metrics.clicks
            total_metrics["cost"] += row.metrics.cost_micros / 1_000_000
            total_metrics["conversions"] += row.metrics.conversions
            total_metrics["conversions_value"] += row.metrics.conversions_value
            total_metrics["all_conversions"] += row.metrics.all_conversions
            total_metrics["view_through_conversions"] += row.metrics.view_through_conversions

        # Calculate derived metrics
        if total_metrics["impressions"] > 0:
            total_metrics["ctr"] = (total_metrics["clicks"] / total_metrics["impressions"]) * 100
        else:
            total_metrics["ctr"] = 0

        if total_metrics["clicks"] > 0:
            total_metrics["average_cpc"] = total_metrics["cost"] / total_metrics["clicks"]
        else:
            total_metrics["average_cpc"] = 0

        if total_metrics["conversions"] > 0:
            total_metrics["cost_per_conversion"] = total_metrics["cost"] / total_metrics["conversions"]
            total_metrics["conversion_rate"] = (total_metrics["conversions"] / total_metrics["clicks"]) * 100
        else:
            total_metrics["cost_per_conversion"] = 0
            total_metrics["conversion_rate"] = 0

        if ad_group_info:
            ad_group_info["metrics"] = total_metrics
            ad_group_info["date_range"] = date_range
            return ad_group_info
        else:
            return {
                "id": ad_group_id,
                "error": "No data found for the specified date range"
            }

    # ========================================================================
    # Bulk Operations
    # ========================================================================

    def bulk_update_ad_group_status(
        self,
        customer_id: str,
        ad_group_ids: List[str],
        status: AdGroupStatus
    ) -> Dict[str, Any]:
        """
        Update status for multiple ad groups at once.

        Args:
            customer_id: Customer ID
            ad_group_ids: List of ad group IDs
            status: New status for all ad groups

        Returns:
            Bulk operation result
        """
        ad_group_service = self.client.get_service("AdGroupService")

        operations = []

        for ad_group_id in ad_group_ids:
            ad_group_operation = self.client.get_type("AdGroupOperation")
            ad_group = ad_group_operation.update

            ad_group.resource_name = ad_group_service.ad_group_path(customer_id, ad_group_id)
            ad_group.status = self.client.enums.AdGroupStatusEnum[status.value]

            self.client.copy_from(
                ad_group_operation.update_mask,
                self.client.get_type("FieldMask", version="v17")(paths=["status"])
            )

            operations.append(ad_group_operation)

        # Execute bulk update
        response = ad_group_service.mutate_ad_groups(
            customer_id=customer_id,
            operations=operations
        )

        logger.info(f"Bulk updated {len(ad_group_ids)} ad groups to {status.value}")

        return {
            "ad_groups_updated": len(ad_group_ids),
            "new_status": status.value,
            "message": f"Successfully updated {len(ad_group_ids)} ad groups"
        }


def create_ad_group_manager(client: GoogleAdsClient) -> AdGroupManager:
    """
    Create an ad group manager instance.

    Args:
        client: Google Ads client

    Returns:
        AdGroupManager instance
    """
    return AdGroupManager(client)
