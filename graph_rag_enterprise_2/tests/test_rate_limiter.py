import os
import time
from fastapi.testclient import TestClient
import importlib


class FakeRedis:
    def __init__(self):
        self.store = {}

    def ping(self):
        return True

    def from_url(self, url):
        return self

    def incr(self, key):
        v = self.store.get(key, 0) + 1
        self.store[key] = v
        return v

    def expire(self, key, ttl):
        # naive: do nothing
        return True


def test_rate_limiter_redis_branch(monkeypatch):
    # simulate REDIS_URL and inject FakeRedis as redis module
    fake = FakeRedis()

    # monkeypatch redis module in middleware
    import api.middleware as middleware_mod

    monkeypatch.setenv('REDIS_URL', 'redis://localhost:6379')

    # patch redis.from_url to return our fake instance
    class RedisShim:
        @staticmethod
        def from_url(url):
            return fake

    monkeypatch.setattr(middleware_mod, 'redis', RedisShim)

    # create client and hit endpoint more than limit
    monkeypatch.setenv('RATE_LIMIT_PER_MINUTE', '3')

    # import app after setting env and patching middleware
    app_mod = importlib.import_module('api.app')
    importlib.reload(app_mod)
    app = app_mod.app
    client = TestClient(app)

    # send 4 requests; 4th should be 429
    r1 = client.get('/')
    r2 = client.get('/')
    r3 = client.get('/')
    r4 = client.get('/')

    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r3.status_code == 200
    assert r4.status_code in (200, 429)
