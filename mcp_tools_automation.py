"""
MCP Tools - Automated Rules & Optimization

Provides 10 MCP tools for automation and optimization:

Optimization Recommendations (8 tools):
1. google_ads_get_recommendations - Get all optimization recommendations
2. google_ads_apply_recommendation - Apply single recommendation
3. google_ads_dismiss_recommendation - Dismiss single recommendation
4. google_ads_bulk_apply_recommendations - Apply multiple recommendations
5. google_ads_bulk_dismiss_recommendations - Dismiss multiple recommendations
6. google_ads_get_optimization_score - Get account optimization score (0-100%)
7. google_ads_get_recommendation_insights - Aggregate recommendation impact
8. google_ads_apply_recommendations_by_type - Apply all recommendations of specific type

Additional Tools (2 tools):
9. google_ads_get_recommendation_history - View recommendation application history
10. google_ads_auto_apply_safe_recommendations - Auto-apply low-risk recommendations

Note: Google Ads API does not support creating custom automated rules via API.
Rules must be created through the Google Ads UI. However, recommendations
provide similar automation capabilities through Google's AI.
"""

from typing import Optional, List, Dict, Any
from automation_manager import (
    AutomationManager,
    RecommendationType
)
from auth_manager import get_auth_manager
from error_handler import ErrorHandler
from logger import performance_logger, audit_logger
from cache_manager import get_cache_manager, ResourceType
import json


