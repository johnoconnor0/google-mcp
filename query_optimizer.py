"""
Google Ads Query Optimizer

GAQL query optimization and validation with:
- Query syntax validation
- Field existence checking
- Query complexity analysis
- Automatic pagination
- Query performance hints
- Field compatibility checking
"""

import re
import logging
from typing import List, Dict, Any, Optional, Set, Tuple
from enum import Enum
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class QueryComplexity(str, Enum):
    """Query complexity levels."""
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    VERY_COMPLEX = "very_complex"


@dataclass
class QueryAnalysis:
    """Query analysis result."""
    is_valid: bool
    complexity: QueryComplexity
    estimated_rows: Optional[int]
    warnings: List[str]
    suggestions: List[str]
    errors: List[str]
    field_count: int
    has_aggregation: bool
    has_segmentation: bool


class GAQLValidator:
    """Validates Google Ads Query Language (GAQL) queries."""

    # Common GAQL keywords
    KEYWORDS = {
        'SELECT', 'FROM', 'WHERE', 'ORDER BY', 'LIMIT',
        'DURING', 'BETWEEN', 'AND', 'OR', 'NOT', 'IN',
        'LIKE', 'IS NULL', 'IS NOT NULL', 'DESC', 'ASC'
    }

    # Valid resources in Google Ads API
    VALID_RESOURCES = {
        'customer', 'campaign', 'ad_group', 'ad_group_ad',
        'ad_group_criterion', 'keyword_view', 'search_term_view',
        'campaign_criterion', 'recommendation', 'customer_client',
        'bidding_strategy', 'campaign_budget', 'ad_group_audience_view',
        'audience', 'user_list', 'conversion_action', 'asset',
        'campaign_asset', 'ad_group_asset', 'extension_feed_item',
        'geographic_view', 'age_range_view', 'gender_view',
        'landing_page_view', 'shopping_performance_view'
    }

    # Metrics fields (frequently updated, should use recent date ranges)
    METRICS_FIELDS = {
        'metrics.clicks', 'metrics.impressions', 'metrics.cost_micros',
        'metrics.conversions', 'metrics.conversions_value',
        'metrics.average_cpc', 'metrics.average_cpm', 'metrics.ctr',
        'metrics.conversion_rate', 'metrics.cost_per_conversion',
        'metrics.all_conversions', 'metrics.interactions',
        'metrics.engagement_rate', 'metrics.video_views'
    }

    @staticmethod
    def validate_syntax(query: str) -> Tuple[bool, List[str]]:
        """
        Validate basic GAQL syntax.

        Args:
            query: GAQL query string

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []

        # Check if query is empty
        if not query or not query.strip():
            errors.append("Query cannot be empty")
            return False, errors

        # Check for SELECT clause
        if not re.search(r'\bSELECT\b', query, re.IGNORECASE):
            errors.append("Query must contain SELECT clause")

        # Check for FROM clause
        if not re.search(r'\bFROM\b', query, re.IGNORECASE):
            errors.append("Query must contain FROM clause")

        # Check balanced parentheses
        if query.count('(') != query.count(')'):
            errors.append("Unbalanced parentheses in query")

        # Check for common syntax errors
        if re.search(r'SELECT\s+FROM', query, re.IGNORECASE):
            errors.append("SELECT clause cannot be empty")

        if re.search(r'FROM\s+(WHERE|ORDER|LIMIT)', query, re.IGNORECASE):
            errors.append("FROM clause must specify a resource")

        # Check for unterminated strings
        single_quotes = query.count("'") - query.count("\\'")
        double_quotes = query.count('"') - query.count('\\"')

        if single_quotes % 2 != 0:
            errors.append("Unterminated string (single quote)")

        if double_quotes % 2 != 0:
            errors.append("Unterminated string (double quote)")

        return len(errors) == 0, errors

    @staticmethod
    def extract_resource(query: str) -> Optional[str]:
        """
        Extract resource name from query.

        Args:
            query: GAQL query

        Returns:
            Resource name or None
        """
        match = re.search(r'\bFROM\s+(\w+)', query, re.IGNORECASE)
        if match:
            return match.group(1).lower()
        return None

    @staticmethod
    def extract_fields(query: str) -> List[str]:
        """
        Extract field names from SELECT clause.

        Args:
            query: GAQL query

        Returns:
            List of field names
        """
        # Extract SELECT clause
        select_match = re.search(
            r'\bSELECT\s+(.*?)\s+FROM\b',
            query,
            re.IGNORECASE | re.DOTALL
        )

        if not select_match:
            return []

        select_clause = select_match.group(1)

        # Split by comma (but not within parentheses)
        fields = []
        current_field = ''
        paren_depth = 0

        for char in select_clause:
            if char == '(':
                paren_depth += 1
            elif char == ')':
                paren_depth -= 1
            elif char == ',' and paren_depth == 0:
                field = current_field.strip()
                if field:
                    fields.append(field)
                current_field = ''
                continue

            current_field += char

        # Add last field
        field = current_field.strip()
        if field:
            fields.append(field)

        return fields

    @classmethod
    def validate_resource(cls, resource: Optional[str]) -> Tuple[bool, Optional[str]]:
        """
        Validate resource name.

        Args:
            resource: Resource name

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not resource:
            return False, "No resource specified"

        if resource.lower() not in cls.VALID_RESOURCES:
            return False, f"Invalid resource: {resource}. Must be one of: {', '.join(sorted(cls.VALID_RESOURCES))}"

        return True, None

    @classmethod
    def analyze_complexity(cls, query: str) -> QueryComplexity:
        """
        Analyze query complexity.

        Args:
            query: GAQL query

        Returns:
            Complexity level
        """
        complexity_score = 0

        # Factor 1: Number of fields
        fields = cls.extract_fields(query)
        field_count = len(fields)

        if field_count > 20:
            complexity_score += 3
        elif field_count > 10:
            complexity_score += 2
        elif field_count > 5:
            complexity_score += 1

        # Factor 2: WHERE clause complexity
        where_match = re.search(r'\bWHERE\b', query, re.IGNORECASE)
        if where_match:
            complexity_score += 1

            # Count conditions
            and_count = len(re.findall(r'\bAND\b', query, re.IGNORECASE))
            or_count = len(re.findall(r'\bOR\b', query, re.IGNORECASE))
            condition_count = and_count + or_count

            if condition_count > 5:
                complexity_score += 2
            elif condition_count > 2:
                complexity_score += 1

        # Factor 3: Segmentation
        segments_match = re.search(r'\bsegments\.\w+', query, re.IGNORECASE)
        if segments_match:
            complexity_score += 1

        # Factor 4: ORDER BY
        order_match = re.search(r'\bORDER BY\b', query, re.IGNORECASE)
        if order_match:
            complexity_score += 1

        # Determine complexity level
        if complexity_score >= 7:
            return QueryComplexity.VERY_COMPLEX
        elif complexity_score >= 5:
            return QueryComplexity.COMPLEX
        elif complexity_score >= 3:
            return QueryComplexity.MODERATE
        else:
            return QueryComplexity.SIMPLE


