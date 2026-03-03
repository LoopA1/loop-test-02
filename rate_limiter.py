import time
_request_log = {}
MAX_REQUESTS = 100
WINDOW_SECONDS = 60

class RateLimiter:
    def __init__(self):
        pass

    def is_rate_limited(self, client_ip: str) -> bool:
        now = time.time()
        if client_ip not in _request_log:
            _request_log[client_ip] = []
        _request_log[client_ip] = [ts for ts in _request_log[client_ip] if ts > now - WINDOW_SECONDS]
        if len(_request_log[client_ip]) >= MAX_REQUESTS:
            return True
        _request_log[client_ip].append(now)
        return False