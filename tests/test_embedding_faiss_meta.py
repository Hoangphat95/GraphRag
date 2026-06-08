import os
import sys
import pickle
import types
import numpy as np

from app.mapper.embedding_matcher import EmbeddingMatcher


def test_faiss_meta_mapping(monkeypatch, tmp_path):
    # prepare fake faiss and meta mapping where index 0 maps to 'brand'
    fake = types.ModuleType('faiss')

    class FakeIndex:
        def search(self, x, k):
            return np.array([[0.95]], dtype='float32'), np.array([[0]], dtype='int64')

    def read_index(p):
        return FakeIndex()

    fake.read_index = read_index
    monkeypatch.setitem(sys.modules, 'faiss', fake)

    # write meta mapping file
    meta = {'dimension': 8, 'count': 1, 'keys': ['brand'], 'values': ['thương hiệu']}
    meta_path = tmp_path / 'faiss_meta.pkl'
    with open(meta_path, 'wb') as fh:
        pickle.dump(meta, fh)

    # create a fake index file and point FAISS_INDEX_PATH to it so EmbeddingMatcher reads index
    fake_index = tmp_path / 'faiss.index'
    fake_index.write_text('fake')
    monkeypatch.setenv('FAISS_INDEX_PATH', str(fake_index))
    monkeypatch.setenv('FAISS_META_PATH', str(meta_path))

    # provide a minimal model that can encode the query
    class FakeModel:
        def encode(self, texts):
            # return a fixed vector
            import numpy as _np
            v = _np.ones((len(texts), 8), dtype='float32')
            return v

    monkeypatch.setattr('mapper.embedding_matcher.get_model', lambda: FakeModel())

    matcher = EmbeddingMatcher()
    res = matcher.match('hãng')
    assert res == 'brand'
