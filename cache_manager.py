"""
Google Ads MCP Cache Manager

Intelligent caching system with:
- In-memory caching (cachetools)
- Redis distributed caching
- Cache invalidation strategies
- TTL configuration per resource type
- Cache key generation
- Cache statistics
"""

import hashlib
import json
import logging
from typing import Optional, Any, Callable, Dict
from functools import wraps
from datetime import timedelta
from enum import Enum

# Try to import caching libraries
try:
    from cachetools import TTLCache, LRUCache
    CACHETOOLS_AVAILABLE = True
except ImportError:
    CACHETOOLS_AVAILABLE = False

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

logger = logging.getLogger(__name__)


class CacheBackend(str, Enum):
    """Cache backend types."""
    MEMORY = "memory"
    REDIS = "redis"
    NONE = "none"


class ResourceType(str, Enum):
    """Google Ads resource types for cache TTL configuration."""
    ACCOUNT = "account"
    CAMPAIGN = "campaign"
    AD_GROUP = "ad_group"
    AD = "ad"
    KEYWORD = "keyword"
    SEARCH_TERM = "search_term"
    PERFORMANCE = "performance"
    RECOMMENDATION = "recommendation"
    AUDIENCE = "audience"
    CONVERSION = "conversion"


# Default TTL (in seconds) for each resource type
DEFAULT_TTL = {
    ResourceType.ACCOUNT: 3600,  # 1 hour (rarely changes)
    ResourceType.CAMPAIGN: 1800,  # 30 minutes
    ResourceType.AD_GROUP: 1800,  # 30 minutes
    ResourceType.AD: 900,  # 15 minutes (can change frequently)
    ResourceType.KEYWORD: 900,  # 15 minutes
    ResourceType.SEARCH_TERM: 600,  # 10 minutes (real-time data)
    ResourceType.PERFORMANCE: 300,  # 5 minutes (performance metrics update frequently)
    ResourceType.RECOMMENDATION: 3600,  # 1 hour (changes slowly)
    ResourceType.AUDIENCE: 1800,  # 30 minutes
    ResourceType.CONVERSION: 600,  # 10 minutes
}


class CacheStats:
    """Track cache statistics."""

    def __init__(self):
        """Initialize cache statistics."""
        self.hits = 0
        self.misses = 0
        self.sets = 0
        self.deletes = 0
        self.errors = 0

    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total = self.hits + self.misses
        if total == 0:
            return 0.0
        return self.hits / total

    def to_dict(self) -> Dict[str, Any]:
        """Convert stats to dictionary."""
        return {
            "hits": self.hits,
            "misses": self.misses,
            "sets": self.sets,
            "deletes": self.deletes,
            "errors": self.errors,
            "hit_rate": f"{self.hit_rate * 100:.2f}%",
            "total_requests": self.hits + self.misses
        }


