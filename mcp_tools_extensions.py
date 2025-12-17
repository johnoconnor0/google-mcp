"""
MCP Tools - Ad Extensions

Tools for managing ad extensions (assets) that enhance ad visibility.

Extension Tools:
1. google_ads_add_sitelink_extension - Add sitelinks
2. google_ads_add_callout_extension - Add callouts
3. google_ads_add_call_extension - Add phone numbers
4. google_ads_add_structured_snippet - Add structured snippets
5. google_ads_add_price_extension - Add price lists
6. google_ads_add_promotion_extension - Add promotions
7. google_ads_extension_performance_report - Extension metrics
"""

from typing import Optional
from extensions_manager import (
    ExtensionsManager,
    SitelinkConfig,
    CalloutConfig,
    CallExtensionConfig,
    CallConversionReportingState
)
from auth_manager import get_auth_manager
from error_handler import ErrorHandler
from logger import get_logger, get_performance_logger, get_audit_logger
import json

logger = get_logger(__name__)
performance_logger = get_performance_logger()
audit_logger = get_audit_logger()


def register_extension_tools(mcp):
    """Register all ad extension MCP tools."""

    @mcp.tool()
    def google_ads_add_sitelink_extension(
        customer_id: str,
        campaign_id: str,
        sitelinks_json: str
    ) -> str:
        """Add sitelink extensions to a campaign.

        Sitelinks are additional links that appear below your main ad, directing
        users to specific pages on your website. They increase ad size, improve CTR,
        and provide more navigation options.

        Args:
            customer_id: Google Ads customer ID (10 digits, no hyphens)
            campaign_id: Campaign ID to add sitelinks
            sitelinks_json: JSON array of sitelink configurations

        Sitelink Configuration Schema:
        ```json
        [
          {
            "link_text": "Shop Now",
            "final_url": "https://example.com/shop",
            "description1": "Browse our products",
            "description2": "Free shipping on orders over $50"
          }
        ]
        ```

        Requirements:
        - Link text: 1-25 characters
        - Description1: Optional, 35 characters max
        - Description2: Optional, 35 characters max
        - Minimum 2 sitelinks recommended

        Returns:
            Sitelink extension creation result

        Example:
            google_ads_add_sitelink_extension(
                customer_id="1234567890",
                campaign_id="12345678",
                sitelinks_json='[{"link_text": "Shop Now", "final_url": "https://example.com/shop"}]'
            )
        """
        with performance_logger.track_operation('add_sitelink_extension', customer_id=customer_id):
            try:
                client = get_auth_manager().get_client()
                extensions_manager = ExtensionsManager(client)

                # Parse sitelinks JSON
                try:
                    sitelinks_data = json.loads(sitelinks_json)
                except json.JSONDecodeError as e:
                    return f"❌ Invalid JSON format: {str(e)}"

                if not isinstance(sitelinks_data, list):
                    return "❌ sitelinks_json must be a JSON array"

                # Validate and create sitelink configs
                sitelinks = []
                for i, sl in enumerate(sitelinks_data):
                    if 'link_text' not in sl or 'final_url' not in sl:
                        return f"❌ Sitelink {i+1} missing required fields (link_text, final_url)"

                    if len(sl['link_text']) > 25:
                        return f"❌ Sitelink {i+1} link_text exceeds 25 characters"

                    sitelinks.append(SitelinkConfig(
                        link_text=sl['link_text'],
                        final_url=sl['final_url'],
                        description1=sl.get('description1'),
                        description2=sl.get('description2')
                    ))

                result = extensions_manager.add_sitelink_extension(
                    customer_id=customer_id,
                    campaign_id=campaign_id,
                    sitelinks=sitelinks
                )

                audit_logger.log_api_call(
                    customer_id=customer_id,
                    operation='add_sitelink_extension',
                    campaign_id=campaign_id,
                    status='success'
                )

                output = f"# 🔗 Sitelink Extensions Added\n\n"
                output += f"**Campaign ID**: {result['campaign_id']}\n"
                output += f"**Sitelinks Added**: {result['sitelinks_added']}\n\n"

                output += "## Sitelinks\n\n"
                for sl in result['sitelinks']:
                    output += f"### {sl['link_text']}\n"
                    output += f"- **URL**: {sl['final_url']}\n\n"

                output += "## Benefits of Sitelinks\n\n"
                output += "✅ **Increased Ad Size** - Take up more space in search results\n"
                output += "✅ **Higher CTR** - Average 10-15% increase in click-through rate\n"
                output += "✅ **Better User Experience** - Direct users to specific pages\n"
                output += "✅ **More Conversions** - Users find what they need faster\n\n"

                output += "💡 **Best Practices**:\n"
                output += "- Use 4-6 sitelinks for maximum visibility\n"
                output += "- Link to your most popular pages\n"
                output += "- Add descriptions for mobile visibility\n"
                output += "- Update seasonally or for promotions\n"

                return output

            except Exception as e:
                error_msg = ErrorHandler.handle_error(e, context="add_sitelink_extension")
                return f"❌ Failed to add sitelink extensions: {error_msg}"

    @mcp.tool()
    def google_ads_add_callout_extension(
        customer_id: str,
        campaign_id: str,
        callouts_json: str
    ) -> str:
        """Add callout extensions to a campaign.

        Callouts are short, descriptive snippets that highlight key benefits,
        features, or offerings. They appear below your ad text.

        Args:
            customer_id: Google Ads customer ID (10 digits, no hyphens)
            campaign_id: Campaign ID to add callouts
            callouts_json: JSON array of callout texts

        Callout Configuration Schema:
        ```json
        [
          {"callout_text": "Free Shipping"},
          {"callout_text": "24/7 Support"},
          {"callout_text": "Price Match Guarantee"}
        ]
        ```

        Requirements:
        - Callout text: 1-25 characters
        - Minimum 2 callouts recommended
        - Maximum 10 callouts per campaign

        Returns:
            Callout extension creation result

        Example:
            google_ads_add_callout_extension(
                customer_id="1234567890",
                campaign_id="12345678",
                callouts_json='[{"callout_text": "Free Shipping"}, {"callout_text": "24/7 Support"}]'
            )
        """
        with performance_logger.track_operation('add_callout_extension', customer_id=customer_id):
            try:
                client = get_auth_manager().get_client()
                extensions_manager = ExtensionsManager(client)

                # Parse callouts JSON
                try:
                    callouts_data = json.loads(callouts_json)
                except json.JSONDecodeError as e:
                    return f"❌ Invalid JSON format: {str(e)}"

                if not isinstance(callouts_data, list):
                    return "❌ callouts_json must be a JSON array"

                # Validate and create callout configs
                callouts = []
                for i, co in enumerate(callouts_data):
                    if 'callout_text' not in co:
                        return f"❌ Callout {i+1} missing callout_text field"

                    if len(co['callout_text']) > 25:
                        return f"❌ Callout {i+1} exceeds 25 characters: '{co['callout_text']}'"

                    callouts.append(CalloutConfig(callout_text=co['callout_text']))

                if len(callouts) > 10:
                    return "❌ Maximum 10 callouts per campaign"

                result = extensions_manager.add_callout_extension(
                    customer_id=customer_id,
                    campaign_id=campaign_id,
                    callouts=callouts
                )

                audit_logger.log_api_call(
                    customer_id=customer_id,
                    operation='add_callout_extension',
                    campaign_id=campaign_id,
                    status='success'
                )

                output = f"# 💬 Callout Extensions Added\n\n"
                output += f"**Campaign ID**: {result['campaign_id']}\n"
                output += f"**Callouts Added**: {result['callouts_added']}\n\n"

                output += "## Callouts\n\n"
                for co in result['callouts']:
                    output += f"- {co['callout_text']}\n"

                output += "\n## Why Use Callouts?\n\n"
                output += "✅ **Highlight Benefits** - Showcase what makes you unique\n"
                output += "✅ **Build Trust** - Display guarantees and certifications\n"
                output += "✅ **Save Space** - Concise messaging in 25 characters\n"
                output += "✅ **Increase Relevance** - Match user search intent\n\n"

                output += "💡 **Best Practices**:\n"
                output += "- Use action-oriented language\n"
                output += "- Focus on unique value propositions\n"
                output += "- Avoid redundancy with ad copy\n"
                output += "- Test different callout combinations\n"

                return output

            except Exception as e:
                error_msg = ErrorHandler.handle_error(e, context="add_callout_extension")
                return f"❌ Failed to add callout extensions: {error_msg}"

    @mcp.tool()
    def google_ads_add_call_extension(
        customer_id: str,
        campaign_id: str,
        phone_number: str,
        country_code: str = "US",
        track_calls: bool = False
    ) -> str:
        """Add call extension to a campaign.

        Call extensions display your phone number with a click-to-call button,
        making it easy for mobile users to contact you directly from the ad.

        Args:
            customer_id: Google Ads customer ID (10 digits, no hyphens)
            campaign_id: Campaign ID to add call extension
            phone_number: Phone number in local format (e.g., "(555) 123-4567")
            country_code: Two-letter country code (default: US)
            track_calls: Enable call conversion tracking

        Returns:
            Call extension creation result

        Example:
            google_ads_add_call_extension(
                customer_id="1234567890",
                campaign_id="12345678",
                phone_number="(555) 123-4567",
                country_code="US",
                track_calls=True
            )
        """
        with performance_logger.track_operation('add_call_extension', customer_id=customer_id):
            try:
                client = get_auth_manager().get_client()
                extensions_manager = ExtensionsManager(client)

                config = CallExtensionConfig(
                    phone_number=phone_number,
                    country_code=country_code,
                    call_conversion_reporting_state=(
                        CallConversionReportingState.USE_ACCOUNT_LEVEL_CALL_CONVERSION_ACTION
                        if track_calls else CallConversionReportingState.DISABLED
                    )
                )

                result = extensions_manager.add_call_extension(
                    customer_id=customer_id,
                    campaign_id=campaign_id,
                    config=config
                )

                audit_logger.log_api_call(
                    customer_id=customer_id,
                    operation='add_call_extension',
                    campaign_id=campaign_id,
                    status='success'
                )

                output = f"# 📞 Call Extension Added\n\n"
                output += f"**Campaign ID**: {result['campaign_id']}\n"
                output += f"**Phone Number**: {result['phone_number']}\n"
                output += f"**Country Code**: {result['country_code']}\n"
                output += f"**Call Tracking**: {'Enabled' if track_calls else 'Disabled'}\n\n"

                output += "## What Are Call Extensions?\n\n"
                output += "Call extensions add a phone number to your ads with a clickable\n"
                output += "call button on mobile devices. Users can call you directly from\n"
                output += "search results without visiting your website.\n\n"

                output += "## Benefits\n\n"
                output += "✅ **Mobile Optimization** - One-tap calling on smartphones\n"
                output += "✅ **Higher Conversion Rates** - Direct contact = faster sales\n"
                output += "✅ **Call Tracking** - Measure calls as conversions\n"
                output += "✅ **Local Businesses** - Essential for location-based services\n\n"

                if track_calls:
                    output += "📊 **Call Tracking Enabled**: Calls will be tracked as conversions\n\n"

                output += "💡 **Best Practices**:\n"
                output += "- Set business hours scheduling\n"
                output += "- Use a dedicated tracking number\n"
                output += "- Enable call reporting to measure ROI\n"
                output += "- Ensure staff is ready to handle calls\n"

                return output

            except Exception as e:
                error_msg = ErrorHandler.handle_error(e, context="add_call_extension")
                return f"❌ Failed to add call extension: {error_msg}"

    @mcp.tool()
    def google_ads_add_structured_snippet(
        customer_id: str,
        campaign_id: str,
        header: str,
        values_json: str
    ) -> str:
        """Add structured snippet extension to a campaign.

        Structured snippets highlight specific aspects of your products or services
        in a predefined format (e.g., Types: Economy, Luxury, SUV).

        Args:
            customer_id: Google Ads customer ID (10 digits, no hyphens)
            campaign_id: Campaign ID to add structured snippet
            header: Snippet header (Types, Brands, Models, Services, Styles, etc.)
            values_json: JSON array of values (3-10 items)

        Common Headers:
        - Amenities, Brands, Courses, Degree programs, Destinations, Featured hotels,
          Insurance coverage, Models, Neighborhoods, Service catalog, Services, Shows,
          Styles, Types

        Returns:
            Structured snippet creation result

        Example:
            google_ads_add_structured_snippet(
                customer_id="1234567890",
                campaign_id="12345678",
                header="Types",
                values_json='["Economy", "Compact", "Luxury", "SUV"]'
            )
        """
        with performance_logger.track_operation('add_structured_snippet', customer_id=customer_id):
            try:
                client = get_auth_manager().get_client()
                extensions_manager = ExtensionsManager(client)

                # Parse values JSON
                try:
                    values = json.loads(values_json)
                except json.JSONDecodeError as e:
                    return f"❌ Invalid JSON format: {str(e)}"

                if not isinstance(values, list):
                    return "❌ values_json must be a JSON array"

                if len(values) < 3:
                    return "❌ Minimum 3 values required"
                if len(values) > 10:
                    return "❌ Maximum 10 values allowed"

                result = extensions_manager.add_structured_snippet(
                    customer_id=customer_id,
                    campaign_id=campaign_id,
                    header=header,
                    values=values
                )

                audit_logger.log_api_call(
                    customer_id=customer_id,
                    operation='add_structured_snippet',
                    campaign_id=campaign_id,
                    status='success'
                )

                output = f"# 📋 Structured Snippet Added\n\n"
                output += f"**Campaign ID**: {result['campaign_id']}\n"
                output += f"**Header**: {result['header']}\n"
                output += f"**Values**: {len(result['values'])}\n\n"

                output += f"## {result['header']}\n\n"
                for value in result['values']:
                    output += f"- {value}\n"

                output += "\n## What Are Structured Snippets?\n\n"
                output += "Structured snippets display lists of your offerings in a\n"
                output += "predefined format below your ad. They help users quickly\n"
                output += "understand what you offer before clicking.\n\n"

                output += "## Benefits\n\n"
                output += "✅ **Quick Overview** - Showcase range of offerings\n"
                output += "✅ **Better Matching** - Help users find what they need\n"
                output += "✅ **Professional Look** - Organized, scannable format\n"
                output += "✅ **More Ad Space** - Increase ad visibility\n\n"

                output += "💡 **Best Practices**:\n"
                output += "- Use relevant, predefined headers\n"
                output += "- List 3-10 most important items\n"
                output += "- Keep values concise and clear\n"
                output += "- Update based on inventory or seasons\n"

                return output

            except Exception as e:
                error_msg = ErrorHandler.handle_error(e, context="add_structured_snippet")
                return f"❌ Failed to add structured snippet: {error_msg}"

    @mcp.tool()
    def google_ads_add_price_extension(
        customer_id: str,
        campaign_id: str,
        price_qualifier: str,
        items_json: str
    ) -> str:
        """Add price extension to a campaign.

        Price extensions display a list of products/services with prices,
        allowing users to browse your offerings directly in the ad.

        Args:
            customer_id: Google Ads customer ID (10 digits, no hyphens)
            campaign_id: Campaign ID to add price extension
            price_qualifier: Qualifier (FROM, UP_TO, AVERAGE, NONE)
            items_json: JSON array of price items (3-8 items)

        Price Item Schema:
        ```json
        [
          {
            "header": "Basic Plan",
            "description": "Perfect for individuals",
            "price": 9.99,
            "final_url": "https://example.com/basic"
          }
        ]
        ```

        Returns:
            Price extension creation result

        Example:
            google_ads_add_price_extension(
                customer_id="1234567890",
                campaign_id="12345678",
                price_qualifier="FROM",
                items_json='[{"header": "Basic", "price": 9.99, "final_url": "https://example.com/basic"}]'
            )
        """
        with performance_logger.track_operation('add_price_extension', customer_id=customer_id):
            try:
                client = get_auth_manager().get_client()
                extensions_manager = ExtensionsManager(client)

                # Parse items JSON
                try:
                    items = json.loads(items_json)
                except json.JSONDecodeError as e:
                    return f"❌ Invalid JSON format: {str(e)}"

                if not isinstance(items, list):
                    return "❌ items_json must be a JSON array"

                if len(items) < 3:
                    return "❌ Minimum 3 price items required"
                if len(items) > 8:
                    return "❌ Maximum 8 price items allowed"

                # Validate items
                for i, item in enumerate(items):
                    if 'header' not in item or 'price' not in item or 'final_url' not in item:
                        return f"❌ Item {i+1} missing required fields (header, price, final_url)"

                result = extensions_manager.add_price_extension(
                    customer_id=customer_id,
                    campaign_id=campaign_id,
                    price_qualifier=price_qualifier,
                    items=items
                )

                audit_logger.log_api_call(
                    customer_id=customer_id,
                    operation='add_price_extension',
                    campaign_id=campaign_id,
                    status='success'
                )

                output = f"# 💰 Price Extension Added\n\n"
                output += f"**Campaign ID**: {result['campaign_id']}\n"
                output += f"**Price Qualifier**: {result['price_qualifier']}\n"
                output += f"**Items**: {result['items_count']}\n\n"

                output += "## Price Items\n\n"
                output += "| Item | Price |\n"
                output += "|------|-------|\n"
                for item in items[:8]:
                    output += f"| {item['header']} | ${item['price']:.2f} |\n"

                output += "\n## What Are Price Extensions?\n\n"
                output += "Price extensions showcase your products or services with prices\n"
                output += "in a mobile-friendly carousel format. Users can browse and click\n"
                output += "on specific items that interest them.\n\n"

                output += "## Benefits\n\n"
                output += "✅ **Transparent Pricing** - Build trust with upfront costs\n"
                output += "✅ **Qualified Clicks** - Users know prices before clicking\n"
                output += "✅ **Mobile-Optimized** - Swipeable carousel on mobile\n"
                output += "✅ **Direct Navigation** - Each item links to specific page\n\n"

                output += "💡 **Best Practices**:\n"
                output += "- Show your most popular items\n"
                output += "- Use clear, concise item names\n"
                output += "- Keep prices competitive and current\n"
                output += "- Include descriptions for clarity\n"

                return output

            except Exception as e:
                error_msg = ErrorHandler.handle_error(e, context="add_price_extension")
                return f"❌ Failed to add price extension: {error_msg}"

    @mcp.tool()
    def google_ads_add_promotion_extension(
        customer_id: str,
        campaign_id: str,
        promotion_target: str,
        occasion: str = "UNKNOWN",
        discount_modifier: str = "NONE",
        money_amount_off: Optional[float] = None,
        percent_off: Optional[int] = None,
        promotion_code: Optional[str] = None
    ) -> str:
        """Add promotion extension to a campaign.

        Promotion extensions highlight special offers, sales, and discounts
        with a prominent visual treatment in your ads.

        Args:
            customer_id: Google Ads customer ID (10 digits, no hyphens)
            campaign_id: Campaign ID to add promotion
            promotion_target: What's being promoted (e.g., "Summer Sale")
            occasion: Occasion (UNKNOWN, NEW_YEARS, VALENTINES_DAY, MOTHERS_DAY,
                     FATHERS_DAY, LABOR_DAY, BACK_TO_SCHOOL, HALLOWEEN,
                     BLACK_FRIDAY, CYBER_MONDAY, CHRISTMAS, BOXING_DAY, INDEPENDENCE_DAY)
            discount_modifier: Modifier (NONE, UP_TO)
            money_amount_off: Dollar amount off (e.g., 25.00 for $25 off)
            percent_off: Percent off (e.g., 20 for 20% off)
            promotion_code: Optional promo code text

        Returns:
            Promotion extension creation result

        Example:
            google_ads_add_promotion_extension(
                customer_id="1234567890",
                campaign_id="12345678",
                promotion_target="Holiday Sale",
                occasion="CHRISTMAS",
                percent_off=25,
                promotion_code="HOLIDAY25"
            )
        """
        with performance_logger.track_operation('add_promotion_extension', customer_id=customer_id):
            try:
                client = get_auth_manager().get_client()
                extensions_manager = ExtensionsManager(client)

                if not money_amount_off and not percent_off:
                    return "❌ Must specify either money_amount_off or percent_off"

                result = extensions_manager.add_promotion_extension(
                    customer_id=customer_id,
                    campaign_id=campaign_id,
                    promotion_target=promotion_target,
                    occasion=occasion,
                    discount_modifier=discount_modifier,
                    money_amount_off=money_amount_off,
                    percent_off=percent_off,
                    promotion_code=promotion_code
                )

                audit_logger.log_api_call(
                    customer_id=customer_id,
                    operation='add_promotion_extension',
                    campaign_id=campaign_id,
                    status='success'
                )

                output = f"# 🎉 Promotion Extension Added\n\n"
                output += f"**Campaign ID**: {result['campaign_id']}\n"
                output += f"**Promotion**: {result['promotion_target']}\n"
                output += f"**Occasion**: {result['occasion']}\n"
                output += f"**Discount**: {result['discount']}\n"
                if result['promotion_code']:
                    output += f"**Promo Code**: {result['promotion_code']}\n"
                output += "\n"

                output += "## What Are Promotion Extensions?\n\n"
                output += "Promotion extensions highlight special offers with a prominent\n"
                output += "visual tag (% or $) that catches user attention. They're perfect\n"
                output += "for seasonal sales, holiday promotions, and limited-time offers.\n\n"

                output += "## Benefits\n\n"
                output += "✅ **Eye-Catching** - Special visual treatment in ads\n"
                output += "✅ **Urgency** - Creates sense of limited-time opportunity\n"
                output += "✅ **Higher CTR** - Promotions typically increase clicks\n"
                output += "✅ **Seasonal Relevance** - Tie to holidays and events\n\n"

                output += "💡 **Best Practices**:\n"
                output += "- Set start and end dates for promotions\n"
                output += "- Use occasion-specific promotions seasonally\n"
                output += "- Include promo code for easy redemption\n"
                output += "- Update regularly to maintain freshness\n"

                return output

            except Exception as e:
                error_msg = ErrorHandler.handle_error(e, context="add_promotion_extension")
                return f"❌ Failed to add promotion extension: {error_msg}"

    @mcp.tool()
    def google_ads_extension_performance_report(
        customer_id: str,
        campaign_id: Optional[str] = None,
        date_range: str = "LAST_30_DAYS"
    ) -> str:
        """Get performance metrics for ad extensions.

        Shows which extensions are performing well and driving clicks,
        helping you optimize your extension strategy.

        Args:
            customer_id: Google Ads customer ID (10 digits, no hyphens)
            campaign_id: Optional campaign ID filter
            date_range: Date range (LAST_7_DAYS, LAST_30_DAYS, LAST_90_DAYS)

        Returns:
            Extension performance report

        Example:
            google_ads_extension_performance_report(
                customer_id="1234567890",
                date_range="LAST_30_DAYS"
            )
        """
        with performance_logger.track_operation('extension_performance_report', customer_id=customer_id):
            try:
                client = get_auth_manager().get_client()
                extensions_manager = ExtensionsManager(client)

                result = extensions_manager.get_extension_performance(
                    customer_id=customer_id,
                    campaign_id=campaign_id,
                    date_range=date_range
                )

                audit_logger.log_api_call(
                    customer_id=customer_id,
                    operation='extension_performance_report',
                    status='success'
                )

                output = f"# 📊 Extension Performance Report\n\n"
                output += f"**Date Range**: {date_range}\n"
                output += f"**Total Extensions**: {result['total_extensions']}\n\n"

                if result['total_extensions'] == 0:
                    output += "❌ No extensions found. Add extensions to improve ad performance!\n\n"
                    output += "**Benefits of Extensions**:\n"
                    output += "- Increase ad visibility and CTR\n"
                    output += "- Provide more information to users\n"
                    output += "- Improve Quality Score\n"
                    output += "- No additional cost (only pay for clicks)\n"
                    return output

                # Performance by type
                output += "## Performance by Extension Type\n\n"
                output += "| Extension Type | Count | Clicks | Impressions | Avg CTR | Cost |\n"
                output += "|----------------|-------|--------|-------------|---------|------|\n"

                for ext_type, data in result['by_type'].items():
                    output += f"| {ext_type} | {data['count']} | "
                    output += f"{data['total_clicks']:,} | {data['total_impressions']:,} | "
                    output += f"{data['avg_ctr']:.2%} | ${data['total_cost']:,.2f} |\n"

                # Top performing extensions
                top_extensions = sorted(
                    result['extensions'],
                    key=lambda x: x['clicks'],
                    reverse=True
                )[:10]

                if top_extensions:
                    output += "\n## Top 10 Performing Extensions\n\n"
                    output += "| Campaign | Type | Clicks | CTR | Cost |\n"
                    output += "|----------|------|--------|-----|------|\n"

                    for ext in top_extensions:
                        output += f"| {ext['campaign_name'][:20]} | "
                        output += f"{ext['field_type']} | "
                        output += f"{ext['clicks']:,} | "
                        output += f"{ext['ctr']:.2%} | "
                        output += f"${ext['cost']:,.2f} |\n"

                output += "\n## Optimization Recommendations\n\n"

                # Find best and worst performing types
                if result['by_type']:
                    best_type = max(result['by_type'].items(), key=lambda x: x[1]['avg_ctr'])
                    output += f"✅ **Best Performer**: {best_type[0]} (CTR: {best_type[1]['avg_ctr']:.2%})\n"
                    output += "💡 Consider adding more of this extension type\n\n"

                output += "**General Tips**:\n"
                output += "- Extensions with CTR > 5% are performing well\n"
                output += "- Remove underperforming extensions\n"
                output += "- Test different extension variations\n"
                output += "- Keep extensions updated and relevant\n"

                return output

            except Exception as e:
                error_msg = ErrorHandler.handle_error(e, context="extension_performance_report")
                return f"❌ Failed to get extension performance: {error_msg}"

    @mcp.tool()
    def google_ads_add_location_extension(
        customer_id: str,
        campaign_id: str,
        business_name: str,
        address_line_1: str,
        city: str,
        province: str,
        postal_code: str,
        country_code: str,
        phone_number: str = ""
    ) -> str:
        """Add a location extension to display your business address in ads.

        Location extensions show your business address, phone number, and a map marker
        with your ads. They help customers find your physical business locations and
        increase foot traffic to your stores.

        Args:
            customer_id: Google Ads customer ID (10 digits, no hyphens)
            campaign_id: Campaign ID to add location extension
            business_name: Business name (up to 80 characters)
            address_line_1: Street address
            city: City name
            province: State/province code (e.g., "CA", "NY", "TX")
            postal_code: ZIP or postal code
            country_code: 2-letter country code (e.g., "US", "GB", "CA")
            phone_number: Optional phone with country code (e.g., "+1-555-123-4567")

        Returns:
            Location extension creation result

        Example:
            google_ads_add_location_extension(
                customer_id="1234567890",
                campaign_id="12345678",
                business_name="Acme Coffee Shop",
                address_line_1="123 Main Street",
                city="San Francisco",
                province="CA",
                postal_code="94102",
                country_code="US",
                phone_number="+1-415-555-1234"
            )

        Benefits:
            - Show your address and location on a map
            - Increase foot traffic to physical locations
            - Make it easy for customers to find you
            - Add phone numbers for direct calls
            - Improve local search visibility

        Requirements:
            - Location extensions require address verification
            - Best practice: Link with Google My Business
            - Phone numbers should include country code
            - All address fields must be valid

        Note:
            For advanced location management, use Google My Business integration
            with Local campaigns for automatic location syncing and store visit tracking.
        """
        with performance_logger.track_operation('add_location_extension', customer_id=customer_id):
            try:
                client = get_auth_manager().get_client()
                extensions_manager = ExtensionsManager(client)

                # Validate inputs
                if len(business_name) > 80:
                    return "❌ Business name must be 80 characters or less"

                if len(country_code) != 2:
                    return "❌ Country code must be exactly 2 characters (e.g., 'US', 'GB')"

                result = extensions_manager.add_location_extension(
                    customer_id=customer_id,
                    campaign_id=campaign_id,
                    business_name=business_name,
                    address_line_1=address_line_1,
                    city=city,
                    province=province,
                    postal_code=postal_code,
                    country_code=country_code,
                    phone_number=phone_number if phone_number else None
                )

                audit_logger.log_api_call(
                    operation="add_location_extension",
                    customer_id=customer_id,
                    details={
                        "campaign_id": campaign_id,
                        "business_name": business_name,
                        "address": result['address'],
                        "country": country_code
                    },
                    response=result
                )

                output = "# ✅ Location Extension Added Successfully\n\n"
                output += f"**Campaign ID**: {result['campaign_id']}\n"
                output += f"**Business Name**: {result['business_name']}\n\n"

                output += "## Location Details\n\n"
                output += f"**Address**: {result['address']}\n"
                output += f"**Country**: {result['country']}\n"
                if result['phone_number']:
                    output += f"**Phone**: {result['phone_number']}\n"

                output += f"\n**Asset Resource**: `{result['asset_resource_name']}`\n\n"

                output += "## What Happens Next\n\n"
                output += "1. **Verification**: Google will verify your business address\n"
                output += "2. **Approval**: Extension will go through policy review (~24 hours)\n"
                output += "3. **Display**: Once approved, your location will show with ads\n"
                output += "4. **Map Integration**: Users will see a map marker and directions link\n\n"

                output += "## Benefits\n\n"
                output += "- 📍 **Local Visibility**: Show up on Google Maps\n"
                output += "- 🚶 **Foot Traffic**: Drive customers to your physical location\n"
                output += "- 📞 **Direct Contact**: Allow customers to call your business\n"
                output += "- 🗺️ **Directions**: Provide easy navigation to your store\n\n"

                output += "## Best Practices\n\n"
                output += "- **Link Google My Business**: For automatic location syncing\n"
                output += "- **Verify Address**: Ensure address is accurate and verifiable\n"
                output += "- **Add Multiple Locations**: Create separate extensions for each store\n"
                output += "- **Monitor Performance**: Track location extension clicks and calls\n"
                output += "- **Update Information**: Keep address and phone current\n\n"

                output += "## Advanced Location Features\n\n"
                output += "For businesses with multiple locations, consider:\n"
                output += "- **Local Campaigns**: Automated campaigns across all locations\n"
                output += "- **Store Visit Tracking**: Measure offline conversions\n"
                output += "- **GMB Integration**: Sync all locations automatically\n"
                output += "- **Location-Specific Ads**: Customize ads per location\n\n"

                output += "Use `google_ads_create_local_campaign` for advanced local advertising."

                return output

            except Exception as e:
                error_msg = ErrorHandler.handle_error(e, context="add_location_extension")
                return f"❌ Failed to add location extension: {error_msg}"

    logger.info("Ad extension tools registered (8 tools)")
