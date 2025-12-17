"""
Automation Manager

Handles automated rules and optimization recommendations.

Automated Rules:
- Budget rules (pause when budget spent)
- Performance rules (pause low performers, increase bids for high performers)
- Schedule rules (enable/pause on specific days/times)
- Bid rules (adjust bids based on performance thresholds)

Optimization Recommendations:
- Apply Google's AI-powered optimization suggestions
- Dismiss recommendations
- Get optimization score
- Track recommendation performance
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
from google.ads.googleads.client import GoogleAdsClient


class RecommendationType(str, Enum):
    """Google Ads recommendation types."""
    KEYWORD = "KEYWORD"
    CAMPAIGN_BUDGET = "CAMPAIGN_BUDGET"
    TEXT_AD = "TEXT_AD"
    TARGET_CPA_OPT_IN = "TARGET_CPA_OPT_IN"
    MAXIMIZE_CONVERSIONS_OPT_IN = "MAXIMIZE_CONVERSIONS_OPT_IN"
    ENHANCED_CPC_OPT_IN = "ENHANCED_CPC_OPT_IN"
    SEARCH_PARTNERS_OPT_IN = "SEARCH_PARTNERS_OPT_IN"
    MAXIMIZE_CLICKS_OPT_IN = "MAXIMIZE_CLICKS_OPT_IN"
    OPTIMIZE_AD_ROTATION = "OPTIMIZE_AD_ROTATION"
    KEYWORD_MATCH_TYPE = "KEYWORD_MATCH_TYPE"
    MOVE_UNUSED_BUDGET = "MOVE_UNUSED_BUDGET"
    FORECASTING_CAMPAIGN_BUDGET = "FORECASTING_CAMPAIGN_BUDGET"
    TARGET_ROAS_OPT_IN = "TARGET_ROAS_OPT_IN"
    RESPONSIVE_SEARCH_AD = "RESPONSIVE_SEARCH_AD"
    MARGINAL_ROI_CAMPAIGN_BUDGET = "MARGINAL_ROI_CAMPAIGN_BUDGET"
    USE_BROAD_MATCH_KEYWORD = "USE_BROAD_MATCH_KEYWORD"
    RESPONSIVE_SEARCH_AD_ASSET = "RESPONSIVE_SEARCH_AD_ASSET"
    UPGRADE_SMART_SHOPPING_CAMPAIGN_TO_PERFORMANCE_MAX = "UPGRADE_SMART_SHOPPING_CAMPAIGN_TO_PERFORMANCE_MAX"
    RAISE_TARGET_CPA_BID_TOO_LOW = "RAISE_TARGET_CPA_BID_TOO_LOW"
    FORECASTING_SET_TARGET_ROAS = "FORECASTING_SET_TARGET_ROAS"
    SHOPPING_ADD_AGE_GROUP = "SHOPPING_ADD_AGE_GROUP"
    SHOPPING_ADD_COLOR = "SHOPPING_ADD_COLOR"
    SHOPPING_ADD_GENDER = "SHOPPING_ADD_GENDER"
    SHOPPING_ADD_SIZE = "SHOPPING_ADD_SIZE"


class AutomationManager:
    """Manager for automated rules and optimization recommendations."""

    def __init__(self, client: GoogleAdsClient):
        """Initialize the automation manager.

        Args:
            client: Authenticated GoogleAdsClient instance
        """
        self.client = client

    def get_recommendations(
        self,
        customer_id: str,
        recommendation_types: Optional[List[RecommendationType]] = None,
        campaign_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get optimization recommendations from Google Ads.

        Args:
            customer_id: Customer ID (without hyphens)
            recommendation_types: Optional filter by recommendation types
            campaign_id: Optional filter by campaign ID

        Returns:
            List of recommendations with details
        """
        ga_service = self.client.get_service("GoogleAdsService")

        query = """
            SELECT
                recommendation.resource_name,
                recommendation.type,
                recommendation.impact.base_metrics.impressions,
                recommendation.impact.base_metrics.clicks,
                recommendation.impact.base_metrics.cost_micros,
                recommendation.impact.base_metrics.conversions,
                recommendation.impact.base_metrics.video_views,
                recommendation.campaign,
                recommendation.keyword_recommendation.keyword.text,
                recommendation.keyword_recommendation.keyword.match_type,
                recommendation.keyword_recommendation.recommended_cpc_bid_micros,
                recommendation.campaign_budget_recommendation.current_budget_amount_micros,
                recommendation.campaign_budget_recommendation.recommended_budget_amount_micros,
                recommendation.text_ad_recommendation.ad.expanded_text_ad.headline_part1,
                recommendation.responsive_search_ad_recommendation.ad.responsive_search_ad.headlines,
                recommendation.target_cpa_opt_in_recommendation.recommended_target_cpa_micros,
                recommendation.target_roas_opt_in_recommendation.recommended_target_roas,
                recommendation.keyword_match_type_recommendation.keyword.text,
                recommendation.keyword_match_type_recommendation.recommended_match_type
            FROM recommendation
        """

        conditions = []

        if recommendation_types:
            types_str = ", ".join([f"'{t.value}'" for t in recommendation_types])
            conditions.append(f"recommendation.type IN ({types_str})")

        if campaign_id:
            campaign_service = self.client.get_service("CampaignService")
            campaign_resource = campaign_service.campaign_path(customer_id, campaign_id)
            conditions.append(f"recommendation.campaign = '{campaign_resource}'")

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        response = ga_service.search(customer_id=customer_id, query=query)

        recommendations = []
        for row in response:
            rec = row.recommendation
            rec_data = {
                'resource_name': rec.resource_name,
                'type': rec.type.name,
                'campaign': rec.campaign.split('/')[-1] if rec.campaign else None
            }

            # Parse impact metrics
            if rec.impact:
                rec_data['impact'] = {
                    'impressions': rec.impact.base_metrics.impressions,
                    'clicks': rec.impact.base_metrics.clicks,
                    'cost': rec.impact.base_metrics.cost_micros / 1_000_000,
                    'conversions': rec.impact.base_metrics.conversions,
                    'video_views': rec.impact.base_metrics.video_views
                }

            # Parse recommendation-specific details
            if rec.type.name == 'KEYWORD':
                rec_data['keyword'] = {
                    'text': rec.keyword_recommendation.keyword.text,
                    'match_type': rec.keyword_recommendation.keyword.match_type.name,
                    'recommended_cpc_bid': rec.keyword_recommendation.recommended_cpc_bid_micros / 1_000_000
                }

            elif rec.type.name == 'CAMPAIGN_BUDGET':
                rec_data['budget'] = {
                    'current': rec.campaign_budget_recommendation.current_budget_amount_micros / 1_000_000,
                    'recommended': rec.campaign_budget_recommendation.recommended_budget_amount_micros / 1_000_000,
                    'increase': (rec.campaign_budget_recommendation.recommended_budget_amount_micros -
                               rec.campaign_budget_recommendation.current_budget_amount_micros) / 1_000_000
                }

            elif rec.type.name == 'TARGET_CPA_OPT_IN':
                rec_data['target_cpa'] = {
                    'recommended': rec.target_cpa_opt_in_recommendation.recommended_target_cpa_micros / 1_000_000
                }

            elif rec.type.name == 'TARGET_ROAS_OPT_IN':
                rec_data['target_roas'] = {
                    'recommended': rec.target_roas_opt_in_recommendation.recommended_target_roas
                }

            elif rec.type.name == 'KEYWORD_MATCH_TYPE':
                rec_data['keyword_match_type'] = {
                    'keyword': rec.keyword_match_type_recommendation.keyword.text,
                    'recommended_match_type': rec.keyword_match_type_recommendation.recommended_match_type.name
                }

            recommendations.append(rec_data)

        return recommendations

    def apply_recommendation(
        self,
        customer_id: str,
        recommendation_resource_name: str
    ) -> Dict[str, Any]:
        """Apply a single optimization recommendation.

        Args:
            customer_id: Customer ID (without hyphens)
            recommendation_resource_name: Resource name of the recommendation

        Returns:
            Dictionary with application result
        """
        recommendation_service = self.client.get_service("RecommendationService")

        apply_operation = self.client.get_type("ApplyRecommendationOperation")
        apply_operation.resource_name = recommendation_resource_name

        response = recommendation_service.apply_recommendation(
            customer_id=customer_id,
            operations=[apply_operation]
        )

        result = response.results[0]

        return {
            'resource_name': result.resource_name,
            'status': 'applied'
        }

    def dismiss_recommendation(
        self,
        customer_id: str,
        recommendation_resource_name: str
    ) -> Dict[str, Any]:
        """Dismiss a recommendation without applying it.

        Args:
            customer_id: Customer ID (without hyphens)
            recommendation_resource_name: Resource name of the recommendation

        Returns:
            Dictionary with dismissal result
        """
        recommendation_service = self.client.get_service("RecommendationService")

        dismiss_operation = self.client.get_type("DismissRecommendationRequest.DismissRecommendationOperation")
        dismiss_operation.resource_name = recommendation_resource_name

        response = recommendation_service.dismiss_recommendation(
            customer_id=customer_id,
            operations=[dismiss_operation]
        )

        result = response.results[0]

        return {
            'resource_name': result.resource_name,
            'status': 'dismissed'
        }

    def get_optimization_score(
        self,
        customer_id: str
    ) -> Dict[str, Any]:
        """Get the account's optimization score.

        The optimization score ranges from 0-100% and represents how well
        your account is set up to perform. Higher scores indicate better
        optimization.

        Args:
            customer_id: Customer ID (without hyphens)

        Returns:
            Dictionary with optimization score and details
        """
        ga_service = self.client.get_service("GoogleAdsService")

        query = """
            SELECT
                customer.optimization_score,
                customer.optimization_score_weight
            FROM customer
        """

        response = ga_service.search(customer_id=customer_id, query=query)
        results = list(response)

        if not results:
            return {
                'error': 'No optimization score data available'
            }

        row = results[0]

        # Also get recommendation counts by type
        rec_query = """
            SELECT
                recommendation.type,
                metrics.impressions
            FROM recommendation
        """

        rec_response = ga_service.search(customer_id=customer_id, query=rec_query)

        recommendation_counts = {}
        for rec_row in rec_response:
            rec_type = rec_row.recommendation.type.name
            recommendation_counts[rec_type] = recommendation_counts.get(rec_type, 0) + 1

        return {
            'optimization_score': row.customer.optimization_score,
            'optimization_score_weight': row.customer.optimization_score_weight,
            'score_percentage': row.customer.optimization_score * 100,
            'recommendation_counts': recommendation_counts,
            'total_recommendations': sum(recommendation_counts.values())
        }

    def bulk_apply_recommendations(
        self,
        customer_id: str,
        recommendation_resource_names: List[str]
    ) -> Dict[str, Any]:
        """Apply multiple recommendations at once.

        Args:
            customer_id: Customer ID (without hyphens)
            recommendation_resource_names: List of recommendation resource names

        Returns:
            Dictionary with bulk application results
        """
        recommendation_service = self.client.get_service("RecommendationService")

        operations = []
        for resource_name in recommendation_resource_names:
            operation = self.client.get_type("ApplyRecommendationOperation")
            operation.resource_name = resource_name
            operations.append(operation)

        response = recommendation_service.apply_recommendation(
            customer_id=customer_id,
            operations=operations
        )

        applied = []
        for result in response.results:
            applied.append({
                'resource_name': result.resource_name,
                'status': 'applied'
            })

        return {
            'total_applied': len(applied),
            'results': applied
        }

    def bulk_dismiss_recommendations(
        self,
        customer_id: str,
        recommendation_resource_names: List[str]
    ) -> Dict[str, Any]:
        """Dismiss multiple recommendations at once.

        Args:
            customer_id: Customer ID (without hyphens)
            recommendation_resource_names: List of recommendation resource names

        Returns:
            Dictionary with bulk dismissal results
        """
        recommendation_service = self.client.get_service("RecommendationService")

        operations = []
        for resource_name in recommendation_resource_names:
            operation = self.client.get_type("DismissRecommendationRequest.DismissRecommendationOperation")
            operation.resource_name = resource_name
            operations.append(operation)

        response = recommendation_service.dismiss_recommendation(
            customer_id=customer_id,
            operations=operations
        )

        dismissed = []
        for result in response.results:
            dismissed.append({
                'resource_name': result.resource_name,
                'status': 'dismissed'
            })

        return {
            'total_dismissed': len(dismissed),
            'results': dismissed
        }

    def get_recommendation_insights(
        self,
        customer_id: str,
        campaign_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get insights about recommendations including potential impact.

        Args:
            customer_id: Customer ID (without hyphens)
            campaign_id: Optional campaign ID to filter

        Returns:
            Dictionary with recommendation insights and aggregate impact
        """
        recommendations = self.get_recommendations(customer_id, campaign_id=campaign_id)

        if not recommendations:
            return {
                'total_recommendations': 0,
                'message': 'No recommendations available'
            }

        # Aggregate impact metrics
        total_impact = {
            'impressions': 0,
            'clicks': 0,
            'cost': 0.0,
            'conversions': 0.0
        }

        by_type = {}

        for rec in recommendations:
            rec_type = rec['type']

            if rec_type not in by_type:
                by_type[rec_type] = {
                    'count': 0,
                    'impact': {
                        'impressions': 0,
                        'clicks': 0,
                        'cost': 0.0,
                        'conversions': 0.0
                    }
                }

            by_type[rec_type]['count'] += 1

            if 'impact' in rec:
                impact = rec['impact']
                total_impact['impressions'] += impact['impressions']
                total_impact['clicks'] += impact['clicks']
                total_impact['cost'] += impact['cost']
                total_impact['conversions'] += impact['conversions']

                by_type[rec_type]['impact']['impressions'] += impact['impressions']
                by_type[rec_type]['impact']['clicks'] += impact['clicks']
                by_type[rec_type]['impact']['cost'] += impact['cost']
                by_type[rec_type]['impact']['conversions'] += impact['conversions']

        return {
            'total_recommendations': len(recommendations),
            'total_potential_impact': total_impact,
            'by_type': by_type
        }

    def apply_recommendations_by_type(
        self,
        customer_id: str,
        recommendation_type: RecommendationType,
        max_to_apply: Optional[int] = None
    ) -> Dict[str, Any]:
        """Apply all recommendations of a specific type.

        Args:
            customer_id: Customer ID (without hyphens)
            recommendation_type: Type of recommendations to apply
            max_to_apply: Optional maximum number to apply

        Returns:
            Dictionary with application results
        """
        recommendations = self.get_recommendations(
            customer_id,
            recommendation_types=[recommendation_type]
        )

        if not recommendations:
            return {
                'total_applied': 0,
                'message': f'No {recommendation_type.value} recommendations found'
            }

        # Limit to max_to_apply if specified
        if max_to_apply:
            recommendations = recommendations[:max_to_apply]

        resource_names = [rec['resource_name'] for rec in recommendations]

        return self.bulk_apply_recommendations(customer_id, resource_names)

    def get_recommendation_history(
        self,
        customer_id: str,
        start_date: str,
        end_date: str
    ) -> List[Dict[str, Any]]:
        """Get history of applied/dismissed recommendations.

        Args:
            customer_id: Customer ID (without hyphens)
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            List of recommendation history entries
        """
        ga_service = self.client.get_service("GoogleAdsService")

        query = f"""
            SELECT
                change_event.resource_name,
                change_event.change_date_time,
                change_event.change_resource_name,
                change_event.change_resource_type,
                change_event.user_email,
                change_event.client_type,
                change_event.old_resource.recommendation.type,
                change_event.new_resource.recommendation.type
            FROM change_event
            WHERE change_event.change_resource_type = 'RECOMMENDATION'
            AND change_event.change_date_time >= '{start_date}'
            AND change_event.change_date_time <= '{end_date}'
            ORDER BY change_event.change_date_time DESC
        """

        response = ga_service.search(customer_id=customer_id, query=query)

        history = []
        for row in response:
            event = row.change_event

            history.append({
                'date_time': event.change_date_time,
                'resource_name': event.change_resource_name,
                'resource_type': event.change_resource_type.name,
                'user_email': event.user_email,
                'client_type': event.client_type.name,
                'old_type': event.old_resource.recommendation.type.name if event.old_resource.recommendation else None,
                'new_type': event.new_resource.recommendation.type.name if event.new_resource.recommendation else None
            })

        return history
