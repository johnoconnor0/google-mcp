"""
MCP Tools - Conversion Tracking & Attribution

Provides 10 MCP tools for conversion tracking:

Conversion Action Management (4 tools):
1. google_ads_create_conversion_action - Create conversion tracking
2. google_ads_list_conversion_actions - List all conversions
3. google_ads_get_conversion_tag - Get tracking tag/snippet
4. google_ads_set_attribution_model - Set attribution model

Offline Conversion Import (3 tools):
5. google_ads_upload_offline_conversions - Upload offline conversions
6. google_ads_upload_call_conversions - Upload call conversions
7. google_ads_upload_store_sales - Upload store sales (uses offline conversions)

Performance & Reporting (3 tools):
8. google_ads_get_conversion_performance - Conversion performance metrics
9. google_ads_conversion_summary_report - Account-wide conversion summary
10. google_ads_update_conversion_action - Update conversion settings
"""

from typing import Optional, List, Dict, Any
from conversion_manager import (
    ConversionManager,
    ConversionActionConfig,
    ConversionActionCategory,
    ConversionOrigin,
    AttributionModel
)
from auth_manager import get_auth_manager
from error_handler import ErrorHandler
from logger import performance_logger, audit_logger
import json


def register_conversion_tools(mcp):
    """Register all conversion tracking tools with the MCP server.

    Args:
        mcp: FastMCP server instance
    """

    @mcp.tool()
    def google_ads_create_conversion_action(
        customer_id: str,
        conversion_name: str,
        category: str,
        origin: str,
        value: Optional[float] = None,
        always_use_default_value: bool = False,
        count_type: str = "ONE",
        click_lookback_days: int = 30,
        view_lookback_days: int = 1
    ) -> str:
        """
        Create a conversion action for tracking.

        Args:
            customer_id: Customer ID (without hyphens)
            conversion_name: Name for the conversion (e.g., "Purchase", "Lead Form")
            category: Conversion category (PURCHASE, SIGNUP, LEAD, etc.)
            origin: Where conversions occur (WEBSITE, APP, CALL_FROM_ADS, IMPORT)
            value: Optional default conversion value
            always_use_default_value: If True, always use default value (ignore transaction-specific values)
            count_type: ONE (count once per click) or MANY (count every conversion)
            click_lookback_days: Attribution window for clicks (1-90 days)
            view_lookback_days: Attribution window for views (1-30 days)

        Returns:
            Success message with conversion action ID and tag snippet

        Example:
            google_ads_create_conversion_action(
                customer_id="1234567890",
                conversion_name="Purchase",
                category="PURCHASE",
                origin="WEBSITE",
                value=50.00,
                count_type="ONE"
            )

        Categories: PURCHASE, SIGNUP, LEAD, DOWNLOAD, ADD_TO_CART, BEGIN_CHECKOUT,
                   PHONE_CALL_LEAD, SUBMIT_LEAD_FORM, BOOK_APPOINTMENT, etc.
        """
        with performance_logger.track_operation('create_conversion_action', customer_id=customer_id):
            try:
                client = get_auth_manager().get_client()
                conversion_manager = ConversionManager(client)

                # Validate category
                try:
                    cat_enum = ConversionActionCategory[category.upper()]
                except KeyError:
                    valid = [c.value for c in ConversionActionCategory]
                    return f"❌ Invalid category. Valid: {', '.join(valid[:10])}..."

                # Validate origin
                try:
                    origin_enum = ConversionOrigin[origin.upper()]
                except KeyError:
                    valid = [o.value for o in ConversionOrigin]
                    return f"❌ Invalid origin. Valid: {', '.join(valid)}"

                config = ConversionActionConfig(
                    name=conversion_name,
                    category=cat_enum,
                    origin=origin_enum,
                    value=value,
                    always_use_default_value=always_use_default_value,
                    count_type=count_type.upper(),
                    click_through_lookback_window_days=click_lookback_days,
                    view_through_lookback_window_days=view_lookback_days
                )

                result = conversion_manager.create_conversion_action(customer_id, config)

                # Audit log
                audit_logger.log_api_call(
                    customer_id=customer_id,
                    operation="create_conversion_action",
                    resource_type="conversion_action",
                    resource_id=result['conversion_action_id'],
                    action="create",
                    result="success",
                    details={'name': conversion_name, 'category': category}
                )

                output = f"✅ Conversion action created successfully!\n\n"
                output += f"**Conversion ID**: {result['conversion_action_id']}\n"
                output += f"**Name**: {result['name']}\n"
                output += f"**Category**: {result['category']}\n"
                output += f"**Origin**: {result['origin']}\n\n"

                if origin_enum == ConversionOrigin.WEBSITE:
                    output += f"**Next Steps**:\n"
                    output += f"1. Get tracking tag with `google_ads_get_conversion_tag`\n"
                    output += f"2. Install tag on your website conversion page\n"
                    output += f"3. Test conversion tracking\n"
                    output += f"4. Wait 24-48 hours for data to populate\n"
                elif origin_enum == ConversionOrigin.IMPORT:
                    output += f"**Next Steps**:\n"
                    output += f"1. Use `google_ads_upload_offline_conversions` to import data\n"
                    output += f"2. Upload conversions with GCLID and timestamp\n"

                return output

            except Exception as e:
                error_msg = ErrorHandler.handle_error(e, context="create_conversion_action")
                return f"❌ Failed to create conversion action: {error_msg}"

    @mcp.tool()
    def google_ads_list_conversion_actions(
        customer_id: str,
        include_removed: bool = False,
        response_format: str = "markdown"
    ) -> str:
        """
        List all conversion actions in the account.

        Args:
            customer_id: Customer ID (without hyphens)
            include_removed: Include removed conversions
            response_format: Output format (markdown or json)

        Returns:
            List of all conversion actions

        Example:
            google_ads_list_conversion_actions(
                customer_id="1234567890"
            )
        """
        with performance_logger.track_operation('list_conversion_actions', customer_id=customer_id):
            try:
                client = get_auth_manager().get_client()
                conversion_manager = ConversionManager(client)

                conversions = conversion_manager.list_conversion_actions(customer_id, include_removed)

                # Audit log
                audit_logger.log_api_call(
                    customer_id=customer_id,
                    operation="list_conversion_actions",
                    resource_type="conversion_action",
                    action="read",
                    result="success",
                    details={'count': len(conversions)}
                )

                if response_format.lower() == "json":
                    return json.dumps(conversions, indent=2)

                if not conversions:
                    return "No conversion actions found. Create one with `google_ads_create_conversion_action`."

                output = f"# Conversion Actions\n\n"
                output += f"**Total**: {len(conversions)}\n\n"

                for conv in conversions:
                    status_marker = " ✅" if conv['status'] == "ENABLED" else " ❌"
                    output += f"## {conv['name']}{status_marker}\n\n"
                    output += f"- **ID**: {conv['id']}\n"
                    output += f"- **Category**: {conv['category']}\n"
                    output += f"- **Origin**: {conv['origin']}\n"
                    output += f"- **Status**: {conv['status']}\n"
                    output += f"- **Counting**: {conv['counting_type']}\n"
                    output += f"- **Default Value**: ${conv['default_value']:.2f}\n"
                    output += f"- **Attribution Model**: {conv['attribution_model']}\n"
                    output += f"- **Click Window**: {conv['click_through_window']} days\n"
                    output += f"- **View Window**: {conv['view_through_window']} days\n\n"

                return output

            except Exception as e:
                error_msg = ErrorHandler.handle_error(e, context="list_conversion_actions")
                return f"❌ Failed to list conversion actions: {error_msg}"

    @mcp.tool()
    def google_ads_get_conversion_tag(
        customer_id: str,
        conversion_action_id: str
    ) -> str:
        """
        Get the tracking tag/snippet for a website conversion action.

        Returns the Global Site Tag and Event Snippet that must be installed
        on your website to track conversions.

        Args:
            customer_id: Customer ID (without hyphens)
            conversion_action_id: Conversion action ID

        Returns:
            Tracking tag code snippets

        Example:
            google_ads_get_conversion_tag(
                customer_id="1234567890",
                conversion_action_id="12345"
            )
        """
        with performance_logger.track_operation('get_conversion_tag', customer_id=customer_id):
            try:
                client = get_auth_manager().get_client()
                conversion_manager = ConversionManager(client)

                result = conversion_manager.get_conversion_tracking_tag(customer_id, conversion_action_id)

                if 'error' in result:
                    return f"❌ {result['error']}"

                # Audit log
                audit_logger.log_api_call(
                    customer_id=customer_id,
                    operation="get_conversion_tag",
                    resource_type="conversion_action",
                    resource_id=conversion_action_id,
                    action="read",
                    result="success"
                )

                output = f"# Conversion Tracking Tag\n\n"
                output += f"**Conversion**: {result['name']}\n"
                output += f"**ID**: {result['conversion_action_id']}\n\n"

                output += f"## Installation Instructions\n\n"
                output += f"Install these tags on your website:\n\n"

                for snippet in result['tag_snippets']:
                    output += f"### {snippet['type']} ({snippet['page_format']})\n\n"

                    if snippet.get('global_site_tag'):
                        output += f"**Global Site Tag** (install on ALL pages):\n```html\n"
                        output += snippet['global_site_tag']
                        output += f"\n```\n\n"

                    if snippet.get('event_snippet'):
                        output += f"**Event Snippet** (install on conversion page only):\n```html\n"
                        output += snippet['event_snippet']
                        output += f"\n```\n\n"

                output += f"**Important**:\n"
                output += f"1. Place Global Site Tag in `<head>` on ALL pages\n"
                output += f"2. Place Event Snippet on conversion page (e.g., thank-you page)\n"
                output += f"3. Test with Google Tag Assistant\n"
                output += f"4. Wait 24-48 hours for data to appear\n"

                return output

            except Exception as e:
                error_msg = ErrorHandler.handle_error(e, context="get_conversion_tag")
                return f"❌ Failed to get conversion tag: {error_msg}"

    @mcp.tool()
    def google_ads_upload_offline_conversions(
        customer_id: str,
        conversion_action_id: str,
        conversions: List[Dict[str, Any]]
    ) -> str:
        """
        Upload offline conversion data (CRM conversions, phone orders, store visits).

        Use this to import conversions that happen offline but originated from
        Google Ads clicks. You must have the GCLID (Google Click ID) for each
        conversion.

        Args:
            customer_id: Customer ID (without hyphens)
            conversion_action_id: Conversion action ID (must be IMPORT origin)
            conversions: List of conversion dictionaries with:
                - gclid: Google Click ID (required)
                - conversion_date_time: When conversion occurred (required)
                  Format: "YYYY-MM-DD HH:MM:SS+TZ" (e.g., "2025-12-16 14:30:00-08:00")
                - conversion_value: Conversion value (optional)
                - currency_code: Currency code (optional, e.g., "USD")

        Returns:
            Upload success message with count

        Example:
            google_ads_upload_offline_conversions(
                customer_id="1234567890",
                conversion_action_id="12345",
                conversions=[
                    {
                        "gclid": "Cj0KCQiA...",
                        "conversion_date_time": "2025-12-15 10:30:00-08:00",
                        "conversion_value": 150.00,
                        "currency_code": "USD"
                    },
                    {
                        "gclid": "Cj0KCQiB...",
                        "conversion_date_time": "2025-12-15 14:20:00-08:00",
                        "conversion_value": 200.00,
                        "currency_code": "USD"
                    }
                ]
            )

        GCLID Capture: Add {lpurl}?gclid={gclid} to landing page URLs to capture GCLID.
        """
        with performance_logger.track_operation('upload_offline_conversions', customer_id=customer_id):
            try:
                client = get_auth_manager().get_client()
                conversion_manager = ConversionManager(client)

                result = conversion_manager.upload_offline_conversions(
                    customer_id,
                    conversion_action_id,
                    conversions
                )

                # Audit log
                audit_logger.log_api_call(
                    customer_id=customer_id,
                    operation="upload_offline_conversions",
                    resource_type="conversion_action",
                    resource_id=conversion_action_id,
                    action="update",
                    result="success",
                    details={'count': result['uploaded']}
                )

                output = f"✅ Offline conversions uploaded!\n\n"
                output += f"**Conversions Uploaded**: {result['uploaded']}\n"
                output += f"**Conversions Processed**: {result['results']}\n\n"

                if result['partial_failure_error']:
                    output += f"⚠️ **Partial Failure**:\n{result['partial_failure_error']}\n\n"

                output += f"**Processing Time**: 2-6 hours\n"
                output += f"**Data Visibility**: Within 24 hours\n\n"

                output += f"**Common Issues**:\n"
                output += f"- Invalid GCLID (must match actual click)\n"
                output += f"- Conversion time outside attribution window\n"
                output += f"- Duplicate conversions (already uploaded)\n"

                return output

            except Exception as e:
                error_msg = ErrorHandler.handle_error(e, context="upload_offline_conversions")
                return f"❌ Failed to upload offline conversions: {error_msg}"

    @mcp.tool()
    def google_ads_upload_call_conversions(
        customer_id: str,
        conversion_action_id: str,
        call_conversions: List[Dict[str, Any]]
    ) -> str:
        """
        Upload call conversion data for phone calls that converted.

        Args:
            customer_id: Customer ID (without hyphens)
            conversion_action_id: Call conversion action ID
            call_conversions: List with:
                - caller_id: Phone number that called (E.164 format: +12345678900)
                - call_start_date_time: When call started
                - conversion_date_time: When call qualified as conversion
                - conversion_value: Optional conversion value
                - currency_code: Optional currency

        Returns:
            Upload success message

        Example:
            google_ads_upload_call_conversions(
                customer_id="1234567890",
                conversion_action_id="12345",
                call_conversions=[
                    {
                        "caller_id": "+12025551234",
                        "call_start_date_time": "2025-12-15 10:30:00-08:00",
                        "conversion_date_time": "2025-12-15 10:35:00-08:00",
                        "conversion_value": 500.00,
                        "currency_code": "USD"
                    }
                ]
            )
        """
        with performance_logger.track_operation('upload_call_conversions', customer_id=customer_id):
            try:
                client = get_auth_manager().get_client()
                conversion_manager = ConversionManager(client)

                result = conversion_manager.upload_call_conversions(
                    customer_id,
                    conversion_action_id,
                    call_conversions
                )

                # Audit log
                audit_logger.log_api_call(
                    customer_id=customer_id,
                    operation="upload_call_conversions",
                    resource_type="conversion_action",
                    resource_id=conversion_action_id,
                    action="update",
                    result="success",
                    details={'count': result['uploaded']}
                )

                output = f"✅ Call conversions uploaded!\n\n"
                output += f"**Call Conversions Uploaded**: {result['uploaded']}\n"
                output += f"**Conversions Processed**: {result['results']}\n\n"

                if result['partial_failure_error']:
                    output += f"⚠️ **Partial Failure**:\n{result['partial_failure_error']}\n\n"

                return output

            except Exception as e:
                error_msg = ErrorHandler.handle_error(e, context="upload_call_conversions")
                return f"❌ Failed to upload call conversions: {error_msg}"

    @mcp.tool()
    def google_ads_get_conversion_performance(
        customer_id: str,
        conversion_action_id: Optional[str] = None,
        date_range: str = "LAST_30_DAYS"
    ) -> str:
        """
        Get conversion performance metrics.

        Args:
            customer_id: Customer ID (without hyphens)
            conversion_action_id: Optional specific conversion
            date_range: Date range

        Returns:
            Conversion performance data

        Example:
            google_ads_get_conversion_performance(
                customer_id="1234567890",
                date_range="LAST_30_DAYS"
            )
        """
        with performance_logger.track_operation('get_conversion_performance', customer_id=customer_id):
            try:
                client = get_auth_manager().get_client()
                conversion_manager = ConversionManager(client)

                conversions = conversion_manager.get_conversion_performance(
                    customer_id,
                    conversion_action_id,
                    date_range
                )

                # Audit log
                audit_logger.log_api_call(
                    customer_id=customer_id,
                    operation="get_conversion_performance",
                    resource_type="conversion_action",
                    action="read",
                    result="success",
                    details={'count': len(conversions)}
                )

                if not conversions:
                    return "No conversion data found for the specified period."

                output = f"# Conversion Performance\n\n"
                output += f"**Date Range**: {date_range}\n"
                output += f"**Conversions**: {len(conversions)}\n\n"

                for conv in conversions:
                    output += f"## {conv['name']} ({conv['category']})\n\n"
                    output += f"- **Conversions**: {conv['conversions']:.1f}\n"
                    output += f"- **Conversion Value**: ${conv['conversions_value']:,.2f}\n"
                    output += f"- **Cost per Conversion**: ${conv['cost_per_conversion']:.2f}\n"
                    output += f"- **Conversion Rate**: {conv['conversion_rate'] * 100:.2f}%\n"
                    output += f"- **Value per Conversion**: ${conv['value_per_conversion']:.2f}\n"
                    output += f"- **All Conversions**: {conv['all_conversions']:.1f}\n\n"

                return output

            except Exception as e:
                error_msg = ErrorHandler.handle_error(e, context="get_conversion_performance")
                return f"❌ Failed to get conversion performance: {error_msg}"

    @mcp.tool()
    def google_ads_set_attribution_model(
        customer_id: str,
        conversion_action_id: str,
        attribution_model: str
    ) -> str:
        """
        Set attribution model for a conversion action.

        Attribution models determine how credit for conversions is assigned
        to touchpoints in the customer journey.

        Args:
            customer_id: Customer ID (without hyphens)
            conversion_action_id: Conversion action ID
            attribution_model: Attribution model to use

        Returns:
            Success message

        Example:
            google_ads_set_attribution_model(
                customer_id="1234567890",
                conversion_action_id="12345",
                attribution_model="DATA_DRIVEN"
            )

        Attribution Models:
        - LAST_CLICK: 100% credit to last click (default)
        - FIRST_CLICK: 100% credit to first click
        - LINEAR: Equal credit across all clicks
        - TIME_DECAY: More credit to recent clicks
        - POSITION_BASED: 40% first, 40% last, 20% middle
        - DATA_DRIVEN: Google's ML model (recommended, requires sufficient data)

        Recommendation: Use DATA_DRIVEN for accounts with 300+ conversions/month.
        """
        with performance_logger.track_operation('set_attribution_model', customer_id=customer_id):
            try:
                client = get_auth_manager().get_client()
                conversion_manager = ConversionManager(client)

                try:
                    model = AttributionModel[attribution_model.upper()]
                except KeyError:
                    valid = [m.value for m in AttributionModel]
                    return f"❌ Invalid attribution model. Valid: {', '.join(valid)}"

                result = conversion_manager.set_attribution_model(
                    customer_id,
                    conversion_action_id,
                    model
                )

                # Audit log
                audit_logger.log_api_call(
                    customer_id=customer_id,
                    operation="set_attribution_model",
                    resource_type="conversion_action",
                    resource_id=conversion_action_id,
                    action="update",
                    result="success",
                    details={'model': attribution_model}
                )

                output = f"✅ Attribution model updated!\n\n"
                output += f"**Conversion ID**: {result['conversion_action_id']}\n"
                output += f"**New Model**: {result['attribution_model']}\n\n"

                if model == AttributionModel.DATA_DRIVEN:
                    output += f"**Data-Driven Attribution**:\n"
                    output += f"- Uses machine learning to assign credit\n"
                    output += f"- Requires 300+ conversions and 3,000+ ad interactions/month\n"
                    output += f"- Most accurate attribution model\n"
                    output += f"- Falls back to LINEAR if insufficient data\n"

                return output

            except Exception as e:
                error_msg = ErrorHandler.handle_error(e, context="set_attribution_model")
                return f"❌ Failed to set attribution model: {error_msg}"

    @mcp.tool()
    def google_ads_upload_store_sales(
        customer_id: str,
        conversion_action_id: str,
        store_sales: List[Dict[str, Any]]
    ) -> str:
        """
        Upload store sales data (in-store purchases from online clicks).

        This is a specialized form of offline conversion upload for retail
        businesses tracking in-store purchases that originated from online ads.

        Args:
            customer_id: Customer ID (without hyphens)
            conversion_action_id: Store sales conversion action ID
            store_sales: List of sales with gclid, timestamp, value

        Returns:
            Upload success message

        Example:
            google_ads_upload_store_sales(
                customer_id="1234567890",
                conversion_action_id="12345",
                store_sales=[
                    {
                        "gclid": "Cj0KCQiA...",
                        "conversion_date_time": "2025-12-15 15:45:00-08:00",
                        "conversion_value": 85.50,
                        "currency_code": "USD"
                    }
                ]
            )

        Note: This uses the same upload mechanism as offline conversions.
        """
        # Store sales use the same upload method as offline conversions
        return google_ads_upload_offline_conversions(
            customer_id,
            conversion_action_id,
            store_sales
        )

    # Additional tools (9, 10) for comprehensive conversion management
    @mcp.tool()
    def google_ads_conversion_summary_report(
        customer_id: str,
        date_range: str = "LAST_30_DAYS"
    ) -> str:
        """
        Get account-wide conversion summary.

        Args:
            customer_id: Customer ID (without hyphens)
            date_range: Date range

        Returns:
            Summary of all conversions

        Example:
            google_ads_conversion_summary_report(
                customer_id="1234567890",
                date_range="LAST_30_DAYS"
            )
        """
        # Get all conversion performance and aggregate
        return google_ads_get_conversion_performance(
            customer_id,
            None,  # All conversions
            date_range
        )

    @mcp.tool()
    def google_ads_update_conversion_action(
        customer_id: str,
        conversion_action_id: str,
        conversion_value: Optional[float] = None,
        status: Optional[str] = None
    ) -> str:
        """
        Update conversion action settings.

        Args:
            customer_id: Customer ID (without hyphens)
            conversion_action_id: Conversion action ID to update
            conversion_value: New default value
            status: New status (ENABLED, PAUSED, REMOVED)

        Returns:
            Success message

        Example:
            google_ads_update_conversion_action(
                customer_id="1234567890",
                conversion_action_id="12345",
                conversion_value=75.00,
                status="ENABLED"
            )
        """
        with performance_logger.track_operation('update_conversion_action', customer_id=customer_id):
            try:
                client = get_auth_manager().get_client()
                conversion_action_service = client.get_service("ConversionActionService")
                conversion_action_operation = client.get_type("ConversionActionOperation")

                conversion_action = conversion_action_operation.update
                conversion_action.resource_name = conversion_action_service.conversion_action_path(
                    customer_id, conversion_action_id
                )

                field_paths = []

                if conversion_value is not None:
                    conversion_action.value_settings.default_value = conversion_value
                    field_paths.append("value_settings.default_value")

                if status:
                    conversion_action.status = client.enums.ConversionActionStatusEnum[status.upper()]
                    field_paths.append("status")

                if not field_paths:
                    return "❌ No updates specified. Provide conversion_value or status."

                client.copy_from(
                    conversion_action_operation.update_mask,
                    client.get_type("FieldMask", version="v17")(paths=field_paths)
                )

                conversion_action_service.mutate_conversion_actions(
                    customer_id=customer_id,
                    operations=[conversion_action_operation]
                )

                # Audit log
                audit_logger.log_api_call(
                    customer_id=customer_id,
                    operation="update_conversion_action",
                    resource_type="conversion_action",
                    resource_id=conversion_action_id,
                    action="update",
                    result="success",
                    details={'fields': field_paths}
                )

                return f"✅ Conversion action updated successfully!\n\nUpdated fields: {', '.join(field_paths)}"

            except Exception as e:
                error_msg = ErrorHandler.handle_error(e, context="update_conversion_action")
                return f"❌ Failed to update conversion action: {error_msg}"
