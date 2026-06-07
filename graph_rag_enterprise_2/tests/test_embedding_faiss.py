import os
import sys
import types
import numpy as np

from mapper.embedding_matcher import EmbeddingMatcher


def test_faiss_integration(monkeypatch, tmp_path):
    # prepare mapper embeddings.npy with same ordering as property_map
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    mapper_dir = os.path.join(repo_root, 'mapper')
    os.makedirs(mapper_dir, exist_ok=True)

    # create deterministic embeddings for the 9 property values
    n = 9
    dim = 8
    vecs = np.random.RandomState(1).randn(n, dim).astype('float32')
    norms = np.linalg.norm(vecs, axis=1, keepdims=True) + 1e-9
    vecs = vecs / norms
    emb_path = os.path.join(mapper_dir, 'embeddings.npy')
    np.save(emb_path, vecs)

    # create fake faiss module that returns index 0 with high score
    fake = types.ModuleType('faiss')

    class FakeIndex:
        def __init__(self, ntotal):
            self.ntotal = ntotal

        def search(self, x, k):
            # return (distances, indices)
            return np.array([[0.95]], dtype='float32'), np.array([[0]], dtype='int64')

    def read_index(path):
        return FakeIndex(ntotal=n)

    fake.read_index = read_index
    monkeypatch.setitem(sys.modules, 'faiss', fake)

    # create a fake index file path and set env var
    fake_index = tmp_path / 'faiss.index'
    fake_index.write_text('fake')
    monkeypatch.setenv('FAISS_INDEX_PATH', str(fake_index))

    matcher = EmbeddingMatcher()
    res = matcher.match('tốc độ tối đa')
    assert res == 'toc_do_toi_da'
