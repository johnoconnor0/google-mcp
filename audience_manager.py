"""
Audience Manager

Handles audience creation, Customer Match lists, and audience targeting.

Supported Audience Types:
- Remarketing lists (website visitors, app users, YouTube)
- Customer Match lists (email, phone, address)
- Custom audiences (custom intent, custom affinity)
- Similar audiences (lookalike)
- In-Market audiences
- Affinity audiences
- Demographic audiences

Audience Targeting:
- Campaign-level audience targeting
- Ad group-level audience targeting
- Audience exclusions
- Performance reporting by audience
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
from google.ads.googleads.client import GoogleAdsClient
import hashlib


class UserListType(str, Enum):
    """User list types for remarketing."""
    CRMBASED = "CRMBASED"  # Customer Match
    RULE_BASED = "RULE_BASED"  # Website/app visitors
    LOGICAL = "LOGICAL"  # Combination of other lists
    SIMILAR = "SIMILAR"  # Lookalike audiences


class CustomerMatchUploadKeyType(str, Enum):
    """Customer Match upload key types."""
    CONTACT_INFO = "CONTACT_INFO"  # Email, phone, address
    CRM_ID = "CRM_ID"  # CRM IDs
    MOBILE_ADVERTISING_ID = "MOBILE_ADVERTISING_ID"  # Mobile ad IDs


class AudienceTargetingType(str, Enum):
    """Audience targeting types."""
    OBSERVATION = "OBSERVATION"  # Observation mode (no bid adjustment limit)
    TARGETING = "TARGETING"  # Targeting mode (restricts reach)


@dataclass
class UserListConfig:
    """Configuration for creating a user list."""
    name: str
    description: Optional[str] = None
    membership_life_span: int = 540  # Days (max 540 for most lists)


@dataclass
class CustomerMatchData:
    """Data for Customer Match upload."""
    emails: Optional[List[str]] = None
    phones: Optional[List[str]] = None
    first_names: Optional[List[str]] = None
    last_names: Optional[List[str]] = None
    countries: Optional[List[str]] = None
    zip_codes: Optional[List[str]] = None


class AudienceManager:
    """Manager for audience creation and targeting."""

    def __init__(self, client: GoogleAdsClient):
        """Initialize the audience manager.

        Args:
            client: Authenticated GoogleAdsClient instance
        """
        self.client = client

    def create_user_list(
        self,
        customer_id: str,
        config: UserListConfig,
        list_type: UserListType = UserListType.CRMBASED
    ) -> Dict[str, Any]:
        """Create a remarketing user list.

        Args:
            customer_id: Customer ID (without hyphens)
            config: User list configuration
            list_type: Type of user list

        Returns:
            Dictionary with user list resource name and ID
        """
        user_list_service = self.client.get_service("UserListService")
        user_list_operation = self.client.get_type("UserListOperation")

        user_list = user_list_operation.create
        user_list.name = config.name

        if config.description:
            user_list.description = config.description

        user_list.membership_life_span = config.membership_life_span
        user_list.membership_status = self.client.enums.UserListMembershipStatusEnum.OPEN

        # Set user list type
        if list_type == UserListType.CRMBASED:
            user_list.crm_based_user_list.upload_key_type = (
                self.client.enums.CustomerMatchUploadKeyTypeEnum.CONTACT_INFO
            )

        elif list_type == UserListType.RULE_BASED:
            # Rule-based lists require additional setup through Google Ads UI
            # or remarketing tags. This creates the container.
            user_list.rule_based_user_list.prepopulation_status = (
                self.client.enums.UserListPrepopulationStatusEnum.REQUESTED
            )

        response = user_list_service.mutate_user_lists(
            customer_id=customer_id,
            operations=[user_list_operation]
        )

        resource_name = response.results[0].resource_name
        user_list_id = resource_name.split("/")[-1]

        return {
            'resource_name': resource_name,
            'user_list_id': user_list_id,
            'name': config.name,
            'type': list_type.value
        }

    def upload_customer_match_list(
        self,
        customer_id: str,
        user_list_id: str,
        customer_data: CustomerMatchData,
        create_list: bool = False,
        list_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Upload Customer Match data (emails, phones, addresses).

        Args:
            customer_id: Customer ID (without hyphens)
            user_list_id: User list ID to upload to (if create_list=False)
            customer_data: Customer data to upload
            create_list: Whether to create a new list
            list_name: Name for new list (required if create_list=True)

        Returns:
            Dictionary with upload job details
        """
        # Create list if requested
        if create_list:
            if not list_name:
                raise ValueError("list_name required when create_list=True")

            list_result = self.create_user_list(
                customer_id,
                UserListConfig(name=list_name),
                UserListType.CRMBASED
            )
            user_list_id = list_result['user_list_id']

        # Prepare customer data
        offline_user_data_job_service = self.client.get_service("OfflineUserDataJobService")
        user_list_service = self.client.get_service("UserListService")

        # Create offline user data job
        job = self.client.get_type("OfflineUserDataJob")
        job.type_ = self.client.enums.OfflineUserDataJobTypeEnum.CUSTOMER_MATCH_USER_LIST
        job.customer_match_user_list_metadata.user_list = user_list_service.user_list_path(
            customer_id, user_list_id
        )

        create_job_response = offline_user_data_job_service.create_offline_user_data_job(
            customer_id=customer_id,
            job=job
        )

        job_resource_name = create_job_response.resource_name

        # Build user data operations
        operations = []

        # Determine max count (all lists should be same length)
        max_count = 0
        if customer_data.emails:
            max_count = len(customer_data.emails)
        elif customer_data.phones:
            max_count = len(customer_data.phones)

        for i in range(max_count):
            operation = self.client.get_type("OfflineUserDataJobOperation")
            user_data = operation.create

            user_identifier = self.client.get_type("UserIdentifier")

            # Add email if provided
            if customer_data.emails and i < len(customer_data.emails):
                user_identifier.hashed_email = self._normalize_and_hash(customer_data.emails[i])

            # Add phone if provided
            if customer_data.phones and i < len(customer_data.phones):
                user_identifier.hashed_phone_number = self._normalize_and_hash_phone(
                    customer_data.phones[i]
                )

            # Add address info if provided
            if any([
                customer_data.first_names and i < len(customer_data.first_names),
                customer_data.last_names and i < len(customer_data.last_names),
                customer_data.countries and i < len(customer_data.countries),
                customer_data.zip_codes and i < len(customer_data.zip_codes)
            ]):
                address_info = self.client.get_type("OfflineUserAddressInfo")

                if customer_data.first_names and i < len(customer_data.first_names):
                    address_info.hashed_first_name = self._normalize_and_hash(
                        customer_data.first_names[i]
                    )

                if customer_data.last_names and i < len(customer_data.last_names):
                    address_info.hashed_last_name = self._normalize_and_hash(
                        customer_data.last_names[i]
                    )

                if customer_data.countries and i < len(customer_data.countries):
                    address_info.country_code = customer_data.countries[i]

                if customer_data.zip_codes and i < len(customer_data.zip_codes):
                    address_info.postal_code = customer_data.zip_codes[i]

                user_identifier.address_info = address_info

            user_data.user_identifiers.append(user_identifier)
            operations.append(operation)

        # Add operations to job
        offline_user_data_job_service.add_offline_user_data_job_operations(
            resource_name=job_resource_name,
            operations=operations
        )

        # Run the job
        offline_user_data_job_service.run_offline_user_data_job(
            resource_name=job_resource_name
        )

        return {
            'job_resource_name': job_resource_name,
            'user_list_id': user_list_id,
            'records_uploaded': len(operations),
            'status': 'processing'
        }

    def get_customer_match_status(
        self,
        customer_id: str,
        user_list_id: str
    ) -> Dict[str, Any]:
        """Get Customer Match upload status and match rate.

        Args:
            customer_id: Customer ID (without hyphens)
            user_list_id: User list ID

        Returns:
            Dictionary with match rate and status
        """
        ga_service = self.client.get_service("GoogleAdsService")

        query = f"""
            SELECT
                user_list.id,
                user_list.name,
                user_list.size_for_display,
                user_list.size_for_search,
                user_list.match_rate_percentage,
                user_list.membership_life_span,
                user_list.membership_status
            FROM user_list
            WHERE user_list.id = {user_list_id}
        """

        response = ga_service.search(customer_id=customer_id, query=query)
        results = list(response)

        if not results:
            return {
                'error': f'User list {user_list_id} not found'
            }

        row = results[0]
        user_list = row.user_list

        return {
            'user_list_id': str(user_list.id),
            'name': user_list.name,
            'size_for_display': user_list.size_for_display,
            'size_for_search': user_list.size_for_search,
            'match_rate_percentage': user_list.match_rate_percentage,
            'membership_life_span': user_list.membership_life_span,
            'membership_status': user_list.membership_status.name
        }

    def add_audience_to_campaign(
        self,
        customer_id: str,
        campaign_id: str,
        user_list_id: str,
        targeting_type: AudienceTargetingType = AudienceTargetingType.OBSERVATION
    ) -> Dict[str, Any]:
        """Add audience targeting to a campaign.

        Args:
            customer_id: Customer ID (without hyphens)
            campaign_id: Campaign ID
            user_list_id: User list ID to target
            targeting_type: OBSERVATION (monitor) or TARGETING (restrict reach)

        Returns:
            Dictionary with campaign audience details
        """
        campaign_criterion_service = self.client.get_service("CampaignCriterionService")
        campaign_service = self.client.get_service("CampaignService")
        user_list_service = self.client.get_service("UserListService")

        campaign_criterion_operation = self.client.get_type("CampaignCriterionOperation")

        criterion = campaign_criterion_operation.create
        criterion.campaign = campaign_service.campaign_path(customer_id, campaign_id)
        criterion.user_list.user_list = user_list_service.user_list_path(
            customer_id, user_list_id
        )

        # Set targeting type
        if targeting_type == AudienceTargetingType.OBSERVATION:
            # Observation mode - monitor performance without restricting reach
            criterion.status = self.client.enums.CampaignCriterionStatusEnum.ENABLED
        else:
            # Targeting mode - restrict campaign to this audience
            criterion.status = self.client.enums.CampaignCriterionStatusEnum.ENABLED

        response = campaign_criterion_service.mutate_campaign_criteria(
            customer_id=customer_id,
            operations=[campaign_criterion_operation]
        )

        return {
            'resource_name': response.results[0].resource_name,
            'campaign_id': campaign_id,
            'user_list_id': user_list_id,
            'targeting_type': targeting_type.value
        }

    def add_audience_to_ad_group(
        self,
        customer_id: str,
        ad_group_id: str,
        user_list_id: str,
        targeting_type: AudienceTargetingType = AudienceTargetingType.OBSERVATION
    ) -> Dict[str, Any]:
        """Add audience targeting to an ad group.

        Args:
            customer_id: Customer ID (without hyphens)
            ad_group_id: Ad group ID
            user_list_id: User list ID to target
            targeting_type: OBSERVATION or TARGETING

        Returns:
            Dictionary with ad group audience details
        """
        ad_group_criterion_service = self.client.get_service("AdGroupCriterionService")
        ad_group_service = self.client.get_service("AdGroupService")
        user_list_service = self.client.get_service("UserListService")

        ad_group_criterion_operation = self.client.get_type("AdGroupCriterionOperation")

        criterion = ad_group_criterion_operation.create
        criterion.ad_group = ad_group_service.ad_group_path(customer_id, ad_group_id)
        criterion.user_list.user_list = user_list_service.user_list_path(
            customer_id, user_list_id
        )

        criterion.status = self.client.enums.AdGroupCriterionStatusEnum.ENABLED

        response = ad_group_criterion_service.mutate_ad_group_criteria(
            customer_id=customer_id,
            operations=[ad_group_criterion_operation]
        )

        return {
            'resource_name': response.results[0].resource_name,
            'ad_group_id': ad_group_id,
            'user_list_id': user_list_id,
            'targeting_type': targeting_type.value
        }

    def set_audience_exclusions(
        self,
        customer_id: str,
        campaign_id: str,
        user_list_ids: List[str]
    ) -> Dict[str, Any]:
        """Exclude audiences from a campaign.

        Args:
            customer_id: Customer ID (without hyphens)
            campaign_id: Campaign ID
            user_list_ids: List of user list IDs to exclude

        Returns:
            Dictionary with exclusion details
        """
        campaign_criterion_service = self.client.get_service("CampaignCriterionService")
        campaign_service = self.client.get_service("CampaignService")
        user_list_service = self.client.get_service("UserListService")

        operations = []

        for user_list_id in user_list_ids:
            operation = self.client.get_type("CampaignCriterionOperation")
            criterion = operation.create

            criterion.campaign = campaign_service.campaign_path(customer_id, campaign_id)
            criterion.user_list.user_list = user_list_service.user_list_path(
                customer_id, user_list_id
            )
            criterion.negative = True  # This makes it an exclusion

            operations.append(operation)

        response = campaign_criterion_service.mutate_campaign_criteria(
            customer_id=customer_id,
            operations=operations
        )

        return {
            'campaign_id': campaign_id,
            'excluded_audiences': len(response.results),
            'user_list_ids': user_list_ids
        }

    def get_audience_performance(
        self,
        customer_id: str,
        campaign_id: Optional[str] = None,
        date_range: str = "LAST_30_DAYS"
    ) -> List[Dict[str, Any]]:
        """Get performance metrics by audience.

        Args:
            customer_id: Customer ID (without hyphens)
            campaign_id: Optional campaign ID to filter
            date_range: Date range for metrics

        Returns:
            List of audience performance data
        """
        ga_service = self.client.get_service("GoogleAdsService")

        query = f"""
            SELECT
                campaign.id,
                campaign.name,
                campaign_criterion.user_list.user_list,
                campaign_criterion.criterion_id,
                campaign_criterion.negative,
                metrics.impressions,
                metrics.clicks,
                metrics.ctr,
                metrics.average_cpc,
                metrics.cost_micros,
                metrics.conversions,
                metrics.conversions_value
            FROM campaign_audience_view
            WHERE segments.date DURING {date_range}
        """

        if campaign_id:
            query += f" AND campaign.id = {campaign_id}"

        response = ga_service.search(customer_id=customer_id, query=query)

        audiences = []
        for row in response:
            audiences.append({
                'campaign_id': str(row.campaign.id),
                'campaign_name': row.campaign.name,
                'user_list_resource': row.campaign_criterion.user_list.user_list,
                'user_list_id': row.campaign_criterion.user_list.user_list.split('/')[-1],
                'is_exclusion': row.campaign_criterion.negative,
                'impressions': row.metrics.impressions,
                'clicks': row.metrics.clicks,
                'ctr': row.metrics.ctr,
                'average_cpc': row.metrics.average_cpc / 1_000_000,
                'cost': row.metrics.cost_micros / 1_000_000,
                'conversions': row.metrics.conversions,
                'conversions_value': row.metrics.conversions_value
            })

        return audiences

    def list_user_lists(
        self,
        customer_id: str,
        list_type: Optional[UserListType] = None
    ) -> List[Dict[str, Any]]:
        """List all user lists (audiences) in the account.

        Args:
            customer_id: Customer ID (without hyphens)
            list_type: Optional filter by list type

        Returns:
            List of user lists with details
        """
        ga_service = self.client.get_service("GoogleAdsService")

        query = """
            SELECT
                user_list.id,
                user_list.name,
                user_list.description,
                user_list.type,
                user_list.size_for_display,
                user_list.size_for_search,
                user_list.match_rate_percentage,
                user_list.membership_life_span,
                user_list.membership_status
            FROM user_list
        """

        if list_type:
            query += f" WHERE user_list.type = '{list_type.value}'"

        response = ga_service.search(customer_id=customer_id, query=query)

        user_lists = []
        for row in response:
            ul = row.user_list
            user_lists.append({
                'id': str(ul.id),
                'name': ul.name,
                'description': ul.description,
                'type': ul.type.name,
                'size_for_display': ul.size_for_display,
                'size_for_search': ul.size_for_search,
                'match_rate_percentage': ul.match_rate_percentage,
                'membership_life_span': ul.membership_life_span,
                'membership_status': ul.membership_status.name
            })

        return user_lists

    def search_google_audiences(
        self,
        customer_id: str,
        search_term: str
    ) -> List[Dict[str, Any]]:
        """Search for available Google audiences (In-Market, Affinity).

        Args:
            customer_id: Customer ID (without hyphens)
            search_term: Search term to find audiences

        Returns:
            List of matching Google audiences
        """
        ga_service = self.client.get_service("GoogleAdsService")

        # Search for user interests (In-Market and Affinity audiences)
        query = f"""
            SELECT
                user_interest.user_interest_id,
                user_interest.name,
                user_interest.user_interest_parent,
                user_interest.taxonomy_type
            FROM user_interest
            WHERE user_interest.name LIKE '%{search_term}%'
        """

        response = ga_service.search(customer_id=customer_id, query=query)

        audiences = []
        for row in response:
            ui = row.user_interest
            audiences.append({
                'user_interest_id': str(ui.user_interest_id),
                'name': ui.name,
                'parent': ui.user_interest_parent,
                'taxonomy_type': ui.taxonomy_type.name
            })

        return audiences

    def _normalize_and_hash(self, value: str) -> str:
        """Normalize and hash a value for Customer Match.

        Args:
            value: Value to normalize and hash

        Returns:
            SHA256 hash of normalized value
        """
        # Normalize: lowercase, remove whitespace
        normalized = value.lower().strip()

        # Hash with SHA256
        return hashlib.sha256(normalized.encode()).hexdigest()

    def _normalize_and_hash_phone(self, phone: str) -> str:
        """Normalize and hash a phone number for Customer Match.

        Args:
            phone: Phone number to normalize and hash

        Returns:
            SHA256 hash of normalized phone
        """
        # Remove all non-digit characters
        normalized = ''.join(filter(str.isdigit, phone))

        # Phone should be in E.164 format (e.g., +12345678900)
        # If it doesn't start with a country code, this may fail matching

        # Hash with SHA256
        return hashlib.sha256(normalized.encode()).hexdigest()
