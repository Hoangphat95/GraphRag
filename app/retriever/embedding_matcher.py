"""Embedding-based semantic matching using SentenceTransformer + optional FAISS."""
import numpy as np
import re
import os

from app.retriever.model_manager import get_model


class EmbeddingMatcher:
    def __init__(self):
        self.model = get_model()
        self.threshold = float(os.environ.get("EMBEDDING_MATCH_THRESHOLD", 0.65))

        self.property_map = {
            "toc_do_toi_da": "tốc độ tối đa",
            "tai_trong_lon_nhat": "tải trọng",
            "noi_ap_tieu_chuan": "áp suất",
            "duong_kinh_vanh": "đường kính vành",
            "duong_kinh_ngoai": "đường kính ngoài",
            "kieu_hoa": "hoa lốp",
            "gia_ban_co_vat": "giá bán",
            "brand": "thương hiệu",
        }
        self.keys = list(self.property_map.keys())
        self.values = list(self.property_map.values())

        base = os.path.dirname(__file__)
        # embeddings.npy lives in the old mapper folder
        emb_path = os.path.join(base, "..", "mapper", "embeddings.npy")
        self.emb_path = emb_path

        # FAISS support
        self.faiss_index = None
        self.faiss_meta = None
        faiss_index_path = os.environ.get("FAISS_INDEX_PATH") or os.path.join(os.getcwd(), "data", "faiss.index")
        faiss_meta_path = os.environ.get("FAISS_META_PATH") or os.path.join(os.getcwd(), "data", "faiss_meta.pkl")

        try:
            import faiss
            if os.path.exists(faiss_index_path):
                try:
                    self.faiss_index = faiss.read_index(faiss_index_path)
                    if os.path.exists(faiss_meta_path):
                        import pickle
                        with open(faiss_meta_path, "rb") as fh:
                            self.faiss_meta = pickle.load(fh)
                except Exception:
                    self.faiss_index = None
        except Exception:
            pass

        # Fallback numpy embeddings
        if self.faiss_index is None:
            if os.path.exists(emb_path):
                try:
                    self.embeddings = np.load(emb_path)
                except Exception:
                    self.embeddings = None
            elif self.model is not None:
                vecs = self.model.encode(self.values)
                self.embeddings = self._normalize(np.array(vecs))
                try:
                    np.save(emb_path, self.embeddings)
                except Exception:
                    pass
            else:
                self.embeddings = None
        else:
            self.embeddings = None

    def is_healthy(self):
        return self.model is not None and self.embeddings is not None

    def _normalize(self, v):
        return v / (np.linalg.norm(v, axis=1, keepdims=True) + 1e-9)

    def _clean_query(self, query):
        q = query.lower()
        q = re.sub(r"\d+(\.\d+)?[-/]\d+", "", q)
        for w in ["lốp", "bao nhiêu", "là gì", "cái", "nào"]:
            q = q.replace(w, "")
        return q.strip()

    def _fallback_match(self, clean_q):
        import difflib
        matches = difflib.get_close_matches(clean_q, self.values, n=1, cutoff=0.4)
        if matches:
            idx = self.values.index(matches[0])
            return self.keys[idx]
        return None

    def match(self, query: str):
        clean_q = self._clean_query(query)
        if not clean_q:
            return None

        # FAISS path
        if self.faiss_index is not None:
            try:
                q_emb = self.model.encode([clean_q])[0] if self.model else None
                if q_emb is None:
                    return self._fallback_match(clean_q)
                q_emb = q_emb / (np.linalg.norm(q_emb) + 1e-9)
                vec = np.array([q_emb], dtype="float32")
                distances, indices = self.faiss_index.search(vec, 1)
                best_score = float(distances[0][0])
                best_idx = int(indices[0][0])
                if best_score < self.threshold:
                    return None
                if self.faiss_meta and isinstance(self.faiss_meta, dict) and "keys" in self.faiss_meta:
                    klist = self.faiss_meta.get("keys")
                    if klist and len(klist) > best_idx:
                        return klist[best_idx]
                return self.keys[best_idx]
            except Exception:
                return self._fallback_match(clean_q)

        # Numpy path
        if self.model is None or self.embeddings is None:
            return self._fallback_match(clean_q)

        q_emb = self.model.encode([clean_q])[0]
        q_emb = q_emb / (np.linalg.norm(q_emb) + 1e-9)

        if self.embeddings.ndim == 2 and self.embeddings.shape[1] != q_emb.shape[0]:
            try:
                vecs = self.model.encode(self.values)
                self.embeddings = self._normalize(np.array(vecs))
                np.save(self.emb_path, self.embeddings)
            except Exception:
                pass

        scores = np.dot(self.embeddings, q_emb)
        best_idx = int(np.argmax(scores))
        best_score = scores[best_idx]
        if best_score < self.threshold:
            return None
        return self.keys[best_idx]
