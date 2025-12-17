"""
MCP Tools - Shopping & Performance Max Campaigns

Tools for Google Shopping campaigns and Performance Max campaigns.

Shopping Tools:
1. google_ads_create_shopping_campaign - Create shopping campaigns
2. google_ads_create_product_group - Product partition management
3. google_ads_shopping_feed_status - Check Merchant Center feed
4. google_ads_shopping_performance - Shopping-specific metrics

Performance Max Tools:
5. google_ads_create_performance_max_campaign - Create PMax campaigns
6. google_ads_create_asset_group - Asset group management
7. google_ads_upload_pmax_assets - Upload text assets
8. google_ads_set_audience_signals - Configure audience signals
9. google_ads_pmax_insights - Performance Max insights
"""

from typing import List, Optional
from shopping_pmax_manager import (
    ShoppingPMaxManager,
    ShoppingCampaignConfig,
    ShoppingCampaignPriority,
    PerformanceMaxCampaignConfig
)
from auth_manager import get_auth_manager
from error_handler import ErrorHandler
from logger import get_logger, get_performance_logger, get_audit_logger
import json

logger = get_logger(__name__)
performance_logger = get_performance_logger()
audit_logger = get_audit_logger()


def register_shopping_pmax_tools(mcp):
    """Register all Shopping and Performance Max MCP tools."""

    @mcp.tool()
    def google_ads_create_shopping_campaign(
        customer_id: str,
        campaign_name: str,
        merchant_center_id: str,
        budget_amount: float,
        priority: str = "LOW",
        target_roas: Optional[float] = None,
        enable_local: bool = False
    ) -> str:
        """Create a Google Shopping campaign.

        Shopping campaigns promote products from your Google Merchant Center account.
        They show product ads with images, prices, and store names on Google Search
        and Google Shopping.

        Args:
            customer_id: Google Ads customer ID (10 digits, no hyphens)
            campaign_name: Name for the shopping campaign
            merchant_center_id: Your Merchant Center account ID
            budget_amount: Daily budget in currency units (e.g., 50.00 for $50/day)
            priority: Campaign priority (LOW, MEDIUM, HIGH) - affects bidding when
                     multiple campaigns target the same product
            target_roas: Optional target return on ad spend (e.g., 3.0 for 300% ROAS)
            enable_local: Enable local inventory ads (requires local product feed)

        Returns:
            Shopping campaign creation result

        Example:
            google_ads_create_shopping_campaign(
                customer_id="1234567890",
                campaign_name="Holiday Shopping Campaign",
                merchant_center_id="123456789",
                budget_amount=100.00,
                priority="HIGH",
                target_roas=3.5
            )
        """
        with performance_logger.track_operation('create_shopping_campaign', customer_id=customer_id):
            try:
                client = get_auth_manager().get_client()
                shopping_manager = ShoppingPMaxManager(client)

                # Validate priority
                try:
                    priority_enum = ShoppingCampaignPriority[priority.upper()]
                except KeyError:
                    return f"❌ Invalid priority. Must be: LOW, MEDIUM, or HIGH"

                config = ShoppingCampaignConfig(
                    name=campaign_name,
                    merchant_center_id=merchant_center_id,
                    budget_amount=budget_amount,
                    priority=priority_enum,
                    target_roas=target_roas,
                    enable_local=enable_local
                )

                result = shopping_manager.create_shopping_campaign(customer_id, config)

                audit_logger.log_api_call(
                    customer_id=customer_id,
                    operation='create_shopping_campaign',
                    campaign_id=result['campaign_id'],
                    status='success'
                )

                output = f"# 🛍️ Shopping Campaign Created\n\n"
                output += f"**Campaign Name**: {result['campaign_name']}\n"
                output += f"**Campaign ID**: {result['campaign_id']}\n"
                output += f"**Merchant Center ID**: {result['merchant_center_id']}\n"
                output += f"**Priority**: {result['priority']}\n"
                output += f"**Daily Budget**: ${result['budget']:.2f}\n"
                output += f"**Status**: PAUSED (ready for products)\n\n"

                output += "## Next Steps\n\n"
                output += "1. ✅ Shopping campaign created successfully\n"
                output += "2. 📦 Ensure products are approved in Merchant Center\n"
                output += "3. 🎯 Create product groups to organize bidding\n"
                output += "4. 💰 Set bids for product groups\n"
                output += "5. ▶️ Enable campaign when ready\n\n"

                if enable_local:
                    output += "📍 **Local inventory ads enabled** - products from your local stores will show\n\n"

                if target_roas:
                    output += f"🎯 **Target ROAS set to {target_roas:.1f}x** - Google will optimize for this return\n"

                return output

            except Exception as e:
                error_msg = ErrorHandler.handle_error(e, context="create_shopping_campaign")
                return f"❌ Failed to create shopping campaign: {error_msg}"

    @mcp.tool()
    def google_ads_create_product_group(
        customer_id: str,
        ad_group_id: str,
        product_condition: Optional[str] = None,
        product_type: Optional[str] = None,
        is_subdivision: bool = False
    ) -> str:
        """Create a product group (product partition) in a shopping ad group.

        Product groups organize your products and allow different bids for different
        product segments. You can partition by: brand, category, condition, type, etc.

        Args:
            customer_id: Google Ads customer ID (10 digits, no hyphens)
            ad_group_id: Shopping ad group ID
            product_condition: Filter by condition (NEW, USED, REFURBISHED)
            product_type: Filter by product type from your feed
            is_subdivision: True to create subdivision (for further partitioning),
                           False to create bidding unit

        Returns:
            Product group creation result

        Example:
            google_ads_create_product_group(
                customer_id="1234567890",
                ad_group_id="12345678",
                product_condition="NEW",
                is_subdivision=False
            )
        """
        with performance_logger.track_operation('create_product_group', customer_id=customer_id):
            try:
                client = get_auth_manager().get_client()
                shopping_manager = ShoppingPMaxManager(client)

                result = shopping_manager.create_product_group(
                    customer_id=customer_id,
                    ad_group_id=ad_group_id,
                    product_condition=product_condition,
                    product_type=product_type,
                    is_subdivision=is_subdivision
                )

                audit_logger.log_api_call(
                    customer_id=customer_id,
                    operation='create_product_group',
                    ad_group_id=ad_group_id,
                    status='success'
                )

                output = f"# 📦 Product Group Created\n\n"
                output += f"**Ad Group ID**: {result['ad_group_id']}\n"
                output += f"**Criterion ID**: {result['criterion_id']}\n"
                output += f"**Type**: {result['type'].upper()}\n\n"

                if product_condition:
                    output += f"**Condition Filter**: {product_condition}\n"
                if product_type:
                    output += f"**Product Type**: {product_type}\n"

                output += "\n"

                if is_subdivision:
                    output += "🔄 **Subdivision created** - you can now create child partitions\n\n"
                    output += "**Next Steps**:\n"
                    output += "- Create child product groups under this subdivision\n"
                    output += "- Further segment by brand, category, or other dimensions\n"
                else:
                    output += "💰 **Bidding unit created** - set a CPC bid for this product group\n\n"
                    output += "**Next Steps**:\n"
                    output += "- Adjust the CPC bid based on product profitability\n"
                    output += "- Monitor performance and optimize bids\n"

                return output

            except Exception as e:
                error_msg = ErrorHandler.handle_error(e, context="create_product_group")
                return f"❌ Failed to create product group: {error_msg}"

    @mcp.tool()
    def google_ads_shopping_feed_status(
        customer_id: str,
        merchant_center_id: str
    ) -> str:
        """Check the status of your Google Merchant Center feed connection.

        Verifies that your Merchant Center account is properly linked to Google Ads
        and that products can flow from Merchant Center to your shopping campaigns.

        Args:
            customer_id: Google Ads customer ID (10 digits, no hyphens)
            merchant_center_id: Your Merchant Center account ID

        Returns:
            Merchant Center feed status

        Example:
            google_ads_shopping_feed_status(
                customer_id="1234567890",
                merchant_center_id="123456789"
            )
        """
        with performance_logger.track_operation('shopping_feed_status', customer_id=customer_id):
            try:
                client = get_auth_manager().get_client()
                shopping_manager = ShoppingPMaxManager(client)

                result = shopping_manager.get_shopping_feed_status(
                    customer_id=customer_id,
                    merchant_center_id=merchant_center_id
                )

                audit_logger.log_api_call(
                    customer_id=customer_id,
                    operation='shopping_feed_status',
                    status='success'
                )

                output = f"# 📊 Merchant Center Feed Status\n\n"
                output += f"**Merchant Center ID**: {result['merchant_center_id']}\n"
                output += f"**Status**: {result['status']}\n\n"

                if result['status'] == 'NOT_LINKED':
                    output += "❌ **Merchant Center account is not linked**\n\n"
                    output += "**To link your Merchant Center account**:\n"
                    output += "1. Go to Google Ads → Tools & Settings → Linked accounts\n"
                    output += "2. Find Google Merchant Center and click 'Link'\n"
                    output += "3. Approve the link request in Merchant Center\n"
                elif result['status'] == 'ENABLED':
                    output += "✅ **Merchant Center is linked and active**\n\n"
                    output += f"**Link ID**: {result.get('link_id', 'N/A')}\n\n"
                    output += "Your products are ready to use in shopping campaigns!\n"
                else:
                    output += f"⚠️ **Status**: {result['message']}\n\n"
                    output += "Check your Merchant Center account for issues.\n"

                return output

            except Exception as e:
                error_msg = ErrorHandler.handle_error(e, context="shopping_feed_status")
                return f"❌ Failed to get feed status: {error_msg}"

    @mcp.tool()
    def google_ads_shopping_performance(
        customer_id: str,
        campaign_id: Optional[str] = None,
        date_range: str = "LAST_30_DAYS"
    ) -> str:
        """Get performance metrics for Shopping campaigns.

        Provides detailed performance data including ROAS (return on ad spend),
        which is critical for shopping campaign optimization.

        Args:
            customer_id: Google Ads customer ID (10 digits, no hyphens)
            campaign_id: Optional specific shopping campaign ID
            date_range: Date range (LAST_7_DAYS, LAST_30_DAYS, LAST_90_DAYS)

        Returns:
            Shopping campaign performance metrics

        Example:
            google_ads_shopping_performance(
                customer_id="1234567890",
                date_range="LAST_30_DAYS"
            )
        """
        with performance_logger.track_operation('shopping_performance', customer_id=customer_id):
            try:
                client = get_auth_manager().get_client()
                shopping_manager = ShoppingPMaxManager(client)

                result = shopping_manager.get_shopping_performance(
                    customer_id=customer_id,
                    campaign_id=campaign_id,
                    date_range=date_range
                )

                audit_logger.log_api_call(
                    customer_id=customer_id,
                    operation='shopping_performance',
                    status='success'
                )

                output = f"# 🛍️ Shopping Campaign Performance\n\n"
                output += f"**Date Range**: {date_range}\n"
                output += f"**Total Campaigns**: {result['total_campaigns']}\n\n"

                if result['total_campaigns'] == 0:
                    output += "❌ No shopping campaigns found or no data for this period.\n"
                    return output

                output += "## Campaign Performance\n\n"
                output += "| Campaign | Impressions | Clicks | Cost | Conv. Value | ROAS |\n"
                output += "|----------|-------------|--------|------|-------------|------|\n"

                for campaign in result['campaigns'][:10]:  # Top 10
                    output += f"| {campaign['campaign_name'][:30]} | "
                    output += f"{campaign['impressions']:,} | "
                    output += f"{campaign['clicks']:,} | "
                    output += f"${campaign['cost']:,.2f} | "
                    output += f"${campaign['conversion_value']:,.2f} | "
                    output += f"{campaign['roas']:.2f}x |\n"

                output += "\n## Key Metrics Summary\n\n"

                total_cost = sum(c['cost'] for c in result['campaigns'])
                total_value = sum(c['conversion_value'] for c in result['campaigns'])
                overall_roas = (total_value / total_cost) if total_cost > 0 else 0

                output += f"- **Total Spend**: ${total_cost:,.2f}\n"
                output += f"- **Total Conversion Value**: ${total_value:,.2f}\n"
                output += f"- **Overall ROAS**: {overall_roas:.2f}x\n\n"

                # ROAS insights
                if overall_roas > 4.0:
                    output += "✅ **Excellent ROAS!** Your shopping campaigns are highly profitable.\n"
                elif overall_roas > 2.0:
                    output += "💚 **Good ROAS.** Campaigns are profitable with room for scaling.\n"
                elif overall_roas > 1.0:
                    output += "⚠️ **Marginal ROAS.** Consider optimizing product groups and bids.\n"
                else:
                    output += "🚨 **Low ROAS.** Review product pricing, margins, and targeting.\n"

                return output

            except Exception as e:
                error_msg = ErrorHandler.handle_error(e, context="shopping_performance")
                return f"❌ Failed to get shopping performance: {error_msg}"

    @mcp.tool()
    def google_ads_create_performance_max_campaign(
        customer_id: str,
        campaign_name: str,
        budget_amount: float,
        conversion_goals_json: str,
        target_roas: Optional[float] = None,
        target_cpa: Optional[float] = None
    ) -> str:
        """Create a Performance Max campaign.

        Performance Max uses Google's AI to optimize across all Google channels:
        Search, Display, YouTube, Gmail, Discover, and Maps.

        Args:
            customer_id: Google Ads customer ID (10 digits, no hyphens)
            campaign_name: Name for the Performance Max campaign
            budget_amount: Daily budget in currency units
            conversion_goals_json: JSON array of conversion action names
            target_roas: Optional target return on ad spend (e.g., 3.0 for 300%)
            target_cpa: Optional target cost per acquisition (if not using ROAS)

        Example:
            google_ads_create_performance_max_campaign(
                customer_id="1234567890",
                campaign_name="PMax - All Products",
                budget_amount=150.00,
                conversion_goals_json='["Purchase", "Add to Cart"]',
                target_roas=4.0
            )
        """
        with performance_logger.track_operation('create_performance_max', customer_id=customer_id):
            try:
                client = get_auth_manager().get_client()
                shopping_manager = ShoppingPMaxManager(client)

                # Parse conversion goals
                try:
                    conversion_goals = json.loads(conversion_goals_json)
                except json.JSONDecodeError:
                    return "❌ Invalid JSON format for conversion_goals_json"

                config = PerformanceMaxCampaignConfig(
                    name=campaign_name,
                    budget_amount=budget_amount,
                    conversion_goals=conversion_goals,
                    target_roas=target_roas,
                    target_cpa=target_cpa
                )

                result = shopping_manager.create_performance_max_campaign(customer_id, config)

                audit_logger.log_api_call(
                    customer_id=customer_id,
                    operation='create_performance_max_campaign',
                    campaign_id=result['campaign_id'],
                    status='success'
                )

                output = f"# 🚀 Performance Max Campaign Created\n\n"
                output += f"**Campaign Name**: {result['campaign_name']}\n"
                output += f"**Campaign ID**: {result['campaign_id']}\n"
                output += f"**Daily Budget**: ${result['budget']:.2f}\n"
                output += f"**Bidding Strategy**: {result['bidding_strategy']}\n"
                output += f"**Status**: PAUSED\n\n"

                if target_roas:
                    output += f"🎯 **Target ROAS**: {target_roas:.1f}x\n\n"
                elif target_cpa:
                    output += f"🎯 **Target CPA**: ${target_cpa:.2f}\n\n"

                output += "## What is Performance Max?\n\n"
                output += "Performance Max uses Google's AI to show your ads across:\n"
                output += "- 🔍 Google Search\n"
                output += "- 📺 YouTube\n"
                output += "- 📧 Gmail\n"
                output += "- 🌐 Display Network\n"
                output += "- 📱 Discover\n"
                output += "- 🗺️ Google Maps\n\n"

                output += "## Next Steps\n\n"
                output += "1. ✅ Campaign created successfully\n"
                output += "2. 📦 Create asset groups with:\n"
                output += "   - Headlines (3-15)\n"
                output += "   - Descriptions (2-5)\n"
                output += "   - Images (at least 1)\n"
                output += "   - Videos (optional)\n"
                output += "3. 🎯 Add audience signals to guide AI\n"
                output += "4. ▶️ Enable campaign when assets are ready\n\n"

                output += "💡 **Tip**: Performance Max needs 6-8 weeks of learning to optimize fully.\n"

                return output

            except Exception as e:
                error_msg = ErrorHandler.handle_error(e, context="create_performance_max")
                return f"❌ Failed to create Performance Max campaign: {error_msg}"

    @mcp.tool()
    def google_ads_create_asset_group(
        customer_id: str,
        campaign_id: str,
        asset_group_name: str,
        final_urls: str
    ) -> str:
        """Create an asset group for a Performance Max campaign.

        Asset groups contain the creative assets (images, videos, text) that
        Performance Max uses across different Google channels.

        Args:
            customer_id: Google Ads customer ID (10 digits, no hyphens)
            campaign_id: Performance Max campaign ID
            asset_group_name: Name for this asset group
            final_urls: Comma-separated list of landing page URLs

        Returns:
            Asset group creation result

        Example:
            google_ads_create_asset_group(
                customer_id="1234567890",
                campaign_id="12345678",
                asset_group_name="Main Products",
                final_urls="https://example.com/products,https://example.com/shop"
            )
        """
        with performance_logger.track_operation('create_asset_group', customer_id=customer_id):
            try:
                client = get_auth_manager().get_client()
                shopping_manager = ShoppingPMaxManager(client)

                # Parse URLs
                urls = [url.strip() for url in final_urls.split(',')]

                result = shopping_manager.create_asset_group(
                    customer_id=customer_id,
                    campaign_id=campaign_id,
                    asset_group_name=asset_group_name,
                    final_urls=urls
                )

                audit_logger.log_api_call(
                    customer_id=customer_id,
                    operation='create_asset_group',
                    campaign_id=campaign_id,
                    status='success'
                )

                output = f"# 📦 Asset Group Created\n\n"
                output += f"**Asset Group Name**: {result['asset_group_name']}\n"
                output += f"**Asset Group ID**: {result['asset_group_id']}\n"
                output += f"**Campaign ID**: {result['campaign_id']}\n"
                output += f"**Status**: PAUSED\n\n"

                output += "**Final URLs**:\n"
                for url in result['final_urls']:
                    output += f"- {url}\n"

                output += "\n## Next Steps\n\n"
                output += "1. ✅ Asset group created\n"
                output += "2. 📝 Upload text assets (headlines, descriptions)\n"
                output += "3. 🖼️ Upload image assets (various sizes)\n"
                output += "4. 📹 Upload video assets (optional)\n"
                output += "5. 🎯 Add audience signals\n"
                output += "6. ▶️ Enable asset group\n\n"

                output += "💡 **Asset Requirements**:\n"
                output += "- Headlines: 3-15 (30 characters max)\n"
                output += "- Long headline: 1 (90 characters max)\n"
                output += "- Descriptions: 2-5 (90 characters max)\n"
                output += "- Images: Minimum 1 landscape + 1 square\n"

                return output

            except Exception as e:
                error_msg = ErrorHandler.handle_error(e, context="create_asset_group")
                return f"❌ Failed to create asset group: {error_msg}"

    @mcp.tool()
    def google_ads_upload_pmax_assets(
        customer_id: str,
        asset_group_id: str,
        headlines_json: str,
        descriptions_json: str,
        long_headline: str
    ) -> str:
        """Upload text assets to a Performance Max asset group.

        Text assets include headlines, descriptions, and a long headline.
        Google's AI will mix and match these across different placements.

        Args:
            customer_id: Google Ads customer ID (10 digits, no hyphens)
            asset_group_id: Asset group ID
            headlines_json: JSON array of headlines (3-15, max 30 chars each)
            descriptions_json: JSON array of descriptions (2-5, max 90 chars each)
            long_headline: Single long headline (max 90 characters)

        Example:
            google_ads_upload_pmax_assets(
                customer_id="1234567890",
                asset_group_id="12345678",
                headlines_json='["Buy Now", "Free Shipping", "Best Prices"]',
                descriptions_json='["Shop the latest products", "Quality guaranteed"]',
                long_headline="Shop Our Complete Product Line Today"
            )
        """
        with performance_logger.track_operation('upload_pmax_assets', customer_id=customer_id):
            try:
                client = get_auth_manager().get_client()
                shopping_manager = ShoppingPMaxManager(client)

                # Parse JSON
                try:
                    headlines = json.loads(headlines_json)
                    descriptions = json.loads(descriptions_json)
                except json.JSONDecodeError as e:
                    return f"❌ Invalid JSON format: {str(e)}"

                # Validate counts
                if len(headlines) < 3 or len(headlines) > 15:
                    return "❌ Headlines must be between 3 and 15"
                if len(descriptions) < 2 or len(descriptions) > 5:
                    return "❌ Descriptions must be between 2 and 5"

                # Validate character limits
                for i, headline in enumerate(headlines):
                    if len(headline) > 30:
                        return f"❌ Headline {i+1} exceeds 30 characters: '{headline}'"

                for i, description in enumerate(descriptions):
                    if len(description) > 90:
                        return f"❌ Description {i+1} exceeds 90 characters"

                if len(long_headline) > 90:
                    return f"❌ Long headline exceeds 90 characters"

                result = shopping_manager.upload_pmax_text_asset(
                    customer_id=customer_id,
                    asset_group_id=asset_group_id,
                    headlines=headlines,
                    descriptions=descriptions,
                    long_headline=long_headline
                )

                audit_logger.log_api_call(
                    customer_id=customer_id,
                    operation='upload_pmax_assets',
                    asset_group_id=asset_group_id,
                    status='success'
                )

                output = f"# 📝 Text Assets Uploaded\n\n"
                output += f"**Asset Group ID**: {result['asset_group_id']}\n"
                output += f"**Total Assets Uploaded**: {result['total_assets']}\n\n"

                output += "## Assets Summary\n\n"
                output += f"- **Headlines**: {result['headlines']}\n"
                output += f"- **Descriptions**: {result['descriptions']}\n"
                output += f"- **Long Headline**: 1\n\n"

                output += "## Uploaded Assets\n\n"

                # Show headlines
                output += "**Headlines**:\n"
                for asset in result['assets']:
                    if asset['type'] == 'HEADLINE':
                        output += f"- {asset['text']}\n"

                output += "\n**Descriptions**:\n"
                for asset in result['assets']:
                    if asset['type'] == 'DESCRIPTION':
                        output += f"- {asset['text']}\n"

                output += f"\n**Long Headline**: {long_headline}\n\n"

                output += "## Next Steps\n\n"
                output += "1. ✅ Text assets uploaded\n"
                output += "2. 🖼️ Upload image assets (required)\n"
                output += "3. 📹 Upload video assets (optional but recommended)\n"
                output += "4. 🎯 Add audience signals\n"
                output += "5. ▶️ Enable asset group and campaign\n\n"

                output += "💡 **Tip**: Google's AI will test different combinations to find what performs best.\n"

                return output

            except Exception as e:
                error_msg = ErrorHandler.handle_error(e, context="upload_pmax_assets")
                return f"❌ Failed to upload assets: {error_msg}"

    @mcp.tool()
    def google_ads_set_audience_signals(
        customer_id: str,
        asset_group_id: str,
        audience_segments_json: str
    ) -> str:
        """Configure audience signals for a Performance Max asset group.

        Audience signals help Google's AI understand who your ideal customers are.
        The AI uses these as starting points and expands to find similar audiences.

        Args:
            customer_id: Google Ads customer ID (10 digits, no hyphens)
            asset_group_id: Asset group ID
            audience_segments_json: JSON array of audience resource names

        Example:
            google_ads_set_audience_signals(
                customer_id="1234567890",
                asset_group_id="12345678",
                audience_segments_json='["customers/1234567890/userLists/123", ...]'
            )
        """
        with performance_logger.track_operation('set_audience_signals', customer_id=customer_id):
            try:
                client = get_auth_manager().get_client()
                shopping_manager = ShoppingPMaxManager(client)

                # Parse audience segments
                try:
                    audience_segments = json.loads(audience_segments_json)
                except json.JSONDecodeError:
                    return "❌ Invalid JSON format for audience_segments_json"

                result = shopping_manager.set_audience_signals(
                    customer_id=customer_id,
                    asset_group_id=asset_group_id,
                    audience_segments=audience_segments
                )

                audit_logger.log_api_call(
                    customer_id=customer_id,
                    operation='set_audience_signals',
                    asset_group_id=asset_group_id,
                    status='success'
                )

                output = f"# 🎯 Audience Signals Configured\n\n"
                output += f"**Asset Group ID**: {result['asset_group_id']}\n"
                output += f"**Audience Signals Added**: {result['audience_signals_added']}\n\n"

                output += "## What are Audience Signals?\n\n"
                output += "Audience signals are **suggestions** to Google's AI about your target customers.\n"
                output += "The AI uses these as starting points and expands beyond them to find:\n"
                output += "- Similar audiences\n"
                output += "- High-converting users\n"
                output += "- New customer segments\n\n"

                output += "## Benefits\n\n"
                output += "✅ **Faster Learning**: AI learns quicker with good signals\n"
                output += "✅ **Better Targeting**: More relevant audience discovery\n"
                output += "✅ **Higher Performance**: Improved conversion rates\n\n"

                output += "## Types of Signals You Can Add\n\n"
                output += "- 👥 Customer Match lists (your existing customers)\n"
                output += "- 🔄 Remarketing audiences (website visitors)\n"
                output += "- 🎯 In-Market audiences (ready to buy)\n"
                output += "- 💼 Affinity audiences (interests)\n"
                output += "- 📊 Similar audiences (lookalikes)\n\n"

                output += "💡 **Tip**: Start with your best-performing audiences from other campaigns.\n"

                return output

            except Exception as e:
                error_msg = ErrorHandler.handle_error(e, context="set_audience_signals")
                return f"❌ Failed to set audience signals: {error_msg}"

    @mcp.tool()
    def google_ads_pmax_insights(
        customer_id: str,
        campaign_id: str,
        date_range: str = "LAST_30_DAYS"
    ) -> str:
        """Get performance insights for a Performance Max campaign.

        Provides comprehensive metrics including all-conversions data which
        captures conversions across all Google properties.

        Args:
            customer_id: Google Ads customer ID (10 digits, no hyphens)
            campaign_id: Performance Max campaign ID
            date_range: Date range (LAST_7_DAYS, LAST_30_DAYS, LAST_90_DAYS)

        Returns:
            Performance Max campaign insights

        Example:
            google_ads_pmax_insights(
                customer_id="1234567890",
                campaign_id="12345678",
                date_range="LAST_30_DAYS"
            )
        """
        with performance_logger.track_operation('pmax_insights', customer_id=customer_id):
            try:
                client = get_auth_manager().get_client()
                shopping_manager = ShoppingPMaxManager(client)

                result = shopping_manager.get_pmax_insights(
                    customer_id=customer_id,
                    campaign_id=campaign_id,
                    date_range=date_range
                )

                if 'error' in result:
                    return f"❌ {result['error']}"

                audit_logger.log_api_call(
                    customer_id=customer_id,
                    operation='pmax_insights',
                    campaign_id=campaign_id,
                    status='success'
                )

                metrics = result['metrics']

                output = f"# 🚀 Performance Max Insights\n\n"
                output += f"**Campaign**: {result['campaign_name']}\n"
                output += f"**Campaign ID**: {result['campaign_id']}\n"
                output += f"**Date Range**: {date_range}\n\n"

                output += "## Campaign Performance\n\n"
                output += f"- **Impressions**: {metrics['impressions']:,}\n"
                output += f"- **Clicks**: {metrics['clicks']:,}\n"
                output += f"- **CTR**: {metrics['ctr']:.2%}\n"
                output += f"- **Cost**: ${metrics['cost']:,.2f}\n"
                output += f"- **Conversions**: {metrics['conversions']:.1f}\n"
                output += f"- **Conversion Value**: ${metrics['conversion_value']:,.2f}\n"
                output += f"- **ROAS**: {metrics['roas']:.2f}x\n\n"

                output += "## All-Conversions Metrics\n\n"
                output += "*Includes conversions from all Google properties*\n\n"
                output += f"- **All Conversions**: {metrics['all_conversions']:.1f}\n"
                output += f"- **All Conversion Value**: ${metrics['all_conversions_value']:,.2f}\n\n"

                # Asset Groups
                output += f"## Asset Groups ({result['total_asset_groups']})\n\n"

                if result['total_asset_groups'] > 0:
                    output += "| Asset Group | Status | Impressions | Clicks | Conv. |\n"
                    output += "|-------------|--------|-------------|--------|-------|\n"

                    for ag in result['asset_groups'][:5]:  # Top 5
                        output += f"| {ag['asset_group_name'][:20]} | "
                        output += f"{ag['status']} | "
                        output += f"{ag['impressions']:,} | "
                        output += f"{ag['clicks']:,} | "
                        output += f"{ag['conversions']:.1f} |\n"
                else:
                    output += "No asset groups found. Create asset groups to start serving ads.\n"

                output += "\n## Performance Analysis\n\n"

                # ROAS analysis
                if metrics['roas'] > 4.0:
                    output += "✅ **Excellent ROAS!** Campaign is highly profitable.\n"
                    output += "💡 Consider increasing budget to scale.\n"
                elif metrics['roas'] > 2.0:
                    output += "💚 **Good ROAS.** Campaign is performing well.\n"
                    output += "💡 Monitor and optimize asset groups.\n"
                elif metrics['roas'] > 1.0:
                    output += "⚠️ **Marginal ROAS.** Room for improvement.\n"
                    output += "💡 Review assets and audience signals.\n"
                else:
                    output += "🚨 **Low ROAS.** Campaign needs optimization.\n"
                    output += "💡 Check assets, budgets, and conversion tracking.\n"

                output += "\n## Optimization Tips\n\n"
                output += "1. 📝 Test different headlines and descriptions\n"
                output += "2. 🖼️ Add high-quality images in multiple sizes\n"
                output += "3. 🎯 Refine audience signals based on performance\n"
                output += "4. 💰 Ensure adequate budget (at least 10x target CPA)\n"
                output += "5. ⏱️ Allow 6-8 weeks for AI learning\n"

                return output

            except Exception as e:
                error_msg = ErrorHandler.handle_error(e, context="pmax_insights")
                return f"❌ Failed to get Performance Max insights: {error_msg}"

    logger.info("Shopping and Performance Max tools registered (9 tools)")
