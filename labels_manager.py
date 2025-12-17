"""
Google Ads Account Labels Manager

Handles label creation, application, and management for organizing campaigns,
ad groups, ads, and keywords.
"""

from typing import Dict, List, Optional, Any
from google.ads.googleads.client import GoogleAdsClient
from performance_logger import performance_logger
from audit_logger import audit_logger


class LabelsManager:
    """Manager for Google Ads account labels."""

    def __init__(self, client: GoogleAdsClient):
        """Initialize the labels manager.

        Args:
            client: Google Ads API client instance
        """
        self.client = client

    def manage_account_labels(
        self,
        customer_id: str,
        action: str,
        label_name: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        label_id: Optional[str] = None,
        description: Optional[str] = None,
        background_color: str = "#FFFFFF",
        text_color: str = "#000000"
    ) -> Dict[str, Any]:
        """Manage account labels (create, apply, remove, list).

        Args:
            customer_id: Google Ads customer ID (without hyphens)
            action: Action to perform (create, apply, remove, list, delete)
            label_name: Label name (required for create, apply, remove)
            resource_type: Resource type (campaign, ad_group, ad, keyword) - required for apply/remove
            resource_id: Resource ID - required for apply/remove
            label_id: Label ID - required for delete
            description: Optional label description (for create)
            background_color: Label background color hex code (for create)
            text_color: Label text color hex code (for create)

        Returns:
            Dictionary with action result
        """
        with performance_logger.track_operation(self, 'manage_account_labels'):
            if action == "create":
                return self._create_label(
                    customer_id,
                    label_name,
                    description,
                    background_color,
                    text_color
                )
            elif action == "apply":
                return self._apply_label(
                    customer_id,
                    label_name,
                    resource_type,
                    resource_id
                )
            elif action == "remove":
                return self._remove_label(
                    customer_id,
                    label_name,
                    resource_type,
                    resource_id
                )
            elif action == "list":
                return self._list_labels(customer_id, resource_type, resource_id)
            elif action == "delete":
                return self._delete_label(customer_id, label_id or label_name)
            else:
                raise ValueError(f"Invalid action: {action}. Must be create, apply, remove, list, or delete")

    def _create_label(
        self,
        customer_id: str,
        label_name: str,
        description: Optional[str] = None,
        background_color: str = "#FFFFFF",
        text_color: str = "#000000"
    ) -> Dict[str, Any]:
        """Create a new label.

        Args:
            customer_id: Customer ID
            label_name: Label name
            description: Optional description
            background_color: Background color hex
            text_color: Text color hex

        Returns:
            Created label details
        """
        if not label_name:
            raise ValueError("label_name is required for create action")

        label_service = self.client.get_service("LabelService")
        label_operation = self.client.get_type("LabelOperation")

        label = label_operation.create
        label.name = label_name

        if description:
            label.description = description

        # Set status
        label.status = self.client.enums.LabelStatusEnum.ENABLED

        # Set colors
        if background_color:
            label.background_color = background_color
        if text_color:
            label.text_color = text_color

        response = label_service.mutate_labels(
            customer_id=customer_id,
            operations=[label_operation]
        )

        label_resource_name = response.results[0].resource_name
        label_id = label_resource_name.split('/')[-1]

        audit_logger.log_api_call(
            operation='create_label',
            customer_id=customer_id,
            details={'label_name': label_name, 'label_id': label_id}
        )

        return {
            'action': 'created',
            'label_id': label_id,
            'label_name': label_name,
            'description': description,
            'background_color': background_color,
            'text_color': text_color,
            'resource_name': label_resource_name
        }

    def _apply_label(
        self,
        customer_id: str,
        label_name: str,
        resource_type: str,
        resource_id: str
    ) -> Dict[str, Any]:
        """Apply label to a resource.

        Args:
            customer_id: Customer ID
            label_name: Label name
            resource_type: Resource type (campaign, ad_group, ad, keyword)
            resource_id: Resource ID

        Returns:
            Application confirmation
        """
        if not all([label_name, resource_type, resource_id]):
            raise ValueError("label_name, resource_type, and resource_id are required for apply action")

        # Get label ID by name
        label_id = self._get_label_id_by_name(customer_id, label_name)

        if not label_id:
            raise ValueError(f"Label '{label_name}' not found. Create it first.")

        # Apply label based on resource type
        if resource_type == "campaign":
            service_name = "CampaignLabelService"
            operation_type = "CampaignLabelOperation"
            label_operation = self.client.get_type(operation_type)
            label_link = label_operation.create
            label_link.campaign = self.client.get_service("CampaignService").campaign_path(customer_id, resource_id)
            label_link.label = self.client.get_service("LabelService").label_path(customer_id, label_id)

        elif resource_type == "ad_group":
            service_name = "AdGroupLabelService"
            operation_type = "AdGroupLabelOperation"
            label_operation = self.client.get_type(operation_type)
            label_link = label_operation.create
            label_link.ad_group = self.client.get_service("AdGroupService").ad_group_path(customer_id, resource_id)
            label_link.label = self.client.get_service("LabelService").label_path(customer_id, label_id)

        elif resource_type == "ad":
            service_name = "AdGroupAdLabelService"
            operation_type = "AdGroupAdLabelOperation"
            # For ads, resource_id should be in format "adGroupId_adId"
            ad_group_id, ad_id = resource_id.split('_')
            label_operation = self.client.get_type(operation_type)
            label_link = label_operation.create
            label_link.ad_group_ad = self.client.get_service("AdGroupAdService").ad_group_ad_path(
                customer_id, ad_group_id, ad_id
            )
            label_link.label = self.client.get_service("LabelService").label_path(customer_id, label_id)

        elif resource_type == "keyword":
            service_name = "AdGroupCriterionLabelService"
            operation_type = "AdGroupCriterionLabelOperation"
            # For keywords, resource_id should be in format "adGroupId_criterionId"
            ad_group_id, criterion_id = resource_id.split('_')
            label_operation = self.client.get_type(operation_type)
            label_link = label_operation.create
            label_link.ad_group_criterion = self.client.get_service("AdGroupCriterionService").ad_group_criterion_path(
                customer_id, ad_group_id, criterion_id
            )
            label_link.label = self.client.get_service("LabelService").label_path(customer_id, label_id)

        else:
            raise ValueError(f"Invalid resource_type: {resource_type}. Must be campaign, ad_group, ad, or keyword")

        # Apply the label
        service = self.client.get_service(service_name)
        response = service.mutate(
            customer_id=customer_id,
            operations=[label_operation]
        )

        audit_logger.log_api_call(
            operation='apply_label',
            customer_id=customer_id,
            details={
                'label_name': label_name,
                'resource_type': resource_type,
                'resource_id': resource_id
            }
        )

        return {
            'action': 'applied',
            'label_name': label_name,
            'label_id': label_id,
            'resource_type': resource_type,
            'resource_id': resource_id
        }

    def _remove_label(
        self,
        customer_id: str,
        label_name: str,
        resource_type: str,
        resource_id: str
    ) -> Dict[str, Any]:
        """Remove label from a resource.

        Args:
            customer_id: Customer ID
            label_name: Label name
            resource_type: Resource type
            resource_id: Resource ID

        Returns:
            Removal confirmation
        """
        if not all([label_name, resource_type, resource_id]):
            raise ValueError("label_name, resource_type, and resource_id are required for remove action")

        # Get label ID by name
        label_id = self._get_label_id_by_name(customer_id, label_name)

        if not label_id:
            raise ValueError(f"Label '{label_name}' not found")

        # Build resource name to remove
        if resource_type == "campaign":
            service_name = "CampaignLabelService"
            operation_type = "CampaignLabelOperation"
            resource_name = self.client.get_service(service_name).campaign_label_path(
                customer_id, resource_id, label_id
            )

        elif resource_type == "ad_group":
            service_name = "AdGroupLabelService"
            operation_type = "AdGroupLabelOperation"
            resource_name = self.client.get_service(service_name).ad_group_label_path(
                customer_id, resource_id, label_id
            )

        elif resource_type == "ad":
            service_name = "AdGroupAdLabelService"
            operation_type = "AdGroupAdLabelOperation"
            ad_group_id, ad_id = resource_id.split('_')
            resource_name = self.client.get_service(service_name).ad_group_ad_label_path(
                customer_id, ad_group_id, ad_id, label_id
            )

        elif resource_type == "keyword":
            service_name = "AdGroupCriterionLabelService"
            operation_type = "AdGroupCriterionLabelOperation"
            ad_group_id, criterion_id = resource_id.split('_')
            resource_name = self.client.get_service(service_name).ad_group_criterion_label_path(
                customer_id, ad_group_id, criterion_id, label_id
            )

        else:
            raise ValueError(f"Invalid resource_type: {resource_type}")

        # Remove the label
        label_operation = self.client.get_type(operation_type)
        label_operation.remove = resource_name

        service = self.client.get_service(service_name)
        service.mutate(
            customer_id=customer_id,
            operations=[label_operation]
        )

        audit_logger.log_api_call(
            operation='remove_label',
            customer_id=customer_id,
            details={
                'label_name': label_name,
                'resource_type': resource_type,
                'resource_id': resource_id
            }
        )

        return {
            'action': 'removed',
            'label_name': label_name,
            'resource_type': resource_type,
            'resource_id': resource_id
        }

    def _list_labels(
        self,
        customer_id: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """List all labels or labels for a specific resource.

        Args:
            customer_id: Customer ID
            resource_type: Optional resource type filter
            resource_id: Optional resource ID filter

        Returns:
            List of labels
        """
        if resource_type and resource_id:
            # Get labels for specific resource
            query_parts = []

            if resource_type == "campaign":
                query_parts = [
                    "SELECT campaign_label.label, label.name, label.description,",
                    "label.status, label.background_color, label.text_color",
                    "FROM campaign_label",
                    f"WHERE campaign.id = {resource_id}"
                ]
            elif resource_type == "ad_group":
                query_parts = [
                    "SELECT ad_group_label.label, label.name, label.description,",
                    "label.status, label.background_color, label.text_color",
                    "FROM ad_group_label",
                    f"WHERE ad_group.id = {resource_id}"
                ]
            elif resource_type == "ad":
                ad_group_id, ad_id = resource_id.split('_')
                query_parts = [
                    "SELECT ad_group_ad_label.label, label.name, label.description,",
                    "label.status, label.background_color, label.text_color",
                    "FROM ad_group_ad_label",
                    f"WHERE ad_group.id = {ad_group_id} AND ad_group_ad.ad.id = {ad_id}"
                ]
            elif resource_type == "keyword":
                ad_group_id, criterion_id = resource_id.split('_')
                query_parts = [
                    "SELECT ad_group_criterion_label.label, label.name, label.description,",
                    "label.status, label.background_color, label.text_color",
                    "FROM ad_group_criterion_label",
                    f"WHERE ad_group.id = {ad_group_id} AND ad_group_criterion.criterion_id = {criterion_id}"
                ]
            else:
                raise ValueError(f"Invalid resource_type: {resource_type}")

            query = " ".join(query_parts)

        else:
            # Get all labels
            query = """
                SELECT label.id, label.name, label.description, label.status,
                       label.background_color, label.text_color
                FROM label
                ORDER BY label.name
            """

        ga_service = self.client.get_service("GoogleAdsService")
        request = self.client.get_type("SearchGoogleAdsRequest")
        request.customer_id = customer_id
        request.query = query.strip()

        response = ga_service.search(request=request)

        labels = []
        for row in response:
            label_data = {
                'label_id': row.label.id if hasattr(row, 'label') else None,
                'label_name': row.label.name,
                'description': row.label.description if row.label.description else '',
                'status': row.label.status.name,
                'background_color': row.label.background_color,
                'text_color': row.label.text_color
            }
            labels.append(label_data)

        audit_logger.log_api_call(
            operation='list_labels',
            customer_id=customer_id,
            details={'resource_type': resource_type, 'resource_id': resource_id}
        )

        return {
            'action': 'listed',
            'total_labels': len(labels),
            'labels': labels,
            'resource_type': resource_type,
            'resource_id': resource_id
        }

    def _delete_label(
        self,
        customer_id: str,
        label_identifier: str
    ) -> Dict[str, Any]:
        """Delete a label entirely.

        Args:
            customer_id: Customer ID
            label_identifier: Label ID or label name

        Returns:
            Deletion confirmation
        """
        if not label_identifier:
            raise ValueError("label_id or label_name is required for delete action")

        # Check if identifier is a name or ID
        if label_identifier.isdigit():
            label_id = label_identifier
        else:
            label_id = self._get_label_id_by_name(customer_id, label_identifier)

        if not label_id:
            raise ValueError(f"Label '{label_identifier}' not found")

        label_service = self.client.get_service("LabelService")
        label_operation = self.client.get_type("LabelOperation")

        label_operation.remove = label_service.label_path(customer_id, label_id)

        label_service.mutate_labels(
            customer_id=customer_id,
            operations=[label_operation]
        )

        audit_logger.log_api_call(
            operation='delete_label',
            customer_id=customer_id,
            details={'label_id': label_id}
        )

        return {
            'action': 'deleted',
            'label_id': label_id
        }

    def _get_label_id_by_name(
        self,
        customer_id: str,
        label_name: str
    ) -> Optional[str]:
        """Get label ID by label name.

        Args:
            customer_id: Customer ID
            label_name: Label name

        Returns:
            Label ID if found, None otherwise
        """
        query = f"""
            SELECT label.id
            FROM label
            WHERE label.name = '{label_name}'
            LIMIT 1
        """

        ga_service = self.client.get_service("GoogleAdsService")
        request = self.client.get_type("SearchGoogleAdsRequest")
        request.customer_id = customer_id
        request.query = query

        try:
            response = ga_service.search(request=request)
            for row in response:
                return str(row.label.id)
        except Exception:
            return None

        return None


def create_labels_manager(client: GoogleAdsClient) -> LabelsManager:
    """Create a labels manager instance.

    Args:
        client: Google Ads client

    Returns:
        Labels manager instance
    """
    return LabelsManager(client)
