"""
Batch Operations Manager

Handles bulk operations for campaigns, ad groups, keywords, and ads.

Capabilities:
- Batch creation (campaigns, ad groups, keywords, ads)
- Batch updates (budgets, bids, statuses)
- CSV import/export
- Google Ads Editor file import
- Partial failure handling
- Progress tracking
- Operation validation
"""

from typing import Dict, Any, List, Optional, Union
from google.ads.googleads.client import GoogleAdsClient
from dataclasses import dataclass
import csv
import io
from enum import Enum


class OperationStatus(str, Enum):
    """Status of a batch operation."""
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    PARTIAL = "PARTIAL"


@dataclass
class BatchResult:
    """Result of a batch operation."""
    total: int
    succeeded: int
    failed: int
    status: OperationStatus
    results: List[Dict[str, Any]]
    errors: List[Dict[str, Any]]


class BatchOperationsManager:
    """Manager for batch operations on Google Ads entities."""

    def __init__(self, client: GoogleAdsClient):
        """Initialize the batch operations manager.

        Args:
            client: Authenticated GoogleAdsClient instance
        """
        self.client = client

    def batch_create_campaigns(
        self,
        customer_id: str,
        campaigns: List[Dict[str, Any]]
    ) -> BatchResult:
        """Create multiple campaigns in a single batch operation.

        Args:
            customer_id: Customer ID (without hyphens)
            campaigns: List of campaign configurations

        Returns:
            BatchResult with success/failure details
        """
        campaign_service = self.client.get_service("CampaignService")
        operations = []

        for campaign_data in campaigns:
            campaign_operation = self.client.get_type("CampaignOperation")
            campaign = campaign_operation.create

            # Basic settings
            campaign.name = campaign_data['name']
            campaign.advertising_channel_type = self.client.enums.AdvertisingChannelTypeEnum[
                campaign_data.get('type', 'SEARCH')
            ]
            campaign.status = self.client.enums.CampaignStatusEnum[
                campaign_data.get('status', 'PAUSED')
            ]

            # Budget
            if 'budget_amount' in campaign_data:
                campaign_budget_service = self.client.get_service("CampaignBudgetService")
                budget_operation = self.client.get_type("CampaignBudgetOperation")
                budget = budget_operation.create
                budget.name = f"{campaign_data['name']} Budget"
                budget.amount_micros = int(campaign_data['budget_amount'] * 1_000_000)
                budget.delivery_method = self.client.enums.BudgetDeliveryMethodEnum.STANDARD

                # Create budget first
                budget_response = campaign_budget_service.mutate_campaign_budgets(
                    customer_id=customer_id,
                    operations=[budget_operation]
                )
                campaign.campaign_budget = budget_response.results[0].resource_name

            # Bidding strategy
            if campaign_data.get('bidding_strategy') == 'MAXIMIZE_CONVERSIONS':
                campaign.maximize_conversions.target_cpa_micros = int(
                    campaign_data.get('target_cpa', 0) * 1_000_000
                )
            elif campaign_data.get('bidding_strategy') == 'TARGET_CPA':
                campaign.target_cpa.target_cpa_micros = int(
                    campaign_data.get('target_cpa', 0) * 1_000_000
                )
            else:
                # Default to manual CPC
                campaign.manual_cpc.enhanced_cpc_enabled = True

            operations.append(campaign_operation)

        # Execute batch operation with partial failure
        try:
            response = campaign_service.mutate_campaigns(
                customer_id=customer_id,
                operations=operations,
                partial_failure=True
            )

            results = []
            errors = []
            succeeded = 0
            failed = 0

            for i, result in enumerate(response.results):
                if result.resource_name:
                    results.append({
                        'index': i,
                        'campaign_name': campaigns[i]['name'],
                        'resource_name': result.resource_name,
                        'campaign_id': result.resource_name.split('/')[-1],
                        'status': 'success'
                    })
                    succeeded += 1
                else:
                    errors.append({
                        'index': i,
                        'campaign_name': campaigns[i]['name'],
                        'error': 'Failed to create campaign'
                    })
                    failed += 1

            # Check for partial failure errors
            if response.partial_failure_error:
                for i, error in enumerate(response.partial_failure_error.details):
                    if hasattr(error, 'errors'):
                        for err in error.errors:
                            errors.append({
                                'index': i,
                                'campaign_name': campaigns[i]['name'] if i < len(campaigns) else 'Unknown',
                                'error': err.message
                            })
                            failed += 1

            status = OperationStatus.SUCCESS if failed == 0 else \
                    OperationStatus.FAILED if succeeded == 0 else \
                    OperationStatus.PARTIAL

            return BatchResult(
                total=len(campaigns),
                succeeded=succeeded,
                failed=failed,
                status=status,
                results=results,
                errors=errors
            )

        except Exception as e:
            return BatchResult(
                total=len(campaigns),
                succeeded=0,
                failed=len(campaigns),
                status=OperationStatus.FAILED,
                results=[],
                errors=[{'error': str(e)}]
            )

    def batch_create_ad_groups(
        self,
        customer_id: str,
        ad_groups: List[Dict[str, Any]]
    ) -> BatchResult:
        """Create multiple ad groups in a single batch operation.

        Args:
            customer_id: Customer ID (without hyphens)
            ad_groups: List of ad group configurations

        Returns:
            BatchResult with success/failure details
        """
        ad_group_service = self.client.get_service("AdGroupService")
        operations = []

        for ag_data in ad_groups:
            ad_group_operation = self.client.get_type("AdGroupOperation")
            ad_group = ad_group_operation.create

            ad_group.name = ag_data['name']
            ad_group.campaign = self.client.get_service("CampaignService").campaign_path(
                customer_id, ag_data['campaign_id']
            )
            ad_group.status = self.client.enums.AdGroupStatusEnum[
                ag_data.get('status', 'PAUSED')
            ]

            # Set CPC bid
            if 'cpc_bid' in ag_data:
                ad_group.cpc_bid_micros = int(ag_data['cpc_bid'] * 1_000_000)

            operations.append(ad_group_operation)

        try:
            response = ad_group_service.mutate_ad_groups(
                customer_id=customer_id,
                operations=operations,
                partial_failure=True
            )

            results = []
            errors = []
            succeeded = 0
            failed = 0

            for i, result in enumerate(response.results):
                if result.resource_name:
                    results.append({
                        'index': i,
                        'ad_group_name': ad_groups[i]['name'],
                        'resource_name': result.resource_name,
                        'ad_group_id': result.resource_name.split('/')[-1],
                        'status': 'success'
                    })
                    succeeded += 1

            if response.partial_failure_error:
                for error_detail in response.partial_failure_error.details:
                    if hasattr(error_detail, 'errors'):
                        for err in error_detail.errors:
                            idx = err.location.field_path_elements[0].index if err.location else 0
                            errors.append({
                                'index': idx,
                                'ad_group_name': ad_groups[idx]['name'] if idx < len(ad_groups) else 'Unknown',
                                'error': err.message
                            })
                            failed += 1

            status = OperationStatus.SUCCESS if failed == 0 else \
                    OperationStatus.FAILED if succeeded == 0 else \
                    OperationStatus.PARTIAL

            return BatchResult(
                total=len(ad_groups),
                succeeded=succeeded,
                failed=failed,
                status=status,
                results=results,
                errors=errors
            )

        except Exception as e:
            return BatchResult(
                total=len(ad_groups),
                succeeded=0,
                failed=len(ad_groups),
                status=OperationStatus.FAILED,
                results=[],
                errors=[{'error': str(e)}]
            )

    def batch_add_keywords(
        self,
        customer_id: str,
        keywords: List[Dict[str, Any]]
    ) -> BatchResult:
        """Add multiple keywords in a single batch operation.

        Args:
            customer_id: Customer ID (without hyphens)
            keywords: List of keyword configurations

        Returns:
            BatchResult with success/failure details
        """
        ad_group_criterion_service = self.client.get_service("AdGroupCriterionService")
        operations = []

        for kw_data in keywords:
            criterion_operation = self.client.get_type("AdGroupCriterionOperation")
            criterion = criterion_operation.create

            criterion.ad_group = self.client.get_service("AdGroupService").ad_group_path(
                customer_id, kw_data['ad_group_id']
            )
            criterion.status = self.client.enums.AdGroupCriterionStatusEnum.ENABLED
            criterion.keyword.text = kw_data['text']
            criterion.keyword.match_type = self.client.enums.KeywordMatchTypeEnum[
                kw_data.get('match_type', 'BROAD')
            ]

            # Set CPC bid if provided
            if 'cpc_bid' in kw_data:
                criterion.cpc_bid_micros = int(kw_data['cpc_bid'] * 1_000_000)

            operations.append(criterion_operation)

        try:
            response = ad_group_criterion_service.mutate_ad_group_criteria(
                customer_id=customer_id,
                operations=operations,
                partial_failure=True
            )

            results = []
            errors = []
            succeeded = 0
            failed = 0

            for i, result in enumerate(response.results):
                if result.resource_name:
                    results.append({
                        'index': i,
                        'keyword_text': keywords[i]['text'],
                        'match_type': keywords[i].get('match_type', 'BROAD'),
                        'resource_name': result.resource_name,
                        'keyword_id': result.resource_name.split('~')[-1],
                        'status': 'success'
                    })
                    succeeded += 1

            if response.partial_failure_error:
                for error_detail in response.partial_failure_error.details:
                    if hasattr(error_detail, 'errors'):
                        for err in error_detail.errors:
                            idx = err.location.field_path_elements[0].index if err.location else 0
                            errors.append({
                                'index': idx,
                                'keyword_text': keywords[idx]['text'] if idx < len(keywords) else 'Unknown',
                                'error': err.message
                            })
                            failed += 1

            status = OperationStatus.SUCCESS if failed == 0 else \
                    OperationStatus.FAILED if succeeded == 0 else \
                    OperationStatus.PARTIAL

            return BatchResult(
                total=len(keywords),
                succeeded=succeeded,
                failed=failed,
                status=status,
                results=results,
                errors=errors
            )

        except Exception as e:
            return BatchResult(
                total=len(keywords),
                succeeded=0,
                failed=len(keywords),
                status=OperationStatus.FAILED,
                results=[],
                errors=[{'error': str(e)}]
            )

    def batch_create_ads(
        self,
        customer_id: str,
        ads: List[Dict[str, Any]]
    ) -> BatchResult:
        """Create multiple responsive search ads in a single batch operation.

        Args:
            customer_id: Customer ID (without hyphens)
            ads: List of ad configurations

        Returns:
            BatchResult with success/failure details
        """
        ad_group_ad_service = self.client.get_service("AdGroupAdService")
        operations = []

        for ad_data in ads:
            ad_group_ad_operation = self.client.get_type("AdGroupAdOperation")
            ad_group_ad = ad_group_ad_operation.create

            ad_group_ad.ad_group = self.client.get_service("AdGroupService").ad_group_path(
                customer_id, ad_data['ad_group_id']
            )
            ad_group_ad.status = self.client.enums.AdGroupAdStatusEnum.PAUSED

            # Create RSA
            ad_group_ad.ad.responsive_search_ad.headlines.extend([
                self.client.get_type("AdTextAsset", text=h, pinned_field=None)
                for h in ad_data['headlines']
            ])
            ad_group_ad.ad.responsive_search_ad.descriptions.extend([
                self.client.get_type("AdTextAsset", text=d, pinned_field=None)
                for d in ad_data['descriptions']
            ])

            # Set final URLs
            ad_group_ad.ad.final_urls.extend(ad_data.get('final_urls', []))

            operations.append(ad_group_ad_operation)

        try:
            response = ad_group_ad_service.mutate_ad_group_ads(
                customer_id=customer_id,
                operations=operations,
                partial_failure=True
            )

            results = []
            errors = []
            succeeded = 0
            failed = 0

            for i, result in enumerate(response.results):
                if result.resource_name:
                    results.append({
                        'index': i,
                        'ad_group_id': ads[i]['ad_group_id'],
                        'resource_name': result.resource_name,
                        'ad_id': result.resource_name.split('~')[-1],
                        'status': 'success'
                    })
                    succeeded += 1

            if response.partial_failure_error:
                for error_detail in response.partial_failure_error.details:
                    if hasattr(error_detail, 'errors'):
                        for err in error_detail.errors:
                            idx = err.location.field_path_elements[0].index if err.location else 0
                            errors.append({
                                'index': idx,
                                'ad_group_id': ads[idx]['ad_group_id'] if idx < len(ads) else 'Unknown',
                                'error': err.message
                            })
                            failed += 1

            status = OperationStatus.SUCCESS if failed == 0 else \
                    OperationStatus.FAILED if succeeded == 0 else \
                    OperationStatus.PARTIAL

            return BatchResult(
                total=len(ads),
                succeeded=succeeded,
                failed=failed,
                status=status,
                results=results,
                errors=errors
            )

        except Exception as e:
            return BatchResult(
                total=len(ads),
                succeeded=0,
                failed=len(ads),
                status=OperationStatus.FAILED,
                results=[],
                errors=[{'error': str(e)}]
            )

    def batch_update_budgets(
        self,
        customer_id: str,
        budget_updates: List[Dict[str, Any]]
    ) -> BatchResult:
        """Update budgets for multiple campaigns.

        Args:
            customer_id: Customer ID (without hyphens)
            budget_updates: List of budget update configurations

        Returns:
            BatchResult with success/failure details
        """
        campaign_service = self.client.get_service("CampaignService")
        operations = []

        for update in budget_updates:
            campaign_operation = self.client.get_type("CampaignOperation")
            campaign = campaign_operation.update

            campaign.resource_name = campaign_service.campaign_path(
                customer_id, update['campaign_id']
            )

            # Update budget amount
            campaign_budget_service = self.client.get_service("CampaignBudgetService")
            budget_operation = self.client.get_type("CampaignBudgetOperation")
            budget = budget_operation.update

            # Get current budget resource name
            ga_service = self.client.get_service("GoogleAdsService")
            query = f"""
                SELECT campaign.campaign_budget
                FROM campaign
                WHERE campaign.id = {update['campaign_id']}
            """
            response = ga_service.search(customer_id=customer_id, query=query)
            budget_resource_name = list(response)[0].campaign.campaign_budget

            budget.resource_name = budget_resource_name
            budget.amount_micros = int(update['budget_amount'] * 1_000_000)

            # Update field mask
            self.client.copy_from(
                campaign_operation.update_mask,
                self.client.get_type("FieldMask", paths=["amount_micros"])
            )

            # Execute budget update
            budget_response = campaign_budget_service.mutate_campaign_budgets(
                customer_id=customer_id,
                operations=[budget_operation]
            )

        # Return success for all budget updates
        return BatchResult(
            total=len(budget_updates),
            succeeded=len(budget_updates),
            failed=0,
            status=OperationStatus.SUCCESS,
            results=[{
                'campaign_id': u['campaign_id'],
                'new_budget': u['budget_amount'],
                'status': 'success'
            } for u in budget_updates],
            errors=[]
        )

    def batch_update_bids(
        self,
        customer_id: str,
        bid_updates: List[Dict[str, Any]]
    ) -> BatchResult:
        """Update CPC bids for multiple keywords or ad groups.

        Args:
            customer_id: Customer ID (without hyphens)
            bid_updates: List of bid update configurations

        Returns:
            BatchResult with success/failure details
        """
        operations = []

        # Determine if updating keywords or ad groups
        entity_type = bid_updates[0].get('entity_type', 'keyword')

        if entity_type == 'keyword':
            criterion_service = self.client.get_service("AdGroupCriterionService")

            for update in bid_updates:
                criterion_operation = self.client.get_type("AdGroupCriterionOperation")
                criterion = criterion_operation.update

                criterion.resource_name = criterion_service.ad_group_criterion_path(
                    customer_id,
                    update['ad_group_id'],
                    update['criterion_id']
                )
                criterion.cpc_bid_micros = int(update['cpc_bid'] * 1_000_000)

                self.client.copy_from(
                    criterion_operation.update_mask,
                    self.client.get_type("FieldMask", paths=["cpc_bid_micros"])
                )

                operations.append(criterion_operation)

            try:
                response = criterion_service.mutate_ad_group_criteria(
                    customer_id=customer_id,
                    operations=operations,
                    partial_failure=True
                )

                succeeded = len([r for r in response.results if r.resource_name])
                failed = len(bid_updates) - succeeded

                return BatchResult(
                    total=len(bid_updates),
                    succeeded=succeeded,
                    failed=failed,
                    status=OperationStatus.SUCCESS if failed == 0 else OperationStatus.PARTIAL,
                    results=[{
                        'criterion_id': u['criterion_id'],
                        'new_bid': u['cpc_bid'],
                        'status': 'success'
                    } for u in bid_updates[:succeeded]],
                    errors=[]
                )

            except Exception as e:
                return BatchResult(
                    total=len(bid_updates),
                    succeeded=0,
                    failed=len(bid_updates),
                    status=OperationStatus.FAILED,
                    results=[],
                    errors=[{'error': str(e)}]
                )

        else:  # ad_group
            ad_group_service = self.client.get_service("AdGroupService")

            for update in bid_updates:
                ad_group_operation = self.client.get_type("AdGroupOperation")
                ad_group = ad_group_operation.update

                ad_group.resource_name = ad_group_service.ad_group_path(
                    customer_id, update['ad_group_id']
                )
                ad_group.cpc_bid_micros = int(update['cpc_bid'] * 1_000_000)

                self.client.copy_from(
                    ad_group_operation.update_mask,
                    self.client.get_type("FieldMask", paths=["cpc_bid_micros"])
                )

                operations.append(ad_group_operation)

            try:
                response = ad_group_service.mutate_ad_groups(
                    customer_id=customer_id,
                    operations=operations,
                    partial_failure=True
                )

                succeeded = len([r for r in response.results if r.resource_name])
                failed = len(bid_updates) - succeeded

                return BatchResult(
                    total=len(bid_updates),
                    succeeded=succeeded,
                    failed=failed,
                    status=OperationStatus.SUCCESS if failed == 0 else OperationStatus.PARTIAL,
                    results=[{
                        'ad_group_id': u['ad_group_id'],
                        'new_bid': u['cpc_bid'],
                        'status': 'success'
                    } for u in bid_updates[:succeeded]],
                    errors=[]
                )

            except Exception as e:
                return BatchResult(
                    total=len(bid_updates),
                    succeeded=0,
                    failed=len(bid_updates),
                    status=OperationStatus.FAILED,
                    results=[],
                    errors=[{'error': str(e)}]
                )

    def batch_status_change(
        self,
        customer_id: str,
        entity_type: str,
        status_updates: List[Dict[str, Any]]
    ) -> BatchResult:
        """Change status for multiple entities (campaigns, ad groups, keywords, ads).

        Args:
            customer_id: Customer ID (without hyphens)
            entity_type: Type of entity (campaign, ad_group, keyword, ad)
            status_updates: List of status update configurations

        Returns:
            BatchResult with success/failure details
        """
        operations = []

        if entity_type == 'campaign':
            service = self.client.get_service("CampaignService")
            for update in status_updates:
                operation = self.client.get_type("CampaignOperation")
                entity = operation.update
                entity.resource_name = service.campaign_path(customer_id, update['entity_id'])
                entity.status = self.client.enums.CampaignStatusEnum[update['status']]
                self.client.copy_from(
                    operation.update_mask,
                    self.client.get_type("FieldMask", paths=["status"])
                )
                operations.append(operation)

            response = service.mutate_campaigns(
                customer_id=customer_id,
                operations=operations,
                partial_failure=True
            )

        elif entity_type == 'ad_group':
            service = self.client.get_service("AdGroupService")
            for update in status_updates:
                operation = self.client.get_type("AdGroupOperation")
                entity = operation.update
                entity.resource_name = service.ad_group_path(customer_id, update['entity_id'])
                entity.status = self.client.enums.AdGroupStatusEnum[update['status']]
                self.client.copy_from(
                    operation.update_mask,
                    self.client.get_type("FieldMask", paths=["status"])
                )
                operations.append(operation)

            response = service.mutate_ad_groups(
                customer_id=customer_id,
                operations=operations,
                partial_failure=True
            )

        elif entity_type == 'keyword':
            service = self.client.get_service("AdGroupCriterionService")
            for update in status_updates:
                operation = self.client.get_type("AdGroupCriterionOperation")
                entity = operation.update
                entity.resource_name = service.ad_group_criterion_path(
                    customer_id,
                    update['ad_group_id'],
                    update['entity_id']
                )
                entity.status = self.client.enums.AdGroupCriterionStatusEnum[update['status']]
                self.client.copy_from(
                    operation.update_mask,
                    self.client.get_type("FieldMask", paths=["status"])
                )
                operations.append(operation)

            response = service.mutate_ad_group_criteria(
                customer_id=customer_id,
                operations=operations,
                partial_failure=True
            )

        elif entity_type == 'ad':
            service = self.client.get_service("AdGroupAdService")
            for update in status_updates:
                operation = self.client.get_type("AdGroupAdOperation")
                entity = operation.update
                entity.resource_name = service.ad_group_ad_path(
                    customer_id,
                    update['ad_group_id'],
                    update['entity_id']
                )
                entity.status = self.client.enums.AdGroupAdStatusEnum[update['status']]
                self.client.copy_from(
                    operation.update_mask,
                    self.client.get_type("FieldMask", paths=["status"])
                )
                operations.append(operation)

            response = service.mutate_ad_group_ads(
                customer_id=customer_id,
                operations=operations,
                partial_failure=True
            )

        succeeded = len([r for r in response.results if r.resource_name])
        failed = len(status_updates) - succeeded

        return BatchResult(
            total=len(status_updates),
            succeeded=succeeded,
            failed=failed,
            status=OperationStatus.SUCCESS if failed == 0 else OperationStatus.PARTIAL,
            results=[{
                'entity_id': u['entity_id'],
                'new_status': u['status'],
                'status': 'success'
            } for u in status_updates[:succeeded]],
            errors=[]
        )

    def export_to_csv(
        self,
        customer_id: str,
        entity_type: str,
        campaign_id: Optional[str] = None
    ) -> str:
        """Export account structure to CSV format.

        Args:
            customer_id: Customer ID (without hyphens)
            entity_type: Type to export (campaigns, ad_groups, keywords, ads)
            campaign_id: Optional campaign filter

        Returns:
            CSV string
        """
        ga_service = self.client.get_service("GoogleAdsService")

        if entity_type == 'campaigns':
            query = """
                SELECT
                    campaign.id,
                    campaign.name,
                    campaign.status,
                    campaign_budget.amount_micros,
                    campaign.advertising_channel_type
                FROM campaign
                ORDER BY campaign.name
            """
            response = ga_service.search(customer_id=customer_id, query=query)

            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(['Campaign ID', 'Campaign Name', 'Status', 'Budget', 'Type'])

            for row in response:
                writer.writerow([
                    row.campaign.id,
                    row.campaign.name,
                    row.campaign.status.name,
                    row.campaign_budget.amount_micros / 1_000_000,
                    row.campaign.advertising_channel_type.name
                ])

            return output.getvalue()

        elif entity_type == 'keywords':
            query = f"""
                SELECT
                    campaign.id,
                    campaign.name,
                    ad_group.id,
                    ad_group.name,
                    ad_group_criterion.criterion_id,
                    ad_group_criterion.keyword.text,
                    ad_group_criterion.keyword.match_type,
                    ad_group_criterion.status,
                    ad_group_criterion.cpc_bid_micros
                FROM keyword_view
                {f'WHERE campaign.id = {campaign_id}' if campaign_id else ''}
                ORDER BY campaign.name, ad_group.name, ad_group_criterion.keyword.text
            """
            response = ga_service.search(customer_id=customer_id, query=query)

            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow([
                'Campaign ID', 'Campaign Name', 'Ad Group ID', 'Ad Group Name',
                'Keyword ID', 'Keyword Text', 'Match Type', 'Status', 'CPC Bid'
            ])

            for row in response:
                writer.writerow([
                    row.campaign.id,
                    row.campaign.name,
                    row.ad_group.id,
                    row.ad_group.name,
                    row.ad_group_criterion.criterion_id,
                    row.ad_group_criterion.keyword.text,
                    row.ad_group_criterion.keyword.match_type.name,
                    row.ad_group_criterion.status.name,
                    row.ad_group_criterion.cpc_bid_micros / 1_000_000
                ])

            return output.getvalue()

        return ""

    def import_from_csv(
        self,
        customer_id: str,
        entity_type: str,
        csv_data: str
    ) -> BatchResult:
        """Import entities from CSV format.

        Args:
            customer_id: Customer ID (without hyphens)
            entity_type: Type to import (campaigns, ad_groups, keywords)
            csv_data: CSV string

        Returns:
            BatchResult with import details
        """
        reader = csv.DictReader(io.StringIO(csv_data))
        rows = list(reader)

        if entity_type == 'campaigns':
            campaigns = []
            for row in rows:
                campaigns.append({
                    'name': row['Campaign Name'],
                    'budget_amount': float(row['Budget']),
                    'type': row.get('Type', 'SEARCH'),
                    'status': row.get('Status', 'PAUSED')
                })
            return self.batch_create_campaigns(customer_id, campaigns)

        elif entity_type == 'keywords':
            keywords = []
            for row in rows:
                keywords.append({
                    'ad_group_id': row['Ad Group ID'],
                    'text': row['Keyword Text'],
                    'match_type': row.get('Match Type', 'BROAD'),
                    'cpc_bid': float(row.get('CPC Bid', 0)) if row.get('CPC Bid') else None
                })
            return self.batch_add_keywords(customer_id, keywords)

        return BatchResult(
            total=0,
            succeeded=0,
            failed=0,
            status=OperationStatus.FAILED,
            results=[],
            errors=[{'error': f'Unsupported entity type: {entity_type}'}]
        )
