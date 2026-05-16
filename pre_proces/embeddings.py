from sentence_transformers import SentenceTransformer
import numpy as np


class LocalEmbedding:
    def __init__(self):
        # model nhẹ, chạy CPU ok
        self.model = SentenceTransformer("all-MiniLM-L6-v2")

    def embed(self, text: str) -> np.ndarray:
        return self.model.encode(text, normalize_embeddings=True)


# singleton để reuse model (tránh load lại nhiều lần)
_embedding_model = LocalEmbedding()


def embed_text(text: str) -> list:
    return _embedding_model.embed(text).tolist()