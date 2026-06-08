from fastapi.testclient import TestClient
import os


def test_query_endpoint_ok(monkeypatch):
    monkeypatch.setenv('RATE_LIMIT_PER_MINUTE', '1000')
    import importlib
    app_mod = importlib.import_module('api.app')
    importlib.reload(app_mod)
    client = TestClient(app_mod.app)
    r = client.get('/query', params={'q': 'test'})
    assert r.status_code == 200


def test_reset_endpoint_ok(monkeypatch):
    monkeypatch.setenv('RATE_LIMIT_PER_MINUTE', '1000')
    import importlib
    app_mod = importlib.import_module('api.app')
    importlib.reload(app_mod)
    client = TestClient(app_mod.app)
    r = client.post('/reset')
    assert r.status_code == 200