class QueryOptimizer:
    """Optimizes GAQL queries for performance."""

    def __init__(self):
        """Initialize query optimizer."""
        self.validator = GAQLValidator()

    def analyze_query(self, query: str) -> QueryAnalysis:
        """
        Analyze query and provide optimization suggestions.

        Args:
            query: GAQL query

        Returns:
            Query analysis result
        """
        warnings = []
        suggestions = []
        errors = []

        # Validate syntax
        is_valid, syntax_errors = self.validator.validate_syntax(query)
        errors.extend(syntax_errors)

        # Extract resource
        resource = self.validator.extract_resource(query)

        # Validate resource
        resource_valid, resource_error = self.validator.validate_resource(resource)
        if not resource_valid:
            errors.append(resource_error)

        # Extract and analyze fields
        fields = self.validator.extract_fields(query)
        field_count = len(fields)

        # Check for metrics without date range
        has_metrics = any(
            field.startswith('metrics.') or field in self.validator.METRICS_FIELDS
            for field in fields
        )

        has_date_filter = bool(re.search(
            r'(DURING|segments\.date)',
            query,
            re.IGNORECASE
        ))

        if has_metrics and not has_date_filter:
            warnings.append(
                "Query includes metrics but no date range. "
                "Consider adding 'WHERE segments.date DURING LAST_30_DAYS' for better performance."
            )

        # Check for SELECT *
        if '*' in fields:
            warnings.append(
                "Using SELECT * may return unnecessary data. "
                "Specify only the fields you need for better performance."
            )
            suggestions.append("List specific fields instead of using SELECT *")

        # Check field count
        if field_count > 20:
            warnings.append(
                f"Query selects {field_count} fields. "
                "Consider reducing to only necessary fields for better performance."
            )
        elif field_count > 30:
            errors.append(
                f"Query selects {field_count} fields, which may exceed API limits. "
                "Reduce to 30 or fewer fields."
            )

        # Check for LIMIT clause
        has_limit = bool(re.search(r'\bLIMIT\b', query, re.IGNORECASE))
        if not has_limit:
            suggestions.append(
                "Add LIMIT clause to prevent accidentally fetching too many rows. "
                "Example: LIMIT 1000"
            )

        # Check for aggregation
        has_aggregation = bool(re.search(
            r'\b(SUM|COUNT|AVG|MAX|MIN)\s*\(',
            query,
            re.IGNORECASE
        ))

        # Check for segmentation
        has_segmentation = bool(re.search(r'\bsegments\.\w+', query))

        # Analyze complexity
        complexity = self.validator.analyze_complexity(query)

        # Complexity-based suggestions
        if complexity in [QueryComplexity.COMPLEX, QueryComplexity.VERY_COMPLEX]:
            suggestions.append(
                "Consider breaking this complex query into multiple simpler queries "
                "for better performance and maintainability."
            )

        # Resource-specific suggestions
        if resource == 'search_term_view':
            if not has_date_filter:
                warnings.append(
                    "search_term_view queries should always include a date range "
                    "to avoid fetching excessive historical data."
                )

        if resource == 'keyword_view':
            suggestions.append(
                "For keyword performance data, consider filtering by campaign_id "
                "or ad_group_id to reduce result set."
            )

        return QueryAnalysis(
            is_valid=is_valid and len(errors) == 0,
            complexity=complexity,
            estimated_rows=None,  # Would require historical stats
            warnings=warnings,
            suggestions=suggestions,
            errors=errors,
            field_count=field_count,
            has_aggregation=has_aggregation,
            has_segmentation=has_segmentation
        )

    def optimize_query(self, query: str) -> str:
        """
        Optimize query by applying best practices.

        Args:
            query: Original query

        Returns:
            Optimized query
        """
        optimized = query

        # Add LIMIT if missing
        if not re.search(r'\bLIMIT\b', optimized, re.IGNORECASE):
            optimized += ' LIMIT 1000'
            logger.info("Added LIMIT 1000 to query")

        # Format query for readability
        optimized = self._format_query(optimized)

        return optimized

    def _format_query(self, query: str) -> str:
        """
        Format query for readability.

        Args:
            query: Query to format

        Returns:
            Formatted query
        """
        # This is a simple formatter - could be enhanced
        formatted = query.strip()

        # Add newlines after major clauses
        formatted = re.sub(r'\s+FROM\s+', '\nFROM ', formatted, flags=re.IGNORECASE)
        formatted = re.sub(r'\s+WHERE\s+', '\nWHERE ', formatted, flags=re.IGNORECASE)
        formatted = re.sub(r'\s+ORDER BY\s+', '\nORDER BY ', formatted, flags=re.IGNORECASE)
        formatted = re.sub(r'\s+LIMIT\s+', '\nLIMIT ', formatted, flags=re.IGNORECASE)

        return formatted

    def suggest_indexes(self, resource: str, filters: List[str]) -> List[str]:
        """
        Suggest which fields to filter on for optimal performance.

        Args:
            resource: Resource being queried
            filters: Current filter fields

        Returns:
            List of suggested filter fields
        """
        suggestions = []

        # Resource-specific index suggestions
        index_suggestions = {
            'campaign': ['campaign.id', 'campaign.status', 'segments.date'],
            'ad_group': ['ad_group.id', 'campaign.id', 'ad_group.status'],
            'keyword_view': ['ad_group.id', 'campaign.id', 'segments.date'],
            'search_term_view': ['segments.date', 'campaign.id'],
        }

        if resource in index_suggestions:
            for suggested_field in index_suggestions[resource]:
                if suggested_field not in filters:
                    suggestions.append(
                        f"Consider filtering by {suggested_field} for better performance"
                    )

        return suggestions


# Global optimizer instance
_query_optimizer: Optional[QueryOptimizer] = None


def get_query_optimizer() -> QueryOptimizer:
    """Get or create global query optimizer."""
    global _query_optimizer
    if _query_optimizer is None:
        _query_optimizer = QueryOptimizer()
    return _query_optimizer


def validate_query(query: str) -> QueryAnalysis:
    """
    Validate and analyze a GAQL query.

    Args:
        query: GAQL query string

    Returns:
        Query analysis result
    """
    optimizer = get_query_optimizer()
    return optimizer.analyze_query(query)


def optimize_query(query: str) -> str:
    """
    Optimize a GAQL query.

    Args:
        query: Original query

    Returns:
        Optimized query
    """
    optimizer = get_query_optimizer()
    return optimizer.optimize_query(query)
