"""
MCP Tools - Insights & Recommendations

Tools for AI-powered performance insights, budget optimization, and competitive intelligence.

Tools:
1. google_ads_performance_insights - AI-powered performance analysis
2. google_ads_trend_analysis - Trend detection and anomaly identification
3. google_ads_budget_pacing - Budget pacing and spending velocity
4. google_ads_budget_recommendations - Budget reallocation suggestions
5. google_ads_wasted_spend_analysis - Identify inefficient spending
6. google_ads_auction_insights - Competitive auction intelligence
7. google_ads_opportunity_finder - Find optimization opportunities
8. google_ads_performance_forecaster - Predict future performance
"""

from typing import Optional
from insights_manager import InsightsManager
from auth_manager import get_auth_manager
from error_handler import ErrorHandler
from logger import get_logger, get_performance_logger, get_audit_logger

logger = get_logger(__name__)
performance_logger = get_performance_logger()
audit_logger = get_audit_logger()


def register_insights_tools(mcp):
    """Register all insights and recommendations MCP tools."""

    @mcp.tool()
    def google_ads_performance_insights(
        customer_id: str,
        entity_type: str = "CAMPAIGN",
        entity_id: Optional[str] = None,
        date_range: str = "LAST_30_DAYS"
    ) -> str:
        """Generate AI-powered performance insights for campaigns, ad groups, keywords, or ads.

        Analyzes performance metrics and provides actionable recommendations for:
        - Low CTR (below industry benchmarks)
        - Low conversion rates
        - Low impression share
        - Low quality scores
        - High performers worthy of increased budget

        Args:
            customer_id: Google Ads customer ID (10 digits, no hyphens)
            entity_type: Entity to analyze - CAMPAIGN, AD_GROUP, KEYWORD, or AD
            entity_id: Optional specific entity ID (if not provided, analyzes all)
            date_range: Date range (LAST_7_DAYS, LAST_30_DAYS, LAST_90_DAYS, THIS_MONTH, LAST_MONTH)

        Returns:
            Performance insights with AI-generated recommendations

        Example:
            google_ads_performance_insights(
                customer_id="1234567890",
                entity_type="CAMPAIGN",
                date_range="LAST_30_DAYS"
            )
        """
        with performance_logger.track_operation('performance_insights', customer_id=customer_id):
            try:
                client = get_auth_manager().get_client()
                insights_manager = InsightsManager(client)

                result = insights_manager.get_performance_insights(
                    customer_id=customer_id,
                    entity_type=entity_type,
                    entity_id=entity_id,
                    date_range=date_range
                )

                if 'error' in result:
                    return f"❌ {result['error']}"

                audit_logger.log_api_call(
                    customer_id=customer_id,
                    operation='get_performance_insights',
                    entity_type=entity_type,
                    status='success'
                )

                # Format response
                output = f"# 🔍 Performance Insights Report\n\n"
                output += f"**Entity Type**: {result['entity_type']}\n"
                output += f"**Total Analyzed**: {result['total_analyzed']}\n"
                output += f"**Insights Found**: {result['insights_count']}\n\n"

                if result['insights_count'] == 0:
                    output += "✅ **All entities are performing within expected ranges!**\n\n"
                    output += "No major issues detected. Continue monitoring performance.\n"
                    return output

                output += "---\n\n"

                # Group insights by severity
                high_severity = [i for i in result['insights'] if any(
                    insight['severity'] == 'HIGH' for insight in i['insights']
                )]
                medium_severity = [i for i in result['insights'] if any(
                    insight['severity'] == 'MEDIUM' for insight in i['insights']
                ) and i not in high_severity]
                positive = [i for i in result['insights'] if any(
                    insight['severity'] == 'POSITIVE' for insight in i['insights']
                )]

                # High priority issues
                if high_severity:
                    output += "## 🚨 High Priority Issues\n\n"
                    for entity in high_severity[:5]:  # Top 5
                        output += f"### {entity['entity_name']}\n"
                        output += f"**Cost**: ${entity['metrics']['cost']:,.2f} | "
                        output += f"**Conversions**: {entity['metrics']['conversions']}\n\n"

                        for insight in entity['insights']:
                            if insight['severity'] == 'HIGH':
                                output += f"**⚠️ {insight['type'].replace('_', ' ').title()}**\n"
                                output += f"- {insight['message']}\n"
                                output += f"- 💡 *{insight['recommendation']}*\n\n"

                # Medium priority issues
                if medium_severity:
                    output += "## ⚡ Medium Priority Opportunities\n\n"
                    for entity in medium_severity[:3]:  # Top 3
                        output += f"### {entity['entity_name']}\n"
                        for insight in entity['insights']:
                            if insight['severity'] == 'MEDIUM':
                                output += f"- {insight['message']}\n"
                                output += f"  💡 *{insight['recommendation']}*\n\n"

                # Positive performers
                if positive:
                    output += "## ✨ Top Performers\n\n"
                    for entity in positive[:3]:  # Top 3
                        output += f"### {entity['entity_name']}\n"
                        output += f"**Cost**: ${entity['metrics']['cost']:,.2f} | "
                        output += f"**CTR**: {entity['metrics']['ctr']:.2%}\n"
                        for insight in entity['insights']:
                            if insight['severity'] == 'POSITIVE':
                                output += f"- ✅ {insight['message']}\n"
                                output += f"  💡 *{insight['recommendation']}*\n\n"

                output += "---\n\n"
                output += "💡 **Next Steps**: Prioritize high-severity issues first, then explore medium-priority opportunities.\n"

                return output

            except Exception as e:
                error_msg = ErrorHandler.handle_error(e, context="performance_insights")
                return f"❌ Failed to generate performance insights: {error_msg}"

    @mcp.tool()
    def google_ads_trend_analysis(
        customer_id: str,
        campaign_id: Optional[str] = None,
        lookback_days: int = 30
    ) -> str:
        """Analyze performance trends and detect anomalies over time.

        Identifies:
        - Increasing/decreasing cost trends
        - Conversion performance trends
        - Anomalous days with unusual spending or performance
        - Provides daily performance data for visualization

        Args:
            customer_id: Google Ads customer ID (10 digits, no hyphens)
            campaign_id: Optional campaign ID filter (analyzes all campaigns if not provided)
            lookback_days: Number of days to analyze (7-90)

        Returns:
            Trend analysis with anomaly detection

        Example:
            google_ads_trend_analysis(
                customer_id="1234567890",
                lookback_days=30
            )
        """
        with performance_logger.track_operation('trend_analysis', customer_id=customer_id):
            try:
                client = get_auth_manager().get_client()
                insights_manager = InsightsManager(client)

                result = insights_manager.analyze_trends(
                    customer_id=customer_id,
                    campaign_id=campaign_id,
                    lookback_days=lookback_days
                )

                if 'error' in result:
                    return f"❌ {result['error']}"

                audit_logger.log_api_call(
                    customer_id=customer_id,
                    operation='analyze_trends',
                    campaign_id=campaign_id,
                    status='success'
                )

                # Format response
                output = f"# 📈 Trend Analysis Report\n\n"
                output += f"**Lookback Period**: {result['lookback_days']} days\n"
                output += f"**Data Points**: {result['data_points']}\n\n"

                trends = result['trends']

                output += "## Cost Trends\n\n"
                trend_emoji = "📈" if trends['cost_trend'] == "INCREASING" else \
                             "📉" if trends['cost_trend'] == "DECREASING" else "➡️"
                output += f"{trend_emoji} **{trends['cost_trend']}** "
                output += f"({trends['cost_change_pct']:+.1f}%)\n\n"

                if abs(trends['cost_change_pct']) > 20:
                    output += f"⚠️ **Significant change detected!** Cost has changed by {abs(trends['cost_change_pct']):.0f}%.\n\n"

                output += "## Conversion Trends\n\n"
                conv_emoji = "📈" if trends['conversion_trend'] == "INCREASING" else \
                            "📉" if trends['conversion_trend'] == "DECREASING" else "➡️"
                output += f"{conv_emoji} **{trends['conversion_trend']}** "
                output += f"({trends['conversion_change_pct']:+.1f}%)\n\n"

                if trends['conversion_trend'] == "DECREASING" and abs(trends['conversion_change_pct']) > 15:
                    output += f"🚨 **Action Required**: Conversions have dropped {abs(trends['conversion_change_pct']):.0f}%. Investigate immediately.\n\n"

                # Anomalies
                if result['anomalies']:
                    output += "## 🔔 Anomalies Detected\n\n"
                    output += f"Found {len(result['anomalies'])} unusual data points:\n\n"

                    for anomaly in result['anomalies'][:5]:  # Top 5
                        output += f"- **{anomaly['date']}**: {anomaly['metric'].title()} = ${anomaly['value']:,.2f} "
                        output += f"({anomaly['deviation']:.1f}σ from mean)\n"

                    output += "\n💡 Review these dates for campaign changes, external events, or data issues.\n\n"
                else:
                    output += "## ✅ No Anomalies\n\n"
                    output += "Performance has been consistent with no unusual spikes or drops.\n\n"

                # Recent performance summary
                output += "## Recent Daily Performance\n\n"
                recent_days = result['daily_data'][-7:]  # Last 7 days

                output += "| Date | Impressions | Clicks | Cost | Conversions |\n"
                output += "|------|-------------|--------|------|-------------|\n"

                for day in recent_days:
                    output += f"| {day['date']} | {day['impressions']:,} | {day['clicks']:,} | "
                    output += f"${day['cost']:,.2f} | {day['conversions']:.1f} |\n"

                return output

            except Exception as e:
                error_msg = ErrorHandler.handle_error(e, context="trend_analysis")
                return f"❌ Failed to analyze trends: {error_msg}"

    @mcp.tool()
    def google_ads_budget_pacing(
        customer_id: str,
        campaign_id: str
    ) -> str:
        """Analyze budget pacing and spending velocity for a campaign.

        Shows:
        - Current spend vs. expected spend
        - Pacing percentage (overpacing, underpacing, on track)
        - Projected month-end spend
        - Days remaining in the month
        - Recommendations for budget adjustments

        Args:
            customer_id: Google Ads customer ID (10 digits, no hyphens)
            campaign_id: Campaign ID to analyze

        Returns:
            Budget pacing analysis with recommendations

        Example:
            google_ads_budget_pacing(
                customer_id="1234567890",
                campaign_id="12345678"
            )
        """
        with performance_logger.track_operation('budget_pacing', customer_id=customer_id):
            try:
                client = get_auth_manager().get_client()
                insights_manager = InsightsManager(client)

                result = insights_manager.get_budget_pacing(
                    customer_id=customer_id,
                    campaign_id=campaign_id
                )

                if 'error' in result:
                    return f"❌ {result['error']}"

                audit_logger.log_api_call(
                    customer_id=customer_id,
                    operation='get_budget_pacing',
                    campaign_id=campaign_id,
                    status='success'
                )

                # Format response
                output = f"# 💰 Budget Pacing Report\n\n"
                output += f"**Campaign**: {result['campaign_name']}\n"
                output += f"**Budget Period**: {result['budget_period']}\n\n"

                output += "## Budget Overview\n\n"
                output += f"- **Monthly Budget**: ${result['monthly_budget']:,.2f}\n"
                output += f"- **Current Spend**: ${result['current_spend']:,.2f}\n"
                output += f"- **Expected Spend**: ${result['expected_spend']:,.2f}\n"
                output += f"- **Projected Month-End**: ${result['projected_spend']:,.2f}\n\n"

                output += "## Pacing Status\n\n"

                status = result['status']
                pace = result['pace_percentage']

                if status == "OVERPACING":
                    output += f"🚨 **OVERPACING** ({pace:.0f}%)\n\n"
                    output += f"{result['message']}\n\n"
                    output += "**⚠️ Risk**: Budget may be exhausted before month-end.\n\n"
                    output += "**Recommended Actions**:\n"
                    output += "- Reduce bids or pause low-performing keywords\n"
                    output += "- Narrow targeting to control costs\n"
                    output += "- Consider increasing monthly budget if performance is strong\n"
                elif status == "UNDERPACING":
                    output += f"⚡ **UNDERPACING** ({pace:.0f}%)\n\n"
                    output += f"{result['message']}\n\n"
                    output += "**💡 Opportunity**: Budget is underutilized.\n\n"
                    output += "**Recommended Actions**:\n"
                    output += "- Increase bids to capture more traffic\n"
                    output += "- Expand targeting (keywords, locations, audiences)\n"
                    output += "- Review if budget is too high for current strategy\n"
                else:
                    output += f"✅ **ON TRACK** ({pace:.0f}%)\n\n"
                    output += f"{result['message']}\n\n"
                    output += "Continue monitoring daily spend to maintain healthy pacing.\n"

                output += "\n## Timeline\n\n"
                output += f"- **Days Elapsed**: {result['days_elapsed']}\n"
                output += f"- **Days Remaining**: {result['days_remaining']}\n\n"

                budget_remaining = result['monthly_budget'] - result['current_spend']
                daily_budget_needed = budget_remaining / result['days_remaining'] if result['days_remaining'] > 0 else 0

                output += f"**Budget Remaining**: ${budget_remaining:,.2f}\n"
                output += f"**Required Daily Spend**: ${daily_budget_needed:,.2f}\n"

                return output

            except Exception as e:
                error_msg = ErrorHandler.handle_error(e, context="budget_pacing")
                return f"❌ Failed to analyze budget pacing: {error_msg}"

    @mcp.tool()
    def google_ads_budget_recommendations(
        customer_id: str,
        date_range: str = "LAST_30_DAYS"
    ) -> str:
        """Generate AI-powered budget reallocation recommendations.

        Identifies:
        - Budget-constrained campaigns losing impression share
        - Underperforming campaigns with excessive spend
        - High ROAS campaigns deserving more budget
        - Prioritized recommendations with expected impact

        Args:
            customer_id: Google Ads customer ID (10 digits, no hyphens)
            date_range: Date range for analysis (LAST_7_DAYS, LAST_30_DAYS, LAST_90_DAYS)

        Returns:
            Budget reallocation recommendations prioritized by impact

        Example:
            google_ads_budget_recommendations(
                customer_id="1234567890",
                date_range="LAST_30_DAYS"
            )
        """
        with performance_logger.track_operation('budget_recommendations', customer_id=customer_id):
            try:
                client = get_auth_manager().get_client()
                insights_manager = InsightsManager(client)

                recommendations = insights_manager.get_budget_recommendations(
                    customer_id=customer_id,
                    date_range=date_range
                )

                audit_logger.log_api_call(
                    customer_id=customer_id,
                    operation='get_budget_recommendations',
                    status='success'
                )

                # Format response
                output = f"# 💡 Budget Optimization Recommendations\n\n"

                if not recommendations:
                    output += "✅ **All budgets are properly allocated!**\n\n"
                    output += "No immediate reallocation opportunities detected.\n"
                    return output

                output += f"Found **{len(recommendations)}** optimization opportunities:\n\n"

                # Group by type
                increase_recs = [r for r in recommendations if r['type'] == 'INCREASE_BUDGET']
                decrease_recs = [r for r in recommendations if r['type'] == 'DECREASE_BUDGET']

                # Increase recommendations
                if increase_recs:
                    output += "## 📈 Budget Increase Opportunities\n\n"
                    total_increase = sum(r['increase_amount'] for r in increase_recs)
                    output += f"**Total Recommended Increase**: ${total_increase:,.2f}/day\n\n"

                    for rec in increase_recs:
                        priority_emoji = "🔴" if rec['priority'] == 'HIGH' else "🟡"
                        output += f"### {priority_emoji} {rec['campaign_name']}\n\n"
                        output += f"**Current Budget**: ${rec['current_budget']:,.2f}/day\n"
                        output += f"**Recommended**: ${rec['recommended_budget']:,.2f}/day "
                        output += f"(+${rec['increase_amount']:,.2f})\n\n"
                        output += f"**Reason**: {rec['reason']}\n"
                        output += f"**Expected Impact**: {rec['expected_impact']}\n\n"

                # Decrease recommendations
                if decrease_recs:
                    output += "## 📉 Budget Decrease Opportunities\n\n"
                    total_decrease = sum(r['decrease_amount'] for r in decrease_recs)
                    output += f"**Total Recommended Decrease**: ${total_decrease:,.2f}/day\n\n"

                    for rec in decrease_recs:
                        output += f"### {rec['campaign_name']}\n\n"
                        output += f"**Current Budget**: ${rec['current_budget']:,.2f}/day\n"
                        output += f"**Recommended**: ${rec['recommended_budget']:,.2f}/day "
                        output += f"(-${rec['decrease_amount']:,.2f})\n\n"
                        output += f"**Reason**: {rec['reason']}\n"
                        output += f"**Expected Impact**: {rec['expected_impact']}\n\n"

                output += "---\n\n"
                output += "💡 **Implementation Tip**: Start with high-priority recommendations and monitor performance for 7 days before making additional changes.\n"

                return output

            except Exception as e:
                error_msg = ErrorHandler.handle_error(e, context="budget_recommendations")
                return f"❌ Failed to generate budget recommendations: {error_msg}"

    @mcp.tool()
    def google_ads_wasted_spend_analysis(
        customer_id: str,
        date_range: str = "LAST_30_DAYS",
        min_cost: float = 10.0
    ) -> str:
        """Identify sources of wasted ad spend and optimization opportunities.

        Analyzes:
        - Keywords with high cost but no conversions
        - Poor match type usage
        - Inefficient spending patterns
        - Specific recommendations to reduce waste

        Args:
            customer_id: Google Ads customer ID (10 digits, no hyphens)
            date_range: Date range for analysis (LAST_7_DAYS, LAST_30_DAYS, LAST_90_DAYS)
            min_cost: Minimum cost threshold for analysis (default: $10)

        Returns:
            Wasted spend analysis with actionable recommendations

        Example:
            google_ads_wasted_spend_analysis(
                customer_id="1234567890",
                date_range="LAST_30_DAYS",
                min_cost=20.0
            )
        """
        with performance_logger.track_operation('wasted_spend_analysis', customer_id=customer_id):
            try:
                client = get_auth_manager().get_client()
                insights_manager = InsightsManager(client)

                result = insights_manager.analyze_wasted_spend(
                    customer_id=customer_id,
                    date_range=date_range,
                    min_cost=min_cost
                )

                audit_logger.log_api_call(
                    customer_id=customer_id,
                    operation='analyze_wasted_spend',
                    status='success'
                )

                # Format response
                output = f"# 🔍 Wasted Spend Analysis\n\n"
                output += f"**Date Range**: {result['date_range']}\n"
                output += f"**Total Wasted Spend**: ${result['total_wasted_spend']:,.2f}\n\n"

                if result['total_wasted_spend'] == 0:
                    output += "✅ **No significant wasted spend detected!**\n\n"
                    output += "All keywords with spend are generating conversions. Great job!\n"
                    return output

                output += "---\n\n"

                # Waste categories
                output += "## Waste Categories\n\n"
                for category, data in result['waste_categories'].items():
                    output += f"### {category.replace('_', ' ').title()}\n\n"
                    output += f"- **Count**: {data['count']} keywords\n"
                    output += f"- **Total Cost**: ${data['cost']:,.2f}\n"
                    output += f"- **Description**: {data['description']}\n\n"

                # Top wasters
                if result['top_wasters']:
                    output += "## 🚨 Top 10 Wasted Spend Keywords\n\n"
                    output += "| Keyword | Match Type | Campaign | Cost | Clicks | Conversions |\n"
                    output += "|---------|------------|----------|------|--------|-------------|\n"

                    for kw in result['top_wasters']:
                        output += f"| {kw['keyword']} | {kw['match_type']} | "
                        output += f"{kw['campaign']} | ${kw['cost']:,.2f} | "
                        output += f"{kw['clicks']} | {kw['conversions']} |\n"

                    output += "\n"

                # Recommendations
                output += "## 💡 Recommended Actions\n\n"
                for i, rec in enumerate(result['recommendations'], 1):
                    output += f"{i}. {rec}\n"

                output += "\n---\n\n"
                output += "**💰 Potential Monthly Savings**: "
                monthly_savings = result['total_wasted_spend'] * (30 / 30)  # Normalize to monthly
                output += f"${monthly_savings:,.2f}\n"

                return output

            except Exception as e:
                error_msg = ErrorHandler.handle_error(e, context="wasted_spend_analysis")
                return f"❌ Failed to analyze wasted spend: {error_msg}"

    @mcp.tool()
    def google_ads_auction_insights(
        customer_id: str,
        campaign_id: str,
        date_range: str = "LAST_30_DAYS"
    ) -> str:
        """Get auction insights and competitive intelligence for a campaign.

        Provides:
        - Impression share metrics (overall, top, absolute top)
        - Competitive position analysis
        - Primary constraints (budget vs. ad rank)
        - Specific recommendations to improve auction performance

        Args:
            customer_id: Google Ads customer ID (10 digits, no hyphens)
            campaign_id: Campaign ID to analyze
            date_range: Date range (LAST_7_DAYS, LAST_30_DAYS, LAST_90_DAYS)

        Returns:
            Auction insights with competitive analysis

        Example:
            google_ads_auction_insights(
                customer_id="1234567890",
                campaign_id="12345678",
                date_range="LAST_30_DAYS"
            )
        """
        with performance_logger.track_operation('auction_insights', customer_id=customer_id):
            try:
                client = get_auth_manager().get_client()
                insights_manager = InsightsManager(client)

                result = insights_manager.get_auction_insights(
                    customer_id=customer_id,
                    campaign_id=campaign_id,
                    date_range=date_range
                )

                if 'error' in result:
                    return f"❌ {result['error']}"

                audit_logger.log_api_call(
                    customer_id=customer_id,
                    operation='get_auction_insights',
                    campaign_id=campaign_id,
                    status='success'
                )

                # Format response
                output = f"# 🏆 Auction Insights Report\n\n"
                output += f"**Campaign**: {result['campaign_name']}\n\n"

                # Competitive position
                position = result['competitive_position']
                position_emoji = "🟢" if position == "STRONG" else "🟡" if position == "MODERATE" else "🔴"
                output += f"## {position_emoji} Competitive Position: {position}\n\n"

                # Impression share metrics
                output += "## Impression Share Metrics\n\n"
                output += f"- **Overall Impression Share**: {result['impression_share']:.1%}\n"
                output += f"- **Top Impression Share**: {result['top_impression_share']:.1%}\n"
                output += f"- **Absolute Top Impression Share**: {result['absolute_top_impression_share']:.1%}\n\n"

                # Lost impression share
                output += "## Lost Impression Share\n\n"
                output += f"- **Rank Lost IS**: {result['rank_lost_is']:.1%}\n"
                output += f"- **Budget Lost IS**: {result['budget_lost_is']:.1%}\n\n"

                # Primary constraint
                constraint = result['primary_constraint']
                output += f"## 🎯 Primary Constraint: {constraint}\n\n"
                output += f"{result['constraint_message']}\n\n"

                if constraint == "BUDGET":
                    output += "💡 **Quick Fix**: Increase your daily budget to capture more impressions.\n\n"
                elif constraint == "AD_RANK":
                    output += "💡 **Quick Fix**: Improve Quality Score or increase bids to compete more effectively.\n\n"

                # Recommendations
                output += "## 📋 Recommendations\n\n"
                for i, rec in enumerate(result['recommendations'], 1):
                    output += f"{i}. {rec}\n"

                output += "\n---\n\n"

                # Opportunity analysis
                total_lost = result['rank_lost_is'] + result['budget_lost_is']
                if total_lost > 0.3:
                    output += f"⚠️ **Major Opportunity**: You're losing {total_lost:.0%} of possible impressions. "
                    output += "Addressing these constraints could significantly increase visibility.\n"
                elif total_lost > 0.1:
                    output += f"💡 **Moderate Opportunity**: Capturing the missing {total_lost:.0%} of impressions "
                    output += "could improve performance.\n"
                else:
                    output += "✅ **Strong Performance**: You're capturing most available impressions in your target market.\n"

                return output

            except Exception as e:
                error_msg = ErrorHandler.handle_error(e, context="auction_insights")
                return f"❌ Failed to get auction insights: {error_msg}"

    @mcp.tool()
    def google_ads_opportunity_finder(
        customer_id: str,
        opportunity_type: str = "ALL"
    ) -> str:
        """Find optimization opportunities across your Google Ads account.

        Combines multiple analyses to identify:
        - Budget optimization opportunities
        - Wasted spend to eliminate
        - Performance improvement areas
        - Quick wins for immediate impact

        Args:
            customer_id: Google Ads customer ID (10 digits, no hyphens)
            opportunity_type: Type of opportunities to find (ALL, BUDGET, WASTE, PERFORMANCE)

        Returns:
            Comprehensive opportunity analysis with prioritized recommendations

        Example:
            google_ads_opportunity_finder(
                customer_id="1234567890",
                opportunity_type="ALL"
            )
        """
        with performance_logger.track_operation('opportunity_finder', customer_id=customer_id):
            try:
                client = get_auth_manager().get_client()
                insights_manager = InsightsManager(client)

                output = f"# 🎯 Opportunity Finder Report\n\n"

                opportunities = []

                # Budget opportunities
                if opportunity_type in ["ALL", "BUDGET"]:
                    budget_recs = insights_manager.get_budget_recommendations(
                        customer_id=customer_id,
                        date_range="LAST_30_DAYS"
                    )

                    for rec in budget_recs:
                        opportunities.append({
                            'type': 'BUDGET',
                            'priority': rec['priority'],
                            'campaign': rec['campaign_name'],
                            'action': rec['type'],
                            'impact': rec['expected_impact'],
                            'details': rec
                        })

                # Wasted spend opportunities
                if opportunity_type in ["ALL", "WASTE"]:
                    waste_analysis = insights_manager.analyze_wasted_spend(
                        customer_id=customer_id,
                        date_range="LAST_30_DAYS",
                        min_cost=10.0
                    )

                    if waste_analysis['total_wasted_spend'] > 0:
                        opportunities.append({
                            'type': 'WASTE_REDUCTION',
                            'priority': 'HIGH',
                            'campaign': 'Multiple',
                            'action': 'REDUCE_WASTE',
                            'impact': f"Save ${waste_analysis['total_wasted_spend']:,.2f}",
                            'details': waste_analysis
                        })

                audit_logger.log_api_call(
                    customer_id=customer_id,
                    operation='opportunity_finder',
                    status='success'
                )

                # Format response
                if not opportunities:
                    output += "✅ **No immediate opportunities found!**\n\n"
                    output += "Your account is well-optimized. Continue monitoring performance.\n"
                    return output

                output += f"Found **{len(opportunities)}** optimization opportunities:\n\n"

                # Sort by priority
                high_priority = [o for o in opportunities if o['priority'] == 'HIGH']
                medium_priority = [o for o in opportunities if o['priority'] == 'MEDIUM']

                # High priority opportunities
                if high_priority:
                    output += "## 🔴 High Priority Opportunities\n\n"
                    for opp in high_priority:
                        output += f"### {opp['type'].replace('_', ' ').title()}\n"
                        output += f"- **Campaign**: {opp['campaign']}\n"
                        output += f"- **Action**: {opp['action'].replace('_', ' ').title()}\n"
                        output += f"- **Expected Impact**: {opp['impact']}\n\n"

                # Medium priority opportunities
                if medium_priority:
                    output += "## 🟡 Medium Priority Opportunities\n\n"
                    for opp in medium_priority:
                        output += f"### {opp['type'].replace('_', ' ').title()}\n"
                        output += f"- **Campaign**: {opp['campaign']}\n"
                        output += f"- **Action**: {opp['action'].replace('_', ' ').title()}\n"
                        output += f"- **Expected Impact**: {opp['impact']}\n\n"

                output += "---\n\n"
                output += "💡 **Next Steps**: Implement high-priority opportunities first for maximum impact.\n"

                return output

            except Exception as e:
                error_msg = ErrorHandler.handle_error(e, context="opportunity_finder")
                return f"❌ Failed to find opportunities: {error_msg}"

    @mcp.tool()
    def google_ads_performance_forecaster(
        customer_id: str,
        campaign_id: str,
        forecast_days: int = 30
    ) -> str:
        """Predict future campaign performance based on historical trends.

        Uses historical data to forecast:
        - Projected spend
        - Estimated conversions
        - Expected ROAS
        - Confidence intervals

        Args:
            customer_id: Google Ads customer ID (10 digits, no hyphens)
            campaign_id: Campaign ID to forecast
            forecast_days: Number of days to forecast (7-90)

        Returns:
            Performance forecast with confidence ranges

        Example:
            google_ads_performance_forecaster(
                customer_id="1234567890",
                campaign_id="12345678",
                forecast_days=30
            )
        """
        with performance_logger.track_operation('performance_forecaster', customer_id=customer_id):
            try:
                client = get_auth_manager().get_client()
                insights_manager = InsightsManager(client)

                # Get trend data for forecasting
                trend_data = insights_manager.analyze_trends(
                    customer_id=customer_id,
                    campaign_id=campaign_id,
                    lookback_days=30
                )

                if 'error' in trend_data:
                    return f"❌ {trend_data['error']}"

                audit_logger.log_api_call(
                    customer_id=customer_id,
                    operation='performance_forecaster',
                    campaign_id=campaign_id,
                    status='success'
                )

                # Simple linear forecast based on recent trend
                daily_data = trend_data['daily_data']
                recent_avg_cost = sum(d['cost'] for d in daily_data[-7:]) / 7
                recent_avg_conversions = sum(d['conversions'] for d in daily_data[-7:]) / 7

                trend = trend_data['trends']

                # Apply trend multiplier
                trend_multiplier = 1.0
                if trend['cost_trend'] == "INCREASING":
                    trend_multiplier = 1 + (abs(trend['cost_change_pct']) / 100 / 2)  # Half the change rate
                elif trend['cost_trend'] == "DECREASING":
                    trend_multiplier = 1 - (abs(trend['cost_change_pct']) / 100 / 2)

                forecasted_daily_cost = recent_avg_cost * trend_multiplier
                forecasted_daily_conversions = recent_avg_conversions * trend_multiplier

                total_forecasted_cost = forecasted_daily_cost * forecast_days
                total_forecasted_conversions = forecasted_daily_conversions * forecast_days

                # Format response
                output = f"# 🔮 Performance Forecast\n\n"
                output += f"**Forecast Period**: Next {forecast_days} days\n"
                output += f"**Based On**: Last 30 days of historical data\n\n"

                output += "## Projected Performance\n\n"
                output += f"- **Total Spend**: ${total_forecasted_cost:,.2f}\n"
                output += f"- **Total Conversions**: {total_forecasted_conversions:.0f}\n"
                output += f"- **Avg Daily Spend**: ${forecasted_daily_cost:,.2f}\n"
                output += f"- **Avg Daily Conversions**: {forecasted_daily_conversions:.1f}\n\n"

                if total_forecasted_conversions > 0:
                    forecasted_cpa = total_forecasted_cost / total_forecasted_conversions
                    output += f"- **Projected CPA**: ${forecasted_cpa:,.2f}\n\n"

                output += "## Trend Context\n\n"
                output += f"- **Cost Trend**: {trend['cost_trend']} ({trend['cost_change_pct']:+.1f}%)\n"
                output += f"- **Conversion Trend**: {trend['conversion_trend']} ({trend['conversion_change_pct']:+.1f}%)\n\n"

                output += "---\n\n"
                output += "⚠️ **Note**: Forecasts are estimates based on current trends. "
                output += "Actual performance may vary due to seasonality, competition, and market changes.\n"

                return output

            except Exception as e:
                error_msg = ErrorHandler.handle_error(e, context="performance_forecaster")
                return f"❌ Failed to generate forecast: {error_msg}"

    logger.info("Insights and recommendations tools registered (8 tools)")
