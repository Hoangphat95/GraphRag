from mapper.model_manager import get_model
import numpy as np
import re
import difflib
import os
import sys


class EmbeddingMatcher:

    def __init__(self):
        self.model = get_model()

        # threshold configurable
        try:
            self.threshold = float(os.environ.get("EMBEDDING_MATCH_THRESHOLD", 0.65))
        except Exception:
            self.threshold = 0.65

        # =========================
        # PROPERTY MAP (EXPANDED)
        # =========================
        self.property_map = {
            "toc_do_toi_da": "tốc độ tối đa",
            "tai_trong_lon_nhat": "tải trọng",
            "noi_ap_tieu_chuan": "áp suất",
            "duong_kinh_vanh": "đường kính vành",
            "duong_kinh_ngoai": "đường kính ngoài",
            "kieu_hoa": "hoa lốp",
            "gia_ban_co_vat": "giá bán",
            "brand": "thương hiệu"
        }

        self.keys = list(self.property_map.keys())
        self.values = list(self.property_map.values())

        base = os.path.dirname(__file__)
        emb_path = os.path.join(base, "embeddings.npy")
        self.emb_path = emb_path

        # Try to load FAISS index first if available
        self.faiss_index = None
        self.faiss_meta = None
        faiss_index_path = os.environ.get("FAISS_INDEX_PATH") or os.path.join(os.getcwd(), "data", "faiss.index")
        faiss_meta_path = os.environ.get("FAISS_META_PATH") or os.path.join(os.getcwd(), "data", "faiss_meta.pkl")

        try:
            import faiss  # type: ignore
            if os.path.exists(faiss_index_path):
                try:
                    self.faiss_index = faiss.read_index(faiss_index_path)
                    # load optional meta
                    if os.path.exists(faiss_meta_path):
                        try:
                            import pickle
                            with open(faiss_meta_path, 'rb') as fh:
                                self.faiss_meta = pickle.load(fh)
                        except Exception:
                            self.faiss_meta = None
                except Exception:
                    # If faiss exists but index can't be read, fallback
                    self.faiss_index = None
        except Exception:
            # faiss not available
            pass

        # If FAISS not used, fall back to numpy embeddings
        if self.faiss_index is None:
            if os.path.exists(emb_path):
                try:
                    loaded = np.load(emb_path)
                    # If a model is available, verify dimensionality matches;
                    # if not, recompute embeddings with current model and overwrite.
                    if self.model is not None:
                        try:
                            vecs = self.model.encode(self.values)
                            vecs = np.array(vecs)
                            if loaded.ndim == 2 and vecs.ndim == 2 and loaded.shape[1] != vecs.shape[1]:
                                # dimension mismatch -> recompute and save
                                self.embeddings = self._normalize(vecs)
                                try:
                                    np.save(emb_path, self.embeddings)
                                except Exception:
                                    pass
                            else:
                                self.embeddings = loaded
                        except Exception:
                            # If model.encode fails for any reason, keep loaded embeddings
                            self.embeddings = loaded
                    else:
                        self.embeddings = loaded
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
            # ensure embeddings attribute exists for health checks
            self.embeddings = None

    def is_healthy(self):
        return self.model is not None and self.embeddings is not None

    # =========================
    # NORMALIZE VECTOR
    # =========================
    def _normalize(self, v):
        return v / (np.linalg.norm(v, axis=1, keepdims=True) + 1e-9)

    # =========================
    # CLEAN QUERY (🔥 QUAN TRỌNG)
    # =========================
    def _clean_query(self, query):
        q = query.lower()

        # remove size pattern
        q = re.sub(r'\d+(\.\d+)?[-/]\d+', '', q)

        # remove stop words đơn giản
        remove_words = ["lốp", "bao nhiêu", "là gì", "cái", "nào"]
        for w in remove_words:
            q = q.replace(w, "")

        return q.strip()

    # =========================
    # MATCH
    # =========================
    def match(self, query: str):

        clean_q = self._clean_query(query)

        if not clean_q:
            return None

        # If FAISS index present, use it (inner-product index expected)
        if self.faiss_index is not None:
            try:
                q_emb = None
                if self.model is not None:
                    q_emb = self.model.encode([clean_q])[0]
                else:
                    # fallback: simple text-based match
                    return self._fallback_match(clean_q)

                q_emb = q_emb / (np.linalg.norm(q_emb) + 1e-9)
                import numpy as _np
                vec = _np.array([q_emb], dtype='float32')
                distances, indices = self.faiss_index.search(vec, 1)
                best_score = float(distances[0][0])
                best_idx = int(indices[0][0])
                if best_score < self.threshold:
                    return None
                # If meta mapping present, try to resolve; else assume same ordering as self.values
                try:
                    if self.faiss_meta and isinstance(self.faiss_meta, dict) and 'keys' in self.faiss_meta:
                        klist = self.faiss_meta.get('keys')
                        if klist and len(klist) > best_idx:
                            return klist[best_idx]
                except Exception:
                    pass
                return self.keys[best_idx]
            except Exception:
                return self._fallback_match(clean_q)

        if self.model is None or self.embeddings is None:
            return self._fallback_match(clean_q)

        q_emb = self.model.encode([clean_q])[0]
        q_emb = q_emb / (np.linalg.norm(q_emb) + 1e-9)

        # If stored embeddings have different dimensionality than model output,
        # try to recompute embeddings with the current model and overwrite file.
        try:
            if self.embeddings is not None and hasattr(self.embeddings, 'ndim') and self.embeddings.ndim == 2:
                if self.embeddings.shape[1] != q_emb.shape[0]:
                    try:
                        vecs = self.model.encode(self.values)
                        self.embeddings = self._normalize(np.array(vecs))
                        try:
                            np.save(self.emb_path, self.embeddings)
                        except Exception:
                            pass
                    except Exception:
                        # if recompute fails, continue and let dot raise a clear error
                        pass
        except Exception:
            pass

        scores = np.dot(self.embeddings, q_emb)

        best_idx = int(np.argmax(scores))
        best_score = scores[best_idx]

        # threshold configurable
        if best_score < self.threshold:
            return None

        return self.keys[best_idx]


    def _fallback_match(self, query: str):
        text = query.lower()
        for key, value in self.property_map.items():
            if value in text:
                return key

        words = set(re.findall(r"\w+", text))
        best_score = 0.0
        best_key = None

        for key, value in self.property_map.items():
            tokens = set(re.findall(r"\w+", value.lower()))
            overlap = len(words & tokens)
            score = overlap / max(len(tokens), 1)
            if score > best_score:
                best_score = score
                best_key = key

        if best_score >= 0.4:
            return best_key

        close_matches = difflib.get_close_matches(text, self.values, n=1, cutoff=0.5)
        if close_matches:
            match_value = close_matches[0]
            for key, value in self.property_map.items():
                if value == match_value:
                    return key

        return None
