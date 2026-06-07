import types
import sys
import os

from retriever.hybrid_retriever import HybridRetriever


def test_hybrid_reports_faiss(monkeypatch):
    # monkeypatch EmbeddingMatcher used inside HybridRetriever
    class FakeEmbed:
        def __init__(self):
            self.faiss_index = object()

        def match(self, q):
            return 'toc_do_toi_da'

    monkeypatch.setattr('retriever.hybrid_retriever.EmbeddingMatcher', lambda: FakeEmbed())

    r = HybridRetriever()
    out = r.retrieve('tốc độ tối đa của lốp')
    assert out.get('uses_faiss') is True
    assert out.get('semantic') == 'toc_do_toi_da'
