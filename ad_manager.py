"""
Ad Manager for Google Ads MCP Server

Provides complete ad lifecycle management including:
- Responsive Search Ads (RSA) creation
- Expanded Text Ads creation
- Ad status management
- Ad performance tracking
- Ad asset management
- Ad preview and testing
- Bulk operations
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

class AdStatus(str, Enum):
    """Ad status options."""
    ENABLED = "ENABLED"
    PAUSED = "PAUSED"
    REMOVED = "REMOVED"


class AdStrength(str, Enum):
    """Ad strength ratings for RSAs."""
    UNSPECIFIED = "UNSPECIFIED"
    UNKNOWN = "UNKNOWN"
    PENDING = "PENDING"
    NO_ADS = "NO_ADS"
    POOR = "POOR"
    AVERAGE = "AVERAGE"
    GOOD = "GOOD"
    EXCELLENT = "EXCELLENT"


@dataclass
class ResponsiveSearchAdConfig:
    """Configuration for creating a Responsive Search Ad."""
    ad_group_id: str
    headlines: List[str]  # 3-15 headlines
    descriptions: List[str]  # 2-4 descriptions
    path1: Optional[str] = None
    path2: Optional[str] = None
    final_urls: Optional[List[str]] = None
    status: AdStatus = AdStatus.PAUSED


# ============================================================================
# Ad Manager
# ============================================================================

class AdManager:
    """Manages Google Ads ad creatives."""

    def __init__(self, client: GoogleAdsClient):
        """
        Initialize the ad manager.

        Args:
            client: Authenticated Google Ads client
        """
        self.client = client

    # ========================================================================
    # Responsive Search Ad Creation
    # ========================================================================

    def create_responsive_search_ad(
        self,
        customer_id: str,
        config: ResponsiveSearchAdConfig
    ) -> Dict[str, Any]:
        """
        Create a Responsive Search Ad (RSA).

        Args:
            customer_id: Customer ID
            config: RSA configuration

        Returns:
            Created ad details
        """
        ad_group_ad_service = self.client.get_service("AdGroupAdService")
        ad_group_service = self.client.get_service("AdGroupService")

        # Create ad group ad operation
        ad_group_ad_operation = self.client.get_type("AdGroupAdOperation")
        ad_group_ad = ad_group_ad_operation.create

        # Set ad group
        ad_group_ad.ad_group = ad_group_service.ad_group_path(
            customer_id, config.ad_group_id
        )

        # Set status
        ad_group_ad.status = self.client.enums.AdGroupAdStatusEnum[config.status.value]

        # Create responsive search ad
        rsa = ad_group_ad.ad.responsive_search_ad

        # Add headlines (3-15 required)
        for headline_text in config.headlines:
            headline = self.client.get_type("AdTextAsset")
            headline.text = headline_text
            rsa.headlines.append(headline)

        # Add descriptions (2-4 required)
        for desc_text in config.descriptions:
            description = self.client.get_type("AdTextAsset")
            description.text = desc_text
            rsa.descriptions.append(description)

        # Set paths if provided
        if config.path1:
            ad_group_ad.ad.responsive_search_ad.path1 = config.path1
        if config.path2:
            ad_group_ad.ad.responsive_search_ad.path2 = config.path2

        # Set final URLs
        if config.final_urls:
            ad_group_ad.ad.final_urls.extend(config.final_urls)

        # Add ad
        response = ad_group_ad_service.mutate_ad_group_ads(
            customer_id=customer_id,
            operations=[ad_group_ad_operation]
        )

        ad_resource_name = response.results[0].resource_name
        ad_id = ad_resource_name.split("/")[-1]

        logger.info(f"Created RSA: {ad_id}")

        return {
            "ad_id": ad_id,
            "resource_name": ad_resource_name,
            "ad_group_id": config.ad_group_id,
            "headline_count": len(config.headlines),
            "description_count": len(config.descriptions),
            "status": config.status.value
        }

    # ========================================================================
    # Ad Updates
    # ========================================================================

    def update_ad_status(
        self,
        customer_id: str,
        ad_group_id: str,
        ad_id: str,
        status: AdStatus
    ) -> Dict[str, Any]:
        """
        Update ad status.

        Args:
            customer_id: Customer ID
            ad_group_id: Ad group ID
            ad_id: Ad ID
            status: New status

        Returns:
            Operation result
        """
        ad_group_ad_service = self.client.get_service("AdGroupAdService")

        ad_group_ad_operation = self.client.get_type("AdGroupAdOperation")
        ad_group_ad = ad_group_ad_operation.update

        ad_group_ad.resource_name = ad_group_ad_service.ad_group_ad_path(
            customer_id, ad_group_id, ad_id
        )
        ad_group_ad.status = self.client.enums.AdGroupAdStatusEnum[status.value]

        # Set field mask
        self.client.copy_from(
            ad_group_ad_operation.update_mask,
            self.client.get_type("FieldMask", version="v17")(paths=["status"])
        )

        # Update ad
        response = ad_group_ad_service.mutate_ad_group_ads(
            customer_id=customer_id,
            operations=[ad_group_ad_operation]
        )

        logger.info(f"Updated ad {ad_id} status to {status.value}")

        return {
            "ad_id": ad_id,
            "new_status": status.value,
            "message": f"Ad status updated to {status.value}"
        }

    # ========================================================================
    # Ad Information
    # ========================================================================

    def list_ads(
        self,
        customer_id: str,
        ad_group_id: str
    ) -> List[Dict[str, Any]]:
        """
        List all ads in an ad group.

        Args:
            customer_id: Customer ID
            ad_group_id: Ad group ID

        Returns:
            List of ads
        """
        query = f"""
            SELECT
                ad_group_ad.ad.id,
                ad_group_ad.ad.type,
                ad_group_ad.status,
                ad_group_ad.ad.responsive_search_ad.headlines,
                ad_group_ad.ad.responsive_search_ad.descriptions,
                ad_group_ad.ad.final_urls,
                ad_group_ad.policy_summary.approval_status,
                ad_group_ad.ad_strength
            FROM ad_group_ad
            WHERE ad_group.id = {ad_group_id}
            AND ad_group_ad.status != REMOVED
            ORDER BY ad_group_ad.ad.id
        """

        ga_service = self.client.get_service("GoogleAdsService")
        response = ga_service.search(customer_id=customer_id, query=query)

        ads = []
        for row in response:
            ad_data = {
                "ad_id": str(row.ad_group_ad.ad.id),
                "ad_type": row.ad_group_ad.ad.type_.name,
                "status": row.ad_group_ad.status.name,
                "approval_status": row.ad_group_ad.policy_summary.approval_status.name if hasattr(row.ad_group_ad, 'policy_summary') else "UNKNOWN",
                "ad_strength": row.ad_group_ad.ad_strength.name if hasattr(row.ad_group_ad, 'ad_strength') else "UNKNOWN"
            }

            # Get RSA details if applicable
            if row.ad_group_ad.ad.type_.name == "RESPONSIVE_SEARCH_AD":
                rsa = row.ad_group_ad.ad.responsive_search_ad
                ad_data["headlines"] = [h.text for h in rsa.headlines]
                ad_data["descriptions"] = [d.text for d in rsa.descriptions]

            # Get final URLs
            ad_data["final_urls"] = list(row.ad_group_ad.ad.final_urls) if row.ad_group_ad.ad.final_urls else []

            ads.append(ad_data)

        return ads

    def get_ad_performance(
        self,
        customer_id: str,
        ad_group_id: Optional[str] = None,
        date_range: str = "LAST_30_DAYS"
    ) -> List[Dict[str, Any]]:
        """
        Get ad performance metrics.

        Args:
            customer_id: Customer ID
            ad_group_id: Optional ad group ID to filter
            date_range: Date range for metrics

        Returns:
            List of ads with performance data
        """
        query = f"""
            SELECT
                ad_group_ad.ad.id,
                ad_group_ad.ad.type,
                ad_group_ad.status,
                ad_group.id,
                ad_group.name,
                campaign.id,
                campaign.name,
                metrics.impressions,
                metrics.clicks,
                metrics.ctr,
                metrics.average_cpc,
                metrics.cost_micros,
                metrics.conversions,
                metrics.conversions_value
            FROM ad_group_ad
            WHERE segments.date DURING {date_range}
        """

        if ad_group_id:
            query += f" AND ad_group.id = {ad_group_id}"

        query += " ORDER BY metrics.cost_micros DESC"

        ga_service = self.client.get_service("GoogleAdsService")
        response = ga_service.search(customer_id=customer_id, query=query)

        ads = []
        for row in response:
            ads.append({
                "ad_id": str(row.ad_group_ad.ad.id),
                "ad_type": row.ad_group_ad.ad.type_.name,
                "status": row.ad_group_ad.status.name,
                "ad_group": {
                    "id": str(row.ad_group.id),
                    "name": row.ad_group.name
                },
                "campaign": {
                    "id": str(row.campaign.id),
                    "name": row.campaign.name
                },
                "metrics": {
                    "impressions": row.metrics.impressions,
                    "clicks": row.metrics.clicks,
                    "ctr": row.metrics.ctr,
                    "average_cpc": row.metrics.average_cpc / 1_000_000 if row.metrics.average_cpc else 0,
                    "cost": row.metrics.cost_micros / 1_000_000,
                    "conversions": row.metrics.conversions,
                    "conversions_value": row.metrics.conversions_value
                }
            })

        return ads

    def get_ad_details(
        self,
        customer_id: str,
        ad_group_id: str,
        ad_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about an ad.

        Args:
            customer_id: Customer ID
            ad_group_id: Ad group ID
            ad_id: Ad ID

        Returns:
            Ad details or None
        """
        query = f"""
            SELECT
                ad_group_ad.ad.id,
                ad_group_ad.ad.type,
                ad_group_ad.status,
                ad_group_ad.ad.responsive_search_ad.headlines,
                ad_group_ad.ad.responsive_search_ad.descriptions,
                ad_group_ad.ad.responsive_search_ad.path1,
                ad_group_ad.ad.responsive_search_ad.path2,
                ad_group_ad.ad.final_urls,
                ad_group_ad.policy_summary.approval_status,
                ad_group_ad.policy_summary.review_status,
                ad_group_ad.ad_strength,
                metrics.impressions,
                metrics.clicks,
                metrics.cost_micros,
                metrics.conversions
            FROM ad_group_ad
            WHERE ad_group.id = {ad_group_id}
            AND ad_group_ad.ad.id = {ad_id}
        """

        ga_service = self.client.get_service("GoogleAdsService")
        response = ga_service.search(customer_id=customer_id, query=query)

        for row in response:
            details = {
                "ad_id": str(row.ad_group_ad.ad.id),
                "ad_type": row.ad_group_ad.ad.type_.name,
                "status": row.ad_group_ad.status.name,
                "approval_status": row.ad_group_ad.policy_summary.approval_status.name if hasattr(row.ad_group_ad, 'policy_summary') else "UNKNOWN",
                "review_status": row.ad_group_ad.policy_summary.review_status.name if hasattr(row.ad_group_ad, 'policy_summary') else "UNKNOWN",
                "ad_strength": row.ad_group_ad.ad_strength.name if hasattr(row.ad_group_ad, 'ad_strength') else "UNKNOWN",
                "final_urls": list(row.ad_group_ad.ad.final_urls) if row.ad_group_ad.ad.final_urls else []
            }

            # RSA-specific details
            if row.ad_group_ad.ad.type_.name == "RESPONSIVE_SEARCH_AD":
                rsa = row.ad_group_ad.ad.responsive_search_ad
                details["headlines"] = [h.text for h in rsa.headlines]
                details["descriptions"] = [d.text for d in rsa.descriptions]
                details["path1"] = rsa.path1 if rsa.path1 else None
                details["path2"] = rsa.path2 if rsa.path2 else None

            # Metrics
            details["metrics"] = {
                "impressions": row.metrics.impressions,
                "clicks": row.metrics.clicks,
                "cost": row.metrics.cost_micros / 1_000_000,
                "conversions": row.metrics.conversions
            }

            return details

        return None

    # ========================================================================
    # Ad Strength and Policy
    # ========================================================================

    def check_ad_approval_status(
        self,
        customer_id: str,
        ad_group_id: str,
        ad_id: str
    ) -> Dict[str, Any]:
        """
        Check ad approval and policy status.

        Args:
            customer_id: Customer ID
            ad_group_id: Ad group ID
            ad_id: Ad ID

        Returns:
            Approval status details
        """
        query = f"""
            SELECT
                ad_group_ad.ad.id,
                ad_group_ad.policy_summary.approval_status,
                ad_group_ad.policy_summary.review_status,
                ad_group_ad.policy_summary.policy_topic_entries
            FROM ad_group_ad
            WHERE ad_group.id = {ad_group_id}
            AND ad_group_ad.ad.id = {ad_id}
        """

        ga_service = self.client.get_service("GoogleAdsService")
        response = ga_service.search(customer_id=customer_id, query=query)

        for row in response:
            policy_summary = row.ad_group_ad.policy_summary if hasattr(row.ad_group_ad, 'policy_summary') else None

            policy_topics = []
            if policy_summary and hasattr(policy_summary, 'policy_topic_entries'):
                for entry in policy_summary.policy_topic_entries:
                    policy_topics.append({
                        "topic": entry.topic if hasattr(entry, 'topic') else "Unknown",
                        "type": entry.type_.name if hasattr(entry, 'type_') else "UNKNOWN"
                    })

            return {
                "ad_id": str(row.ad_group_ad.ad.id),
                "approval_status": policy_summary.approval_status.name if policy_summary else "UNKNOWN",
                "review_status": policy_summary.review_status.name if policy_summary else "UNKNOWN",
                "policy_topics": policy_topics
            }

        return None

    # ========================================================================
    # Bulk Operations
    # ========================================================================

    def bulk_update_ad_status(
        self,
        customer_id: str,
        status_updates: List[Dict[str, Any]],
        status: AdStatus
    ) -> Dict[str, Any]:
        """
        Update status for multiple ads at once.

        Args:
            customer_id: Customer ID
            status_updates: List of dicts with 'ad_group_id' and 'ad_id'
            status: New status for all ads

        Returns:
            Bulk operation result
        """
        ad_group_ad_service = self.client.get_service("AdGroupAdService")

        operations = []

        for update in status_updates:
            ad_group_ad_operation = self.client.get_type("AdGroupAdOperation")
            ad_group_ad = ad_group_ad_operation.update

            ad_group_ad.resource_name = ad_group_ad_service.ad_group_ad_path(
                customer_id,
                update['ad_group_id'],
                update['ad_id']
            )
            ad_group_ad.status = self.client.enums.AdGroupAdStatusEnum[status.value]

            self.client.copy_from(
                ad_group_ad_operation.update_mask,
                self.client.get_type("FieldMask", version="v17")(paths=["status"])
            )

            operations.append(ad_group_ad_operation)

        # Execute bulk update
        response = ad_group_ad_service.mutate_ad_group_ads(
            customer_id=customer_id,
            operations=operations
        )

        logger.info(f"Bulk updated {len(operations)} ads to {status.value}")

        return {
            "ads_updated": len(operations),
            "new_status": status.value,
            "message": f"Successfully updated {len(operations)} ads"
        }


def create_ad_manager(client: GoogleAdsClient) -> AdManager:
    """
    Create an ad manager instance.

    Args:
        client: Google Ads client

    Returns:
        AdManager instance
    """
    return AdManager(client)
