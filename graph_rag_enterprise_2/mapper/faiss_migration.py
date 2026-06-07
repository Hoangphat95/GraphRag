"""FAISS migration helper: build a FAISS index from existing value store embeddings.

This script is optional and safe to include even if `faiss` is not installed.
Run as: `python mapper/faiss_migration.py` to create `data/faiss.index` and `data/faiss_meta.pkl`.
"""
import os
import pickle
import logging
import argparse
import numpy as np

logger = logging.getLogger(__name__)


def migrate(index_path='data/faiss.index', meta_path='data/faiss_meta.pkl', force=False, save_meta=True):
    try:
        import faiss
    except Exception:
        print('faiss not installed; install faiss-cpu or faiss-gpu to run migration')
        return False

    # ensure data dir
    d = os.path.dirname(index_path) or 'data'
    os.makedirs(d, exist_ok=True)

    # try to load existing embeddings from embeddings.npy (used by EmbeddingMatcher)
    base = os.path.dirname(__file__)
    emb_path = os.path.join(base, 'embeddings.npy')
    vals_path = os.path.join(base, 'values.pkl')

    if not os.path.exists(emb_path):
        print('No embeddings.npy found; run your embedding pipeline first')
        return False

    vecs = np.load(emb_path)
    # normalize vectors for inner-product/cosine
    norms = np.linalg.norm(vecs, axis=1, keepdims=True) + 1e-9
    vecs = vecs / norms

    dim = vecs.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(vecs.astype('float32'))

    # save index (skip if exists unless force)
    if os.path.exists(index_path) and not force:
        print(f'Index already exists at {index_path}; use --force to overwrite')
    else:
        faiss.write_index(index, index_path)

    if not save_meta:
        print(f'Wrote FAISS index {index_path} ({index.ntotal} vectors, dim={dim})')
        return True

    # save metadata (keys/values mapping) if available from mapper.embedding_matcher
    keys = []
    values = []
    try:
        # attempt to import the embedding matcher to get its property map order
        from mapper.embedding_matcher import EmbeddingMatcher as _EM
        em = _EM()
        keys = em.keys
        values = em.values
    except Exception:
        # fallback: try to load values.pkl if present
        if os.path.exists(vals_path):
            try:
                with open(vals_path, 'rb') as fh:
                    meta = pickle.load(fh)
                    # meta may contain keys/values
                    keys = meta.get('keys') if isinstance(meta, dict) else []
                    values = meta.get('values') if isinstance(meta, dict) else []
            except Exception:
                logger.exception('failed to load values mapping')

    meta_out = {'dimension': dim, 'count': index.ntotal, 'keys': keys, 'values': values}
    with open(meta_path, 'wb') as fh:
        pickle.dump(meta_out, fh)

    print(f'Wrote FAISS index {index_path} ({index.ntotal} vectors, dim={dim})')
    print(f'Wrote meta {meta_path}')
    return True


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Build FAISS index from embeddings.npy')
    parser.add_argument('--index-path', default=os.environ.get('FAISS_INDEX_PATH', 'data/faiss.index'))
    parser.add_argument('--meta-path', default=os.environ.get('FAISS_META_PATH', 'data/faiss_meta.pkl'))
    parser.add_argument('--force', action='store_true')
    parser.add_argument('--no-meta', action='store_true', help='Do not write meta file')

    args = parser.parse_args()
    migrate(index_path=args.index_path, meta_path=args.meta_path, force=args.force, save_meta=not args.no_meta)
