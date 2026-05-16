from mapper.model_manager import get_model
import numpy as np
import re
import difflib


class EmbeddingMatcher:

    def __init__(self):
        self.model = get_model()

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

        if self.model is not None:
            self.embeddings = self._normalize(
                self.model.encode(self.values)
            )
        else:
            self.embeddings = None

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

        if self.model is None or self.embeddings is None:
            return self._fallback_match(clean_q)

        q_emb = self.model.encode([clean_q])[0]
        q_emb = q_emb / (np.linalg.norm(q_emb) + 1e-9)

        scores = np.dot(self.embeddings, q_emb)

        best_idx = int(np.argmax(scores))
        best_score = scores[best_idx]

        # 🔥 threshold cao hơn
        if best_score < 0.65:
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
