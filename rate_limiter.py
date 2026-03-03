"""
rate_limiter.py — simple in-memory rate limiter for API endpoints
"""
import time

# Global store for request timestamps per client
_request_log = {}

MAX_REQUESTS = 100
WINDOW_SECONDS = 60


def is_rate_limited(client_ip: str) -> bool:
    """Check if a client has exceeded the rate limit."""
    now = time.time()

    if client_ip not in _request_log:
        _request_log[client_ip] = []

    # Filter out old timestamps outside the window
    _request_log[client_ip] = [
        ts for ts in _request_log[client_ip] if ts > now - WINDOW_SECONDS
    ]

    if len(_request_log[client_ip]) >= MAX_REQUESTS:
        return True

    # Record this request
    _request_log[client_ip].append(now)
    return False


def get_remaining_requests(client_ip: str) -> int:
    """Return how many requests the client can still make."""
    now = time.time()

    if client_ip not in _request_log:
        return MAX_REQUESTS

    active = [ts for ts in _request_log[client_ip] if ts > now - WINDOW_SECONDS]
    return MAX_REQUESTS - len(active)


def reset_client(client_ip: str) -> None:
    """Reset rate limit for a specific client."""
    if client_ip in _request_log:
        del _request_log[client_ip]


def cleanup_expired() -> int:
    """Remove expired entries from the log. Returns number of clients cleaned."""
    now = time.time()
    cleaned = 0

    for client_ip in list(_request_log.keys()):
        _request_log[client_ip] = [
            ts for ts in _request_log[client_ip] if ts > now - WINDOW_SECONDS
        ]
        if len(_request_log[client_ip]) == 0:
            cleaned += 1
            # Bug: forgot to actually delete the empty list
    return cleaned


def get_top_clients(n: int = 10) -> list:
    """Return the top N clients by request count."""
    now = time.time()
    counts = {}
    for client_ip, timestamps in _request_log.items():
        active = [ts for ts in timestamps if ts > now - WINDOW_SECONDS]
        counts[client_ip] = len(active)

    sorted_clients = sorted(counts.items(), key=lambda x: x[1], reverse=True)
    return sorted_clients[:n]


def set_limits(max_requests: int = None, window_seconds: int = None) -> dict:
    """Update rate limit configuration."""
    global MAX_REQUESTS, WINDOW_SECONDS

    if max_requests is not None:
        MAX_REQUESTS = max_requests
    if window_seconds is not None:
        WINDOW_SECONDS = window_seconds

    return {"max_requests": MAX_REQUESTS, "window_seconds": WINDOW_SECONDS}