class MemoryCache:
    """In-memory cache using cachetools."""

    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        """
        Initialize memory cache.

        Args:
            max_size: Maximum number of items in cache
            default_ttl: Default TTL in seconds
        """
        if not CACHETOOLS_AVAILABLE:
            raise ImportError("cachetools is required for memory cache. Install with: pip install cachetools")

        self.default_ttl = default_ttl
        self.cache = TTLCache(maxsize=max_size, ttl=default_ttl)
        self.stats = CacheStats()
        logger.info(f"Memory cache initialized (max_size={max_size}, default_ttl={default_ttl}s)")

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        try:
            value = self.cache.get(key)
            if value is not None:
                self.stats.hits += 1
                logger.debug(f"Cache hit: {key}")
                return value
            else:
                self.stats.misses += 1
                logger.debug(f"Cache miss: {key}")
                return None
        except Exception as e:
            self.stats.errors += 1
            logger.error(f"Cache get error for key {key}: {e}")
            return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set value in cache."""
        try:
            # Note: cachetools TTLCache uses global TTL, so ttl parameter is ignored
            # For per-key TTL, we'd need a more complex implementation
            self.cache[key] = value
            self.stats.sets += 1
            logger.debug(f"Cache set: {key}")
        except Exception as e:
            self.stats.errors += 1
            logger.error(f"Cache set error for key {key}: {e}")

    def delete(self, key: str):
        """Delete value from cache."""
        try:
            if key in self.cache:
                del self.cache[key]
                self.stats.deletes += 1
                logger.debug(f"Cache delete: {key}")
        except Exception as e:
            self.stats.errors += 1
            logger.error(f"Cache delete error for key {key}: {e}")

    def clear(self):
        """Clear all cache entries."""
        self.cache.clear()
        logger.info("Memory cache cleared")

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        stats = self.stats.to_dict()
        stats["backend"] = "memory"
        stats["size"] = len(self.cache)
        stats["max_size"] = self.cache.maxsize
        return stats


class RedisCache:
    """Redis-based distributed cache."""

    def __init__(self, redis_url: str, default_ttl: int = 3600):
        """
        Initialize Redis cache.

        Args:
            redis_url: Redis connection URL (e.g., redis://localhost:6379)
            default_ttl: Default TTL in seconds
        """
        if not REDIS_AVAILABLE:
            raise ImportError("redis is required for Redis cache. Install with: pip install redis")

        self.default_ttl = default_ttl
        self.client = redis.from_url(redis_url, decode_responses=True)
        self.stats = CacheStats()

        # Test connection
        try:
            self.client.ping()
            logger.info(f"Redis cache initialized (url={redis_url}, default_ttl={default_ttl}s)")
        except Exception as e:
            logger.error(f"Redis connection failed: {e}")
            raise

    def get(self, key: str) -> Optional[Any]:
        """Get value from Redis."""
        try:
            value_str = self.client.get(key)
            if value_str:
                self.stats.hits += 1
                logger.debug(f"Redis cache hit: {key}")
                # Deserialize JSON
                return json.loads(value_str)
            else:
                self.stats.misses += 1
                logger.debug(f"Redis cache miss: {key}")
                return None
        except Exception as e:
            self.stats.errors += 1
            logger.error(f"Redis get error for key {key}: {e}")
            return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set value in Redis."""
        try:
            ttl_seconds = ttl or self.default_ttl
            # Serialize to JSON
            value_str = json.dumps(value)
            self.client.setex(key, ttl_seconds, value_str)
            self.stats.sets += 1
            logger.debug(f"Redis cache set: {key} (TTL={ttl_seconds}s)")
        except Exception as e:
            self.stats.errors += 1
            logger.error(f"Redis set error for key {key}: {e}")

    def delete(self, key: str):
        """Delete value from Redis."""
        try:
            self.client.delete(key)
            self.stats.deletes += 1
            logger.debug(f"Redis cache delete: {key}")
        except Exception as e:
            self.stats.errors += 1
            logger.error(f"Redis delete error for key {key}: {e}")

    def clear(self):
        """Clear all cache entries (use with caution!)."""
        try:
            self.client.flushdb()
            logger.warning("Redis cache cleared (entire database flushed)")
        except Exception as e:
            logger.error(f"Redis clear error: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        stats = self.stats.to_dict()
        stats["backend"] = "redis"

        # Add Redis-specific stats
        try:
            info = self.client.info()
            stats["connected_clients"] = info.get("connected_clients", 0)
            stats["used_memory_human"] = info.get("used_memory_human", "unknown")
            stats["total_keys"] = self.client.dbsize()
        except Exception as e:
            logger.error(f"Failed to get Redis stats: {e}")

        return stats


class NoCache:
    """No-op cache for when caching is disabled."""

    def __init__(self):
        """Initialize no-op cache."""
        logger.info("Caching disabled")

    def get(self, key: str) -> None:
        """Always return None (cache miss)."""
        return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Do nothing."""
        pass

    def delete(self, key: str):
        """Do nothing."""
        pass

    def clear(self):
        """Do nothing."""
        pass

    def get_stats(self) -> Dict[str, Any]:
        """Return empty stats."""
        return {
            "backend": "none",
            "message": "Caching is disabled"
        }


class CacheManager:
    """
    Manages caching with intelligent invalidation.
    """

    def __init__(
        self,
        backend: CacheBackend = CacheBackend.MEMORY,
        redis_url: Optional[str] = None,
        max_size: int = 1000,
        default_ttl: int = 3600
    ):
        """
        Initialize cache manager.

        Args:
            backend: Cache backend to use
            redis_url: Redis URL (required if backend is REDIS)
            max_size: Max cache size (for memory backend)
            default_ttl: Default TTL in seconds
        """
        self.backend_type = backend

        # Initialize appropriate backend
        if backend == CacheBackend.MEMORY:
            self.backend = MemoryCache(max_size=max_size, default_ttl=default_ttl)
        elif backend == CacheBackend.REDIS:
            if not redis_url:
                raise ValueError("redis_url is required for Redis backend")
            self.backend = RedisCache(redis_url=redis_url, default_ttl=default_ttl)
        else:
            self.backend = NoCache()

    def _generate_key(
        self,
        customer_id: str,
        resource_type: ResourceType,
        operation: str,
        **params
    ) -> str:
        """
        Generate cache key.

        Args:
            customer_id: Google Ads customer ID
            resource_type: Resource type
            operation: Operation name
            **params: Additional parameters to include in key

        Returns:
            Cache key string
        """
        # Create deterministic key from parameters
        key_parts = [
            f"customer:{customer_id}",
            f"resource:{resource_type.value}",
            f"operation:{operation}"
        ]

        # Add sorted parameters for deterministic key
        if params:
            param_str = json.dumps(params, sort_keys=True)
            param_hash = hashlib.md5(param_str.encode()).hexdigest()
            key_parts.append(f"params:{param_hash}")

        return ":".join(key_parts)

    def get(
        self,
        customer_id: str,
        resource_type: ResourceType,
        operation: str,
        **params
    ) -> Optional[Any]:
        """
        Get cached value.

        Args:
            customer_id: Google Ads customer ID
            resource_type: Resource type
            operation: Operation name
            **params: Additional parameters

        Returns:
            Cached value or None
        """
        key = self._generate_key(customer_id, resource_type, operation, **params)
        return self.backend.get(key)

    def set(
        self,
        customer_id: str,
        resource_type: ResourceType,
        operation: str,
        value: Any,
        ttl: Optional[int] = None,
        **params
    ):
        """
        Set cached value.

        Args:
            customer_id: Google Ads customer ID
            resource_type: Resource type
            operation: Operation name
            value: Value to cache
            ttl: Optional TTL override (uses resource type default if None)
            **params: Additional parameters
        """
        key = self._generate_key(customer_id, resource_type, operation, **params)

        # Use resource-specific TTL if not provided
        if ttl is None:
            ttl = DEFAULT_TTL.get(resource_type, 3600)

        self.backend.set(key, value, ttl=ttl)

    def invalidate(
        self,
        customer_id: str,
        resource_type: Optional[ResourceType] = None,
        operation: Optional[str] = None
    ):
        """
        Invalidate cache entries.

        Args:
            customer_id: Google Ads customer ID
            resource_type: Optional resource type to invalidate
            operation: Optional operation to invalidate

        Note: This is a simple implementation. For Redis, you'd use pattern matching.
        """
        # For now, this is a placeholder
        # In production, you'd want to track keys or use Redis SCAN/DELETE patterns
        logger.warning(f"Cache invalidation requested for customer {customer_id}")
        # TODO: Implement pattern-based invalidation

    def clear(self):
        """Clear all cache entries."""
        self.backend.clear()

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return self.backend.get_stats()


def cached(
    resource_type: ResourceType,
    operation: str,
    ttl: Optional[int] = None,
    cache_manager: Optional[CacheManager] = None
):
    """
    Decorator to cache function results.

    Args:
        resource_type: Resource type being cached
        operation: Operation name
        ttl: Optional TTL override
        cache_manager: Cache manager instance (uses global if None)

    Returns:
        Decorated function

    Example:
        @cached(ResourceType.CAMPAIGN, "list_campaigns", ttl=300)
        async def get_campaigns(customer_id: str, **kwargs):
            # Function implementation
            pass
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(customer_id: str, *args, **kwargs):
            # Get cache manager
            cm = cache_manager or get_cache_manager()

            # Try to get from cache
            cached_value = cm.get(
                customer_id=customer_id,
                resource_type=resource_type,
                operation=operation,
                **kwargs
            )

            if cached_value is not None:
                logger.debug(f"Returning cached result for {operation}")
                return cached_value

            # Execute function
            result = await func(customer_id, *args, **kwargs)

            # Cache the result
            cm.set(
                customer_id=customer_id,
                resource_type=resource_type,
                operation=operation,
                value=result,
                ttl=ttl,
                **kwargs
            )

            return result

        return wrapper
    return decorator


# Global cache manager instance
_cache_manager: Optional[CacheManager] = None


def get_cache_manager() -> CacheManager:
    """Get or create global cache manager."""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager(backend=CacheBackend.MEMORY)
    return _cache_manager


def initialize_cache(
    backend: CacheBackend = CacheBackend.MEMORY,
    **kwargs
) -> CacheManager:
    """
    Initialize global cache manager.

    Args:
        backend: Cache backend type
        **kwargs: Backend-specific arguments

    Returns:
        Initialized cache manager
    """
    global _cache_manager
    _cache_manager = CacheManager(backend=backend, **kwargs)
    return _cache_manager
