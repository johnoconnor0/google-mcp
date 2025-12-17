"""
MCP Tools - Batch Operations

Tools for bulk operations on campaigns, ad groups, keywords, and ads.

Tools:
1. google_ads_batch_create_campaigns - Create multiple campaigns
2. google_ads_batch_create_ad_groups - Create multiple ad groups
3. google_ads_batch_add_keywords - Add multiple keywords
4. google_ads_batch_create_ads - Create multiple ads
5. google_ads_batch_update_budgets - Update multiple budgets
6. google_ads_batch_update_bids - Update multiple bids
7. google_ads_batch_pause_campaigns - Pause multiple campaigns
8. google_ads_batch_enable_campaigns - Enable multiple campaigns
9. google_ads_batch_status_change - Change status for multiple entities
10. google_ads_export_to_csv - Export account structure to CSV
11. google_ads_import_from_csv - Import entities from CSV
"""

from typing import List, Dict, Any, Optional
from batch_operations_manager import BatchOperationsManager, BatchResult
from auth_manager import get_auth_manager
from error_handler import ErrorHandler
from logger import get_logger, get_performance_logger, get_audit_logger
import json

logger = get_logger(__name__)
performance_logger = get_performance_logger()
audit_logger = get_audit_logger()


def register_batch_tools(mcp):
    """Register all batch operation MCP tools."""

    @mcp.tool()
    def google_ads_batch_create_campaigns(
        customer_id: str,
        campaigns_json: str
    ) -> str:
        """Create multiple campaigns in a single batch operation.

        Supports partial failure - some campaigns may succeed while others fail.

        Args:
            customer_id: Google Ads customer ID (10 digits, no hyphens)
            campaigns_json: JSON array of campaign configurations

        Campaign Configuration Schema:
        ```json
        [
          {
            "name": "Campaign Name",
            "type": "SEARCH",
            "status": "PAUSED",
            "budget_amount": 50.00,
            "bidding_strategy": "MAXIMIZE_CONVERSIONS",
            "target_cpa": 25.00
          }
        ]
        ```

        Required Fields: name, budget_amount
        Optional Fields: type (default: SEARCH), status (default: PAUSED),
                        bidding_strategy, target_cpa

        Returns:
            Batch operation result with success/failure details

        Example:
            google_ads_batch_create_campaigns(
                customer_id="1234567890",
                campaigns_json='[{"name": "Campaign 1", "budget_amount": 50}, ...]'
            )
        """
        with performance_logger.track_operation('batch_create_campaigns', customer_id=customer_id):
            try:
                client = get_auth_manager().get_client()
                batch_manager = BatchOperationsManager(client)

                # Parse campaigns JSON
                campaigns = json.loads(campaigns_json)

                if not isinstance(campaigns, list):
                    return "❌ campaigns_json must be a JSON array"

                if len(campaigns) == 0:
                    return "❌ campaigns_json cannot be empty"

                # Execute batch operation
                result = batch_manager.batch_create_campaigns(customer_id, campaigns)

                audit_logger.log_api_call(
                    customer_id=customer_id,
                    operation='batch_create_campaigns',
                    details={'total': result.total, 'succeeded': result.succeeded, 'failed': result.failed},
                    status='success' if result.status.value != 'FAILED' else 'failed'
                )

                # Format response
                output = f"# 🚀 Batch Campaign Creation\n\n"
                output += f"**Status**: {result.status.value}\n"
                output += f"**Total**: {result.total} campaigns\n"
                output += f"**Succeeded**: {result.succeeded} ✅\n"
                output += f"**Failed**: {result.failed} ❌\n\n"

                if result.succeeded > 0:
                    output += "## ✅ Successfully Created\n\n"
                    for res in result.results:
                        output += f"- **{res['campaign_name']}** (ID: {res['campaign_id']})\n"
                    output += "\n"

                if result.failed > 0:
                    output += "## ❌ Failed\n\n"
                    for err in result.errors:
                        output += f"- **{err.get('campaign_name', 'Unknown')}**: {err['error']}\n"
                    output += "\n"

                return output

            except json.JSONDecodeError as e:
                return f"❌ Invalid JSON format: {str(e)}"
            except Exception as e:
                error_msg = ErrorHandler.handle_error(e, context="batch_create_campaigns")
                return f"❌ Batch operation failed: {error_msg}"

    @mcp.tool()
    def google_ads_batch_create_ad_groups(
        customer_id: str,
        ad_groups_json: str
    ) -> str:
        """Create multiple ad groups in a single batch operation.

        Args:
            customer_id: Google Ads customer ID (10 digits, no hyphens)
            ad_groups_json: JSON array of ad group configurations

        Ad Group Configuration Schema:
        ```json
        [
          {
            "name": "Ad Group Name",
            "campaign_id": "12345678",
            "status": "PAUSED",
            "cpc_bid": 2.50
          }
        ]
        ```

        Required Fields: name, campaign_id
        Optional Fields: status (default: PAUSED), cpc_bid

        Returns:
            Batch operation result with success/failure details

        Example:
            google_ads_batch_create_ad_groups(
                customer_id="1234567890",
                ad_groups_json='[{"name": "Ad Group 1", "campaign_id": "12345678", "cpc_bid": 2.50}]'
            )
        """
        with performance_logger.track_operation('batch_create_ad_groups', customer_id=customer_id):
            try:
                client = get_auth_manager().get_client()
                batch_manager = BatchOperationsManager(client)

                ad_groups = json.loads(ad_groups_json)

                if not isinstance(ad_groups, list):
                    return "❌ ad_groups_json must be a JSON array"

                result = batch_manager.batch_create_ad_groups(customer_id, ad_groups)

                audit_logger.log_api_call(
                    customer_id=customer_id,
                    operation='batch_create_ad_groups',
                    details={'total': result.total, 'succeeded': result.succeeded},
                    status='success' if result.status.value != 'FAILED' else 'failed'
                )

                output = f"# 🚀 Batch Ad Group Creation\n\n"
                output += f"**Status**: {result.status.value}\n"
                output += f"**Total**: {result.total} ad groups\n"
                output += f"**Succeeded**: {result.succeeded} ✅\n"
                output += f"**Failed**: {result.failed} ❌\n\n"

                if result.succeeded > 0:
                    output += "## ✅ Successfully Created\n\n"
                    for res in result.results:
                        output += f"- **{res['ad_group_name']}** (ID: {res['ad_group_id']})\n"

                if result.failed > 0:
                    output += "\n## ❌ Failed\n\n"
                    for err in result.errors:
                        output += f"- **{err.get('ad_group_name', 'Unknown')}**: {err['error']}\n"

                return output

            except json.JSONDecodeError as e:
                return f"❌ Invalid JSON format: {str(e)}"
            except Exception as e:
                error_msg = ErrorHandler.handle_error(e, context="batch_create_ad_groups")
                return f"❌ Batch operation failed: {error_msg}"

    @mcp.tool()
    def google_ads_batch_add_keywords(
        customer_id: str,
        keywords_json: str
    ) -> str:
        """Add multiple keywords in a single batch operation.

        Args:
            customer_id: Google Ads customer ID (10 digits, no hyphens)
            keywords_json: JSON array of keyword configurations

        Keyword Configuration Schema:
        ```json
        [
          {
            "ad_group_id": "12345678",
            "text": "keyword phrase",
            "match_type": "EXACT",
            "cpc_bid": 1.50
          }
        ]
        ```

        Required Fields: ad_group_id, text
        Optional Fields: match_type (default: BROAD), cpc_bid
        Match Types: EXACT, PHRASE, BROAD

        Returns:
            Batch operation result with success/failure details

        Example:
            google_ads_batch_add_keywords(
                customer_id="1234567890",
                keywords_json='[{"ad_group_id": "12345678", "text": "running shoes", "match_type": "EXACT"}]'
            )
        """
        with performance_logger.track_operation('batch_add_keywords', customer_id=customer_id):
            try:
                client = get_auth_manager().get_client()
                batch_manager = BatchOperationsManager(client)

                keywords = json.loads(keywords_json)

                if not isinstance(keywords, list):
                    return "❌ keywords_json must be a JSON array"

                result = batch_manager.batch_add_keywords(customer_id, keywords)

                audit_logger.log_api_call(
                    customer_id=customer_id,
                    operation='batch_add_keywords',
                    details={'total': result.total, 'succeeded': result.succeeded},
                    status='success' if result.status.value != 'FAILED' else 'failed'
                )

                output = f"# 🚀 Batch Keyword Addition\n\n"
                output += f"**Status**: {result.status.value}\n"
                output += f"**Total**: {result.total} keywords\n"
                output += f"**Succeeded**: {result.succeeded} ✅\n"
                output += f"**Failed**: {result.failed} ❌\n\n"

                if result.succeeded > 0:
                    output += "## ✅ Successfully Added\n\n"
                    output += "| Keyword | Match Type | Keyword ID |\n"
                    output += "|---------|------------|------------|\n"
                    for res in result.results:
                        output += f"| {res['keyword_text']} | {res['match_type']} | {res['keyword_id']} |\n"

                if result.failed > 0:
                    output += "\n## ❌ Failed\n\n"
                    for err in result.errors:
                        output += f"- **{err.get('keyword_text', 'Unknown')}**: {err['error']}\n"

                return output

            except json.JSONDecodeError as e:
                return f"❌ Invalid JSON format: {str(e)}"
            except Exception as e:
                error_msg = ErrorHandler.handle_error(e, context="batch_add_keywords")
                return f"❌ Batch operation failed: {error_msg}"

    @mcp.tool()
    def google_ads_batch_create_ads(
        customer_id: str,
        ads_json: str
    ) -> str:
        """Create multiple responsive search ads in a single batch operation.

        Args:
            customer_id: Google Ads customer ID (10 digits, no hyphens)
            ads_json: JSON array of ad configurations

        Ad Configuration Schema:
        ```json
        [
          {
            "ad_group_id": "12345678",
            "headlines": ["Headline 1", "Headline 2", "Headline 3"],
            "descriptions": ["Description 1", "Description 2"],
            "final_urls": ["https://example.com"]
          }
        ]
        ```

        Required Fields: ad_group_id, headlines (3-15), descriptions (2-4), final_urls

        Returns:
            Batch operation result with success/failure details

        Example:
            google_ads_batch_create_ads(
                customer_id="1234567890",
                ads_json='[{"ad_group_id": "12345678", "headlines": ["H1", "H2", "H3"], ...}]'
            )
        """
        with performance_logger.track_operation('batch_create_ads', customer_id=customer_id):
            try:
                client = get_auth_manager().get_client()
                batch_manager = BatchOperationsManager(client)

                ads = json.loads(ads_json)

                if not isinstance(ads, list):
                    return "❌ ads_json must be a JSON array"

                result = batch_manager.batch_create_ads(customer_id, ads)

                audit_logger.log_api_call(
                    customer_id=customer_id,
                    operation='batch_create_ads',
                    details={'total': result.total, 'succeeded': result.succeeded},
                    status='success' if result.status.value != 'FAILED' else 'failed'
                )

                output = f"# 🚀 Batch Ad Creation\n\n"
                output += f"**Status**: {result.status.value}\n"
                output += f"**Total**: {result.total} ads\n"
                output += f"**Succeeded**: {result.succeeded} ✅\n"
                output += f"**Failed**: {result.failed} ❌\n\n"

                if result.succeeded > 0:
                    output += "## ✅ Successfully Created\n\n"
                    for res in result.results:
                        output += f"- Ad Group ID {res['ad_group_id']} → Ad ID: {res['ad_id']}\n"

                if result.failed > 0:
                    output += "\n## ❌ Failed\n\n"
                    for err in result.errors:
                        output += f"- Ad Group ID {err.get('ad_group_id', 'Unknown')}: {err['error']}\n"

                return output

            except json.JSONDecodeError as e:
                return f"❌ Invalid JSON format: {str(e)}"
            except Exception as e:
                error_msg = ErrorHandler.handle_error(e, context="batch_create_ads")
                return f"❌ Batch operation failed: {error_msg}"

    @mcp.tool()
    def google_ads_batch_update_budgets(
        customer_id: str,
        budget_updates_json: str
    ) -> str:
        """Update budgets for multiple campaigns in a single batch operation.

        Args:
            customer_id: Google Ads customer ID (10 digits, no hyphens)
            budget_updates_json: JSON array of budget update configurations

        Budget Update Schema:
        ```json
        [
          {
            "campaign_id": "12345678",
            "budget_amount": 75.00
          }
        ]
        ```

        Required Fields: campaign_id, budget_amount (daily budget in currency units)

        Returns:
            Batch operation result with success/failure details

        Example:
            google_ads_batch_update_budgets(
                customer_id="1234567890",
                budget_updates_json='[{"campaign_id": "12345678", "budget_amount": 75.00}]'
            )
        """
        with performance_logger.track_operation('batch_update_budgets', customer_id=customer_id):
            try:
                client = get_auth_manager().get_client()
                batch_manager = BatchOperationsManager(client)

                budget_updates = json.loads(budget_updates_json)

                if not isinstance(budget_updates, list):
                    return "❌ budget_updates_json must be a JSON array"

                result = batch_manager.batch_update_budgets(customer_id, budget_updates)

                audit_logger.log_api_call(
                    customer_id=customer_id,
                    operation='batch_update_budgets',
                    details={'total': result.total, 'succeeded': result.succeeded},
                    status='success'
                )

                output = f"# 💰 Batch Budget Update\n\n"
                output += f"**Status**: {result.status.value}\n"
                output += f"**Total**: {result.total} campaigns\n"
                output += f"**Succeeded**: {result.succeeded} ✅\n\n"

                output += "## Updated Budgets\n\n"
                output += "| Campaign ID | New Budget |\n"
                output += "|-------------|------------|\n"
                for res in result.results:
                    output += f"| {res['campaign_id']} | ${res['new_budget']:.2f} |\n"

                return output

            except json.JSONDecodeError as e:
                return f"❌ Invalid JSON format: {str(e)}"
            except Exception as e:
                error_msg = ErrorHandler.handle_error(e, context="batch_update_budgets")
                return f"❌ Batch operation failed: {error_msg}"

    @mcp.tool()
    def google_ads_batch_update_bids(
        customer_id: str,
        entity_type: str,
        bid_updates_json: str
    ) -> str:
        """Update CPC bids for multiple keywords or ad groups in a single batch operation.

        Args:
            customer_id: Google Ads customer ID (10 digits, no hyphens)
            entity_type: Type of entity (keyword or ad_group)
            bid_updates_json: JSON array of bid update configurations

        Bid Update Schema (Keywords):
        ```json
        [
          {
            "ad_group_id": "12345678",
            "criterion_id": "87654321",
            "cpc_bid": 2.50
          }
        ]
        ```

        Bid Update Schema (Ad Groups):
        ```json
        [
          {
            "ad_group_id": "12345678",
            "cpc_bid": 2.50
          }
        ]
        ```

        Returns:
            Batch operation result with success/failure details

        Example:
            google_ads_batch_update_bids(
                customer_id="1234567890",
                entity_type="keyword",
                bid_updates_json='[{"ad_group_id": "12345678", "criterion_id": "87654321", "cpc_bid": 2.50}]'
            )
        """
        with performance_logger.track_operation('batch_update_bids', customer_id=customer_id):
            try:
                client = get_auth_manager().get_client()
                batch_manager = BatchOperationsManager(client)

                bid_updates = json.loads(bid_updates_json)

                if not isinstance(bid_updates, list):
                    return "❌ bid_updates_json must be a JSON array"

                # Add entity_type to each update
                for update in bid_updates:
                    update['entity_type'] = entity_type

                result = batch_manager.batch_update_bids(customer_id, bid_updates)

                audit_logger.log_api_call(
                    customer_id=customer_id,
                    operation='batch_update_bids',
                    details={'total': result.total, 'succeeded': result.succeeded, 'entity_type': entity_type},
                    status='success' if result.status.value != 'FAILED' else 'failed'
                )

                output = f"# 💵 Batch Bid Update ({entity_type.title()})\n\n"
                output += f"**Status**: {result.status.value}\n"
                output += f"**Total**: {result.total} {entity_type}s\n"
                output += f"**Succeeded**: {result.succeeded} ✅\n"
                output += f"**Failed**: {result.failed} ❌\n\n"

                if result.succeeded > 0:
                    output += "## Updated Bids\n\n"
                    if entity_type == 'keyword':
                        output += "| Criterion ID | New Bid |\n"
                        output += "|--------------|----------|\n"
                        for res in result.results:
                            output += f"| {res['criterion_id']} | ${res['new_bid']:.2f} |\n"
                    else:
                        output += "| Ad Group ID | New Bid |\n"
                        output += "|-------------|----------|\n"
                        for res in result.results:
                            output += f"| {res['ad_group_id']} | ${res['new_bid']:.2f} |\n"

                return output

            except json.JSONDecodeError as e:
                return f"❌ Invalid JSON format: {str(e)}"
            except Exception as e:
                error_msg = ErrorHandler.handle_error(e, context="batch_update_bids")
                return f"❌ Batch operation failed: {error_msg}"

    @mcp.tool()
    def google_ads_batch_pause_campaigns(
        customer_id: str,
        campaign_ids: str
    ) -> str:
        """Pause multiple campaigns in a single batch operation.

        Args:
            customer_id: Google Ads customer ID (10 digits, no hyphens)
            campaign_ids: Comma-separated list of campaign IDs

        Returns:
            Batch operation result

        Example:
            google_ads_batch_pause_campaigns(
                customer_id="1234567890",
                campaign_ids="12345678,87654321,11111111"
            )
        """
        with performance_logger.track_operation('batch_pause_campaigns', customer_id=customer_id):
            try:
                client = get_auth_manager().get_client()
                batch_manager = BatchOperationsManager(client)

                # Parse campaign IDs
                ids = [id.strip() for id in campaign_ids.split(',')]

                status_updates = [
                    {'entity_id': campaign_id, 'status': 'PAUSED'}
                    for campaign_id in ids
                ]

                result = batch_manager.batch_status_change(customer_id, 'campaign', status_updates)

                audit_logger.log_api_call(
                    customer_id=customer_id,
                    operation='batch_pause_campaigns',
                    details={'total': result.total, 'succeeded': result.succeeded},
                    status='success'
                )

                output = f"# ⏸️ Batch Campaign Pause\n\n"
                output += f"**Total**: {result.total} campaigns\n"
                output += f"**Paused**: {result.succeeded} ✅\n\n"

                output += "## Paused Campaigns\n\n"
                for res in result.results:
                    output += f"- Campaign ID: {res['entity_id']}\n"

                return output

            except Exception as e:
                error_msg = ErrorHandler.handle_error(e, context="batch_pause_campaigns")
                return f"❌ Batch operation failed: {error_msg}"

    @mcp.tool()
    def google_ads_batch_enable_campaigns(
        customer_id: str,
        campaign_ids: str
    ) -> str:
        """Enable multiple campaigns in a single batch operation.

        Args:
            customer_id: Google Ads customer ID (10 digits, no hyphens)
            campaign_ids: Comma-separated list of campaign IDs

        Returns:
            Batch operation result

        Example:
            google_ads_batch_enable_campaigns(
                customer_id="1234567890",
                campaign_ids="12345678,87654321,11111111"
            )
        """
        with performance_logger.track_operation('batch_enable_campaigns', customer_id=customer_id):
            try:
                client = get_auth_manager().get_client()
                batch_manager = BatchOperationsManager(client)

                ids = [id.strip() for id in campaign_ids.split(',')]

                status_updates = [
                    {'entity_id': campaign_id, 'status': 'ENABLED'}
                    for campaign_id in ids
                ]

                result = batch_manager.batch_status_change(customer_id, 'campaign', status_updates)

                audit_logger.log_api_call(
                    customer_id=customer_id,
                    operation='batch_enable_campaigns',
                    details={'total': result.total, 'succeeded': result.succeeded},
                    status='success'
                )

                output = f"# ▶️ Batch Campaign Enable\n\n"
                output += f"**Total**: {result.total} campaigns\n"
                output += f"**Enabled**: {result.succeeded} ✅\n\n"

                output += "## Enabled Campaigns\n\n"
                for res in result.results:
                    output += f"- Campaign ID: {res['entity_id']}\n"

                return output

            except Exception as e:
                error_msg = ErrorHandler.handle_error(e, context="batch_enable_campaigns")
                return f"❌ Batch operation failed: {error_msg}"

    @mcp.tool()
    def google_ads_batch_status_change(
        customer_id: str,
        entity_type: str,
        status_updates_json: str
    ) -> str:
        """Change status for multiple entities (campaigns, ad groups, keywords, ads).

        Args:
            customer_id: Google Ads customer ID (10 digits, no hyphens)
            entity_type: Type of entity (campaign, ad_group, keyword, ad)
            status_updates_json: JSON array of status update configurations

        Status Update Schema (Campaign/Ad Group):
        ```json
        [
          {
            "entity_id": "12345678",
            "status": "ENABLED"
          }
        ]
        ```

        Status Update Schema (Keyword/Ad):
        ```json
        [
          {
            "ad_group_id": "12345678",
            "entity_id": "87654321",
            "status": "ENABLED"
          }
        ]
        ```

        Valid Statuses:
        - Campaign: ENABLED, PAUSED, REMOVED
        - Ad Group: ENABLED, PAUSED, REMOVED
        - Keyword: ENABLED, PAUSED, REMOVED
        - Ad: ENABLED, PAUSED, REMOVED

        Returns:
            Batch operation result

        Example:
            google_ads_batch_status_change(
                customer_id="1234567890",
                entity_type="campaign",
                status_updates_json='[{"entity_id": "12345678", "status": "ENABLED"}]'
            )
        """
        with performance_logger.track_operation('batch_status_change', customer_id=customer_id):
            try:
                client = get_auth_manager().get_client()
                batch_manager = BatchOperationsManager(client)

                status_updates = json.loads(status_updates_json)

                if not isinstance(status_updates, list):
                    return "❌ status_updates_json must be a JSON array"

                result = batch_manager.batch_status_change(customer_id, entity_type, status_updates)

                audit_logger.log_api_call(
                    customer_id=customer_id,
                    operation='batch_status_change',
                    details={'total': result.total, 'succeeded': result.succeeded, 'entity_type': entity_type},
                    status='success' if result.status.value != 'FAILED' else 'failed'
                )

                output = f"# 🔄 Batch Status Change ({entity_type.title()})\n\n"
                output += f"**Status**: {result.status.value}\n"
                output += f"**Total**: {result.total} {entity_type}s\n"
                output += f"**Succeeded**: {result.succeeded} ✅\n"
                output += f"**Failed**: {result.failed} ❌\n\n"

                if result.succeeded > 0:
                    output += "## Updated Status\n\n"
                    output += "| Entity ID | New Status |\n"
                    output += "|-----------|------------|\n"
                    for res in result.results:
                        output += f"| {res['entity_id']} | {res['new_status']} |\n"

                return output

            except json.JSONDecodeError as e:
                return f"❌ Invalid JSON format: {str(e)}"
            except Exception as e:
                error_msg = ErrorHandler.handle_error(e, context="batch_status_change")
                return f"❌ Batch operation failed: {error_msg}"

    @mcp.tool()
    def google_ads_export_to_csv(
        customer_id: str,
        entity_type: str,
        campaign_id: Optional[str] = None
    ) -> str:
        """Export account structure to CSV format.

        Args:
            customer_id: Google Ads customer ID (10 digits, no hyphens)
            entity_type: Type to export (campaigns, keywords)
            campaign_id: Optional campaign ID filter (for keywords export)

        Returns:
            CSV formatted data

        Example:
            google_ads_export_to_csv(
                customer_id="1234567890",
                entity_type="campaigns"
            )
        """
        with performance_logger.track_operation('export_to_csv', customer_id=customer_id):
            try:
                client = get_auth_manager().get_client()
                batch_manager = BatchOperationsManager(client)

                csv_data = batch_manager.export_to_csv(customer_id, entity_type, campaign_id)

                audit_logger.log_api_call(
                    customer_id=customer_id,
                    operation='export_to_csv',
                    details={'entity_type': entity_type},
                    status='success'
                )

                output = f"# 📊 CSV Export ({entity_type.title()})\n\n"
                output += "```csv\n"
                output += csv_data
                output += "```\n\n"
                output += f"**💡 Tip**: Copy the CSV data above to use in spreadsheets or for import operations.\n"

                return output

            except Exception as e:
                error_msg = ErrorHandler.handle_error(e, context="export_to_csv")
                return f"❌ Export failed: {error_msg}"

    @mcp.tool()
    def google_ads_import_from_csv(
        customer_id: str,
        entity_type: str,
        csv_data: str
    ) -> str:
        """Import entities from CSV format.

        Args:
            customer_id: Google Ads customer ID (10 digits, no hyphens)
            entity_type: Type to import (campaigns, keywords)
            csv_data: CSV formatted data

        CSV Format for Campaigns:
        ```
        Campaign Name,Budget,Type,Status
        My Campaign,50.00,SEARCH,PAUSED
        ```

        CSV Format for Keywords:
        ```
        Ad Group ID,Keyword Text,Match Type,CPC Bid
        12345678,running shoes,EXACT,2.50
        ```

        Returns:
            Import result with success/failure details

        Example:
            google_ads_import_from_csv(
                customer_id="1234567890",
                entity_type="campaigns",
                csv_data="Campaign Name,Budget,Type\\nTest Campaign,50.00,SEARCH"
            )
        """
        with performance_logger.track_operation('import_from_csv', customer_id=customer_id):
            try:
                client = get_auth_manager().get_client()
                batch_manager = BatchOperationsManager(client)

                result = batch_manager.import_from_csv(customer_id, entity_type, csv_data)

                audit_logger.log_api_call(
                    customer_id=customer_id,
                    operation='import_from_csv',
                    details={'entity_type': entity_type, 'total': result.total, 'succeeded': result.succeeded},
                    status='success' if result.status.value != 'FAILED' else 'failed'
                )

                output = f"# 📥 CSV Import ({entity_type.title()})\n\n"
                output += f"**Status**: {result.status.value}\n"
                output += f"**Total**: {result.total} {entity_type}\n"
                output += f"**Imported**: {result.succeeded} ✅\n"
                output += f"**Failed**: {result.failed} ❌\n\n"

                if result.succeeded > 0:
                    output += "## ✅ Successfully Imported\n\n"
                    for res in result.results:
                        output += f"- {res}\n"

                if result.failed > 0:
                    output += "\n## ❌ Failed\n\n"
                    for err in result.errors:
                        output += f"- {err['error']}\n"

                return output

            except Exception as e:
                error_msg = ErrorHandler.handle_error(e, context="import_from_csv")
                return f"❌ Import failed: {error_msg}"

    logger.info("Batch operation tools registered (11 tools)")
