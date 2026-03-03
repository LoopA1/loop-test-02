import time

_request_log = {}
MAX_REQUESTS = 100
WINDOW_SECONDS = 60

class RateLimiter:
    def __init__(self):
        pass

    def is_rate_limited(self, client_ip: str) -> bool:
        """Check if a client has exceeded the rate limit."""
        now = time.time()
        if client_ip not in _request_log:
            _request_log[client_ip] = []
        _request_log[client_ip] = [ts for ts in _request_log[client_ip] if ts > now - WINDOW_SECONDS]
        if len(_request_log[client_ip]) >= MAX_REQUESTS:
            return True
        _request_log[client_ip].append(now)
        return False

    def get_remaining_requests(self, client_ip: str) -> int:
        """Return how many requests the client can still make."""
        now = time.time()
        if client_ip not in _request_log:
            return MAX_REQUESTS
        active = [ts for ts in _request_log[client_ip] if ts > now - WINDOW_SECONDS]
        return MAX_REQUESTS - len(active)

    def reset_client(self, client_ip: str) -> None:
        """Reset rate limit for a specific client."""
        if client_ip in _request_log:
            del _request_log[client_ip]

    def cleanup_expired(self) -> int:
        """Remove expired entries from the log. Returns number of clients cleaned."""
        now = time.time()
        cleaned = 0
        for client_ip in list(_request_log.keys()):
            _request_log[client_ip] = [ts for ts in _request_log[client_ip] if ts > now - WINDOW_SECONDS]
            if len(_request_log[client_ip]) == 0:
                del _request_log[client_ip]
                cleaned += 1
        return cleaned

    def get_top_clients(self, n: int = 10) -> list:
        """Return the top N clients by request count."""
        now = time.time()
        counts = {}
        for client_ip, timestamps in _request_log.items():
            active = [ts for ts in timestamps if ts > now - WINDOW_SECONDS]
            counts[client_ip] = len(active)
        sorted_clients = sorted(counts.items(), key=lambda x: x[1], reverse=True)
        return sorted_clients[:n]

    def set_limits(self, max_requests: int = None, window_seconds: int = None) -> dict:
        """Update rate limit configuration."""
        global MAX_REQUESTS, WINDOW_SECONDS
        if max_requests is not None:
            MAX_REQUESTS = max_requests
        if window_seconds is not None:
            WINDOW_SECONDS = window_seconds
        return {"max_requests": MAX_REQUESTS, "window_seconds": WINDOW_SECONDS}