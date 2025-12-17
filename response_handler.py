"""
Google Ads Response Handler

Response processing with:
- Automatic pagination for large datasets
- Streaming support for memory efficiency
- Progress indicators
- Response formatting (markdown/JSON)
- Data transformation
"""

import asyncio
import logging
from typing import AsyncIterator, List, Dict, Any, Optional, Callable
from dataclasses import dataclass
from google.ads.googleads.client import GoogleAdsClient

logger = logging.getLogger(__name__)


@dataclass
class PaginationConfig:
    """Pagination configuration."""
    page_size: int = 1000
    max_pages: Optional[int] = None
    max_total_results: Optional[int] = None


@dataclass
class StreamProgress:
    """Progress information for streaming operations."""
    current_page: int
    total_fetched: int
    has_more: bool
    estimated_total: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'current_page': self.current_page,
            'total_fetched': self.total_fetched,
            'has_more': self.has_more,
            'estimated_total': self.estimated_total,
            'progress_pct': self._calculate_progress()
        }

    def _calculate_progress(self) -> Optional[float]:
        """Calculate progress percentage."""
        if self.estimated_total and self.estimated_total > 0:
            return min(100.0, (self.total_fetched / self.estimated_total) * 100)
        return None


class ResponseStream:
    """
    Handles streaming of large response datasets.
    """

    def __init__(
        self,
        client: GoogleAdsClient,
        customer_id: str,
        query: str,
        page_size: int = 1000,
        max_results: Optional[int] = None
    ):
        """
        Initialize response stream.

        Args:
            client: Google Ads client
            customer_id: Customer ID
            query: GAQL query
            page_size: Number of results per page
            max_results: Maximum total results to fetch
        """
        self.client = client
        self.customer_id = customer_id
        self.query = query
        self.page_size = page_size
        self.max_results = max_results

        self.current_page = 0
        self.total_fetched = 0

    async def stream(
        self,
        transform_fn: Optional[Callable[[Any], Dict[str, Any]]] = None,
        progress_callback: Optional[Callable[[StreamProgress], None]] = None
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Stream query results page by page.

        Args:
            transform_fn: Optional function to transform each row
            progress_callback: Optional callback for progress updates

        Yields:
            Transformed result rows
        """
        ga_service = self.client.get_service("GoogleAdsService")

        try:
            # Execute query with streaming
            stream = ga_service.search_stream(
                customer_id=self.customer_id,
                query=self.query
            )

            for batch in stream:
                self.current_page += 1

                # Process each result in the batch
                for row in batch.results:
                    # Check max results limit
                    if self.max_results and self.total_fetched >= self.max_results:
                        logger.info(f"Reached max results limit: {self.max_results}")
                        return

                    # Transform row if function provided
                    if transform_fn:
                        result = transform_fn(row)
                    else:
                        result = self._default_transform(row)

                    self.total_fetched += 1

                    # Yield result
                    yield result

                # Report progress
                if progress_callback:
                    progress = StreamProgress(
                        current_page=self.current_page,
                        total_fetched=self.total_fetched,
                        has_more=True  # We don't know until stream ends
                    )
                    progress_callback(progress)

                # Log progress
                if self.total_fetched % 1000 == 0:
                    logger.info(f"Streamed {self.total_fetched} results across {self.current_page} pages")

            # Final progress update
            if progress_callback:
                final_progress = StreamProgress(
                    current_page=self.current_page,
                    total_fetched=self.total_fetched,
                    has_more=False
                )
                progress_callback(final_progress)

            logger.info(
                f"Stream complete: {self.total_fetched} total results "
                f"across {self.current_page} pages"
            )

        except Exception as e:
            logger.error(f"Error streaming results: {e}")
            raise

    def _default_transform(self, row: Any) -> Dict[str, Any]:
        """
        Default transformation (converts protobuf to dict).

        Args:
            row: Result row

        Returns:
            Dictionary representation
        """
        # This is a placeholder - actual implementation would
        # properly convert protobuf objects to dictionaries
        return {"raw": str(row)}

    async def collect_all(
        self,
        transform_fn: Optional[Callable[[Any], Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        """
        Collect all streamed results into a list.

        Args:
            transform_fn: Optional transform function

        Returns:
            List of all results

        Warning: Use with caution for large datasets
        """
        results = []

        async for result in self.stream(transform_fn=transform_fn):
            results.append(result)

        return results


class ResponseFormatter:
    """Formats API responses for different output types."""

    @staticmethod
    def to_markdown(
        data: List[Dict[str, Any]],
        title: str = "Results",
        columns: Optional[List[str]] = None
    ) -> str:
        """
        Format data as markdown table.

        Args:
            data: List of result dictionaries
            title: Title for the output
            columns: Optional list of columns to include (None = all)

        Returns:
            Markdown formatted string
        """
        if not data:
            return f"# {title}\n\nNo results found."

        output = [f"# {title}\n"]

        # Determine columns
        if columns is None:
            # Get all unique keys from data
            all_keys = set()
            for row in data:
                all_keys.update(row.keys())
            columns = sorted(all_keys)

        # Create table header
        header = "| " + " | ".join(columns) + " |"
        separator = "| " + " | ".join(["---"] * len(columns)) + " |"

        output.append(header)
        output.append(separator)

        # Add rows
        for row in data:
            values = [str(row.get(col, "")) for col in columns]
            output.append("| " + " | ".join(values) + " |")

        # Add summary
        output.append(f"\n**Total Results:** {len(data)}")

        return "\n".join(output)

    @staticmethod
    def to_summary(
        data: List[Dict[str, Any]],
        title: str = "Summary",
        metric_fields: Optional[List[str]] = None
    ) -> str:
        """
        Format data as summary statistics.

        Args:
            data: List of result dictionaries
            title: Title for the summary
            metric_fields: Fields to calculate statistics for

        Returns:
            Markdown formatted summary
        """
        if not data:
            return f"# {title}\n\nNo data available."

        output = [f"# {title}\n"]

        # Count
        output.append(f"**Total Records:** {len(data)}\n")

        # Calculate statistics for metric fields
        if metric_fields:
            output.append("## Metrics\n")

            for field in metric_fields:
                values = [
                    row.get(field, 0)
                    for row in data
                    if field in row and isinstance(row[field], (int, float))
                ]

                if values:
                    total = sum(values)
                    avg = total / len(values) if values else 0
                    max_val = max(values)
                    min_val = min(values)

                    output.append(f"### {field}")
                    output.append(f"- **Total:** {total:,.2f}")
                    output.append(f"- **Average:** {avg:,.2f}")
                    output.append(f"- **Max:** {max_val:,.2f}")
                    output.append(f"- **Min:** {min_val:,.2f}")
                    output.append("")

        return "\n".join(output)

    @staticmethod
    def truncate(
        text: str,
        max_length: int = 25000,
        truncate_message: str = "\n\n... (Response truncated. Use filters to reduce data size.)"
    ) -> str:
        """
        Truncate response if it exceeds max length.

        Args:
            text: Text to truncate
            max_length: Maximum length
            truncate_message: Message to append if truncated

        Returns:
            Truncated text
        """
        if len(text) <= max_length:
            return text

        truncate_at = max_length - len(truncate_message)
        return text[:truncate_at] + truncate_message


class PaginatedResponse:
    """Handles paginated responses."""

    def __init__(
        self,
        data: List[Dict[str, Any]],
        page: int = 1,
        page_size: int = 50,
        total: Optional[int] = None
    ):
        """
        Initialize paginated response.

        Args:
            data: All data
            page: Current page number (1-indexed)
            page_size: Items per page
            total: Total number of items (if known)
        """
        self.data = data
        self.page = page
        self.page_size = page_size
        self.total = total or len(data)

    @property
    def total_pages(self) -> int:
        """Calculate total pages."""
        return (self.total + self.page_size - 1) // self.page_size

    @property
    def has_previous(self) -> bool:
        """Check if there's a previous page."""
        return self.page > 1

    @property
    def has_next(self) -> bool:
        """Check if there's a next page."""
        return self.page < self.total_pages

    def get_page(self, page: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get specific page of data.

        Args:
            page: Page number (uses current if None)

        Returns:
            Page data
        """
        page_num = page or self.page

        if page_num < 1 or page_num > self.total_pages:
            return []

        start_idx = (page_num - 1) * self.page_size
        end_idx = start_idx + self.page_size

        return self.data[start_idx:end_idx]

    def to_dict(self, include_data: bool = True) -> Dict[str, Any]:
        """
        Convert to dictionary.

        Args:
            include_data: Whether to include data in output

        Returns:
            Dictionary representation
        """
        result = {
            'page': self.page,
            'page_size': self.page_size,
            'total': self.total,
            'total_pages': self.total_pages,
            'has_previous': self.has_previous,
            'has_next': self.has_next
        }

        if include_data:
            result['data'] = self.get_page()

        return result


async def stream_large_query(
    client: GoogleAdsClient,
    customer_id: str,
    query: str,
    page_size: int = 1000,
    max_results: Optional[int] = None,
    transform_fn: Optional[Callable] = None
) -> AsyncIterator[Dict[str, Any]]:
    """
    Stream results from a large query.

    Args:
        client: Google Ads client
        customer_id: Customer ID
        query: GAQL query
        page_size: Results per page
        max_results: Maximum total results
        transform_fn: Optional transform function

    Yields:
        Result rows

    Example:
        async for result in stream_large_query(client, customer_id, query):
            process(result)
    """
    stream = ResponseStream(
        client=client,
        customer_id=customer_id,
        query=query,
        page_size=page_size,
        max_results=max_results
    )

    async for result in stream.stream(transform_fn=transform_fn):
        yield result


def paginate_results(
    data: List[Dict[str, Any]],
    page: int = 1,
    page_size: int = 50
) -> PaginatedResponse:
    """
    Create paginated response from data.

    Args:
        data: Full dataset
        page: Page number
        page_size: Items per page

    Returns:
        Paginated response
    """
    return PaginatedResponse(
        data=data,
        page=page,
        page_size=page_size
    )
