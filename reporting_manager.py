"""
Reporting Manager

Handles performance reports, analytics, and comparative analysis.

Report Types:
- Account performance overview
- Geographic performance (countries, cities, regions)
- Demographic performance (age, gender, household income)
- Device performance (mobile, desktop, tablet)
- Time performance (hour of day, day of week)
- Search analytics (impression share, auction insights)
- Comparative analysis (period-over-period, YoY)
"""

from typing import Dict, Any, List, Optional
from google.ads.googleads.client import GoogleAdsClient
from datetime import datetime, timedelta


class ReportingManager:
    """Manager for performance reporting and analytics."""

    def __init__(self, client: GoogleAdsClient):
        """Initialize the reporting manager.

        Args:
            client: Authenticated GoogleAdsClient instance
        """
        self.client = client

    def get_account_performance(
        self,
        customer_id: str,
        date_range: str = "LAST_30_DAYS"
    ) -> Dict[str, Any]:
        """Get account-level performance overview.

        Args:
            customer_id: Customer ID (without hyphens)
            date_range: Date range for metrics

        Returns:
            Account performance metrics
        """
        ga_service = self.client.get_service("GoogleAdsService")

        query = f"""
            SELECT
                customer.id,
                customer.descriptive_name,
                metrics.impressions,
                metrics.clicks,
                metrics.ctr,
                metrics.average_cpc,
                metrics.cost_micros,
                metrics.conversions,
                metrics.conversions_value,
                metrics.cost_per_conversion,
                metrics.conversions_from_interactions_rate,
                metrics.search_impression_share,
                metrics.search_rank_lost_impression_share,
                metrics.search_budget_lost_impression_share
            FROM customer
            WHERE segments.date DURING {date_range}
        """

        response = ga_service.search(customer_id=customer_id, query=query)
        results = list(response)

        if not results:
            return {'error': 'No data found'}

        row = results[0]

        return {
            'customer_id': str(row.customer.id),
            'account_name': row.customer.descriptive_name,
            'impressions': row.metrics.impressions,
            'clicks': row.metrics.clicks,
            'ctr': row.metrics.ctr,
            'average_cpc': row.metrics.average_cpc / 1_000_000,
            'cost': row.metrics.cost_micros / 1_000_000,
            'conversions': row.metrics.conversions,
            'conversions_value': row.metrics.conversions_value,
            'cost_per_conversion': row.metrics.cost_per_conversion,
            'conversion_rate': row.metrics.conversions_from_interactions_rate,
            'search_impression_share': row.metrics.search_impression_share,
            'rank_lost_is': row.metrics.search_rank_lost_impression_share,
            'budget_lost_is': row.metrics.search_budget_lost_impression_share
        }

    def get_geographic_performance(
        self,
        customer_id: str,
        campaign_id: Optional[str] = None,
        date_range: str = "LAST_30_DAYS"
    ) -> List[Dict[str, Any]]:
        """Get performance by geographic location.

        Args:
            customer_id: Customer ID (without hyphens)
            campaign_id: Optional campaign ID filter
            date_range: Date range

        Returns:
            List of location performance data
        """
        ga_service = self.client.get_service("GoogleAdsService")

        query = f"""
            SELECT
                geographic_view.country_criterion_id,
                geographic_view.location_type,
                metrics.impressions,
                metrics.clicks,
                metrics.ctr,
                metrics.average_cpc,
                metrics.cost_micros,
                metrics.conversions
            FROM geographic_view
            WHERE segments.date DURING {date_range}
        """

        if campaign_id:
            query += f" AND campaign.id = {campaign_id}"

        query += " ORDER BY metrics.cost_micros DESC LIMIT 100"

        response = ga_service.search(customer_id=customer_id, query=query)

        locations = []
        for row in response:
            locations.append({
                'country_id': str(row.geographic_view.country_criterion_id),
                'location_type': row.geographic_view.location_type.name,
                'impressions': row.metrics.impressions,
                'clicks': row.metrics.clicks,
                'ctr': row.metrics.ctr,
                'average_cpc': row.metrics.average_cpc / 1_000_000,
                'cost': row.metrics.cost_micros / 1_000_000,
                'conversions': row.metrics.conversions
            })

        return locations

    def get_demographic_performance(
        self,
        customer_id: str,
        campaign_id: Optional[str] = None,
        date_range: str = "LAST_30_DAYS"
    ) -> List[Dict[str, Any]]:
        """Get performance by age and gender demographics.

        Args:
            customer_id: Customer ID (without hyphens)
            campaign_id: Optional campaign ID filter
            date_range: Date range

        Returns:
            List of demographic performance data
        """
        ga_service = self.client.get_service("GoogleAdsService")

        query = f"""
            SELECT
                ad_group_criterion.age_range.type,
                ad_group_criterion.gender.type,
                metrics.impressions,
                metrics.clicks,
                metrics.ctr,
                metrics.cost_micros,
                metrics.conversions
            FROM age_range_view
            WHERE segments.date DURING {date_range}
        """

        if campaign_id:
            query += f" AND campaign.id = {campaign_id}"

        response = ga_service.search(customer_id=customer_id, query=query)

        demographics = []
        for row in response:
            demographics.append({
                'age_range': row.ad_group_criterion.age_range.type.name,
                'gender': row.ad_group_criterion.gender.type.name,
                'impressions': row.metrics.impressions,
                'clicks': row.metrics.clicks,
                'ctr': row.metrics.ctr,
                'cost': row.metrics.cost_micros / 1_000_000,
                'conversions': row.metrics.conversions
            })

        return demographics

    def get_device_performance(
        self,
        customer_id: str,
        campaign_id: Optional[str] = None,
        date_range: str = "LAST_30_DAYS"
    ) -> List[Dict[str, Any]]:
        """Get performance by device type.

        Args:
            customer_id: Customer ID (without hyphens)
            campaign_id: Optional campaign ID filter
            date_range: Date range

        Returns:
            List of device performance data
        """
        ga_service = self.client.get_service("GoogleAdsService")

        query = f"""
            SELECT
                segments.device,
                metrics.impressions,
                metrics.clicks,
                metrics.ctr,
                metrics.average_cpc,
                metrics.cost_micros,
                metrics.conversions,
                metrics.cost_per_conversion
            FROM campaign
            WHERE segments.date DURING {date_range}
        """

        if campaign_id:
            query += f" AND campaign.id = {campaign_id}"

        response = ga_service.search(customer_id=customer_id, query=query)

        devices = []
        for row in response:
            devices.append({
                'device': row.segments.device.name,
                'impressions': row.metrics.impressions,
                'clicks': row.metrics.clicks,
                'ctr': row.metrics.ctr,
                'average_cpc': row.metrics.average_cpc / 1_000_000,
                'cost': row.metrics.cost_micros / 1_000_000,
                'conversions': row.metrics.conversions,
                'cost_per_conversion': row.metrics.cost_per_conversion
            })

        return devices

    def get_time_performance(
        self,
        customer_id: str,
        campaign_id: Optional[str] = None,
        date_range: str = "LAST_30_DAYS"
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Get performance by hour of day and day of week.

        Args:
            customer_id: Customer ID (without hyphens)
            campaign_id: Optional campaign ID filter
            date_range: Date range

        Returns:
            Dictionary with hour_of_day and day_of_week performance
        """
        ga_service = self.client.get_service("GoogleAdsService")

        # Hour of day
        hour_query = f"""
            SELECT
                segments.hour,
                metrics.impressions,
                metrics.clicks,
                metrics.ctr,
                metrics.cost_micros,
                metrics.conversions
            FROM campaign
            WHERE segments.date DURING {date_range}
        """

        if campaign_id:
            hour_query += f" AND campaign.id = {campaign_id}"

        hour_response = ga_service.search(customer_id=customer_id, query=hour_query)

        hours = []
        for row in hour_response:
            hours.append({
                'hour': row.segments.hour,
                'impressions': row.metrics.impressions,
                'clicks': row.metrics.clicks,
                'ctr': row.metrics.ctr,
                'cost': row.metrics.cost_micros / 1_000_000,
                'conversions': row.metrics.conversions
            })

        # Day of week
        dow_query = f"""
            SELECT
                segments.day_of_week,
                metrics.impressions,
                metrics.clicks,
                metrics.ctr,
                metrics.cost_micros,
                metrics.conversions
            FROM campaign
            WHERE segments.date DURING {date_range}
        """

        if campaign_id:
            dow_query += f" AND campaign.id = {campaign_id}"

        dow_response = ga_service.search(customer_id=customer_id, query=dow_query)

        days = []
        for row in dow_response:
            days.append({
                'day_of_week': row.segments.day_of_week.name,
                'impressions': row.metrics.impressions,
                'clicks': row.metrics.clicks,
                'ctr': row.metrics.ctr,
                'cost': row.metrics.cost_micros / 1_000_000,
                'conversions': row.metrics.conversions
            })

        return {
            'by_hour': hours,
            'by_day_of_week': days
        }

    def compare_periods(
        self,
        customer_id: str,
        current_start: str,
        current_end: str,
        previous_start: str,
        previous_end: str
    ) -> Dict[str, Any]:
        """Compare performance between two time periods.

        Args:
            customer_id: Customer ID (without hyphens)
            current_start: Current period start (YYYY-MM-DD)
            current_end: Current period end (YYYY-MM-DD)
            previous_start: Previous period start (YYYY-MM-DD)
            previous_end: Previous period end (YYYY-MM-DD)

        Returns:
            Comparison data with deltas and percentages
        """
        ga_service = self.client.get_service("GoogleAdsService")

        # Get current period
        current_query = f"""
            SELECT
                metrics.impressions,
                metrics.clicks,
                metrics.ctr,
                metrics.cost_micros,
                metrics.conversions,
                metrics.conversions_value
            FROM customer
            WHERE segments.date BETWEEN '{current_start}' AND '{current_end}'
        """

        current_response = ga_service.search(customer_id=customer_id, query=current_query)
        current = list(current_response)[0].metrics

        # Get previous period
        previous_query = f"""
            SELECT
                metrics.impressions,
                metrics.clicks,
                metrics.ctr,
                metrics.cost_micros,
                metrics.conversions,
                metrics.conversions_value
            FROM customer
            WHERE segments.date BETWEEN '{previous_start}' AND '{previous_end}'
        """

        previous_response = ga_service.search(customer_id=customer_id, query=previous_query)
        previous = list(previous_response)[0].metrics

        def calc_change(curr, prev):
            if prev == 0:
                return 100.0 if curr > 0 else 0.0
            return ((curr - prev) / prev) * 100

        return {
            'current_period': {
                'start': current_start,
                'end': current_end,
                'impressions': current.impressions,
                'clicks': current.clicks,
                'cost': current.cost_micros / 1_000_000,
                'conversions': current.conversions,
                'conversions_value': current.conversions_value
            },
            'previous_period': {
                'start': previous_start,
                'end': previous_end,
                'impressions': previous.impressions,
                'clicks': previous.clicks,
                'cost': previous.cost_micros / 1_000_000,
                'conversions': previous.conversions,
                'conversions_value': previous.conversions_value
            },
            'changes': {
                'impressions_change': calc_change(current.impressions, previous.impressions),
                'clicks_change': calc_change(current.clicks, previous.clicks),
                'cost_change': calc_change(current.cost_micros, previous.cost_micros),
                'conversions_change': calc_change(current.conversions, previous.conversions),
                'value_change': calc_change(current.conversions_value, previous.conversions_value)
            }
        }

    def get_search_impression_share(
        self,
        customer_id: str,
        campaign_id: Optional[str] = None,
        date_range: str = "LAST_30_DAYS"
    ) -> Dict[str, Any]:
        """Get search impression share metrics.

        Args:
            customer_id: Customer ID (without hyphens)
            campaign_id: Optional campaign ID filter
            date_range: Date range

        Returns:
            Impression share data
        """
        ga_service = self.client.get_service("GoogleAdsService")

        query = f"""
            SELECT
                campaign.id,
                campaign.name,
                metrics.impressions,
                metrics.search_impression_share,
                metrics.search_rank_lost_impression_share,
                metrics.search_budget_lost_impression_share,
                metrics.search_exact_match_impression_share,
                metrics.search_top_impression_share,
                metrics.search_absolute_top_impression_share
            FROM campaign
            WHERE segments.date DURING {date_range}
        """

        if campaign_id:
            query += f" AND campaign.id = {campaign_id}"

        response = ga_service.search(customer_id=customer_id, query=query)

        campaigns = []
        for row in response:
            campaigns.append({
                'campaign_id': str(row.campaign.id),
                'campaign_name': row.campaign.name,
                'impressions': row.metrics.impressions,
                'impression_share': row.metrics.search_impression_share,
                'rank_lost_is': row.metrics.search_rank_lost_impression_share,
                'budget_lost_is': row.metrics.search_budget_lost_impression_share,
                'exact_match_is': row.metrics.search_exact_match_impression_share,
                'top_is': row.metrics.search_top_impression_share,
                'absolute_top_is': row.metrics.search_absolute_top_impression_share
            })

        return {'campaigns': campaigns}

    def compare_campaigns(
        self,
        customer_id: str,
        campaign_ids: List[str],
        date_range: str = "LAST_30_DAYS"
    ) -> Dict[str, Any]:
        """Compare performance across multiple campaigns.

        Args:
            customer_id: Customer ID (without hyphens)
            campaign_ids: List of campaign IDs to compare
            date_range: Date range for comparison

        Returns:
            Comparative campaign metrics
        """
        ga_service = self.client.get_service("GoogleAdsService")

        # Build campaign ID filter
        campaign_filter = " OR ".join([f"campaign.id = {cid}" for cid in campaign_ids])

        query = f"""
            SELECT
                campaign.id,
                campaign.name,
                campaign.status,
                campaign.advertising_channel_type,
                metrics.impressions,
                metrics.clicks,
                metrics.ctr,
                metrics.cost_micros,
                metrics.conversions,
                metrics.conversions_value,
                metrics.cost_per_conversion,
                metrics.average_cpc
            FROM campaign
            WHERE ({campaign_filter})
              AND segments.date DURING {date_range}
        """

        response = ga_service.search(customer_id=customer_id, query=query)

        campaigns = []
        total_impressions = 0
        total_clicks = 0
        total_cost = 0
        total_conversions = 0
        total_conversion_value = 0

        for row in response:
            cost = row.metrics.cost_micros / 1_000_000
            conv_value = row.metrics.conversions_value

            campaign_data = {
                'campaign_id': str(row.campaign.id),
                'campaign_name': row.campaign.name,
                'status': row.campaign.status.name,
                'channel_type': row.campaign.advertising_channel_type.name,
                'impressions': row.metrics.impressions,
                'clicks': row.metrics.clicks,
                'ctr': row.metrics.ctr,
                'cost': cost,
                'conversions': row.metrics.conversions,
                'conversion_value': conv_value,
                'cost_per_conversion': row.metrics.cost_per_conversion,
                'average_cpc': row.metrics.average_cpc / 1_000_000 if row.metrics.average_cpc else 0
            }

            # Calculate derived metrics
            if row.metrics.conversions > 0:
                campaign_data['roas'] = conv_value / cost if cost > 0 else 0
            else:
                campaign_data['roas'] = 0

            campaigns.append(campaign_data)

            # Aggregate totals
            total_impressions += row.metrics.impressions
            total_clicks += row.metrics.clicks
            total_cost += cost
            total_conversions += row.metrics.conversions
            total_conversion_value += conv_value

        # Calculate overall metrics
        overall_ctr = (total_clicks / total_impressions) if total_impressions > 0 else 0
        overall_avg_cpc = (total_cost / total_clicks) if total_clicks > 0 else 0
        overall_cost_per_conv = (total_cost / total_conversions) if total_conversions > 0 else 0
        overall_roas = (total_conversion_value / total_cost) if total_cost > 0 else 0

        # Calculate shares (what % of total each campaign represents)
        for campaign in campaigns:
            campaign['impression_share_of_total'] = (
                (campaign['impressions'] / total_impressions * 100) if total_impressions > 0 else 0
            )
            campaign['cost_share_of_total'] = (
                (campaign['cost'] / total_cost * 100) if total_cost > 0 else 0
            )
            campaign['conversion_share_of_total'] = (
                (campaign['conversions'] / total_conversions * 100) if total_conversions > 0 else 0
            )

        # Rank campaigns by different metrics
        campaigns_by_impressions = sorted(campaigns, key=lambda x: x['impressions'], reverse=True)
        campaigns_by_conversions = sorted(campaigns, key=lambda x: x['conversions'], reverse=True)
        campaigns_by_roas = sorted(campaigns, key=lambda x: x['roas'], reverse=True)
        campaigns_by_ctr = sorted(campaigns, key=lambda x: x['ctr'], reverse=True)

        return {
            'campaigns': campaigns,
            'total_campaigns': len(campaigns),
            'totals': {
                'impressions': total_impressions,
                'clicks': total_clicks,
                'cost': total_cost,
                'conversions': total_conversions,
                'conversion_value': total_conversion_value,
                'ctr': overall_ctr,
                'average_cpc': overall_avg_cpc,
                'cost_per_conversion': overall_cost_per_conv,
                'roas': overall_roas
            },
            'rankings': {
                'by_impressions': [{'campaign_id': c['campaign_id'], 'campaign_name': c['campaign_name'], 'value': c['impressions']} for c in campaigns_by_impressions],
                'by_conversions': [{'campaign_id': c['campaign_id'], 'campaign_name': c['campaign_name'], 'value': c['conversions']} for c in campaigns_by_conversions],
                'by_roas': [{'campaign_id': c['campaign_id'], 'campaign_name': c['campaign_name'], 'value': c['roas']} for c in campaigns_by_roas],
                'by_ctr': [{'campaign_id': c['campaign_id'], 'campaign_name': c['campaign_name'], 'value': c['ctr']} for c in campaigns_by_ctr]
            },
            'best_performers': {
                'highest_impressions': campaigns_by_impressions[0] if campaigns_by_impressions else None,
                'highest_conversions': campaigns_by_conversions[0] if campaigns_by_conversions else None,
                'highest_roas': campaigns_by_roas[0] if campaigns_by_roas else None,
                'highest_ctr': campaigns_by_ctr[0] if campaigns_by_ctr else None
            }
        }

    def build_custom_report(
        self,
        customer_id: str,
        report_name: str,
        resource_type: str,
        metrics: List[str],
        dimensions: List[str],
        date_range: str = "LAST_30_DAYS",
        filters: Optional[Dict[str, Any]] = None,
        sort_by: Optional[str] = None,
        limit: int = 1000
    ) -> Dict[str, Any]:
        """Build custom report with user-defined metrics and dimensions.

        Args:
            customer_id: Google Ads customer ID (without hyphens)
            report_name: Name for the custom report
            resource_type: Resource to query (campaign, ad_group, ad, keyword, etc.)
            metrics: List of metric names (e.g., ['impressions', 'clicks', 'cost_micros'])
            dimensions: List of dimension names (e.g., ['campaign.name', 'ad_group.name'])
            date_range: Date range for metrics (default: LAST_30_DAYS)
            filters: Optional filters (e.g., {'campaign.status': 'ENABLED'})
            sort_by: Optional field to sort by (e.g., 'metrics.impressions DESC')
            limit: Maximum number of rows to return (default: 1000)

        Returns:
            Dictionary containing:
                - report_name: str
                - resource_type: str
                - date_range: str
                - total_rows: int
                - columns: List[str]
                - data: List[Dict[str, Any]]
                - filters_applied: Dict[str, Any]
                - sort_order: str
        """
        with performance_logger.track_operation(self, 'build_custom_report'):
            # Build SELECT clause
            select_fields = dimensions + [f"metrics.{m}" if not m.startswith('metrics.') else m for m in metrics]

            # Build FROM clause
            resource_mapping = {
                'campaign': 'campaign',
                'ad_group': 'ad_group',
                'ad': 'ad_group_ad',
                'keyword': 'ad_group_criterion',
                'search_term': 'search_term_view',
                'placement': 'group_placement_view',
                'video': 'video'
            }
            from_resource = resource_mapping.get(resource_type, resource_type)

            # Build WHERE clause
            where_conditions = [f"segments.date DURING {date_range}"]
            if filters:
                for key, value in filters.items():
                    if isinstance(value, str):
                        where_conditions.append(f"{key} = '{value}'")
                    else:
                        where_conditions.append(f"{key} = {value}")

            # Build ORDER BY clause
            order_clause = f" ORDER BY {sort_by}" if sort_by else ""

            # Build LIMIT clause
            limit_clause = f" LIMIT {limit}"

            # Construct GAQL query
            query = f"""
                SELECT {', '.join(select_fields)}
                FROM {from_resource}
                WHERE {' AND '.join(where_conditions)}
                {order_clause}
                {limit_clause}
            """

            # Execute query
            ga_service = self.client.get_service("GoogleAdsService")
            request = self.client.get_type("SearchGoogleAdsRequest")
            request.customer_id = customer_id
            request.query = query.strip()

            audit_logger.log_api_call(
                operation='custom_report',
                customer_id=customer_id,
                details={'query': query.strip()}
            )

            response = ga_service.search(request=request)

            # Parse results
            rows = []
            for row in response:
                row_data = {}

                # Extract dimensions
                for dim in dimensions:
                    parts = dim.split('.')
                    value = row
                    for part in parts:
                        value = getattr(value, part, None)
                        if value is None:
                            break
                    row_data[dim] = str(value) if value is not None else ''

                # Extract metrics
                for metric in metrics:
                    metric_name = metric.replace('metrics.', '')
                    value = getattr(row.metrics, metric_name, None)
                    row_data[f"metrics.{metric_name}"] = value

                rows.append(row_data)

            return {
                'report_name': report_name,
                'resource_type': resource_type,
                'date_range': date_range,
                'total_rows': len(rows),
                'columns': select_fields,
                'data': rows,
                'filters_applied': filters or {},
                'sort_order': sort_by or 'none',
                'query': query.strip()
            }

    def get_demographic_performance(
        self,
        customer_id: str,
        campaign_id: Optional[str] = None,
        date_range: str = "LAST_30_DAYS",
        dimension: str = "age_range"
    ) -> Dict[str, Any]:
        """Get performance metrics broken down by demographics.

        Args:
            customer_id: Google Ads customer ID
            campaign_id: Optional campaign ID to filter by
            date_range: Date range for metrics
            dimension: Demographic dimension (age_range, gender, parental_status, household_income)

        Returns:
            Dictionary with demographic performance breakdown
        """
        with performance_logger.track_operation(self, 'get_demographic_performance'):
            # Map dimension to correct field
            dimension_fields = {
                'age_range': 'ad_group_criterion.age_range.type',
                'gender': 'ad_group_criterion.gender.type',
                'parental_status': 'ad_group_criterion.parental_status.type',
                'household_income': 'ad_group_criterion.income_range.type'
            }

            if dimension not in dimension_fields:
                raise ValueError(f"Invalid dimension: {dimension}. Must be one of: {list(dimension_fields.keys())}")

            dimension_field = dimension_fields[dimension]

            # Build query
            query_parts = [
                f"SELECT campaign.id, campaign.name, {dimension_field},",
                "metrics.impressions, metrics.clicks, metrics.ctr,",
                "metrics.cost_micros, metrics.conversions, metrics.conversions_value",
                "FROM ad_group_criterion",
                f"WHERE segments.date DURING {date_range}",
                f"AND ad_group_criterion.type IN ('AGE_RANGE', 'GENDER', 'PARENTAL_STATUS', 'INCOME_RANGE')"
            ]

            if campaign_id:
                query_parts.append(f"AND campaign.id = {campaign_id}")

            query = " ".join(query_parts)

            ga_service = self.client.get_service("GoogleAdsService")
            request = self.client.get_type("SearchGoogleAdsRequest")
            request.customer_id = customer_id
            request.query = query

            audit_logger.log_api_call(
                operation='demographic_performance',
                customer_id=customer_id,
                details={'dimension': dimension, 'campaign_id': campaign_id}
            )

            response = ga_service.search(request=request)

            # Parse results
            demographics = []
            total_impressions = 0
            total_clicks = 0
            total_cost = 0
            total_conversions = 0
            total_value = 0

            for row in response:
                # Extract demographic value
                if dimension == 'age_range':
                    demo_value = row.ad_group_criterion.age_range.type.name
                elif dimension == 'gender':
                    demo_value = row.ad_group_criterion.gender.type.name
                elif dimension == 'parental_status':
                    demo_value = row.ad_group_criterion.parental_status.type.name
                else:  # household_income
                    demo_value = row.ad_group_criterion.income_range.type.name

                impressions = row.metrics.impressions
                clicks = row.metrics.clicks
                cost = row.metrics.cost_micros / 1_000_000
                conversions = row.metrics.conversions
                value = row.metrics.conversions_value

                demographics.append({
                    'campaign_id': row.campaign.id,
                    'campaign_name': row.campaign.name,
                    'demographic_value': demo_value,
                    'impressions': impressions,
                    'clicks': clicks,
                    'ctr': row.metrics.ctr,
                    'cost': cost,
                    'conversions': conversions,
                    'conversion_value': value,
                    'cost_per_conversion': cost / conversions if conversions > 0 else 0
                })

                total_impressions += impressions
                total_clicks += clicks
                total_cost += cost
                total_conversions += conversions
                total_value += value

            # Calculate share of total for each demographic
            for demo in demographics:
                demo['impression_share'] = (demo['impressions'] / total_impressions * 100) if total_impressions > 0 else 0
                demo['click_share'] = (demo['clicks'] / total_clicks * 100) if total_clicks > 0 else 0
                demo['cost_share'] = (demo['cost'] / total_cost * 100) if total_cost > 0 else 0

            # Sort by impressions
            demographics.sort(key=lambda x: x['impressions'], reverse=True)

            return {
                'dimension': dimension,
                'date_range': date_range,
                'campaign_id': campaign_id,
                'total_demographics': len(demographics),
                'demographics': demographics,
                'totals': {
                    'impressions': total_impressions,
                    'clicks': total_clicks,
                    'cost': total_cost,
                    'conversions': total_conversions,
                    'conversion_value': total_value,
                    'overall_ctr': (total_clicks / total_impressions * 100) if total_impressions > 0 else 0,
                    'overall_cpc': (total_cost / total_clicks) if total_clicks > 0 else 0
                }
            }

    def get_placement_performance(
        self,
        customer_id: str,
        campaign_id: Optional[str] = None,
        date_range: str = "LAST_30_DAYS",
        placement_type: str = "all"
    ) -> Dict[str, Any]:
        """Get Display Network placement performance.

        Args:
            customer_id: Google Ads customer ID
            campaign_id: Optional campaign ID to filter by
            date_range: Date range for metrics
            placement_type: Type of placements (all, website, app, video, youtube_channel, youtube_video)

        Returns:
            Dictionary with placement performance data
        """
        with performance_logger.track_operation(self, 'get_placement_performance'):
            # Build query
            query_parts = [
                "SELECT campaign.id, campaign.name,",
                "group_placement_view.placement, group_placement_view.placement_type,",
                "group_placement_view.display_name,",
                "metrics.impressions, metrics.clicks, metrics.ctr,",
                "metrics.cost_micros, metrics.conversions, metrics.conversions_value",
                "FROM group_placement_view",
                f"WHERE segments.date DURING {date_range}"
            ]

            if campaign_id:
                query_parts.append(f"AND campaign.id = {campaign_id}")

            if placement_type != "all":
                type_mapping = {
                    'website': 'WEBSITE',
                    'app': 'MOBILE_APP_CATEGORY',
                    'video': 'YOUTUBE_VIDEO',
                    'youtube_channel': 'YOUTUBE_CHANNEL',
                    'youtube_video': 'YOUTUBE_VIDEO'
                }
                if placement_type in type_mapping:
                    query_parts.append(f"AND group_placement_view.placement_type = '{type_mapping[placement_type]}'")

            query_parts.append("ORDER BY metrics.impressions DESC")
            query_parts.append("LIMIT 1000")

            query = " ".join(query_parts)

            ga_service = self.client.get_service("GoogleAdsService")
            request = self.client.get_type("SearchGoogleAdsRequest")
            request.customer_id = customer_id
            request.query = query

            audit_logger.log_api_call(
                operation='placement_performance',
                customer_id=customer_id,
                details={'placement_type': placement_type, 'campaign_id': campaign_id}
            )

            response = ga_service.search(request=request)

            # Parse results
            placements = []
            total_impressions = 0
            total_clicks = 0
            total_cost = 0
            total_conversions = 0

            for row in response:
                impressions = row.metrics.impressions
                clicks = row.metrics.clicks
                cost = row.metrics.cost_micros / 1_000_000
                conversions = row.metrics.conversions

                placements.append({
                    'campaign_id': row.campaign.id,
                    'campaign_name': row.campaign.name,
                    'placement': row.group_placement_view.placement,
                    'placement_type': row.group_placement_view.placement_type.name,
                    'display_name': row.group_placement_view.display_name,
                    'impressions': impressions,
                    'clicks': clicks,
                    'ctr': row.metrics.ctr,
                    'cost': cost,
                    'conversions': conversions,
                    'conversion_value': row.metrics.conversions_value,
                    'cost_per_conversion': cost / conversions if conversions > 0 else 0
                })

                total_impressions += impressions
                total_clicks += clicks
                total_cost += cost
                total_conversions += conversions

            return {
                'placement_type_filter': placement_type,
                'date_range': date_range,
                'campaign_id': campaign_id,
                'total_placements': len(placements),
                'placements': placements,
                'totals': {
                    'impressions': total_impressions,
                    'clicks': total_clicks,
                    'cost': total_cost,
                    'conversions': total_conversions,
                    'overall_ctr': (total_clicks / total_impressions * 100) if total_impressions > 0 else 0
                }
            }

    def get_video_performance(
        self,
        customer_id: str,
        campaign_id: Optional[str] = None,
        date_range: str = "LAST_30_DAYS"
    ) -> Dict[str, Any]:
        """Get YouTube video ad performance metrics.

        Args:
            customer_id: Google Ads customer ID
            campaign_id: Optional campaign ID to filter by
            date_range: Date range for metrics

        Returns:
            Dictionary with video performance data
        """
        with performance_logger.track_operation(self, 'get_video_performance'):
            # Build query for video metrics
            query_parts = [
                "SELECT campaign.id, campaign.name,",
                "ad_group.id, ad_group.name,",
                "ad_group_ad.ad.id, ad_group_ad.ad.name,",
                "metrics.impressions, metrics.clicks, metrics.ctr,",
                "metrics.cost_micros,",
                "metrics.video_views, metrics.video_view_rate,",
                "metrics.video_quartile_p25_rate, metrics.video_quartile_p50_rate,",
                "metrics.video_quartile_p75_rate, metrics.video_quartile_p100_rate",
                "FROM ad_group_ad",
                f"WHERE segments.date DURING {date_range}",
                "AND ad_group_ad.ad.type = 'VIDEO_AD'"
            ]

            if campaign_id:
                query_parts.append(f"AND campaign.id = {campaign_id}")

            query_parts.append("ORDER BY metrics.video_views DESC")

            query = " ".join(query_parts)

            ga_service = self.client.get_service("GoogleAdsService")
            request = self.client.get_type("SearchGoogleAdsRequest")
            request.customer_id = customer_id
            request.query = query

            audit_logger.log_api_call(
                operation='video_performance',
                customer_id=customer_id,
                details={'campaign_id': campaign_id}
            )

            response = ga_service.search(request=request)

            # Parse results
            videos = []
            total_impressions = 0
            total_views = 0
            total_cost = 0

            for row in response:
                impressions = row.metrics.impressions
                views = row.metrics.video_views
                cost = row.metrics.cost_micros / 1_000_000

                videos.append({
                    'campaign_id': row.campaign.id,
                    'campaign_name': row.campaign.name,
                    'ad_group_id': row.ad_group.id,
                    'ad_group_name': row.ad_group.name,
                    'ad_id': row.ad_group_ad.ad.id,
                    'ad_name': row.ad_group_ad.ad.name,
                    'impressions': impressions,
                    'clicks': row.metrics.clicks,
                    'ctr': row.metrics.ctr,
                    'cost': cost,
                    'video_views': views,
                    'view_rate': row.metrics.video_view_rate,
                    'cpv': cost / views if views > 0 else 0,
                    'quartile_25_rate': row.metrics.video_quartile_p25_rate,
                    'quartile_50_rate': row.metrics.video_quartile_p50_rate,
                    'quartile_75_rate': row.metrics.video_quartile_p75_rate,
                    'quartile_100_rate': row.metrics.video_quartile_p100_rate
                })

                total_impressions += impressions
                total_views += views
                total_cost += cost

            return {
                'date_range': date_range,
                'campaign_id': campaign_id,
                'total_videos': len(videos),
                'videos': videos,
                'totals': {
                    'impressions': total_impressions,
                    'video_views': total_views,
                    'cost': total_cost,
                    'overall_view_rate': (total_views / total_impressions * 100) if total_impressions > 0 else 0,
                    'overall_cpv': (total_cost / total_views) if total_views > 0 else 0
                }
            }

    def get_landing_page_performance(
        self,
        customer_id: str,
        campaign_id: Optional[str] = None,
        date_range: str = "LAST_30_DAYS"
    ) -> Dict[str, Any]:
        """Get landing page performance analysis.

        Args:
            customer_id: Google Ads customer ID
            campaign_id: Optional campaign ID to filter by
            date_range: Date range for metrics

        Returns:
            Dictionary with landing page performance data
        """
        with performance_logger.track_operation(self, 'get_landing_page_performance'):
            # Build query
            query_parts = [
                "SELECT campaign.id, campaign.name,",
                "landing_page_view.unexpanded_final_url,",
                "metrics.impressions, metrics.clicks, metrics.ctr,",
                "metrics.cost_micros, metrics.conversions, metrics.conversions_value,",
                "metrics.bounce_rate, metrics.average_time_on_site",
                "FROM landing_page_view",
                f"WHERE segments.date DURING {date_range}"
            ]

            if campaign_id:
                query_parts.append(f"AND campaign.id = {campaign_id}")

            query_parts.append("ORDER BY metrics.impressions DESC")
            query_parts.append("LIMIT 1000")

            query = " ".join(query_parts)

            ga_service = self.client.get_service("GoogleAdsService")
            request = self.client.get_type("SearchGoogleAdsRequest")
            request.customer_id = customer_id
            request.query = query

            audit_logger.log_api_call(
                operation='landing_page_performance',
                customer_id=customer_id,
                details={'campaign_id': campaign_id}
            )

            response = ga_service.search(request=request)

            # Parse results
            pages = []
            total_impressions = 0
            total_clicks = 0
            total_conversions = 0
            total_cost = 0

            for row in response:
                impressions = row.metrics.impressions
                clicks = row.metrics.clicks
                conversions = row.metrics.conversions
                cost = row.metrics.cost_micros / 1_000_000

                pages.append({
                    'campaign_id': row.campaign.id,
                    'campaign_name': row.campaign.name,
                    'landing_page_url': row.landing_page_view.unexpanded_final_url,
                    'impressions': impressions,
                    'clicks': clicks,
                    'ctr': row.metrics.ctr,
                    'cost': cost,
                    'conversions': conversions,
                    'conversion_value': row.metrics.conversions_value,
                    'conversion_rate': (conversions / clicks * 100) if clicks > 0 else 0,
                    'cost_per_conversion': cost / conversions if conversions > 0 else 0,
                    'bounce_rate': row.metrics.bounce_rate,
                    'avg_time_on_site': row.metrics.average_time_on_site
                })

                total_impressions += impressions
                total_clicks += clicks
                total_conversions += conversions
                total_cost += cost

            # Sort by conversion rate
            pages.sort(key=lambda x: x['conversion_rate'], reverse=True)

            return {
                'date_range': date_range,
                'campaign_id': campaign_id,
                'total_landing_pages': len(pages),
                'landing_pages': pages,
                'totals': {
                    'impressions': total_impressions,
                    'clicks': total_clicks,
                    'conversions': total_conversions,
                    'cost': total_cost,
                    'overall_conversion_rate': (total_conversions / total_clicks * 100) if total_clicks > 0 else 0
                }
            }

    def compare_year_over_year(
        self,
        customer_id: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        current_period: str = "THIS_YEAR",
        comparison_years: int = 1
    ) -> Dict[str, Any]:
        """Compare performance metrics year-over-year.

        Args:
            customer_id: Google Ads customer ID
            resource_type: Type of resource (campaign, ad_group, keyword)
            resource_id: Optional specific resource ID
            current_period: Current period to analyze (THIS_YEAR, LAST_YEAR)
            comparison_years: Number of years to compare (1-5)

        Returns:
            Dictionary with year-over-year comparison data
        """
        with performance_logger.track_operation(self, 'compare_year_over_year'):
            import datetime

            # Calculate date ranges for each year
            current_year = datetime.datetime.now().year
            date_ranges = []

            for i in range(comparison_years + 1):
                year = current_year - i
                date_ranges.append({
                    'year': year,
                    'start_date': f"{year}-01-01",
                    'end_date': f"{year}-12-31"
                })

            # Build base query
            resource_mapping = {
                'campaign': ('campaign', 'campaign.id', 'campaign.name'),
                'ad_group': ('ad_group', 'ad_group.id', 'ad_group.name'),
                'keyword': ('ad_group_criterion', 'ad_group_criterion.criterion_id', 'ad_group_criterion.keyword.text')
            }

            if resource_type not in resource_mapping:
                raise ValueError(f"Invalid resource type: {resource_type}")

            from_table, id_field, name_field = resource_mapping[resource_type]

            # Query each year
            yearly_data = []

            for date_range in date_ranges:
                query_parts = [
                    f"SELECT {name_field},",
                    "metrics.impressions, metrics.clicks, metrics.ctr,",
                    "metrics.cost_micros, metrics.conversions, metrics.conversions_value",
                    f"FROM {from_table}",
                    f"WHERE segments.date BETWEEN '{date_range['start_date']}' AND '{date_range['end_date']}'"
                ]

                if resource_id:
                    query_parts.append(f"AND {id_field} = {resource_id}")

                query = " ".join(query_parts)

                ga_service = self.client.get_service("GoogleAdsService")
                request = self.client.get_type("SearchGoogleAdsRequest")
                request.customer_id = customer_id
                request.query = query

                response = ga_service.search(request=request)

                # Aggregate yearly totals
                year_totals = {
                    'year': date_range['year'],
                    'impressions': 0,
                    'clicks': 0,
                    'cost': 0,
                    'conversions': 0,
                    'conversion_value': 0
                }

                for row in response:
                    year_totals['impressions'] += row.metrics.impressions
                    year_totals['clicks'] += row.metrics.clicks
                    year_totals['cost'] += row.metrics.cost_micros / 1_000_000
                    year_totals['conversions'] += row.metrics.conversions
                    year_totals['conversion_value'] += row.metrics.conversions_value

                # Calculate derived metrics
                year_totals['ctr'] = (year_totals['clicks'] / year_totals['impressions'] * 100) if year_totals['impressions'] > 0 else 0
                year_totals['cpc'] = (year_totals['cost'] / year_totals['clicks']) if year_totals['clicks'] > 0 else 0
                year_totals['conversion_rate'] = (year_totals['conversions'] / year_totals['clicks'] * 100) if year_totals['clicks'] > 0 else 0

                yearly_data.append(year_totals)

            audit_logger.log_api_call(
                operation='year_over_year_comparison',
                customer_id=customer_id,
                details={'resource_type': resource_type, 'comparison_years': comparison_years}
            )

            # Calculate year-over-year growth rates
            if len(yearly_data) >= 2:
                current = yearly_data[0]
                previous = yearly_data[1]

                growth_rates = {
                    'impressions_growth': ((current['impressions'] - previous['impressions']) / previous['impressions'] * 100) if previous['impressions'] > 0 else 0,
                    'clicks_growth': ((current['clicks'] - previous['clicks']) / previous['clicks'] * 100) if previous['clicks'] > 0 else 0,
                    'cost_growth': ((current['cost'] - previous['cost']) / previous['cost'] * 100) if previous['cost'] > 0 else 0,
                    'conversions_growth': ((current['conversions'] - previous['conversions']) / previous['conversions'] * 100) if previous['conversions'] > 0 else 0,
                    'ctr_change': current['ctr'] - previous['ctr'],
                    'cpc_change': current['cpc'] - previous['cpc']
                }
            else:
                growth_rates = {}

            return {
                'resource_type': resource_type,
                'resource_id': resource_id,
                'comparison_years': comparison_years,
                'yearly_data': yearly_data,
                'growth_rates': growth_rates
            }

    def compare_campaigns_bulk(
        self,
        customer_id: str,
        campaign_ids: List[str],
        date_range: str = "LAST_30_DAYS",
        group_by: Optional[str] = None
    ) -> Dict[str, Any]:
        """Compare performance across 10+ campaigns with optional grouping.

        Args:
            customer_id: Google Ads customer ID
            campaign_ids: List of campaign IDs (10-100 campaigns)
            date_range: Date range for metrics
            group_by: Optional grouping (campaign_type, status, label)

        Returns:
            Dictionary with bulk campaign comparison data
        """
        with performance_logger.track_operation(self, 'compare_campaigns_bulk'):
            if len(campaign_ids) < 10:
                raise ValueError("Use google_ads_campaign_comparison for fewer than 10 campaigns")

            if len(campaign_ids) > 100:
                raise ValueError("Maximum 100 campaigns allowed")

            # Build query for all campaigns
            campaign_filter = " OR ".join([f"campaign.id = {cid}" for cid in campaign_ids])

            query_parts = [
                "SELECT campaign.id, campaign.name, campaign.status,",
                "campaign.advertising_channel_type,",
                "metrics.impressions, metrics.clicks, metrics.ctr,",
                "metrics.cost_micros, metrics.conversions, metrics.conversions_value",
                "FROM campaign",
                f"WHERE segments.date DURING {date_range}",
                f"AND ({campaign_filter})"
            ]

            query = " ".join(query_parts)

            ga_service = self.client.get_service("GoogleAdsService")
            request = self.client.get_type("SearchGoogleAdsRequest")
            request.customer_id = customer_id
            request.query = query

            audit_logger.log_api_call(
                operation='bulk_campaign_comparison',
                customer_id=customer_id,
                details={'campaign_count': len(campaign_ids), 'group_by': group_by}
            )

            response = ga_service.search(request=request)

            # Parse results
            campaigns = []
            totals = {
                'impressions': 0,
                'clicks': 0,
                'cost': 0,
                'conversions': 0,
                'conversion_value': 0
            }

            for row in response:
                impressions = row.metrics.impressions
                clicks = row.metrics.clicks
                cost = row.metrics.cost_micros / 1_000_000
                conversions = row.metrics.conversions
                value = row.metrics.conversions_value

                campaign_data = {
                    'campaign_id': row.campaign.id,
                    'campaign_name': row.campaign.name,
                    'status': row.campaign.status.name,
                    'campaign_type': row.campaign.advertising_channel_type.name,
                    'impressions': impressions,
                    'clicks': clicks,
                    'ctr': row.metrics.ctr,
                    'cost': cost,
                    'conversions': conversions,
                    'conversion_value': value,
                    'cpc': cost / clicks if clicks > 0 else 0,
                    'cpa': cost / conversions if conversions > 0 else 0,
                    'roas': value / cost if cost > 0 else 0
                }

                campaigns.append(campaign_data)

                totals['impressions'] += impressions
                totals['clicks'] += clicks
                totals['cost'] += cost
                totals['conversions'] += conversions
                totals['conversion_value'] += value

            # Group by if requested
            grouped_data = {}
            if group_by:
                for campaign in campaigns:
                    key = campaign.get(group_by, 'Unknown')
                    if key not in grouped_data:
                        grouped_data[key] = {
                            'campaigns': [],
                            'totals': {
                                'impressions': 0,
                                'clicks': 0,
                                'cost': 0,
                                'conversions': 0,
                                'conversion_value': 0
                            }
                        }

                    grouped_data[key]['campaigns'].append(campaign)
                    grouped_data[key]['totals']['impressions'] += campaign['impressions']
                    grouped_data[key]['totals']['clicks'] += campaign['clicks']
                    grouped_data[key]['totals']['cost'] += campaign['cost']
                    grouped_data[key]['totals']['conversions'] += campaign['conversions']
                    grouped_data[key]['totals']['conversion_value'] += campaign['conversion_value']

            # Find outliers (campaigns performing significantly above/below average)
            if campaigns:
                avg_ctr = sum(c['ctr'] for c in campaigns) / len(campaigns)
                avg_cpa = sum(c['cpa'] for c in campaigns if c['cpa'] > 0) / len([c for c in campaigns if c['cpa'] > 0]) if any(c['cpa'] > 0 for c in campaigns) else 0
                avg_roas = sum(c['roas'] for c in campaigns if c['roas'] > 0) / len([c for c in campaigns if c['roas'] > 0]) if any(c['roas'] > 0 for c in campaigns) else 0

                top_performers = [c for c in campaigns if c['roas'] > avg_roas * 1.5]
                underperformers = [c for c in campaigns if c['roas'] > 0 and c['roas'] < avg_roas * 0.5]
            else:
                top_performers = []
                underperformers = []

            return {
                'total_campaigns': len(campaigns),
                'date_range': date_range,
                'group_by': group_by,
                'campaigns': campaigns,
                'grouped_data': grouped_data if group_by else None,
                'totals': totals,
                'averages': {
                    'avg_ctr': avg_ctr if campaigns else 0,
                    'avg_cpa': avg_cpa if campaigns else 0,
                    'avg_roas': avg_roas if campaigns else 0
                },
                'outliers': {
                    'top_performers': top_performers,
                    'underperformers': underperformers
                }
            }

    def get_paid_organic_report(
        self,
        customer_id: str,
        date_range: str = "LAST_30_DAYS"
    ) -> Dict[str, Any]:
        """Get combined paid and organic search performance.

        Note: This requires Google Search Console integration which may not be
        available for all accounts. Returns paid search data with placeholder
        for organic data.

        Args:
            customer_id: Google Ads customer ID
            date_range: Date range for metrics

        Returns:
            Dictionary with paid and organic performance data
        """
        with performance_logger.track_operation(self, 'get_paid_organic_report'):
            # Get paid search performance
            query = f"""
                SELECT
                    campaign.id,
                    campaign.name,
                    metrics.impressions,
                    metrics.clicks,
                    metrics.ctr,
                    metrics.average_cpc,
                    metrics.cost_micros
                FROM campaign
                WHERE segments.date DURING {date_range}
                AND campaign.advertising_channel_type = 'SEARCH'
            """

            ga_service = self.client.get_service("GoogleAdsService")
            request = self.client.get_type("SearchGoogleAdsRequest")
            request.customer_id = customer_id
            request.query = query

            response = ga_service.search(request=request)

            paid_campaigns = []
            total_paid_impressions = 0
            total_paid_clicks = 0
            total_paid_cost = 0

            for row in response:
                impressions = row.metrics.impressions
                clicks = row.metrics.clicks
                cost = row.metrics.cost_micros / 1_000_000

                paid_campaigns.append({
                    'campaign_id': row.campaign.id,
                    'campaign_name': row.campaign.name,
                    'impressions': impressions,
                    'clicks': clicks,
                    'ctr': row.metrics.ctr,
                    'avg_cpc': row.metrics.average_cpc,
                    'cost': cost
                })

                total_paid_impressions += impressions
                total_paid_clicks += clicks
                total_paid_cost += cost

            audit_logger.log_api_call(
                operation='paid_organic_report',
                customer_id=customer_id,
                details={'date_range': date_range}
            )

            # Note: Organic data would come from Google Search Console API
            # This is a placeholder indicating the integration requirement
            return {
                'date_range': date_range,
                'paid_search': {
                    'campaigns': paid_campaigns,
                    'total_impressions': total_paid_impressions,
                    'total_clicks': total_paid_clicks,
                    'total_cost': total_paid_cost,
                    'average_ctr': (total_paid_clicks / total_paid_impressions * 100) if total_paid_impressions > 0 else 0
                },
                'organic_search': {
                    'note': 'Organic data requires Google Search Console integration',
                    'integration_required': True,
                    'total_impressions': 0,
                    'total_clicks': 0,
                    'average_position': 0
                },
                'combined': {
                    'total_impressions': total_paid_impressions,
                    'total_clicks': total_paid_clicks,
                    'paid_click_share': 100.0  # Would be calculated with organic data
                }
            }

    def analyze_trends(
        self,
        customer_id: str,
        metric: str,
        resource_type: str = "campaign",
        resource_id: Optional[str] = None,
        lookback_days: int = 90
    ) -> Dict[str, Any]:
        """Analyze trends with statistical modeling.

        Args:
            customer_id: Google Ads customer ID
            metric: Metric to analyze (impressions, clicks, conversions, cost)
            resource_type: Resource type (campaign, ad_group, keyword)
            resource_id: Optional specific resource ID
            lookback_days: Number of days to analyze (default: 90)

        Returns:
            Dictionary with trend analysis
        """
        with performance_logger.track_operation(self, 'analyze_trends'):
            import datetime
            from scipy import stats
            import numpy as np

            # Calculate date range
            end_date = datetime.datetime.now()
            start_date = end_date - datetime.timedelta(days=lookback_days)

            # Build query based on resource type
            resource_mapping = {
                'campaign': ('campaign', 'campaign.id', 'campaign.name'),
                'ad_group': ('ad_group', 'ad_group.id', 'ad_group.name'),
                'keyword': ('ad_group_criterion', 'ad_group_criterion.criterion_id', 'ad_group_criterion.keyword.text')
            }

            if resource_type not in resource_mapping:
                raise ValueError(f"Invalid resource_type: {resource_type}")

            from_table, id_field, name_field = resource_mapping[resource_type]

            # Validate metric
            valid_metrics = ['impressions', 'clicks', 'conversions', 'cost', 'ctr', 'conversion_rate']
            if metric not in valid_metrics:
                raise ValueError(f"Invalid metric: {metric}. Must be one of: {valid_metrics}")

            metric_field = f"metrics.{metric}" if metric not in ['cost'] else "metrics.cost_micros"

            query_parts = [
                f"SELECT segments.date, {metric_field}",
                f"FROM {from_table}",
                f"WHERE segments.date BETWEEN '{start_date.strftime('%Y-%m-%d')}' AND '{end_date.strftime('%Y-%m-%d')}'"
            ]

            if resource_id:
                query_parts.append(f"AND {id_field} = {resource_id}")

            query_parts.append("ORDER BY segments.date ASC")

            query = " ".join(query_parts)

            ga_service = self.client.get_service("GoogleAdsService")
            request = self.client.get_type("SearchGoogleAdsRequest")
            request.customer_id = customer_id
            request.query = query

            response = ga_service.search(request=request)

            # Collect daily data
            daily_data = []
            for row in response:
                if metric == 'cost':
                    value = row.metrics.cost_micros / 1_000_000
                else:
                    value = getattr(row.metrics, metric)

                daily_data.append({
                    'date': row.segments.date,
                    'value': value
                })

            if len(daily_data) < 7:
                return {
                    'error': 'Insufficient data for trend analysis (minimum 7 days required)',
                    'data_points': len(daily_data)
                }

            # Prepare data for analysis
            dates = [d['date'] for d in daily_data]
            values = np.array([d['value'] for d in daily_data])
            x = np.arange(len(values))

            # Linear regression for trend
            slope, intercept, r_value, p_value, std_err = stats.linregress(x, values)

            # Determine trend direction
            if p_value < 0.05:  # Statistically significant
                if slope > 0:
                    trend_direction = 'upward'
                else:
                    trend_direction = 'downward'
            else:
                trend_direction = 'stable'

            # Calculate percent change
            first_value = values[0] if values[0] > 0 else 1
            last_value = values[-1] if values[-1] > 0 else 1
            percent_change = ((last_value - first_value) / first_value) * 100

            # Detect anomalies (values beyond 2 standard deviations)
            mean = np.mean(values)
            std = np.std(values)
            anomalies = []

            for i, (date, value) in enumerate(zip(dates, values)):
                z_score = (value - mean) / std if std > 0 else 0
                if abs(z_score) > 2:
                    anomalies.append({
                        'date': date,
                        'value': float(value),
                        'z_score': float(z_score),
                        'deviation': 'high' if z_score > 0 else 'low'
                    })

            # Forecast next 7 days using linear trend
            future_x = np.arange(len(values), len(values) + 7)
            forecast_values = slope * future_x + intercept
            forecast_dates = [(end_date + datetime.timedelta(days=i+1)).strftime('%Y-%m-%d') for i in range(7)]

            forecast = [
                {'date': date, 'predicted_value': float(value)}
                for date, value in zip(forecast_dates, forecast_values)
            ]

            audit_logger.log_api_call(
                operation='trend_analysis',
                customer_id=customer_id,
                details={'metric': metric, 'resource_type': resource_type, 'lookback_days': lookback_days}
            )

            return {
                'metric': metric,
                'resource_type': resource_type,
                'resource_id': resource_id,
                'date_range': {
                    'start_date': start_date.strftime('%Y-%m-%d'),
                    'end_date': end_date.strftime('%Y-%m-%d'),
                    'days': lookback_days
                },
                'trend': {
                    'direction': trend_direction,
                    'slope': float(slope),
                    'percent_change': float(percent_change),
                    'r_squared': float(r_value ** 2),
                    'p_value': float(p_value),
                    'statistically_significant': p_value < 0.05
                },
                'statistics': {
                    'mean': float(mean),
                    'std_dev': float(std),
                    'min': float(np.min(values)),
                    'max': float(np.max(values)),
                    'median': float(np.median(values))
                },
                'anomalies': anomalies,
                'forecast': forecast,
                'daily_data': [
                    {'date': d['date'], 'value': float(d['value'])}
                    for d in daily_data
                ]
            }

    def get_competitor_insights(
        self,
        customer_id: str,
        campaign_id: Optional[str] = None,
        date_range: str = "LAST_30_DAYS"
    ) -> Dict[str, Any]:
        """Get detailed competitor insights from auction data.

        Args:
            customer_id: Google Ads customer ID
            campaign_id: Optional campaign ID filter
            date_range: Date range for metrics

        Returns:
            Dictionary with competitor insights
        """
        with performance_logger.track_operation(self, 'get_competitor_insights'):
            # Query auction insights
            query_parts = [
                "SELECT campaign.id, campaign.name,",
                "ad_group.id, ad_group.name,",
                "auction_insight.domain,",
                "metrics.impression_share,",
                "metrics.overlap_rate,",
                "metrics.position_above_rate,",
                "metrics.top_of_page_rate,",
                "metrics.absolute_top_impression_percentage,",
                "metrics.outranking_share",
                "FROM auction_insight",
                f"WHERE segments.date DURING {date_range}"
            ]

            if campaign_id:
                query_parts.append(f"AND campaign.id = {campaign_id}")

            query_parts.append("ORDER BY metrics.impression_share DESC")
            query_parts.append("LIMIT 100")

            query = " ".join(query_parts)

            ga_service = self.client.get_service("GoogleAdsService")
            request = self.client.get_type("SearchGoogleAdsRequest")
            request.customer_id = customer_id
            request.query = query

            audit_logger.log_api_call(
                operation='competitor_insights',
                customer_id=customer_id,
                details={'campaign_id': campaign_id, 'date_range': date_range}
            )

            try:
                response = ga_service.search(request=request)
            except Exception as e:
                # Auction insights may not be available for all accounts
                return {
                    'error': 'Auction insights not available',
                    'message': 'This feature requires eligible campaigns with sufficient impression volume',
                    'details': str(e)
                }

            # Parse competitor data
            competitors = []
            your_impression_share = 0

            for row in response:
                domain = row.auction_insight.domain

                competitor_data = {
                    'campaign_id': row.campaign.id,
                    'campaign_name': row.campaign.name,
                    'ad_group_id': row.ad_group.id,
                    'ad_group_name': row.ad_group.name,
                    'domain': domain,
                    'impression_share': row.metrics.impression_share,
                    'overlap_rate': row.metrics.overlap_rate,
                    'position_above_rate': row.metrics.position_above_rate,
                    'top_of_page_rate': row.metrics.top_of_page_rate,
                    'absolute_top_rate': row.metrics.absolute_top_impression_percentage,
                    'outranking_share': row.metrics.outranking_share
                }

                if 'yourdomain.com' in domain.lower():  # Placeholder - would need actual domain detection
                    your_impression_share = row.metrics.impression_share
                else:
                    competitors.append(competitor_data)

            # Rank competitors
            top_competitors = sorted(competitors, key=lambda x: x['impression_share'], reverse=True)[:10]
            most_overlap = sorted(competitors, key=lambda x: x['overlap_rate'], reverse=True)[:5]
            highest_outranking = sorted([c for c in competitors if c['outranking_share'] > your_impression_share],
                                       key=lambda x: x['outranking_share'], reverse=True)[:5]

            return {
                'date_range': date_range,
                'campaign_id': campaign_id,
                'your_impression_share': your_impression_share,
                'total_competitors': len(competitors),
                'competitors': competitors,
                'top_competitors': {
                    'by_impression_share': top_competitors,
                    'by_overlap_rate': most_overlap,
                    'outranking_you': highest_outranking
                },
                'competitive_position': {
                    'average_competitor_impression_share': sum(c['impression_share'] for c in competitors) / len(competitors) if competitors else 0,
                    'your_rank': len([c for c in competitors if c['impression_share'] > your_impression_share]) + 1,
                    'total_market_players': len(competitors) + 1
                }
            }
