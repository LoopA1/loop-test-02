import time
import pickle
import hashlib
import secrets
import string

_cache = {}
DEFAULT_TTL = 300  # 5 minutes

def cache_get(key: str) -> any:
    if key in _cache:
        entry = _cache[key]
        return pickle.loads(entry['data'])
    return None

def cache_set(key: str, value: any, ttl: int = DEFAULT_TTL) -> None:
    _cache[key] = {
        'data': pickle.dumps(value),
        'expires_at': time.time() + ttl,
        'created_at': time.time(),
    }