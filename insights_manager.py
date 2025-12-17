"""
Insights Manager

Handles AI-powered performance insights, budget optimization, and competitive intelligence.

Capabilities:
- Performance insights and anomaly detection
- Trend analysis and forecasting
- Budget pacing and reallocation recommendations
- Wasted spend identification
- Auction insights and competitive analysis
- Industry benchmarking
"""

from typing import Dict, Any, List, Optional
from google.ads.googleads.client import GoogleAdsClient
from datetime import datetime, timedelta
import statistics


class InsightsManager:
    """Manager for AI-powered insights and competitive intelligence."""

    def __init__(self, client: GoogleAdsClient):
        """Initialize the insights manager.

        Args:
            client: Authenticated GoogleAdsClient instance
        """
        self.client = client

    def get_performance_insights(
        self,
        customer_id: str,
        entity_type: str = "CAMPAIGN",
        entity_id: Optional[str] = None,
        date_range: str = "LAST_30_DAYS"
    ) -> Dict[str, Any]:
        """Generate AI-powered performance insights.

        Args:
            customer_id: Customer ID (without hyphens)
            entity_type: CAMPAIGN, AD_GROUP, KEYWORD, or AD
            entity_id: Optional specific entity ID
            date_range: Date range for analysis

        Returns:
            Performance insights with recommendations
        """
        ga_service = self.client.get_service("GoogleAdsService")

        # Build query based on entity type
        entity_map = {
            "CAMPAIGN": "campaign",
            "AD_GROUP": "ad_group",
            "KEYWORD": "ad_group_criterion",
            "AD": "ad_group_ad"
        }

        entity = entity_map.get(entity_type.upper(), "campaign")

        query = f"""
            SELECT
                {entity}.id,
                {entity}.name,
                metrics.impressions,
                metrics.clicks,
                metrics.ctr,
                metrics.cost_micros,
                metrics.conversions,
                metrics.conversions_value,
                metrics.cost_per_conversion,
                metrics.search_impression_share,
                metrics.quality_score
            FROM {entity}
            WHERE segments.date DURING {date_range}
        """

        if entity_id:
            query += f" AND {entity}.id = {entity_id}"

        query += " ORDER BY metrics.cost_micros DESC LIMIT 100"

        response = ga_service.search(customer_id=customer_id, query=query)

        insights = []
        for row in response:
            entity_obj = getattr(row, entity)
            metrics = row.metrics

            # Calculate performance scores
            ctr_benchmark = 0.02  # 2% industry average
            cvr_benchmark = 0.05  # 5% industry average

            ctr = metrics.ctr
            cvr = metrics.conversions / metrics.clicks if metrics.clicks > 0 else 0

            # Generate insights
            entity_insights = {
                'entity_id': str(entity_obj.id),
                'entity_name': entity_obj.name if hasattr(entity_obj, 'name') else 'N/A',
                'metrics': {
                    'impressions': metrics.impressions,
                    'clicks': metrics.clicks,
                    'ctr': ctr,
                    'cost': metrics.cost_micros / 1_000_000,
                    'conversions': metrics.conversions,
                    'cost_per_conversion': metrics.cost_per_conversion
                },
                'insights': []
            }

            # CTR insights
            if ctr < ctr_benchmark * 0.5:
                entity_insights['insights'].append({
                    'type': 'LOW_CTR',
                    'severity': 'HIGH',
                    'message': f'CTR ({ctr:.2%}) is significantly below benchmark ({ctr_benchmark:.2%})',
                    'recommendation': 'Review ad copy and targeting. Consider testing new ad variations.'
                })
            elif ctr > ctr_benchmark * 1.5:
                entity_insights['insights'].append({
                    'type': 'HIGH_CTR',
                    'severity': 'POSITIVE',
                    'message': f'CTR ({ctr:.2%}) is performing well above benchmark',
                    'recommendation': 'Consider increasing budget to capture more traffic.'
                })

            # Conversion rate insights
            if cvr < cvr_benchmark * 0.5 and metrics.clicks > 50:
                entity_insights['insights'].append({
                    'type': 'LOW_CONVERSION_RATE',
                    'severity': 'HIGH',
                    'message': f'Conversion rate ({cvr:.2%}) is below expected level',
                    'recommendation': 'Review landing page experience and conversion funnel.'
                })

            # Impression share insights
            if hasattr(metrics, 'search_impression_share'):
                is_value = metrics.search_impression_share
                if is_value < 0.5:
                    entity_insights['insights'].append({
                        'type': 'LOW_IMPRESSION_SHARE',
                        'severity': 'MEDIUM',
                        'message': f'Only capturing {is_value:.0%} of available impressions',
                        'recommendation': 'Increase budget or improve ad rank to capture more impressions.'
                    })

            # Quality score insights
            if hasattr(metrics, 'quality_score') and metrics.quality_score < 5:
                entity_insights['insights'].append({
                    'type': 'LOW_QUALITY_SCORE',
                    'severity': 'HIGH',
                    'message': f'Quality Score ({metrics.quality_score}/10) needs improvement',
                    'recommendation': 'Improve ad relevance, expected CTR, and landing page experience.'
                })

            if entity_insights['insights']:
                insights.append(entity_insights)

        return {
            'entity_type': entity_type,
            'total_analyzed': len(list(response)),
            'insights_count': len(insights),
            'insights': insights
        }

    def analyze_trends(
        self,
        customer_id: str,
        campaign_id: Optional[str] = None,
        lookback_days: int = 30
    ) -> Dict[str, Any]:
        """Analyze performance trends and detect anomalies.

        Args:
            customer_id: Customer ID (without hyphens)
            campaign_id: Optional campaign ID filter
            lookback_days: Number of days to analyze

        Returns:
            Trend analysis with anomaly detection
        """
        ga_service = self.client.get_service("GoogleAdsService")

        # Get daily performance data
        query = f"""
            SELECT
                segments.date,
                metrics.impressions,
                metrics.clicks,
                metrics.ctr,
                metrics.cost_micros,
                metrics.conversions
            FROM campaign
            WHERE segments.date DURING LAST_{lookback_days}_DAYS
        """

        if campaign_id:
            query += f" AND campaign.id = {campaign_id}"

        query += " ORDER BY segments.date"

        response = ga_service.search(customer_id=customer_id, query=query)

        # Collect daily data
        daily_data = []
        for row in response:
            daily_data.append({
                'date': str(row.segments.date),
                'impressions': row.metrics.impressions,
                'clicks': row.metrics.clicks,
                'ctr': row.metrics.ctr,
                'cost': row.metrics.cost_micros / 1_000_000,
                'conversions': row.metrics.conversions
            })

        if not daily_data:
            return {'error': 'No data available for trend analysis'}

        # Calculate trends
        costs = [d['cost'] for d in daily_data]
        conversions = [d['conversions'] for d in daily_data]
        ctrs = [d['ctr'] for d in daily_data]

        # Simple trend detection (comparing first half vs second half)
        mid_point = len(daily_data) // 2

        cost_first_half = sum(costs[:mid_point]) / mid_point if mid_point > 0 else 0
        cost_second_half = sum(costs[mid_point:]) / (len(costs) - mid_point) if mid_point < len(costs) else 0

        conv_first_half = sum(conversions[:mid_point]) / mid_point if mid_point > 0 else 0
        conv_second_half = sum(conversions[mid_point:]) / (len(conversions) - mid_point) if mid_point < len(conversions) else 0

        # Detect anomalies (values beyond 2 standard deviations)
        anomalies = []
        if len(costs) > 3:
            cost_mean = statistics.mean(costs)
            cost_stdev = statistics.stdev(costs)

            for i, day in enumerate(daily_data):
                if abs(day['cost'] - cost_mean) > 2 * cost_stdev:
                    anomalies.append({
                        'date': day['date'],
                        'metric': 'cost',
                        'value': day['cost'],
                        'deviation': abs(day['cost'] - cost_mean) / cost_stdev
                    })

        # Calculate trend direction
        cost_trend = "INCREASING" if cost_second_half > cost_first_half * 1.1 else \
                     "DECREASING" if cost_second_half < cost_first_half * 0.9 else "STABLE"

        conv_trend = "INCREASING" if conv_second_half > conv_first_half * 1.1 else \
                     "DECREASING" if conv_second_half < conv_first_half * 0.9 else "STABLE"

        return {
            'lookback_days': lookback_days,
            'data_points': len(daily_data),
            'trends': {
                'cost_trend': cost_trend,
                'cost_change_pct': ((cost_second_half - cost_first_half) / cost_first_half * 100) if cost_first_half > 0 else 0,
                'conversion_trend': conv_trend,
                'conversion_change_pct': ((conv_second_half - conv_first_half) / conv_first_half * 100) if conv_first_half > 0 else 0
            },
            'anomalies': anomalies,
            'daily_data': daily_data
        }

    def get_budget_pacing(
        self,
        customer_id: str,
        campaign_id: str
    ) -> Dict[str, Any]:
        """Analyze budget pacing and spending velocity.

        Args:
            customer_id: Customer ID (without hyphens)
            campaign_id: Campaign ID

        Returns:
            Budget pacing analysis
        """
        ga_service = self.client.get_service("GoogleAdsService")

        # Get campaign budget and current month spend
        query = f"""
            SELECT
                campaign.id,
                campaign.name,
                campaign_budget.amount_micros,
                campaign_budget.period,
                metrics.cost_micros
            FROM campaign
            WHERE campaign.id = {campaign_id}
              AND segments.date DURING THIS_MONTH
        """

        response = ga_service.search(customer_id=customer_id, query=query)
        results = list(response)

        if not results:
            return {'error': 'Campaign not found or no data available'}

        row = results[0]

        # Calculate pacing
        now = datetime.now()
        days_in_month = (datetime(now.year, now.month + 1, 1) - timedelta(days=1)).day if now.month < 12 else 31
        days_elapsed = now.day
        days_remaining = days_in_month - days_elapsed

        budget_period = row.campaign_budget.period.name

        if budget_period == "DAILY":
            daily_budget = row.campaign_budget.amount_micros / 1_000_000
            monthly_budget = daily_budget * days_in_month
        else:
            monthly_budget = row.campaign_budget.amount_micros / 1_000_000

        current_spend = row.metrics.cost_micros / 1_000_000
        expected_spend = (monthly_budget / days_in_month) * days_elapsed

        pace_percentage = (current_spend / expected_spend * 100) if expected_spend > 0 else 0

        projected_spend = (current_spend / days_elapsed) * days_in_month if days_elapsed > 0 else 0

        # Determine pacing status
        if pace_percentage > 120:
            status = "OVERPACING"
            message = f"Spending {pace_percentage - 100:.0f}% faster than budget allows"
        elif pace_percentage < 80:
            status = "UNDERPACING"
            message = f"Spending {100 - pace_percentage:.0f}% slower than expected"
        else:
            status = "ON_TRACK"
            message = "Budget pacing is healthy"

        return {
            'campaign_id': campaign_id,
            'campaign_name': row.campaign.name,
            'budget_period': budget_period,
            'monthly_budget': monthly_budget,
            'current_spend': current_spend,
            'expected_spend': expected_spend,
            'projected_spend': projected_spend,
            'pace_percentage': pace_percentage,
            'days_elapsed': days_elapsed,
            'days_remaining': days_remaining,
            'status': status,
            'message': message
        }

    def get_budget_recommendations(
        self,
        customer_id: str,
        date_range: str = "LAST_30_DAYS"
    ) -> List[Dict[str, Any]]:
        """Generate budget reallocation recommendations.

        Args:
            customer_id: Customer ID (without hyphens)
            date_range: Date range for analysis

        Returns:
            List of budget recommendations
        """
        ga_service = self.client.get_service("GoogleAdsService")

        query = f"""
            SELECT
                campaign.id,
                campaign.name,
                campaign_budget.amount_micros,
                metrics.cost_micros,
                metrics.conversions,
                metrics.cost_per_conversion,
                metrics.search_budget_lost_impression_share,
                metrics.conversions_value
            FROM campaign
            WHERE segments.date DURING {date_range}
              AND campaign.status = 'ENABLED'
            ORDER BY metrics.cost_micros DESC
        """

        response = ga_service.search(customer_id=customer_id, query=query)

        recommendations = []

        for row in response:
            campaign = row.campaign
            metrics = row.metrics
            budget = row.campaign_budget

            daily_budget = budget.amount_micros / 1_000_000
            avg_daily_spend = (metrics.cost_micros / 1_000_000) / 30  # Approximate

            # Identify budget-constrained campaigns
            if metrics.search_budget_lost_impression_share > 0.2:
                lost_is = metrics.search_budget_lost_impression_share
                recommended_increase = daily_budget * (lost_is / (1 - lost_is))

                recommendations.append({
                    'campaign_id': str(campaign.id),
                    'campaign_name': campaign.name,
                    'type': 'INCREASE_BUDGET',
                    'priority': 'HIGH',
                    'current_budget': daily_budget,
                    'recommended_budget': daily_budget + recommended_increase,
                    'increase_amount': recommended_increase,
                    'reason': f'Losing {lost_is:.0%} of impressions due to budget',
                    'expected_impact': f'Could capture {lost_is:.0%} more impressions'
                })

            # Identify underperforming campaigns with high spend
            if metrics.conversions == 0 and metrics.cost_micros > 50_000_000:  # $50+
                recommendations.append({
                    'campaign_id': str(campaign.id),
                    'campaign_name': campaign.name,
                    'type': 'DECREASE_BUDGET',
                    'priority': 'MEDIUM',
                    'current_budget': daily_budget,
                    'recommended_budget': daily_budget * 0.5,
                    'decrease_amount': daily_budget * 0.5,
                    'reason': 'No conversions despite significant spend',
                    'expected_impact': 'Reduce wasted spend, reallocate to performing campaigns'
                })

            # Identify high ROAS campaigns
            if metrics.conversions > 0:
                roas = metrics.conversions_value / (metrics.cost_micros / 1_000_000)
                if roas > 4.0 and avg_daily_spend < daily_budget * 0.8:
                    recommendations.append({
                        'campaign_id': str(campaign.id),
                        'campaign_name': campaign.name,
                        'type': 'INCREASE_BUDGET',
                        'priority': 'HIGH',
                        'current_budget': daily_budget,
                        'recommended_budget': daily_budget * 1.3,
                        'increase_amount': daily_budget * 0.3,
                        'reason': f'Strong ROAS ({roas:.1f}x) with budget headroom',
                        'expected_impact': 'Scale winning campaign for more revenue'
                    })

        return sorted(recommendations, key=lambda x: 1 if x['priority'] == 'HIGH' else 2)

    def analyze_wasted_spend(
        self,
        customer_id: str,
        date_range: str = "LAST_30_DAYS",
        min_cost: float = 10.0
    ) -> Dict[str, Any]:
        """Identify sources of wasted ad spend.

        Args:
            customer_id: Customer ID (without hyphens)
            date_range: Date range for analysis
            min_cost: Minimum cost threshold for analysis

        Returns:
            Wasted spend analysis
        """
        ga_service = self.client.get_service("GoogleAdsService")

        # Analyze keywords with high cost but no conversions
        keyword_query = f"""
            SELECT
                ad_group.id,
                ad_group.name,
                campaign.name,
                ad_group_criterion.keyword.text,
                ad_group_criterion.keyword.match_type,
                metrics.cost_micros,
                metrics.clicks,
                metrics.conversions
            FROM keyword_view
            WHERE segments.date DURING {date_range}
              AND metrics.cost_micros > {int(min_cost * 1_000_000)}
            ORDER BY metrics.cost_micros DESC
            LIMIT 50
        """

        keyword_response = ga_service.search(customer_id=customer_id, query=keyword_query)

        wasted_keywords = []
        for row in keyword_response:
            cost = row.metrics.cost_micros / 1_000_000
            if row.metrics.conversions == 0 and cost > min_cost:
                wasted_keywords.append({
                    'keyword': row.ad_group_criterion.keyword.text,
                    'match_type': row.ad_group_criterion.keyword.match_type.name,
                    'campaign': row.campaign.name,
                    'ad_group': row.ad_group.name,
                    'cost': cost,
                    'clicks': row.metrics.clicks,
                    'conversions': row.metrics.conversions
                })

        total_wasted = sum(k['cost'] for k in wasted_keywords)

        # Categorize waste types
        waste_categories = {
            'non_converting_keywords': {
                'count': len(wasted_keywords),
                'cost': total_wasted,
                'description': 'Keywords with spend but no conversions'
            }
        }

        return {
            'date_range': date_range,
            'total_wasted_spend': total_wasted,
            'waste_categories': waste_categories,
            'top_wasters': wasted_keywords[:10],
            'recommendations': [
                'Add non-converting keywords as negatives',
                'Review keyword match types (consider using phrase/exact instead of broad)',
                'Reallocate budget to converting keywords'
            ]
        }

    def get_auction_insights(
        self,
        customer_id: str,
        campaign_id: str,
        date_range: str = "LAST_30_DAYS"
    ) -> Dict[str, Any]:
        """Get auction insights and competitive data.

        Args:
            customer_id: Customer ID (without hyphens)
            campaign_id: Campaign ID
            date_range: Date range

        Returns:
            Auction insights data
        """
        ga_service = self.client.get_service("GoogleAdsService")

        query = f"""
            SELECT
                campaign.id,
                campaign.name,
                metrics.search_impression_share,
                metrics.search_rank_lost_impression_share,
                metrics.search_budget_lost_impression_share,
                metrics.search_top_impression_share,
                metrics.search_absolute_top_impression_share,
                metrics.search_exact_match_impression_share
            FROM campaign
            WHERE campaign.id = {campaign_id}
              AND segments.date DURING {date_range}
        """

        response = ga_service.search(customer_id=customer_id, query=query)
        results = list(response)

        if not results:
            return {'error': 'No auction insights data available'}

        row = results[0]
        metrics = row.metrics

        # Calculate competitive position
        total_is = metrics.search_impression_share
        rank_lost = metrics.search_rank_lost_impression_share
        budget_lost = metrics.search_budget_lost_impression_share

        competitive_position = "STRONG" if total_is > 0.7 else \
                              "MODERATE" if total_is > 0.4 else "WEAK"

        # Identify primary constraint
        if budget_lost > rank_lost:
            primary_constraint = "BUDGET"
            constraint_message = f"Budget is limiting visibility ({budget_lost:.0%} lost)"
        elif rank_lost > budget_lost:
            primary_constraint = "AD_RANK"
            constraint_message = f"Ad rank is limiting visibility ({rank_lost:.0%} lost)"
        else:
            primary_constraint = "NONE"
            constraint_message = "No significant constraints"

        return {
            'campaign_id': campaign_id,
            'campaign_name': row.campaign.name,
            'impression_share': total_is,
            'top_impression_share': metrics.search_top_impression_share,
            'absolute_top_impression_share': metrics.search_absolute_top_impression_share,
            'rank_lost_is': rank_lost,
            'budget_lost_is': budget_lost,
            'competitive_position': competitive_position,
            'primary_constraint': primary_constraint,
            'constraint_message': constraint_message,
            'recommendations': self._get_auction_recommendations(
                total_is, rank_lost, budget_lost,
                metrics.search_top_impression_share
            )
        }

    def _get_auction_recommendations(
        self,
        impression_share: float,
        rank_lost: float,
        budget_lost: float,
        top_is: float
    ) -> List[str]:
        """Generate auction-specific recommendations."""
        recommendations = []

        if budget_lost > 0.15:
            recommendations.append("Increase daily budget to capture more impressions")

        if rank_lost > 0.15:
            recommendations.append("Improve Quality Score or increase bids to improve ad rank")

        if top_is < 0.3:
            recommendations.append("Increase bids to show in top positions more often")

        if impression_share < 0.5:
            recommendations.append("Review targeting settings - may be too restrictive")

        return recommendations if recommendations else ["Continue current strategy"]
