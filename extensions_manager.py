"""
Extensions Manager

Handles ad extensions (now called "assets" in Google Ads API).

Extension Types:
- Sitelink extensions - Additional links below your ad
- Callout extensions - Short descriptive text
- Call extensions - Phone number with call button
- Location extensions - Business address from Google My Business
- Price extensions - Product/service pricing
- Promotion extensions - Special offers and deals
- Structured snippets - Lists of products/services
- Image extensions - Visual assets

Performance:
- Extension-level performance reporting
- Impact analysis on ad performance
"""

from typing import Dict, Any, List, Optional
from google.ads.googleads.client import GoogleAdsClient
from dataclasses import dataclass
from enum import Enum


class DayOfWeek(str, Enum):
    """Days of the week for scheduling."""
    MONDAY = "MONDAY"
    TUESDAY = "TUESDAY"
    WEDNESDAY = "WEDNESDAY"
    THURSDAY = "THURSDAY"
    FRIDAY = "FRIDAY"
    SATURDAY = "SATURDAY"
    SUNDAY = "SUNDAY"


class CallConversionReportingState(str, Enum):
    """Call conversion reporting states."""
    DISABLED = "DISABLED"
    USE_ACCOUNT_LEVEL_CALL_CONVERSION_ACTION = "USE_ACCOUNT_LEVEL_CALL_CONVERSION_ACTION"
    USE_RESOURCE_LEVEL_CALL_CONVERSION_ACTION = "USE_RESOURCE_LEVEL_CALL_CONVERSION_ACTION"


@dataclass
class SitelinkConfig:
    """Configuration for sitelink extension."""
    link_text: str
    final_url: str
    description1: Optional[str] = None
    description2: Optional[str] = None


@dataclass
class CalloutConfig:
    """Configuration for callout extension."""
    callout_text: str


@dataclass
class CallExtensionConfig:
    """Configuration for call extension."""
    phone_number: str
    country_code: str = "US"
    call_conversion_reporting_state: CallConversionReportingState = CallConversionReportingState.DISABLED


