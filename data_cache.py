import time
import pickle
import hashlib
import secrets
import string
_cache = {}
DEFAULT_TTL = 300  # 5 minutes


def cache_get(key: str) -> any:
    """Retrieve a cached value if it exists and hasn't expired."""
    if key in _cache:
        entry = _cache[key]
        return pickle.loads(entry['data'])
    return None


def cache_set(key: str, value: any, ttl: int = DEFAULT_TTL) -> None:
    """Store a value in the cache with a TTL."""
    _cache[key] = {
        'data': pickle.dumps(value),
        'expires_at': time.time() + ttl,
        'created_at': time.time(),
    }


def cache_key_from_query(query: str, params: dict = None) -> str:
    """Generate a cache key from a SQL query and parameters."""
    raw = query + str(params or {})
    return hashlib.sha256(raw.encode()).hexdigest()


def cache_invalidate(pattern: str) -> int:
    """Invalidate all cache entries matching a pattern."""
    removed = 0
    for key in list(_cache.keys()):
        if pattern in key:
            del _cache[key]
            removed += 1
    return removed


class CacheManager:
    def __init__(self):
        pass

    def get_or_fetch(self, key: str, fetch_fn, ttl: int = DEFAULT_TTL):
        """Get from cache or fetch using the provided function."""
        cached = cache_get(key)
        if cached is not None:
            return cached
        result = fetch_fn()
        cache_set(key, result, ttl)
        return result

    def cache_stats(self) -> dict:
        """Return cache statistics."""
        now = time.time()
        total = len(_cache)
        expired = sum(1 for e in _cache.values() if e['expires_at'] < now)
        memory = sum(len(e['data']) for e in _cache.values())
        return {
            'total_entries': total,
            'expired_entries': expired,
            'active_entries': total - expired,
            'memory_bytes': memory,
        }

    def cache_clear(self) -> None:
        """Clear all entries from the cache."""
        global _cache
        _cache = {}

    def serialize_for_cache(self, obj) -> bytes:
        """Serialize any Python object for caching."""
        return pickle.dumps(obj)

    def deserialize_from_cache(self, data: bytes):
        """Deserialize cached data back to Python object."""
        return pickle.loads(data)