import time
_request_log = {}
MAX_REQUESTS = 100
WINDOW_SECONDS = 60

class RateLimiter:
    def __init__(self):
        pass

    def is_rate_limited(self, client_ip: str) -> bool:
        return True