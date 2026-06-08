import os
import time
import json
try:
    import redis
except Exception:
    redis = None

from fastapi import Request
from starlette.responses import Response


class APIKeyAuthMiddleware:
    def __init__(self, app, header_name: str = "x-api-key"):
        self.app = app
        self.header_name = header_name
        self.api_key = os.environ.get("API_KEY")

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        if self.api_key:
            req = Request(scope, receive=receive)
            key = req.headers.get(self.header_name)
            if key != self.api_key:
                res = Response(status_code=401, content=json.dumps({"error": "Unauthorized"}), media_type="application/json")
                await res(scope, receive, send)
                return

        await self.app(scope, receive, send)


class SimpleRateLimitMiddleware:
    """Simple rate limiter using Redis if available, else in-memory counters.

    Config via env:
      RATE_LIMIT_PER_MINUTE (default 60)
    """

    def __init__(self, app):
        self.app = app
        self.limit = int(os.environ.get("RATE_LIMIT_PER_MINUTE", 60))
        self.backend = None
        if redis and os.environ.get("REDIS_URL"):
            try:
                self._redis = redis.from_url(os.environ.get("REDIS_URL"))
                self._redis.ping()
                self.backend = "redis"
            except Exception:
                self._redis = None
                self.backend = "memory"
        else:
            self._redis = None
            self.backend = "memory"

        self.counters = {}

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        req = Request(scope, receive=receive)
        client = req.client.host if req.client else "unknown"

        allowed = True
        if self.backend == "redis" and self._redis:
            key = f"rate:{client}:{int(time.time()//60)}"
            try:
                val = self._redis.incr(key)
                if val == 1:
                    self._redis.expire(key, 65)
                if val > self.limit:
                    allowed = False
            except Exception:
                allowed = True
        else:
            # memory counter per minute
            minute = int(time.time()//60)
            entry = self.counters.get(client)
            if not entry or entry[0] != minute:
                self.counters[client] = [minute, 1]
            else:
                entry[1] += 1
                if entry[1] > self.limit:
                    allowed = False

        if not allowed:
            res = Response(status_code=429, content=json.dumps({"error": "Too Many Requests"}), media_type="application/json")
            await res(scope, receive, send)
            return

        await self.app(scope, receive, send)
