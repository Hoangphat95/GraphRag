from fastapi.testclient import TestClient
import types
import sys

import api.app as app_module
from api.app import app


def test_health_without_faiss(monkeypatch):
    # ensure retriever.embed has no faiss_index
    chatbot = getattr(app_module, 'chatbot', None)
    if chatbot and getattr(chatbot, 'retriever', None):
        setattr(chatbot.retriever.embed, 'faiss_index', None)

    client = TestClient(app)
    resp = client.get('/health')
    assert resp.status_code == 200
    data = resp.json()
    assert data['status'] == 'ok'
    assert data['faiss'] is not None
    assert data['faiss']['available'] in (False,)


def test_health_with_faiss(monkeypatch):
    chatbot = getattr(app_module, 'chatbot', None)
    # attach a fake faiss index with ntotal
    class FakeIndex:
        ntotal = 42

    if chatbot and getattr(chatbot, 'retriever', None):
        setattr(chatbot.retriever.embed, 'faiss_index', FakeIndex())

    client = TestClient(app)
    resp = client.get('/health')
    assert resp.status_code == 200
    data = resp.json()
    assert data['faiss']['available'] is True
    assert data['faiss']['index_count'] == 42
