"""
Conversion Tracking Manager

Handles conversion actions, offline conversion imports, and attribution.

Conversion Types:
- Website conversions (page views, form submissions, purchases)
- Phone call conversions (click-to-call, call extensions)
- App conversions (downloads, in-app actions)
- Import conversions (offline, CRM, store sales)

Attribution Models:
- Last Click
- First Click
- Linear
- Time Decay
- Position Based
- Data-Driven (recommended)
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
from google.ads.googleads.client import GoogleAdsClient
import hashlib


class ConversionActionCategory(str, Enum):
    """Conversion action categories."""
    DEFAULT = "DEFAULT"
    PAGE_VIEW = "PAGE_VIEW"
    PURCHASE = "PURCHASE"
    SIGNUP = "SIGNUP"
    LEAD = "LEAD"
    DOWNLOAD = "DOWNLOAD"
    ADD_TO_CART = "ADD_TO_CART"
    BEGIN_CHECKOUT = "BEGIN_CHECKOUT"
    SUBSCRIBE_PAID = "SUBSCRIBE_PAID"
    PHONE_CALL_LEAD = "PHONE_CALL_LEAD"
    IMPORTED_LEAD = "IMPORTED_LEAD"
    SUBMIT_LEAD_FORM = "SUBMIT_LEAD_FORM"
    BOOK_APPOINTMENT = "BOOK_APPOINTMENT"
    REQUEST_QUOTE = "REQUEST_QUOTE"
    CONTACT = "CONTACT"
    STORE_SALE = "STORE_SALE"
    STORE_VISIT = "STORE_VISIT"


class ConversionOrigin(str, Enum):
    """Where conversions originate from."""
    WEBSITE = "WEBSITE"
    GOOGLE_HOSTED = "GOOGLE_HOSTED"
    APP = "APP"
    CALL_FROM_ADS = "CALL_FROM_ADS"
    STORE = "STORE"
    YOUTUBE_HOSTED = "YOUTUBE_HOSTED"
    IMPORT = "IMPORT"


class AttributionModel(str, Enum):
    """Attribution model types."""
    LAST_CLICK = "LAST_CLICK"
    FIRST_CLICK = "FIRST_CLICK"
    LINEAR = "LINEAR"
    TIME_DECAY = "TIME_DECAY"
    POSITION_BASED = "POSITION_BASED"
    DATA_DRIVEN = "DATA_DRIVEN"


@dataclass
class ConversionActionConfig:
    """Configuration for creating a conversion action."""
    name: str
    category: ConversionActionCategory
    origin: ConversionOrigin
    value: Optional[float] = None
    always_use_default_value: bool = False
    count_type: str = "ONE"  # ONE or MANY
    click_through_lookback_window_days: int = 30
    view_through_lookback_window_days: int = 1
    phone_call_duration_seconds: Optional[int] = None  # For call conversions


class ConversionManager:
    """Manager for conversion tracking and attribution."""

    def __init__(self, client: GoogleAdsClient):
        """Initialize the conversion manager.

        Args:
            client: Authenticated GoogleAdsClient instance
        """
        self.client = client

    def create_conversion_action(
        self,
        customer_id: str,
        config: ConversionActionConfig
    ) -> Dict[str, Any]:
        """Create a conversion action for tracking.

        Args:
            customer_id: Customer ID (without hyphens)
            config: Conversion action configuration

        Returns:
            Dictionary with conversion action details and tracking tag
        """
        conversion_action_service = self.client.get_service("ConversionActionService")
        conversion_action_operation = self.client.get_type("ConversionActionOperation")

        conversion_action = conversion_action_operation.create
        conversion_action.name = config.name
        conversion_action.category = self.client.enums.ConversionActionCategoryEnum[config.category.value]
        conversion_action.origin = self.client.enums.ConversionOriginEnum[config.origin.value]
        conversion_action.status = self.client.enums.ConversionActionStatusEnum.ENABLED

        # Set counting type
        if config.count_type == "ONE":
            conversion_action.counting_type = self.client.enums.ConversionActionCountingTypeEnum.ONE_PER_CLICK
        else:
            conversion_action.counting_type = self.client.enums.ConversionActionCountingTypeEnum.MANY_PER_CLICK

        # Set value settings
        conversion_action.value_settings.default_value = config.value if config.value else 0
        conversion_action.value_settings.always_use_default_value = config.always_use_default_value

        # Set attribution settings
        conversion_action.click_through_lookback_window_days = config.click_through_lookback_window_days
        conversion_action.view_through_lookback_window_days = config.view_through_lookback_window_days

        # Set phone call duration for call conversions
        if config.phone_call_duration_seconds and config.category == ConversionActionCategory.PHONE_CALL_LEAD:
            conversion_action.phone_call_duration_seconds = config.phone_call_duration_seconds

        response = conversion_action_service.mutate_conversion_actions(
            customer_id=customer_id,
            operations=[conversion_action_operation]
        )

        resource_name = response.results[0].resource_name
        conversion_action_id = resource_name.split("/")[-1]

        return {
            'resource_name': resource_name,
            'conversion_action_id': conversion_action_id,
            'name': config.name,
            'category': config.category.value,
            'origin': config.origin.value
        }

    def list_conversion_actions(
        self,
        customer_id: str,
        include_removed: bool = False
    ) -> List[Dict[str, Any]]:
        """List all conversion actions in the account.

        Args:
            customer_id: Customer ID (without hyphens)
            include_removed: Whether to include removed conversions

        Returns:
            List of conversion actions
        """
        ga_service = self.client.get_service("GoogleAdsService")

        query = """
            SELECT
                conversion_action.id,
                conversion_action.name,
                conversion_action.category,
                conversion_action.origin,
                conversion_action.status,
                conversion_action.counting_type,
                conversion_action.value_settings.default_value,
                conversion_action.value_settings.always_use_default_value,
                conversion_action.click_through_lookback_window_days,
                conversion_action.view_through_lookback_window_days,
                conversion_action.attribution_model_settings.attribution_model
            FROM conversion_action
        """

        if not include_removed:
            query += " WHERE conversion_action.status != 'REMOVED'"

        response = ga_service.search(customer_id=customer_id, query=query)

        conversions = []
        for row in response:
            ca = row.conversion_action
            conversions.append({
                'id': str(ca.id),
                'name': ca.name,
                'category': ca.category.name,
                'origin': ca.origin.name,
                'status': ca.status.name,
                'counting_type': ca.counting_type.name,
                'default_value': ca.value_settings.default_value,
                'always_use_default_value': ca.value_settings.always_use_default_value,
                'click_through_window': ca.click_through_lookback_window_days,
                'view_through_window': ca.view_through_lookback_window_days,
                'attribution_model': ca.attribution_model_settings.attribution_model.name
            })

        return conversions

    def upload_offline_conversions(
        self,
        customer_id: str,
        conversion_action_id: str,
        conversions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Upload offline conversion data.

        Args:
            customer_id: Customer ID (without hyphens)
            conversion_action_id: Conversion action ID
            conversions: List of conversion dictionaries with:
                - gclid: Google Click ID
                - conversion_date_time: Conversion time (YYYY-MM-DD HH:MM:SS+TZ)
                - conversion_value: Optional conversion value
                - currency_code: Optional currency (e.g., "USD")

        Returns:
            Upload result
        """
        conversion_upload_service = self.client.get_service("ConversionUploadService")
        conversion_action_service = self.client.get_service("ConversionActionService")

        click_conversions = []

        for conv in conversions:
            click_conversion = self.client.get_type("ClickConversion")
            click_conversion.gclid = conv['gclid']
            click_conversion.conversion_action = conversion_action_service.conversion_action_path(
                customer_id, conversion_action_id
            )
            click_conversion.conversion_date_time = conv['conversion_date_time']

            if 'conversion_value' in conv:
                click_conversion.conversion_value = conv['conversion_value']

            if 'currency_code' in conv:
                click_conversion.currency_code = conv['currency_code']

            click_conversions.append(click_conversion)

        response = conversion_upload_service.upload_click_conversions(
            customer_id=customer_id,
            conversions=click_conversions,
            partial_failure=True
        )

        return {
            'uploaded': len(conversions),
            'results': len(response.results),
            'partial_failure_error': str(response.partial_failure_error) if response.partial_failure_error else None
        }

    def upload_call_conversions(
        self,
        customer_id: str,
        conversion_action_id: str,
        call_conversions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Upload call conversion data.

        Args:
            customer_id: Customer ID (without hyphens)
            conversion_action_id: Conversion action ID
            call_conversions: List with:
                - caller_id: Phone number that called
                - call_start_date_time: Call time
                - conversion_date_time: When call qualified as conversion
                - conversion_value: Optional value

        Returns:
            Upload result
        """
        conversion_upload_service = self.client.get_service("ConversionUploadService")
        conversion_action_service = self.client.get_service("ConversionActionService")

        call_convs = []

        for conv in call_conversions:
            call_conversion = self.client.get_type("CallConversion")
            call_conversion.caller_id = conv['caller_id']
            call_conversion.call_start_date_time = conv['call_start_date_time']
            call_conversion.conversion_date_time = conv['conversion_date_time']
            call_conversion.conversion_action = conversion_action_service.conversion_action_path(
                customer_id, conversion_action_id
            )

            if 'conversion_value' in conv:
                call_conversion.conversion_value = conv['conversion_value']

            if 'currency_code' in conv:
                call_conversion.currency_code = conv['currency_code']

            call_convs.append(call_conversion)

        response = conversion_upload_service.upload_call_conversions(
            customer_id=customer_id,
            conversions=call_convs,
            partial_failure=True
        )

        return {
            'uploaded': len(call_conversions),
            'results': len(response.results),
            'partial_failure_error': str(response.partial_failure_error) if response.partial_failure_error else None
        }

    def get_conversion_performance(
        self,
        customer_id: str,
        conversion_action_id: Optional[str] = None,
        date_range: str = "LAST_30_DAYS"
    ) -> List[Dict[str, Any]]:
        """Get conversion performance metrics.

        Args:
            customer_id: Customer ID (without hyphens)
            conversion_action_id: Optional specific conversion action
            date_range: Date range

        Returns:
            List of conversion performance data
        """
        ga_service = self.client.get_service("GoogleAdsService")

        query = f"""
            SELECT
                conversion_action.id,
                conversion_action.name,
                conversion_action.category,
                metrics.conversions,
                metrics.conversions_value,
                metrics.cost_per_conversion,
                metrics.conversions_from_interactions_rate,
                metrics.value_per_conversion,
                metrics.all_conversions,
                metrics.all_conversions_value
            FROM conversion_action
            WHERE segments.date DURING {date_range}
        """

        if conversion_action_id:
            query += f" AND conversion_action.id = {conversion_action_id}"

        response = ga_service.search(customer_id=customer_id, query=query)

        conversions = []
        for row in response:
            conversions.append({
                'conversion_action_id': str(row.conversion_action.id),
                'name': row.conversion_action.name,
                'category': row.conversion_action.category.name,
                'conversions': row.metrics.conversions,
                'conversions_value': row.metrics.conversions_value,
                'cost_per_conversion': row.metrics.cost_per_conversion,
                'conversion_rate': row.metrics.conversions_from_interactions_rate,
                'value_per_conversion': row.metrics.value_per_conversion,
                'all_conversions': row.metrics.all_conversions,
                'all_conversions_value': row.metrics.all_conversions_value
            })

        return conversions

    def set_attribution_model(
        self,
        customer_id: str,
        conversion_action_id: str,
        attribution_model: AttributionModel
    ) -> Dict[str, Any]:
        """Set attribution model for a conversion action.

        Args:
            customer_id: Customer ID (without hyphens)
            conversion_action_id: Conversion action ID
            attribution_model: Attribution model to set

        Returns:
            Updated conversion action details
        """
        conversion_action_service = self.client.get_service("ConversionActionService")
        conversion_action_operation = self.client.get_type("ConversionActionOperation")

        conversion_action = conversion_action_operation.update
        conversion_action.resource_name = conversion_action_service.conversion_action_path(
            customer_id, conversion_action_id
        )

        conversion_action.attribution_model_settings.attribution_model = (
            self.client.enums.AttributionModelEnum[attribution_model.value]
        )

        self.client.copy_from(
            conversion_action_operation.update_mask,
            self.client.get_type("FieldMask", version="v17")(
                paths=["attribution_model_settings.attribution_model"]
            )
        )

        response = conversion_action_service.mutate_conversion_actions(
            customer_id=customer_id,
            operations=[conversion_action_operation]
        )

        return {
            'resource_name': response.results[0].resource_name,
            'conversion_action_id': conversion_action_id,
            'attribution_model': attribution_model.value
        }

    def get_conversion_tracking_tag(
        self,
        customer_id: str,
        conversion_action_id: str
    ) -> Dict[str, Any]:
        """Get the tracking tag/snippet for a conversion action.

        Args:
            customer_id: Customer ID (without hyphens)
            conversion_action_id: Conversion action ID

        Returns:
            Tracking tag details
        """
        ga_service = self.client.get_service("GoogleAdsService")

        query = f"""
            SELECT
                conversion_action.id,
                conversion_action.name,
                conversion_action.tag_snippets
            FROM conversion_action
            WHERE conversion_action.id = {conversion_action_id}
        """

        response = ga_service.search(customer_id=customer_id, query=query)
        results = list(response)

        if not results:
            return {'error': f'Conversion action {conversion_action_id} not found'}

        row = results[0]
        ca = row.conversion_action

        # Extract tag snippets
        tag_snippets = []
        for snippet in ca.tag_snippets:
            tag_snippets.append({
                'type': snippet.type_.name,
                'page_format': snippet.page_format.name,
                'global_site_tag': snippet.global_site_tag,
                'event_snippet': snippet.event_snippet
            })

        return {
            'conversion_action_id': str(ca.id),
            'name': ca.name,
            'tag_snippets': tag_snippets
        }
