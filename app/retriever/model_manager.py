"""Embedding model manager — lazily loads SentenceTransformer."""
try:
    from sentence_transformers import SentenceTransformer
except Exception as e:
    SentenceTransformer = None
    MODEL_IMPORT_ERROR = e

_model = None


def get_model():
    global _model
    if _model is None:
        if SentenceTransformer is None:
            print(f"[WARN] sentence_transformers unavailable: {MODEL_IMPORT_ERROR}")
            return None
        print("[LOAD] Loading embedding model...")
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model