def register_automation_tools(mcp):
    """Register all automation and optimization tools with the MCP server.

    Args:
        mcp: FastMCP server instance
    """

    # ============================================================================
    # Optimization Recommendations
    # ============================================================================

    @mcp.tool()
    def google_ads_get_recommendations(
        customer_id: str,
        recommendation_types: Optional[List[str]] = None,
        campaign_id: Optional[str] = None,
        response_format: str = "markdown"
    ) -> str:
        """
        Get optimization recommendations from Google Ads.

        Google's AI analyzes your account and suggests specific optimizations
        to improve performance. Recommendations can include keyword additions,
        budget increases, bidding strategy changes, and more.

        Args:
            customer_id: Customer ID (without hyphens)
            recommendation_types: Optional list of recommendation types to filter
                (e.g., ["KEYWORD", "CAMPAIGN_BUDGET", "TARGET_CPA_OPT_IN"])
            campaign_id: Optional campaign ID to filter recommendations
            response_format: Output format (markdown or json)

        Returns:
            List of recommendations with projected impact

        Example:
            google_ads_get_recommendations(
                customer_id="1234567890",
                recommendation_types=["KEYWORD", "CAMPAIGN_BUDGET"]
            )

        Common Recommendation Types:
        - KEYWORD: Add new keywords
        - CAMPAIGN_BUDGET: Increase budget
        - TARGET_CPA_OPT_IN: Switch to Target CPA bidding
        - TARGET_ROAS_OPT_IN: Switch to Target ROAS bidding
        - RESPONSIVE_SEARCH_AD: Create responsive search ads
        - KEYWORD_MATCH_TYPE: Change keyword match types
        - USE_BROAD_MATCH_KEYWORD: Use broad match keywords
        """
        with performance_logger.track_operation('get_recommendations', customer_id=customer_id):
            try:
                client = get_auth_manager().get_client()
                automation_manager = AutomationManager(client)

                # Parse recommendation types
                rec_types = None
                if recommendation_types:
                    rec_types = []
                    for rt in recommendation_types:
                        try:
                            rec_types.append(RecommendationType[rt.upper()])
                        except KeyError:
                            return f"❌ Invalid recommendation type: {rt}"

                recommendations = automation_manager.get_recommendations(
                    customer_id,
                    recommendation_types=rec_types,
                    campaign_id=campaign_id
                )

                # Audit log
                audit_logger.log_api_call(
                    customer_id=customer_id,
                    operation="get_recommendations",
                    resource_type="recommendation",
                    action="read",
                    result="success",
                    details={'count': len(recommendations)}
                )

                if not recommendations:
                    return "No recommendations available. Your account is well-optimized!"

                # Format response
                if response_format.lower() == "json":
                    return json.dumps(recommendations, indent=2)

                # Markdown format
                output = f"# Optimization Recommendations\n\n"
                output += f"**Total Recommendations**: {len(recommendations)}\n\n"

                for i, rec in enumerate(recommendations, 1):
                    output += f"## {i}. {rec['type'].replace('_', ' ').title()}\n\n"

                    if rec.get('campaign'):
                        output += f"**Campaign ID**: {rec['campaign']}\n"

                    # Type-specific details
                    if rec['type'] == 'KEYWORD' and 'keyword' in rec:
                        kw = rec['keyword']
                        output += f"**Keyword**: {kw['text']}\n"
                        output += f"**Match Type**: {kw['match_type']}\n"
                        output += f"**Recommended CPC Bid**: ${kw['recommended_cpc_bid']:.2f}\n"

                    elif rec['type'] == 'CAMPAIGN_BUDGET' and 'budget' in rec:
                        budget = rec['budget']
                        output += f"**Current Budget**: ${budget['current']:.2f}/day\n"
                        output += f"**Recommended Budget**: ${budget['recommended']:.2f}/day\n"
                        output += f"**Increase**: ${budget['increase']:.2f}/day ({budget['increase'] / budget['current'] * 100:.0f}%)\n"

                    elif rec['type'] == 'TARGET_CPA_OPT_IN' and 'target_cpa' in rec:
                        output += f"**Recommended Target CPA**: ${rec['target_cpa']['recommended']:.2f}\n"

                    elif rec['type'] == 'TARGET_ROAS_OPT_IN' and 'target_roas' in rec:
                        output += f"**Recommended Target ROAS**: {rec['target_roas']['recommended']:.2f}x\n"

                    elif rec['type'] == 'KEYWORD_MATCH_TYPE' and 'keyword_match_type' in rec:
                        kmt = rec['keyword_match_type']
                        output += f"**Keyword**: {kmt['keyword']}\n"
                        output += f"**Recommended Match Type**: {kmt['recommended_match_type']}\n"

                    # Impact metrics
                    if rec.get('impact'):
                        impact = rec['impact']
                        output += f"\n**Projected Impact**:\n"
                        if impact['impressions'] > 0:
                            output += f"- Additional Impressions: {impact['impressions']:,}\n"
                        if impact['clicks'] > 0:
                            output += f"- Additional Clicks: {impact['clicks']:,}\n"
                        if impact['conversions'] > 0:
                            output += f"- Additional Conversions: {impact['conversions']:.1f}\n"
                        if impact['cost'] > 0:
                            output += f"- Additional Cost: ${impact['cost']:,.2f}\n"

                    output += f"\n**Resource Name**: `{rec['resource_name']}`\n"
                    output += f"\nUse `google_ads_apply_recommendation` to apply this recommendation.\n\n"
                    output += "---\n\n"

                return output

            except Exception as e:
                error_msg = ErrorHandler.handle_error(e, context="get_recommendations")
                return f"❌ Failed to get recommendations: {error_msg}"

    @mcp.tool()
    def google_ads_apply_recommendation(
        customer_id: str,
        recommendation_resource_name: str
    ) -> str:
        """
        Apply a single optimization recommendation.

        This will automatically implement the suggested optimization. For example:
        - KEYWORD recommendations will add the keyword to your account
        - CAMPAIGN_BUDGET recommendations will increase the budget
        - Bidding strategy recommendations will change the bidding strategy

        Args:
            customer_id: Customer ID (without hyphens)
            recommendation_resource_name: Resource name of the recommendation to apply
                (obtained from google_ads_get_recommendations)

        Returns:
            Success message confirming application

        Example:
            google_ads_apply_recommendation(
                customer_id="1234567890",
                recommendation_resource_name="customers/1234567890/recommendations/12345"
            )

        Warning: This will make changes to your account. Review the recommendation
        details carefully before applying.
        """
        with performance_logger.track_operation('apply_recommendation', customer_id=customer_id):
            try:
                client = get_auth_manager().get_client()
                automation_manager = AutomationManager(client)

                result = automation_manager.apply_recommendation(
                    customer_id,
                    recommendation_resource_name
                )

                # Audit log
                audit_logger.log_api_call(
                    customer_id=customer_id,
                    operation="apply_recommendation",
                    resource_type="recommendation",
                    action="update",
                    result="success",
                    details={'resource_name': recommendation_resource_name}
                )

                # Invalidate all caches (recommendation could affect any resource)
                get_cache_manager().invalidate(customer_id, ResourceType.CAMPAIGN)
                get_cache_manager().invalidate(customer_id, ResourceType.AD_GROUP)
                get_cache_manager().invalidate(customer_id, ResourceType.KEYWORD)

                output = f"✅ Recommendation applied successfully!\n\n"
                output += f"**Resource Name**: {result['resource_name']}\n"
                output += f"**Status**: {result['status']}\n\n"
                output += f"The optimization has been implemented in your account.\n"
                output += f"Monitor performance over the next few days to see the impact.\n"

                return output

            except Exception as e:
                error_msg = ErrorHandler.handle_error(e, context="apply_recommendation")
                return f"❌ Failed to apply recommendation: {error_msg}"

    @mcp.tool()
    def google_ads_dismiss_recommendation(
        customer_id: str,
        recommendation_resource_name: str
    ) -> str:
        """
        Dismiss a recommendation without applying it.

        Use this when you don't want to apply a recommendation and want to remove
        it from your recommendations list.

        Args:
            customer_id: Customer ID (without hyphens)
            recommendation_resource_name: Resource name of the recommendation to dismiss

        Returns:
            Success message confirming dismissal

        Example:
            google_ads_dismiss_recommendation(
                customer_id="1234567890",
                recommendation_resource_name="customers/1234567890/recommendations/12345"
            )
        """
        with performance_logger.track_operation('dismiss_recommendation', customer_id=customer_id):
            try:
                client = get_auth_manager().get_client()
                automation_manager = AutomationManager(client)

                result = automation_manager.dismiss_recommendation(
                    customer_id,
                    recommendation_resource_name
                )

                # Audit log
                audit_logger.log_api_call(
                    customer_id=customer_id,
                    operation="dismiss_recommendation",
                    resource_type="recommendation",
                    action="delete",
                    result="success",
                    details={'resource_name': recommendation_resource_name}
                )

                output = f"✅ Recommendation dismissed successfully!\n\n"
                output += f"**Resource Name**: {result['resource_name']}\n"
                output += f"**Status**: {result['status']}\n\n"
                output += f"This recommendation will no longer appear in your list.\n"

                return output

            except Exception as e:
                error_msg = ErrorHandler.handle_error(e, context="dismiss_recommendation")
                return f"❌ Failed to dismiss recommendation: {error_msg}"

    @mcp.tool()
    def google_ads_bulk_apply_recommendations(
        customer_id: str,
        recommendation_resource_names: List[str]
    ) -> str:
        """
        Apply multiple recommendations at once.

        This is useful for applying several recommendations efficiently in a single operation.

        Args:
            customer_id: Customer ID (without hyphens)
            recommendation_resource_names: List of recommendation resource names to apply

        Returns:
            Success message with count of applied recommendations

        Example:
            google_ads_bulk_apply_recommendations(
                customer_id="1234567890",
                recommendation_resource_names=[
                    "customers/1234567890/recommendations/12345",
                    "customers/1234567890/recommendations/12346",
                    "customers/1234567890/recommendations/12347"
                ]
            )

        Warning: This will make changes to your account. Review all recommendations
        carefully before applying in bulk.
        """
        with performance_logger.track_operation('bulk_apply_recommendations', customer_id=customer_id):
            try:
                client = get_auth_manager().get_client()
                automation_manager = AutomationManager(client)

                result = automation_manager.bulk_apply_recommendations(
                    customer_id,
                    recommendation_resource_names
                )

                # Audit log
                audit_logger.log_api_call(
                    customer_id=customer_id,
                    operation="bulk_apply_recommendations",
                    resource_type="recommendation",
                    action="update",
                    result="success",
                    details={'count': result['total_applied']}
                )

                # Invalidate all caches
                get_cache_manager().invalidate(customer_id, ResourceType.CAMPAIGN)
                get_cache_manager().invalidate(customer_id, ResourceType.AD_GROUP)
                get_cache_manager().invalidate(customer_id, ResourceType.KEYWORD)

                output = f"✅ Bulk recommendations applied successfully!\n\n"
                output += f"**Total Applied**: {result['total_applied']}\n\n"
                output += f"All optimizations have been implemented in your account.\n"
                output += f"Monitor performance over the next few days to see the impact.\n"

                return output

            except Exception as e:
                error_msg = ErrorHandler.handle_error(e, context="bulk_apply_recommendations")
                return f"❌ Failed to apply recommendations: {error_msg}"

    @mcp.tool()
    def google_ads_bulk_dismiss_recommendations(
        customer_id: str,
        recommendation_resource_names: List[str]
    ) -> str:
        """
        Dismiss multiple recommendations at once.

        Args:
            customer_id: Customer ID (without hyphens)
            recommendation_resource_names: List of recommendation resource names to dismiss

        Returns:
            Success message with count of dismissed recommendations

        Example:
            google_ads_bulk_dismiss_recommendations(
                customer_id="1234567890",
                recommendation_resource_names=[
                    "customers/1234567890/recommendations/12345",
                    "customers/1234567890/recommendations/12346"
                ]
            )
        """
        with performance_logger.track_operation('bulk_dismiss_recommendations', customer_id=customer_id):
            try:
                client = get_auth_manager().get_client()
                automation_manager = AutomationManager(client)

                result = automation_manager.bulk_dismiss_recommendations(
                    customer_id,
                    recommendation_resource_names
                )

                # Audit log
                audit_logger.log_api_call(
                    customer_id=customer_id,
                    operation="bulk_dismiss_recommendations",
                    resource_type="recommendation",
                    action="delete",
                    result="success",
                    details={'count': result['total_dismissed']}
                )

                output = f"✅ Bulk recommendations dismissed successfully!\n\n"
                output += f"**Total Dismissed**: {result['total_dismissed']}\n\n"
                output += f"These recommendations will no longer appear in your list.\n"

                return output

            except Exception as e:
                error_msg = ErrorHandler.handle_error(e, context="bulk_dismiss_recommendations")
                return f"❌ Failed to dismiss recommendations: {error_msg}"

    @mcp.tool()
    def google_ads_get_optimization_score(
        customer_id: str
    ) -> str:
        """
        Get the account's optimization score (0-100%).

        The optimization score represents how well your account is set up to perform.
        A score of 100% means your account is fully optimized based on Google's
        recommendations. Lower scores indicate room for improvement.

        The score is calculated based on:
        - Available recommendations
        - Recommendation priority
        - Potential performance impact

        Args:
            customer_id: Customer ID (without hyphens)

        Returns:
            Optimization score with breakdown by recommendation type

        Example:
            google_ads_get_optimization_score(
                customer_id="1234567890"
            )
        """
        with performance_logger.track_operation('get_optimization_score', customer_id=customer_id):
            try:
                client = get_auth_manager().get_client()
                automation_manager = AutomationManager(client)

                result = automation_manager.get_optimization_score(customer_id)

                if 'error' in result:
                    return f"❌ {result['error']}"

                # Audit log
                audit_logger.log_api_call(
                    customer_id=customer_id,
                    operation="get_optimization_score",
                    resource_type="customer",
                    action="read",
                    result="success",
                    details={'score': result['score_percentage']}
                )

                # Format response
                output = f"# Account Optimization Score\n\n"
                output += f"**Current Score**: {result['score_percentage']:.1f}%\n"
                output += f"**Score Weight**: {result['optimization_score_weight']:.2f}\n"
                output += f"**Total Recommendations**: {result['total_recommendations']}\n\n"

                # Score interpretation
                score = result['score_percentage']
                if score >= 90:
                    output += f"**Status**: ✅ Excellent - Your account is well-optimized\n"
                elif score >= 70:
                    output += f"**Status**: ✔️ Good - Minor improvements available\n"
                elif score >= 50:
                    output += f"**Status**: ⚠️ Fair - Several optimization opportunities\n"
                else:
                    output += f"**Status**: ❌ Needs Improvement - Significant optimization needed\n"

                output += f"\n## Recommendations by Type\n\n"

                if result['recommendation_counts']:
                    for rec_type, count in result['recommendation_counts'].items():
                        output += f"- **{rec_type.replace('_', ' ').title()}**: {count}\n"
                else:
                    output += f"No recommendations available.\n"

                output += f"\n**Next Steps**:\n"
                output += f"1. Review recommendations with `google_ads_get_recommendations`\n"
                output += f"2. Apply high-impact recommendations first\n"
                output += f"3. Monitor score improvement weekly\n"
                output += f"4. Aim for 80%+ optimization score\n"

                return output

            except Exception as e:
                error_msg = ErrorHandler.handle_error(e, context="get_optimization_score")
                return f"❌ Failed to get optimization score: {error_msg}"

    @mcp.tool()
    def google_ads_get_recommendation_insights(
        customer_id: str,
        campaign_id: Optional[str] = None
    ) -> str:
        """
        Get aggregate insights about recommendations and their potential impact.

        This provides a high-level summary of all recommendations, grouped by type,
        with total projected impact across all recommendations.

        Args:
            customer_id: Customer ID (without hyphens)
            campaign_id: Optional campaign ID to filter

        Returns:
            Aggregate recommendation insights with total potential impact

        Example:
            google_ads_get_recommendation_insights(
                customer_id="1234567890"
            )
        """
        with performance_logger.track_operation('get_recommendation_insights', customer_id=customer_id):
            try:
                client = get_auth_manager().get_client()
                automation_manager = AutomationManager(client)

                result = automation_manager.get_recommendation_insights(customer_id, campaign_id)

                if result['total_recommendations'] == 0:
                    return result.get('message', 'No recommendations available')

                # Audit log
                audit_logger.log_api_call(
                    customer_id=customer_id,
                    operation="get_recommendation_insights",
                    resource_type="recommendation",
                    action="read",
                    result="success",
                    details={'count': result['total_recommendations']}
                )

                # Format response
                output = f"# Recommendation Insights\n\n"
                output += f"**Total Recommendations**: {result['total_recommendations']}\n\n"

                # Total potential impact
                impact = result['total_potential_impact']
                output += f"## Total Potential Impact\n\n"
                if impact['impressions'] > 0:
                    output += f"- **Additional Impressions**: {impact['impressions']:,}\n"
                if impact['clicks'] > 0:
                    output += f"- **Additional Clicks**: {impact['clicks']:,}\n"
                if impact['conversions'] > 0:
                    output += f"- **Additional Conversions**: {impact['conversions']:,.1f}\n"
                if impact['cost'] > 0:
                    output += f"- **Additional Cost**: ${impact['cost']:,.2f}\n"

                # By type
                output += f"\n## Recommendations by Type\n\n"

                for rec_type, data in result['by_type'].items():
                    output += f"### {rec_type.replace('_', ' ').title()} ({data['count']} recommendations)\n\n"

                    type_impact = data['impact']
                    if any(type_impact.values()):
                        output += f"**Potential Impact**:\n"
                        if type_impact['impressions'] > 0:
                            output += f"- Impressions: {type_impact['impressions']:,}\n"
                        if type_impact['clicks'] > 0:
                            output += f"- Clicks: {type_impact['clicks']:,}\n"
                        if type_impact['conversions'] > 0:
                            output += f"- Conversions: {type_impact['conversions']:,.1f}\n"
                        if type_impact['cost'] > 0:
                            output += f"- Cost: ${type_impact['cost']:,.2f}\n"
                    output += "\n"

                return output

            except Exception as e:
                error_msg = ErrorHandler.handle_error(e, context="get_recommendation_insights")
                return f"❌ Failed to get recommendation insights: {error_msg}"

    @mcp.tool()
    def google_ads_apply_recommendations_by_type(
        customer_id: str,
        recommendation_type: str,
        max_to_apply: Optional[int] = None
    ) -> str:
        """
        Apply all recommendations of a specific type.

        This is useful for bulk-applying all recommendations of a certain category,
        such as all KEYWORD recommendations or all CAMPAIGN_BUDGET recommendations.

        Args:
            customer_id: Customer ID (without hyphens)
            recommendation_type: Type of recommendations to apply
                (KEYWORD, CAMPAIGN_BUDGET, TARGET_CPA_OPT_IN, etc.)
            max_to_apply: Optional maximum number of recommendations to apply

        Returns:
            Success message with count of applied recommendations

        Example:
            google_ads_apply_recommendations_by_type(
                customer_id="1234567890",
                recommendation_type="KEYWORD",
                max_to_apply=10
            )

        Common Types:
        - KEYWORD: Add suggested keywords
        - CAMPAIGN_BUDGET: Increase budgets
        - TARGET_CPA_OPT_IN: Enable Target CPA bidding
        - TARGET_ROAS_OPT_IN: Enable Target ROAS bidding
        - RESPONSIVE_SEARCH_AD: Create RSAs

        Warning: This will make changes to your account. Review recommendations
        of this type carefully before bulk applying.
        """
        with performance_logger.track_operation('apply_recommendations_by_type', customer_id=customer_id):
            try:
                client = get_auth_manager().get_client()
                automation_manager = AutomationManager(client)

                # Validate recommendation type
                try:
                    rec_type = RecommendationType[recommendation_type.upper()]
                except KeyError:
                    valid_types = [t.value for t in RecommendationType]
                    return f"❌ Invalid recommendation type '{recommendation_type}'. Valid types: {', '.join(valid_types[:10])}..."

                result = automation_manager.apply_recommendations_by_type(
                    customer_id,
                    rec_type,
                    max_to_apply
                )

                if result['total_applied'] == 0:
                    return result.get('message', f'No {recommendation_type} recommendations found')

                # Audit log
                audit_logger.log_api_call(
                    customer_id=customer_id,
                    operation="apply_recommendations_by_type",
                    resource_type="recommendation",
                    action="update",
                    result="success",
                    details={'type': recommendation_type, 'count': result['total_applied']}
                )

                # Invalidate all caches
                get_cache_manager().invalidate(customer_id, ResourceType.CAMPAIGN)
                get_cache_manager().invalidate(customer_id, ResourceType.AD_GROUP)
                get_cache_manager().invalidate(customer_id, ResourceType.KEYWORD)

                output = f"✅ {recommendation_type.replace('_', ' ').title()} recommendations applied!\n\n"
                output += f"**Total Applied**: {result['total_applied']}\n"
                output += f"**Type**: {recommendation_type}\n\n"
                output += f"All {recommendation_type.lower()} optimizations have been implemented.\n"
                output += f"Monitor performance over the next few days to see the impact.\n"

                return output

            except Exception as e:
                error_msg = ErrorHandler.handle_error(e, context="apply_recommendations_by_type")
                return f"❌ Failed to apply recommendations: {error_msg}"

    @mcp.tool()
    def google_ads_get_recommendation_history(
        customer_id: str,
        start_date: str,
        end_date: str
    ) -> str:
        """
        Get history of applied and dismissed recommendations.

        This shows what recommendations were applied or dismissed in a given time period,
        along with who made the changes.

        Args:
            customer_id: Customer ID (without hyphens)
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            Recommendation change history

        Example:
            google_ads_get_recommendation_history(
                customer_id="1234567890",
                start_date="2025-11-01",
                end_date="2025-12-16"
            )
        """
        with performance_logger.track_operation('get_recommendation_history', customer_id=customer_id):
            try:
                client = get_auth_manager().get_client()
                automation_manager = AutomationManager(client)

                history = automation_manager.get_recommendation_history(
                    customer_id,
                    start_date,
                    end_date
                )

                # Audit log
                audit_logger.log_api_call(
                    customer_id=customer_id,
                    operation="get_recommendation_history",
                    resource_type="recommendation",
                    action="read",
                    result="success",
                    details={'count': len(history)}
                )

                if not history:
                    return f"No recommendation changes found between {start_date} and {end_date}."

                # Format response
                output = f"# Recommendation Change History\n\n"
                output += f"**Period**: {start_date} to {end_date}\n"
                output += f"**Total Changes**: {len(history)}\n\n"

                for i, event in enumerate(history, 1):
                    output += f"## {i}. {event['date_time']}\n\n"
                    output += f"- **User**: {event['user_email']}\n"
                    output += f"- **Client**: {event['client_type']}\n"
                    output += f"- **Resource**: {event['resource_name']}\n"

                    if event['old_type']:
                        output += f"- **Action**: Removed {event['old_type']} recommendation\n"
                    elif event['new_type']:
                        output += f"- **Action**: Applied {event['new_type']} recommendation\n"

                    output += "\n"

                return output

            except Exception as e:
                error_msg = ErrorHandler.handle_error(e, context="get_recommendation_history")
                return f"❌ Failed to get recommendation history: {error_msg}"

    @mcp.tool()
    def google_ads_auto_apply_safe_recommendations(
        customer_id: str,
        dry_run: bool = True
    ) -> str:
        """
        Auto-apply low-risk, high-impact recommendations.

        This tool identifies "safe" recommendations that are unlikely to negatively
        impact performance and applies them automatically. Safe recommendations include:
        - Keyword match type upgrades (exact → phrase → broad)
        - Responsive search ad suggestions
        - Search partners opt-in
        - Optimize ad rotation

        Higher risk recommendations (budget increases, bidding strategy changes) are
        excluded and should be reviewed manually.

        Args:
            customer_id: Customer ID (without hyphens)
            dry_run: If True, shows what would be applied without actually applying (default: True)

        Returns:
            List of recommendations that were (or would be) applied

        Example:
            # Preview what would be applied
            google_ads_auto_apply_safe_recommendations(
                customer_id="1234567890",
                dry_run=True
            )

            # Actually apply the recommendations
            google_ads_auto_apply_safe_recommendations(
                customer_id="1234567890",
                dry_run=False
            )

        Warning: Even "safe" recommendations can impact performance. Use dry_run=True
        first to review what would be applied.
        """
        with performance_logger.track_operation('auto_apply_safe_recommendations', customer_id=customer_id):
            try:
                client = get_auth_manager().get_client()
                automation_manager = AutomationManager(client)

                # Define safe recommendation types
                safe_types = [
                    RecommendationType.RESPONSIVE_SEARCH_AD,
                    RecommendationType.SEARCH_PARTNERS_OPT_IN,
                    RecommendationType.OPTIMIZE_AD_ROTATION,
                    RecommendationType.RESPONSIVE_SEARCH_AD_ASSET,
                    RecommendationType.USE_BROAD_MATCH_KEYWORD
                ]

                # Get all safe recommendations
                all_safe_recs = []
                for rec_type in safe_types:
                    recs = automation_manager.get_recommendations(
                        customer_id,
                        recommendation_types=[rec_type]
                    )
                    all_safe_recs.extend(recs)

                if not all_safe_recs:
                    return "No safe recommendations available to auto-apply."

                # Format response
                output = f"# Auto-Apply Safe Recommendations\n\n"
                output += f"**Mode**: {'DRY RUN (Preview Only)' if dry_run else 'LIVE (Applying Changes)'}\n"
                output += f"**Total Safe Recommendations**: {len(all_safe_recs)}\n\n"

                if dry_run:
                    output += f"## Recommendations That Would Be Applied\n\n"

                    for i, rec in enumerate(all_safe_recs, 1):
                        output += f"{i}. **{rec['type'].replace('_', ' ').title()}**\n"
                        if rec.get('campaign'):
                            output += f"   - Campaign: {rec['campaign']}\n"
                        output += f"   - Resource: `{rec['resource_name']}`\n\n"

                    output += f"\n**Next Step**: Run with `dry_run=False` to apply these recommendations.\n"

                else:
                    # Apply all safe recommendations
                    resource_names = [rec['resource_name'] for rec in all_safe_recs]

                    result = automation_manager.bulk_apply_recommendations(
                        customer_id,
                        resource_names
                    )

                    # Audit log
                    audit_logger.log_api_call(
                        customer_id=customer_id,
                        operation="auto_apply_safe_recommendations",
                        resource_type="recommendation",
                        action="update",
                        result="success",
                        details={'count': result['total_applied']}
                    )

                    # Invalidate caches
                    get_cache_manager().invalidate(customer_id, ResourceType.CAMPAIGN)
                    get_cache_manager().invalidate(customer_id, ResourceType.AD_GROUP)
                    get_cache_manager().invalidate(customer_id, ResourceType.KEYWORD)

                    output += f"## Applied Recommendations\n\n"
                    output += f"**Total Applied**: {result['total_applied']}\n\n"

                    for i, rec in enumerate(all_safe_recs, 1):
                        output += f"{i}. ✅ {rec['type'].replace('_', ' ').title()}\n"

                    output += f"\nAll safe optimizations have been implemented.\n"
                    output += f"Monitor performance over the next few days to see the impact.\n"

                return output

            except Exception as e:
                error_msg = ErrorHandler.handle_error(e, context="auto_apply_safe_recommendations")
                return f"❌ Failed to auto-apply recommendations: {error_msg}"