class ExtensionsManager:
    """Manager for ad extensions (assets)."""

    def __init__(self, client: GoogleAdsClient):
        """Initialize the extensions manager.

        Args:
            client: Authenticated GoogleAdsClient instance
        """
        self.client = client

    def add_sitelink_extension(
        self,
        customer_id: str,
        campaign_id: str,
        sitelinks: List[SitelinkConfig]
    ) -> Dict[str, Any]:
        """Add sitelink extensions to a campaign.

        Args:
            customer_id: Customer ID (without hyphens)
            campaign_id: Campaign ID
            sitelinks: List of sitelink configurations

        Returns:
            Created sitelink extension details
        """
        asset_service = self.client.get_service("AssetService")
        campaign_asset_service = self.client.get_service("CampaignAssetService")

        created_sitelinks = []

        for sitelink in sitelinks:
            # Create sitelink asset
            asset_operation = self.client.get_type("AssetOperation")
            asset = asset_operation.create

            asset.type_ = self.client.enums.AssetTypeEnum.SITELINK
            asset.sitelink_asset.link_text = sitelink.link_text
            asset.sitelink_asset.description1 = sitelink.description1 or ""
            asset.sitelink_asset.description2 = sitelink.description2 or ""
            asset.final_urls.append(sitelink.final_url)

            # Create asset
            asset_response = asset_service.mutate_assets(
                customer_id=customer_id,
                operations=[asset_operation]
            )
            asset_resource_name = asset_response.results[0].resource_name

            # Link asset to campaign
            campaign_asset_operation = self.client.get_type("CampaignAssetOperation")
            campaign_asset = campaign_asset_operation.create

            campaign_asset.asset = asset_resource_name
            campaign_asset.campaign = self.client.get_service("CampaignService").campaign_path(
                customer_id, campaign_id
            )
            campaign_asset.field_type = self.client.enums.AssetFieldTypeEnum.SITELINK

            campaign_asset_service.mutate_campaign_assets(
                customer_id=customer_id,
                operations=[campaign_asset_operation]
            )

            created_sitelinks.append({
                'link_text': sitelink.link_text,
                'final_url': sitelink.final_url,
                'asset_resource_name': asset_resource_name
            })

        return {
            'campaign_id': campaign_id,
            'sitelinks_added': len(created_sitelinks),
            'sitelinks': created_sitelinks
        }

    def add_callout_extension(
        self,
        customer_id: str,
        campaign_id: str,
        callouts: List[CalloutConfig]
    ) -> Dict[str, Any]:
        """Add callout extensions to a campaign.

        Args:
            customer_id: Customer ID (without hyphens)
            campaign_id: Campaign ID
            callouts: List of callout configurations

        Returns:
            Created callout extension details
        """
        asset_service = self.client.get_service("AssetService")
        campaign_asset_service = self.client.get_service("CampaignAssetService")

        created_callouts = []

        for callout in callouts:
            # Create callout asset
            asset_operation = self.client.get_type("AssetOperation")
            asset = asset_operation.create

            asset.type_ = self.client.enums.AssetTypeEnum.CALLOUT
            asset.callout_asset.callout_text = callout.callout_text

            # Create asset
            asset_response = asset_service.mutate_assets(
                customer_id=customer_id,
                operations=[asset_operation]
            )
            asset_resource_name = asset_response.results[0].resource_name

            # Link asset to campaign
            campaign_asset_operation = self.client.get_type("CampaignAssetOperation")
            campaign_asset = campaign_asset_operation.create

            campaign_asset.asset = asset_resource_name
            campaign_asset.campaign = self.client.get_service("CampaignService").campaign_path(
                customer_id, campaign_id
            )
            campaign_asset.field_type = self.client.enums.AssetFieldTypeEnum.CALLOUT

            campaign_asset_service.mutate_campaign_assets(
                customer_id=customer_id,
                operations=[campaign_asset_operation]
            )

            created_callouts.append({
                'callout_text': callout.callout_text,
                'asset_resource_name': asset_resource_name
            })

        return {
            'campaign_id': campaign_id,
            'callouts_added': len(created_callouts),
            'callouts': created_callouts
        }

    def add_call_extension(
        self,
        customer_id: str,
        campaign_id: str,
        config: CallExtensionConfig
    ) -> Dict[str, Any]:
        """Add call extension to a campaign.

        Args:
            customer_id: Customer ID (without hyphens)
            campaign_id: Campaign ID
            config: Call extension configuration

        Returns:
            Created call extension details
        """
        asset_service = self.client.get_service("AssetService")
        campaign_asset_service = self.client.get_service("CampaignAssetService")

        # Create call asset
        asset_operation = self.client.get_type("AssetOperation")
        asset = asset_operation.create

        asset.type_ = self.client.enums.AssetTypeEnum.CALL
        asset.call_asset.phone_number = config.phone_number
        asset.call_asset.country_code = config.country_code
        asset.call_asset.call_conversion_reporting_state = (
            self.client.enums.CallConversionReportingStateEnum[config.call_conversion_reporting_state.value]
        )

        # Create asset
        asset_response = asset_service.mutate_assets(
            customer_id=customer_id,
            operations=[asset_operation]
        )
        asset_resource_name = asset_response.results[0].resource_name

        # Link asset to campaign
        campaign_asset_operation = self.client.get_type("CampaignAssetOperation")
        campaign_asset = campaign_asset_operation.create

        campaign_asset.asset = asset_resource_name
        campaign_asset.campaign = self.client.get_service("CampaignService").campaign_path(
            customer_id, campaign_id
        )
        campaign_asset.field_type = self.client.enums.AssetFieldTypeEnum.CALL

        campaign_asset_service.mutate_campaign_assets(
            customer_id=customer_id,
            operations=[campaign_asset_operation]
        )

        return {
            'campaign_id': campaign_id,
            'phone_number': config.phone_number,
            'country_code': config.country_code,
            'asset_resource_name': asset_resource_name
        }

    def add_structured_snippet(
        self,
        customer_id: str,
        campaign_id: str,
        header: str,
        values: List[str]
    ) -> Dict[str, Any]:
        """Add structured snippet extension to a campaign.

        Args:
            customer_id: Customer ID (without hyphens)
            campaign_id: Campaign ID
            header: Snippet header (e.g., "Types", "Brands", "Services")
            values: List of values (e.g., ["Economy", "Compact", "SUV"])

        Returns:
            Created structured snippet details
        """
        asset_service = self.client.get_service("AssetService")
        campaign_asset_service = self.client.get_service("CampaignAssetService")

        # Create structured snippet asset
        asset_operation = self.client.get_type("AssetOperation")
        asset = asset_operation.create

        asset.type_ = self.client.enums.AssetTypeEnum.STRUCTURED_SNIPPET
        asset.structured_snippet_asset.header = header
        asset.structured_snippet_asset.values.extend(values)

        # Create asset
        asset_response = asset_service.mutate_assets(
            customer_id=customer_id,
            operations=[asset_operation]
        )
        asset_resource_name = asset_response.results[0].resource_name

        # Link asset to campaign
        campaign_asset_operation = self.client.get_type("CampaignAssetOperation")
        campaign_asset = campaign_asset_operation.create

        campaign_asset.asset = asset_resource_name
        campaign_asset.campaign = self.client.get_service("CampaignService").campaign_path(
            customer_id, campaign_id
        )
        campaign_asset.field_type = self.client.enums.AssetFieldTypeEnum.STRUCTURED_SNIPPET

        campaign_asset_service.mutate_campaign_assets(
            customer_id=customer_id,
            operations=[campaign_asset_operation]
        )

        return {
            'campaign_id': campaign_id,
            'header': header,
            'values': values,
            'asset_resource_name': asset_resource_name
        }

    def add_price_extension(
        self,
        customer_id: str,
        campaign_id: str,
        price_qualifier: str,
        items: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Add price extension to a campaign.

        Args:
            customer_id: Customer ID (without hyphens)
            campaign_id: Campaign ID
            price_qualifier: Qualifier like "From", "Up to", "Average"
            items: List of price items with header, description, price, final_url

        Returns:
            Created price extension details
        """
        asset_service = self.client.get_service("AssetService")
        campaign_asset_service = self.client.get_service("CampaignAssetService")

        # Create price asset
        asset_operation = self.client.get_type("AssetOperation")
        asset = asset_operation.create

        asset.type_ = self.client.enums.AssetTypeEnum.PRICE
        asset.price_asset.type_ = self.client.enums.PriceExtensionTypeEnum.SERVICES
        asset.price_asset.price_qualifier = self.client.enums.PriceExtensionPriceQualifierEnum[price_qualifier.upper().replace(" ", "_")]
        asset.price_asset.language_code = "en"

        # Add price offerings
        for item in items[:8]:  # Max 8 items
            price_offering = self.client.get_type("PriceOffering")
            price_offering.header = item['header']
            price_offering.description = item.get('description', '')
            price_offering.final_urls.append(item['final_url'])

            # Price amount
            price_offering.price.amount_micros = int(item['price'] * 1_000_000)
            price_offering.price.currency_code = "USD"

            asset.price_asset.price_offerings.append(price_offering)

        # Create asset
        asset_response = asset_service.mutate_assets(
            customer_id=customer_id,
            operations=[asset_operation]
        )
        asset_resource_name = asset_response.results[0].resource_name

        # Link asset to campaign
        campaign_asset_operation = self.client.get_type("CampaignAssetOperation")
        campaign_asset = campaign_asset_operation.create

        campaign_asset.asset = asset_resource_name
        campaign_asset.campaign = self.client.get_service("CampaignService").campaign_path(
            customer_id, campaign_id
        )
        campaign_asset.field_type = self.client.enums.AssetFieldTypeEnum.PRICE

        campaign_asset_service.mutate_campaign_assets(
            customer_id=customer_id,
            operations=[campaign_asset_operation]
        )

        return {
            'campaign_id': campaign_id,
            'price_qualifier': price_qualifier,
            'items_count': len(items),
            'asset_resource_name': asset_resource_name
        }

    def add_promotion_extension(
        self,
        customer_id: str,
        campaign_id: str,
        promotion_target: str,
        occasion: str,
        discount_modifier: str,
        money_amount_off: Optional[float] = None,
        percent_off: Optional[int] = None,
        promotion_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """Add promotion extension to a campaign.

        Args:
            customer_id: Customer ID (without hyphens)
            campaign_id: Campaign ID
            promotion_target: What's being promoted (e.g., "Summer Sale")
            occasion: Promotion occasion (e.g., "UNKNOWN", "NEW_YEARS", "BACK_TO_SCHOOL")
            discount_modifier: Type like "UP_TO", "NONE"
            money_amount_off: Dollar amount off (e.g., 25.00 for $25 off)
            percent_off: Percent off (e.g., 20 for 20% off)
            promotion_code: Promo code text

        Returns:
            Created promotion extension details
        """
        asset_service = self.client.get_service("AssetService")
        campaign_asset_service = self.client.get_service("CampaignAssetService")

        # Create promotion asset
        asset_operation = self.client.get_type("AssetOperation")
        asset = asset_operation.create

        asset.type_ = self.client.enums.AssetTypeEnum.PROMOTION
        asset.promotion_asset.promotion_target = promotion_target
        asset.promotion_asset.occasion = self.client.enums.PromotionExtensionOccasionEnum[occasion.upper()]
        asset.promotion_asset.discount_modifier = self.client.enums.PromotionExtensionDiscountModifierEnum[discount_modifier.upper()]

        # Set discount
        if money_amount_off:
            asset.promotion_asset.money_amount_off.amount_micros = int(money_amount_off * 1_000_000)
            asset.promotion_asset.money_amount_off.currency_code = "USD"
        elif percent_off:
            asset.promotion_asset.percent_off = percent_off

        # Set promo code
        if promotion_code:
            asset.promotion_asset.promotion_code = promotion_code

        # Create asset
        asset_response = asset_service.mutate_assets(
            customer_id=customer_id,
            operations=[asset_operation]
        )
        asset_resource_name = asset_response.results[0].resource_name

        # Link asset to campaign
        campaign_asset_operation = self.client.get_type("CampaignAssetOperation")
        campaign_asset = campaign_asset_operation.create

        campaign_asset.asset = asset_resource_name
        campaign_asset.campaign = self.client.get_service("CampaignService").campaign_path(
            customer_id, campaign_id
        )
        campaign_asset.field_type = self.client.enums.AssetFieldTypeEnum.PROMOTION

        campaign_asset_service.mutate_campaign_assets(
            customer_id=customer_id,
            operations=[campaign_asset_operation]
        )

        return {
            'campaign_id': campaign_id,
            'promotion_target': promotion_target,
            'occasion': occasion,
            'discount': f"${money_amount_off}" if money_amount_off else f"{percent_off}%",
            'promotion_code': promotion_code,
            'asset_resource_name': asset_resource_name
        }

    def add_location_extension(
        self,
        customer_id: str,
        campaign_id: str,
        business_name: str,
        address_line_1: str,
        city: str,
        province: str,
        postal_code: str,
        country_code: str,
        phone_number: Optional[str] = None
    ) -> Dict[str, Any]:
        """Add a location extension to a campaign.

        Location extensions link Google My Business locations to campaigns,
        displaying business address, phone number, and map markers in ads.

        Args:
            customer_id: Customer ID (without hyphens)
            campaign_id: Campaign ID to add location extension
            business_name: Business name
            address_line_1: Street address
            city: City name
            province: State/province code (e.g., "CA", "NY")
            postal_code: Zip/postal code
            country_code: Country code (e.g., "US", "GB")
            phone_number: Optional phone number with country code (e.g., "+1-555-123-4567")

        Returns:
            Location extension creation result
        """
        asset_service = self.client.get_service("AssetService")
        campaign_asset_service = self.client.get_service("CampaignAssetService")

        # Create location asset
        asset_operation = self.client.get_type("AssetOperation")
        asset = asset_operation.create
        asset.type_ = self.client.enums.AssetTypeEnum.LOCATION
        asset.name = f"Location: {business_name}"

        # Set location details
        location_asset = asset.location_asset
        location_asset.business_name = business_name

        # Set address
        location_asset.address_line_1 = address_line_1
        location_asset.city = city
        location_asset.province = province
        location_asset.postal_code = postal_code
        location_asset.country_code = country_code

        # Set phone number if provided
        if phone_number:
            location_asset.phone_number = phone_number

        # Create asset
        asset_response = asset_service.mutate_assets(
            customer_id=customer_id,
            operations=[asset_operation]
        )
        asset_resource_name = asset_response.results[0].resource_name

        # Link asset to campaign
        campaign_asset_operation = self.client.get_type("CampaignAssetOperation")
        campaign_asset = campaign_asset_operation.create

        campaign_asset.asset = asset_resource_name
        campaign_asset.campaign = self.client.get_service("CampaignService").campaign_path(
            customer_id, campaign_id
        )
        campaign_asset.field_type = self.client.enums.AssetFieldTypeEnum.LOCATION

        campaign_asset_service.mutate_campaign_assets(
            customer_id=customer_id,
            operations=[campaign_asset_operation]
        )

        return {
            'campaign_id': campaign_id,
            'business_name': business_name,
            'address': f"{address_line_1}, {city}, {province} {postal_code}",
            'country': country_code,
            'phone_number': phone_number,
            'asset_resource_name': asset_resource_name
        }

    def get_extension_performance(
        self,
        customer_id: str,
        campaign_id: Optional[str] = None,
        date_range: str = "LAST_30_DAYS"
    ) -> Dict[str, Any]:
        """Get performance metrics for extensions.

        Args:
            customer_id: Customer ID (without hyphens)
            campaign_id: Optional campaign ID filter
            date_range: Date range for metrics

        Returns:
            Extension performance data
        """
        ga_service = self.client.get_service("GoogleAdsService")

        query = f"""
            SELECT
                campaign.id,
                campaign.name,
                campaign_asset.field_type,
                asset.type,
                asset.name,
                metrics.clicks,
                metrics.impressions,
                metrics.ctr,
                metrics.cost_micros
            FROM campaign_asset
            WHERE segments.date DURING {date_range}
        """

        if campaign_id:
            query += f" AND campaign.id = {campaign_id}"

        query += " ORDER BY metrics.clicks DESC"

        response = ga_service.search(customer_id=customer_id, query=query)

        extensions = []
        for row in response:
            extensions.append({
                'campaign_id': str(row.campaign.id),
                'campaign_name': row.campaign.name,
                'field_type': row.campaign_asset.field_type.name,
                'asset_type': row.asset.type_.name,
                'asset_name': row.asset.name if hasattr(row.asset, 'name') else 'N/A',
                'clicks': row.metrics.clicks,
                'impressions': row.metrics.impressions,
                'ctr': row.metrics.ctr,
                'cost': row.metrics.cost_micros / 1_000_000
            })

        # Group by extension type
        by_type = {}
        for ext in extensions:
            ext_type = ext['field_type']
            if ext_type not in by_type:
                by_type[ext_type] = {
                    'total_clicks': 0,
                    'total_impressions': 0,
                    'total_cost': 0,
                    'count': 0
                }
            by_type[ext_type]['total_clicks'] += ext['clicks']
            by_type[ext_type]['total_impressions'] += ext['impressions']
            by_type[ext_type]['total_cost'] += ext['cost']
            by_type[ext_type]['count'] += 1

        # Calculate averages
        for ext_type, data in by_type.items():
            if data['total_impressions'] > 0:
                data['avg_ctr'] = data['total_clicks'] / data['total_impressions']
            else:
                data['avg_ctr'] = 0

        return {
            'extensions': extensions,
            'total_extensions': len(extensions),
            'by_type': by_type
        }

    def add_image_extension(
        self,
        customer_id: str,
        campaign_id: str,
        image_url: str,
        image_name: str,
        aspect_ratio: str = "1.91:1"
    ) -> Dict[str, Any]:
        """Add image asset extension to campaign.

        Args:
            customer_id: Customer ID (without hyphens)
            campaign_id: Campaign ID
            image_url: URL of the image to upload
            image_name: Name for the image asset
            aspect_ratio: Image aspect ratio (1.91:1, 1:1, 4:3)

        Returns:
            Dictionary with image extension details
        """
        import requests
        import base64

        # Download image
        response = requests.get(image_url)
        if response.status_code != 200:
            raise ValueError(f"Failed to download image from {image_url}")

        image_data = base64.b64encode(response.content).decode('utf-8')

        # Create image asset
        asset_service = self.client.get_service("AssetService")
        asset_operation = self.client.get_type("AssetOperation")

        asset = asset_operation.create
        asset.type_ = self.client.enums.AssetTypeEnum.IMAGE
        asset.image_asset.data = image_data.encode('utf-8')
        asset.image_asset.file_size = len(response.content)
        asset.image_asset.mime_type = self.client.enums.MimeTypeEnum.IMAGE_JPEG
        asset.image_asset.full_size.height_pixels = response.headers.get('height', 0)
        asset.image_asset.full_size.width_pixels = response.headers.get('width', 0)
        asset.name = image_name

        # Upload image asset
        asset_response = asset_service.mutate_assets(
            customer_id=customer_id,
            operations=[asset_operation]
        )

        asset_resource_name = asset_response.results[0].resource_name

        # Link image to campaign
        campaign_asset_service = self.client.get_service("CampaignAssetService")
        campaign_asset_operation = self.client.get_type("CampaignAssetOperation")

        campaign_asset = campaign_asset_operation.create
        campaign_asset.asset = asset_resource_name
        campaign_asset.campaign = self.client.get_service("CampaignService").campaign_path(customer_id, campaign_id)
        campaign_asset.field_type = self.client.enums.AssetFieldTypeEnum.MARKETING_IMAGE

        campaign_asset_service.mutate_campaign_assets(
            customer_id=customer_id,
            operations=[campaign_asset_operation]
        )

        return {
            'campaign_id': campaign_id,
            'image_name': image_name,
            'image_url': image_url,
            'aspect_ratio': aspect_ratio,
            'asset_resource_name': asset_resource_name,
            'file_size_bytes': len(response.content)
        }

    def remove_extension(
        self,
        customer_id: str,
        extension_type: str,
        extension_id: str,
        remove_from: str = "campaign",
        resource_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Remove or delete extension asset.

        Args:
            customer_id: Customer ID (without hyphens)
            extension_type: Type of extension (sitelink, callout, call, etc.)
            extension_id: Extension asset resource name or ID
            remove_from: Where to remove from (campaign, ad_group, account)
            resource_id: Optional campaign or ad group ID (required if remove_from is campaign or ad_group)

        Returns:
            Dictionary with removal confirmation
        """
        # Map extension type to asset field type
        extension_type_mapping = {
            'sitelink': 'SITELINK',
            'callout': 'CALLOUT',
            'call': 'CALL',
            'structured_snippet': 'STRUCTURED_SNIPPET',
            'location': 'LOCATION',
            'price': 'PRICE',
            'promotion': 'PROMOTION',
            'image': 'MARKETING_IMAGE'
        }

        if extension_type not in extension_type_mapping:
            raise ValueError(f"Invalid extension type: {extension_type}")

        asset_field_type = extension_type_mapping[extension_type]

        if remove_from == "campaign":
            if not resource_id:
                raise ValueError("resource_id (campaign_id) is required when remove_from='campaign'")

            # Remove campaign asset link
            campaign_asset_service = self.client.get_service("CampaignAssetService")
            campaign_asset_operation = self.client.get_type("CampaignAssetOperation")

            # Build resource name
            resource_name = campaign_asset_service.campaign_asset_path(
                customer_id,
                resource_id,  # campaign_id
                extension_id,  # asset_id
                asset_field_type
            )

            campaign_asset_operation.remove = resource_name

            campaign_asset_service.mutate_campaign_assets(
                customer_id=customer_id,
                operations=[campaign_asset_operation]
            )

            return {
                'action': 'removed_from_campaign',
                'campaign_id': resource_id,
                'extension_type': extension_type,
                'extension_id': extension_id
            }

        elif remove_from == "ad_group":
            if not resource_id:
                raise ValueError("resource_id (ad_group_id) is required when remove_from='ad_group'")

            # Remove ad group asset link
            ad_group_asset_service = self.client.get_service("AdGroupAssetService")
            ad_group_asset_operation = self.client.get_type("AdGroupAssetOperation")

            # Build resource name
            resource_name = ad_group_asset_service.ad_group_asset_path(
                customer_id,
                resource_id,  # ad_group_id
                extension_id,  # asset_id
                asset_field_type
            )

            ad_group_asset_operation.remove = resource_name

            ad_group_asset_service.mutate_ad_group_assets(
                customer_id=customer_id,
                operations=[ad_group_asset_operation]
            )

            return {
                'action': 'removed_from_ad_group',
                'ad_group_id': resource_id,
                'extension_type': extension_type,
                'extension_id': extension_id
            }

        elif remove_from == "account":
            # Delete asset entirely
            asset_service = self.client.get_service("AssetService")
            asset_operation = self.client.get_type("AssetOperation")

            asset_operation.remove = asset_service.asset_path(customer_id, extension_id)

            asset_service.mutate_assets(
                customer_id=customer_id,
                operations=[asset_operation]
            )

            return {
                'action': 'deleted_asset',
                'extension_type': extension_type,
                'extension_id': extension_id
            }

        else:
            raise ValueError(f"Invalid remove_from value: {remove_from}. Must be campaign, ad_group, or account")
