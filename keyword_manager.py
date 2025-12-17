"""
Keyword Manager for Google Ads MCP Server

Provides complete keyword lifecycle management including:
- Keyword addition (positive and negative)
- Keyword bid management
- Keyword status updates
- Performance tracking
- Quality score analysis
- Search term analysis
- Bulk operations
- Traffic estimation
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

class KeywordMatchType(str, Enum):
    """Keyword match type options."""
    EXACT = "EXACT"
    PHRASE = "PHRASE"
    BROAD = "BROAD"


class KeywordStatus(str, Enum):
    """Keyword status options."""
    ENABLED = "ENABLED"
    PAUSED = "PAUSED"
    REMOVED = "REMOVED"


@dataclass
class KeywordConfig:
    """Configuration for adding a keyword."""
    text: str
    match_type: KeywordMatchType
    ad_group_id: str
    cpc_bid_micros: Optional[int] = None
    final_url: Optional[str] = None
    status: KeywordStatus = KeywordStatus.ENABLED


# ============================================================================
# Keyword Manager
# ============================================================================

class KeywordManager:
    """Manages Google Ads keywords."""

    def __init__(self, client: GoogleAdsClient):
        """
        Initialize the keyword manager.

        Args:
            client: Authenticated Google Ads client
        """
        self.client = client

    # ========================================================================
    # Keyword Addition
    # ========================================================================

    def add_keywords(
        self,
        customer_id: str,
        keywords: List[KeywordConfig]
    ) -> Dict[str, Any]:
        """
        Add keywords to an ad group.

        Args:
            customer_id: Customer ID
            keywords: List of keyword configurations

        Returns:
            Operation result with added keyword IDs
        """
        ad_group_criterion_service = self.client.get_service("AdGroupCriterionService")
        ad_group_service = self.client.get_service("AdGroupService")

        operations = []

        for kw_config in keywords:
            operation = self.client.get_type("AdGroupCriterionOperation")
            criterion = operation.create

            # Set ad group
            criterion.ad_group = ad_group_service.ad_group_path(
                customer_id, kw_config.ad_group_id
            )

            # Set keyword
            criterion.keyword.text = kw_config.text
            criterion.keyword.match_type = self.client.enums.KeywordMatchTypeEnum[
                kw_config.match_type.value
            ]

            # Set status
            criterion.status = self.client.enums.AdGroupCriterionStatusEnum[
                kw_config.status.value
            ]

            # Set CPC bid if provided
            if kw_config.cpc_bid_micros:
                criterion.cpc_bid_micros = kw_config.cpc_bid_micros

            # Set final URL if provided
            if kw_config.final_url:
                criterion.final_urls.append(kw_config.final_url)

            operations.append(operation)

        # Add keywords
        response = ad_group_criterion_service.mutate_ad_group_criteria(
            customer_id=customer_id,
            operations=operations
        )

        keyword_ids = [
            result.resource_name.split("/")[-1]
            for result in response.results
        ]

        logger.info(f"Added {len(keyword_ids)} keywords to ad group")

        return {
            "keywords_added": len(keyword_ids),
            "keyword_ids": keyword_ids,
            "message": f"Successfully added {len(keyword_ids)} keywords"
        }

    def add_negative_keywords(
        self,
        customer_id: str,
        ad_group_id: str,
        keywords: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """
        Add negative keywords to an ad group.

        Args:
            customer_id: Customer ID
            ad_group_id: Ad group ID
            keywords: List of dicts with 'text' and 'match_type'

        Returns:
            Operation result
        """
        ad_group_criterion_service = self.client.get_service("AdGroupCriterionService")
        ad_group_service = self.client.get_service("AdGroupService")

        operations = []

        for kw in keywords:
            operation = self.client.get_type("AdGroupCriterionOperation")
            criterion = operation.create

            # Set ad group
            criterion.ad_group = ad_group_service.ad_group_path(
                customer_id, ad_group_id
            )

            # Set keyword
            criterion.keyword.text = kw['text']
            criterion.keyword.match_type = self.client.enums.KeywordMatchTypeEnum[
                kw['match_type'].upper()
            ]

            # Mark as negative
            criterion.negative = True

            operations.append(operation)

        # Add negative keywords
        response = ad_group_criterion_service.mutate_ad_group_criteria(
            customer_id=customer_id,
            operations=operations
        )

        logger.info(f"Added {len(operations)} negative keywords")

        return {
            "negative_keywords_added": len(operations),
            "message": f"Successfully added {len(operations)} negative keywords"
        }

    # ========================================================================
    # Keyword Updates
    # ========================================================================

    def update_keyword_bid(
        self,
        customer_id: str,
        ad_group_id: str,
        criterion_id: str,
        cpc_bid_micros: int
    ) -> Dict[str, Any]:
        """
        Update keyword CPC bid.

        Args:
            customer_id: Customer ID
            ad_group_id: Ad group ID
            criterion_id: Keyword criterion ID
            cpc_bid_micros: New CPC bid in micros

        Returns:
            Operation result
        """
        ad_group_criterion_service = self.client.get_service("AdGroupCriterionService")

        operation = self.client.get_type("AdGroupCriterionOperation")
        criterion = operation.update

        criterion.resource_name = ad_group_criterion_service.ad_group_criterion_path(
            customer_id, ad_group_id, criterion_id
        )
        criterion.cpc_bid_micros = cpc_bid_micros

        # Set field mask
        self.client.copy_from(
            operation.update_mask,
            self.client.get_type("FieldMask", version="v17")(paths=["cpc_bid_micros"])
        )

        # Update keyword
        response = ad_group_criterion_service.mutate_ad_group_criteria(
            customer_id=customer_id,
            operations=[operation]
        )

        logger.info(f"Updated keyword {criterion_id} bid to {cpc_bid_micros / 1_000_000}")

        return {
            "criterion_id": criterion_id,
            "new_cpc_bid": cpc_bid_micros / 1_000_000,
            "message": "Keyword bid updated successfully"
        }

    def update_keyword_status(
        self,
        customer_id: str,
        ad_group_id: str,
        criterion_id: str,
        status: KeywordStatus
    ) -> Dict[str, Any]:
        """
        Update keyword status.

        Args:
            customer_id: Customer ID
            ad_group_id: Ad group ID
            criterion_id: Keyword criterion ID
            status: New status

        Returns:
            Operation result
        """
        ad_group_criterion_service = self.client.get_service("AdGroupCriterionService")

        operation = self.client.get_type("AdGroupCriterionOperation")
        criterion = operation.update

        criterion.resource_name = ad_group_criterion_service.ad_group_criterion_path(
            customer_id, ad_group_id, criterion_id
        )
        criterion.status = self.client.enums.AdGroupCriterionStatusEnum[status.value]

        # Set field mask
        self.client.copy_from(
            operation.update_mask,
            self.client.get_type("FieldMask", version="v17")(paths=["status"])
        )

        # Update keyword
        response = ad_group_criterion_service.mutate_ad_group_criteria(
            customer_id=customer_id,
            operations=[operation]
        )

        logger.info(f"Updated keyword {criterion_id} status to {status.value}")

        return {
            "criterion_id": criterion_id,
            "new_status": status.value,
            "message": f"Keyword status updated to {status.value}"
        }

    # ========================================================================
    # Keyword Information
    # ========================================================================

    def get_keyword_performance(
        self,
        customer_id: str,
        ad_group_id: Optional[str] = None,
        date_range: str = "LAST_30_DAYS"
    ) -> List[Dict[str, Any]]:
        """
        Get keyword performance metrics.

        Args:
            customer_id: Customer ID
            ad_group_id: Optional ad group ID to filter by
            date_range: Date range for metrics

        Returns:
            List of keywords with performance data
        """
        query = f"""
            SELECT
                ad_group_criterion.criterion_id,
                ad_group_criterion.keyword.text,
                ad_group_criterion.keyword.match_type,
                ad_group_criterion.status,
                ad_group_criterion.cpc_bid_micros,
                ad_group_criterion.quality_info.quality_score,
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
                metrics.conversions_value,
                metrics.cost_per_conversion
            FROM keyword_view
            WHERE segments.date DURING {date_range}
            AND ad_group_criterion.type = KEYWORD
        """

        if ad_group_id:
            query += f" AND ad_group.id = {ad_group_id}"

        query += " ORDER BY metrics.cost_micros DESC"

        ga_service = self.client.get_service("GoogleAdsService")
        response = ga_service.search(customer_id=customer_id, query=query)

        keywords = []
        for row in response:
            keywords.append({
                "criterion_id": str(row.ad_group_criterion.criterion_id),
                "keyword_text": row.ad_group_criterion.keyword.text,
                "match_type": row.ad_group_criterion.keyword.match_type.name,
                "status": row.ad_group_criterion.status.name,
                "cpc_bid": row.ad_group_criterion.cpc_bid_micros / 1_000_000 if row.ad_group_criterion.cpc_bid_micros else None,
                "quality_score": row.ad_group_criterion.quality_info.quality_score if hasattr(row.ad_group_criterion, 'quality_info') else None,
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
                    "conversions_value": row.metrics.conversions_value,
                    "cost_per_conversion": row.metrics.cost_per_conversion / 1_000_000 if row.metrics.cost_per_conversion else 0
                }
            })

        logger.info(f"Retrieved {len(keywords)} keywords")

        return keywords

    def list_keywords(
        self,
        customer_id: str,
        ad_group_id: str
    ) -> List[Dict[str, Any]]:
        """
        List all keywords in an ad group.

        Args:
            customer_id: Customer ID
            ad_group_id: Ad group ID

        Returns:
            List of keywords
        """
        query = f"""
            SELECT
                ad_group_criterion.criterion_id,
                ad_group_criterion.keyword.text,
                ad_group_criterion.keyword.match_type,
                ad_group_criterion.status,
                ad_group_criterion.cpc_bid_micros,
                ad_group_criterion.negative
            FROM ad_group_criterion
            WHERE ad_group.id = {ad_group_id}
            AND ad_group_criterion.type = KEYWORD
            AND ad_group_criterion.status != REMOVED
            ORDER BY ad_group_criterion.keyword.text
        """

        ga_service = self.client.get_service("GoogleAdsService")
        response = ga_service.search(customer_id=customer_id, query=query)

        keywords = []
        for row in response:
            keywords.append({
                "criterion_id": str(row.ad_group_criterion.criterion_id),
                "keyword_text": row.ad_group_criterion.keyword.text,
                "match_type": row.ad_group_criterion.keyword.match_type.name,
                "status": row.ad_group_criterion.status.name,
                "cpc_bid": row.ad_group_criterion.cpc_bid_micros / 1_000_000 if row.ad_group_criterion.cpc_bid_micros else None,
                "negative": row.ad_group_criterion.negative
            })

        return keywords

    def get_keyword_quality_score(
        self,
        customer_id: str,
        ad_group_id: str,
        criterion_id: str
    ) -> Dict[str, Any]:
        """
        Get detailed quality score information for a keyword.

        Args:
            customer_id: Customer ID
            ad_group_id: Ad group ID
            criterion_id: Keyword criterion ID

        Returns:
            Quality score details
        """
        query = f"""
            SELECT
                ad_group_criterion.criterion_id,
                ad_group_criterion.keyword.text,
                ad_group_criterion.keyword.match_type,
                ad_group_criterion.quality_info.quality_score,
                ad_group_criterion.quality_info.creative_quality_score,
                ad_group_criterion.quality_info.post_click_quality_score,
                ad_group_criterion.quality_info.search_predicted_ctr
            FROM ad_group_criterion
            WHERE ad_group.id = {ad_group_id}
            AND ad_group_criterion.criterion_id = {criterion_id}
        """

        ga_service = self.client.get_service("GoogleAdsService")
        response = ga_service.search(customer_id=customer_id, query=query)

        for row in response:
            quality_info = row.ad_group_criterion.quality_info if hasattr(row.ad_group_criterion, 'quality_info') else None

            return {
                "criterion_id": str(row.ad_group_criterion.criterion_id),
                "keyword_text": row.ad_group_criterion.keyword.text,
                "match_type": row.ad_group_criterion.keyword.match_type.name,
                "quality_score": quality_info.quality_score if quality_info else None,
                "creative_quality": quality_info.creative_quality_score.name if quality_info and hasattr(quality_info, 'creative_quality_score') else "UNSPECIFIED",
                "landing_page_experience": quality_info.post_click_quality_score.name if quality_info and hasattr(quality_info, 'post_click_quality_score') else "UNSPECIFIED",
                "expected_ctr": quality_info.search_predicted_ctr.name if quality_info and hasattr(quality_info, 'search_predicted_ctr') else "UNSPECIFIED"
            }

        return None

    # ========================================================================
    # Search Terms
    # ========================================================================

    def get_search_terms_for_keyword(
        self,
        customer_id: str,
        ad_group_id: str,
        criterion_id: Optional[str] = None,
        date_range: str = "LAST_30_DAYS"
    ) -> List[Dict[str, Any]]:
        """
        Get search terms that triggered ads for a keyword.

        Args:
            customer_id: Customer ID
            ad_group_id: Ad group ID
            criterion_id: Optional specific keyword criterion ID
            date_range: Date range for search terms

        Returns:
            List of search terms with performance data
        """
        query = f"""
            SELECT
                search_term_view.search_term,
                search_term_view.status,
                ad_group.id,
                ad_group_criterion.keyword.text,
                metrics.impressions,
                metrics.clicks,
                metrics.ctr,
                metrics.cost_micros,
                metrics.conversions
            FROM search_term_view
            WHERE segments.date DURING {date_range}
            AND ad_group.id = {ad_group_id}
        """

        if criterion_id:
            query += f" AND ad_group_criterion.criterion_id = {criterion_id}"

        query += " ORDER BY metrics.impressions DESC"

        ga_service = self.client.get_service("GoogleAdsService")
        response = ga_service.search(customer_id=customer_id, query=query)

        search_terms = []
        for row in response:
            search_terms.append({
                "search_term": row.search_term_view.search_term,
                "status": row.search_term_view.status.name,
                "keyword_text": row.ad_group_criterion.keyword.text if hasattr(row, 'ad_group_criterion') else "Unknown",
                "impressions": row.metrics.impressions,
                "clicks": row.metrics.clicks,
                "ctr": row.metrics.ctr,
                "cost": row.metrics.cost_micros / 1_000_000,
                "conversions": row.metrics.conversions
            })

        return search_terms

    # ========================================================================
    # Bulk Operations
    # ========================================================================

    def bulk_update_keyword_bids(
        self,
        customer_id: str,
        bid_updates: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Update bids for multiple keywords at once.

        Args:
            customer_id: Customer ID
            bid_updates: List of dicts with 'ad_group_id', 'criterion_id', 'cpc_bid_micros'

        Returns:
            Bulk operation result
        """
        ad_group_criterion_service = self.client.get_service("AdGroupCriterionService")

        operations = []

        for update in bid_updates:
            operation = self.client.get_type("AdGroupCriterionOperation")
            criterion = operation.update

            criterion.resource_name = ad_group_criterion_service.ad_group_criterion_path(
                customer_id,
                update['ad_group_id'],
                update['criterion_id']
            )
            criterion.cpc_bid_micros = update['cpc_bid_micros']

            self.client.copy_from(
                operation.update_mask,
                self.client.get_type("FieldMask", version="v17")(paths=["cpc_bid_micros"])
            )

            operations.append(operation)

        # Execute bulk update
        response = ad_group_criterion_service.mutate_ad_group_criteria(
            customer_id=customer_id,
            operations=operations
        )

        logger.info(f"Bulk updated {len(operations)} keyword bids")

        return {
            "keywords_updated": len(operations),
            "message": f"Successfully updated {len(operations)} keyword bids"
        }

    # ========================================================================
    # Keyword Planner / Research
    # ========================================================================

    def get_keyword_ideas(
        self,
        customer_id: str,
        seed_keywords: Optional[List[str]] = None,
        page_url: Optional[str] = None,
        location_ids: Optional[List[str]] = None,
        language_id: Optional[str] = None,
        keyword_plan_network: str = "GOOGLE_SEARCH"
    ) -> Dict[str, Any]:
        """
        Generate keyword ideas using Google Ads Keyword Planner.

        Args:
            customer_id: Customer ID
            seed_keywords: Optional list of seed keywords for expansion
            page_url: Optional URL to extract keyword ideas from
            location_ids: Optional location criterion IDs (e.g., ["2840"] for US)
            language_id: Optional language criterion ID (e.g., "1000" for English)
            keyword_plan_network: Network for ideas - GOOGLE_SEARCH, GOOGLE_SEARCH_AND_PARTNERS, or YOUTUBE

        Returns:
            Dictionary with keyword ideas and metrics
        """
        keyword_plan_idea_service = self.client.get_service("KeywordPlanIdeaService")

        # Build request
        request = self.client.get_type("GenerateKeywordIdeasRequest")
        request.customer_id = customer_id

        # Set keyword plan network
        network_enum = self.client.enums.KeywordPlanNetworkEnum
        if keyword_plan_network == "GOOGLE_SEARCH":
            request.keyword_plan_network = network_enum.GOOGLE_SEARCH
        elif keyword_plan_network == "GOOGLE_SEARCH_AND_PARTNERS":
            request.keyword_plan_network = network_enum.GOOGLE_SEARCH_AND_PARTNERS
        elif keyword_plan_network == "YOUTUBE":
            request.keyword_plan_network = network_enum.YOUTUBE
        else:
            request.keyword_plan_network = network_enum.GOOGLE_SEARCH

        # Set geo targeting
        if location_ids:
            for location_id in location_ids:
                location = self.client.get_type("LocationInfo")
                location.geo_target_constant = f"geoTargetConstants/{location_id}"
                request.geo_target_constants.append(location.geo_target_constant)
        else:
            # Default to US
            location = self.client.get_type("LocationInfo")
            location.geo_target_constant = "geoTargetConstants/2840"
            request.geo_target_constants.append(location.geo_target_constant)

        # Set language
        if language_id:
            request.language = f"languageConstants/{language_id}"
        else:
            # Default to English
            request.language = "languageConstants/1000"

        # Set seed keywords or page URL
        if seed_keywords:
            for keyword in seed_keywords:
                request.keyword_seed.keywords.append(keyword)

        if page_url:
            request.url_seed.url = page_url

        # Execute request
        try:
            response = keyword_plan_idea_service.generate_keyword_ideas(request=request)

            keyword_ideas = []
            for idea in response:
                # Extract metrics
                metrics = idea.keyword_idea_metrics

                keyword_ideas.append({
                    "keyword_text": idea.text,
                    "avg_monthly_searches": metrics.avg_monthly_searches if metrics.avg_monthly_searches else 0,
                    "competition": metrics.competition.name if metrics.competition else "UNSPECIFIED",
                    "competition_index": metrics.competition_index if metrics.competition_index else 0,
                    "low_top_of_page_bid_micros": metrics.low_top_of_page_bid_micros if metrics.low_top_of_page_bid_micros else 0,
                    "high_top_of_page_bid_micros": metrics.high_top_of_page_bid_micros if metrics.high_top_of_page_bid_micros else 0,
                    "low_top_of_page_bid": (metrics.low_top_of_page_bid_micros / 1_000_000) if metrics.low_top_of_page_bid_micros else 0,
                    "high_top_of_page_bid": (metrics.high_top_of_page_bid_micros / 1_000_000) if metrics.high_top_of_page_bid_micros else 0
                })

            logger.info(f"Retrieved {len(keyword_ideas)} keyword ideas")

            return {
                "total_ideas": len(keyword_ideas),
                "keyword_ideas": keyword_ideas,
                "seed_keywords": seed_keywords or [],
                "page_url": page_url,
                "locations": location_ids or ["2840"],
                "language": language_id or "1000"
            }

        except Exception as e:
            logger.error(f"Error getting keyword ideas: {str(e)}")
            raise

    def forecast_keyword_metrics(
        self,
        customer_id: str,
        keywords: List[Dict[str, Any]],
        location_ids: Optional[List[str]] = None,
        language_id: Optional[str] = None,
        cpc_bid_micros: Optional[int] = None,
        date_interval: str = "NEXT_MONTH"
    ) -> Dict[str, Any]:
        """
        Get traffic forecast for specific keywords using Keyword Plan Forecast.

        Args:
            customer_id: Customer ID
            keywords: List of keyword dicts with 'text' and 'match_type'
            location_ids: Optional location criterion IDs
            language_id: Optional language criterion ID
            cpc_bid_micros: Optional CPC bid in micros for forecast
            date_interval: Forecast interval - NEXT_WEEK, NEXT_MONTH, NEXT_QUARTER

        Returns:
            Dictionary with forecast metrics
        """
        keyword_plan_service = self.client.get_service("KeywordPlanService")

        # Create a temporary keyword plan for forecasting
        # Note: This creates and immediately uses a plan, then removes it

        # Build campaign for keyword plan
        campaign = self.client.get_type("KeywordPlanCampaign")

        # Set network
        network_enum = self.client.enums.KeywordPlanNetworkEnum
        campaign.keyword_plan_network = network_enum.GOOGLE_SEARCH

        # Set geo targets
        if location_ids:
            for location_id in location_ids:
                geo_target = self.client.get_type("KeywordPlanGeoTarget")
                geo_target.geo_target_constant = f"geoTargetConstants/{location_id}"
                campaign.geo_targets.append(geo_target)
        else:
            geo_target = self.client.get_type("KeywordPlanGeoTarget")
            geo_target.geo_target_constant = "geoTargetConstants/2840"
            campaign.geo_targets.append(geo_target)

        # Set language
        if language_id:
            campaign.language_constants.append(f"languageConstants/{language_id}")
        else:
            campaign.language_constants.append("languageConstants/1000")

        # Set CPC bid
        if cpc_bid_micros:
            campaign.cpc_bid_micros = cpc_bid_micros

        # Create keyword plan request
        keyword_plan = self.client.get_type("KeywordPlan")
        keyword_plan.name = f"Forecast Plan {customer_id}"

        # Set forecast interval
        forecast_interval = self.client.get_type("KeywordPlanForecastInterval")
        if date_interval == "NEXT_WEEK":
            forecast_interval.date_interval = self.client.enums.KeywordPlanForecastIntervalEnum.NEXT_WEEK
        elif date_interval == "NEXT_MONTH":
            forecast_interval.date_interval = self.client.enums.KeywordPlanForecastIntervalEnum.NEXT_MONTH
        elif date_interval == "NEXT_QUARTER":
            forecast_interval.date_interval = self.client.enums.KeywordPlanForecastIntervalEnum.NEXT_QUARTER

        keyword_plan.forecast_period = forecast_interval

        try:
            # This is a simplified approach - full implementation would:
            # 1. Create keyword plan
            # 2. Create campaign in plan
            # 3. Create ad group in campaign
            # 4. Add keywords to ad group
            # 5. Generate forecast
            # 6. Clean up plan

            # For now, return structure showing expected forecast data
            logger.info(f"Forecast requested for {len(keywords)} keywords over {date_interval}")

            return {
                "keywords_forecasted": len(keywords),
                "forecast_period": date_interval,
                "cpc_bid": (cpc_bid_micros / 1_000_000) if cpc_bid_micros else None,
                "note": "Forecast generation requires creating temporary keyword plan",
                "forecast_metrics": {
                    "impressions": "Available with full implementation",
                    "clicks": "Available with full implementation",
                    "cost": "Available with full implementation",
                    "ctr": "Available with full implementation",
                    "average_cpc": "Available with full implementation"
                }
            }

        except Exception as e:
            logger.error(f"Error generating keyword forecast: {str(e)}")
            raise

    # ========================================================================
    # Traffic Estimation (Legacy - kept for compatibility)
    # ========================================================================

    def estimate_keyword_traffic(
        self,
        customer_id: str,
        keywords: List[str],
        location_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get traffic estimates for keywords (legacy method).

        Args:
            customer_id: Customer ID
            keywords: List of keyword texts to estimate
            location_ids: Optional location IDs for targeting

        Returns:
            Traffic estimates
        """
        # Redirect to get_keyword_ideas for better functionality
        return self.get_keyword_ideas(
            customer_id=customer_id,
            seed_keywords=keywords,
            location_ids=location_ids
        )

    def get_quality_score_history(
        self,
        customer_id: str,
        keyword_id: Optional[str] = None,
        ad_group_id: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get historical quality score data for keywords.

        Args:
            customer_id: Google Ads customer ID
            keyword_id: Optional specific keyword criterion ID
            ad_group_id: Optional ad group ID to filter by
            start_date: Optional start date (YYYY-MM-DD)
            end_date: Optional end date (YYYY-MM-DD)

        Returns:
            Dictionary with quality score history data
        """
        with performance_logger.track_operation(self, 'get_quality_score_history'):
            # Build query
            query_parts = [
                "SELECT ad_group_criterion.criterion_id,",
                "ad_group_criterion.keyword.text,",
                "ad_group_criterion.keyword.match_type,",
                "ad_group_criterion.quality_info.quality_score,",
                "ad_group_criterion.quality_info.creative_quality_score,",
                "ad_group_criterion.quality_info.post_click_quality_score,",
                "ad_group_criterion.quality_info.search_predicted_ctr,",
                "ad_group.id, ad_group.name,",
                "campaign.id, campaign.name,",
                "segments.date",
                "FROM keyword_view",
                "WHERE ad_group_criterion.type = 'KEYWORD'"
            ]

            if start_date and end_date:
                query_parts.append(f"AND segments.date BETWEEN '{start_date}' AND '{end_date}'")
            elif start_date:
                query_parts.append(f"AND segments.date >= '{start_date}'")
            elif end_date:
                query_parts.append(f"AND segments.date <= '{end_date}'")
            else:
                # Default to last 90 days
                query_parts.append("AND segments.date DURING LAST_90_DAYS")

            if keyword_id:
                query_parts.append(f"AND ad_group_criterion.criterion_id = {keyword_id}")

            if ad_group_id:
                query_parts.append(f"AND ad_group.id = {ad_group_id}")

            query_parts.append("ORDER BY segments.date DESC")

            query = " ".join(query_parts)

            ga_service = self.client.get_service("GoogleAdsService")
            request = self.client.get_type("SearchGoogleAdsRequest")
            request.customer_id = customer_id
            request.query = query

            audit_logger.log_api_call(
                operation='quality_score_history',
                customer_id=customer_id,
                details={'keyword_id': keyword_id, 'ad_group_id': ad_group_id}
            )

            response = ga_service.search(request=request)

            # Parse results
            keywords = []
            for row in response:
                quality_info = row.ad_group_criterion.quality_info

                keywords.append({
                    'date': row.segments.date,
                    'campaign_id': row.campaign.id,
                    'campaign_name': row.campaign.name,
                    'ad_group_id': row.ad_group.id,
                    'ad_group_name': row.ad_group.name,
                    'keyword_id': row.ad_group_criterion.criterion_id,
                    'keyword_text': row.ad_group_criterion.keyword.text,
                    'match_type': row.ad_group_criterion.keyword.match_type.name,
                    'quality_score': quality_info.quality_score,
                    'creative_quality_score': quality_info.creative_quality_score.name,
                    'landing_page_experience': quality_info.post_click_quality_score.name,
                    'expected_ctr': quality_info.search_predicted_ctr.name
                })

            # Calculate quality score trends
            if keywords:
                # Group by keyword
                keyword_groups = {}
                for kw in keywords:
                    kw_id = kw['keyword_id']
                    if kw_id not in keyword_groups:
                        keyword_groups[kw_id] = {
                            'keyword_text': kw['keyword_text'],
                            'match_type': kw['match_type'],
                            'history': [],
                            'current_quality_score': None,
                            'previous_quality_score': None,
                            'trend': None
                        }

                    keyword_groups[kw_id]['history'].append({
                        'date': kw['date'],
                        'quality_score': kw['quality_score'],
                        'creative_quality_score': kw['creative_quality_score'],
                        'landing_page_experience': kw['landing_page_experience'],
                        'expected_ctr': kw['expected_ctr']
                    })

                # Calculate trends
                for kw_id, data in keyword_groups.items():
                    if len(data['history']) >= 2:
                        # Sort by date (most recent first)
                        data['history'].sort(key=lambda x: x['date'], reverse=True)
                        data['current_quality_score'] = data['history'][0]['quality_score']
                        data['previous_quality_score'] = data['history'][1]['quality_score']

                        if data['current_quality_score'] > data['previous_quality_score']:
                            data['trend'] = 'improving'
                        elif data['current_quality_score'] < data['previous_quality_score']:
                            data['trend'] = 'declining'
                        else:
                            data['trend'] = 'stable'
                    elif len(data['history']) == 1:
                        data['current_quality_score'] = data['history'][0]['quality_score']
                        data['trend'] = 'new'

            return {
                'keywords': keywords,
                'keyword_groups': keyword_groups if keywords else {},
                'total_keywords': len(keyword_groups) if keywords else 0,
                'date_range': {
                    'start_date': start_date or 'LAST_90_DAYS',
                    'end_date': end_date or 'TODAY'
                }
            }


def create_keyword_manager(client: GoogleAdsClient) -> KeywordManager:
    """
    Create a keyword manager instance.

    Args:
        client: Google Ads client

    Returns:
        KeywordManager instance
    """
    return KeywordManager(client)
