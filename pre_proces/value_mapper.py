# app/value_mapper.py

import numpy as np
import re
from embeddings import embed_text
from value_store import ValueStore, normalize_text


def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


def find_exact_match(candidate: str, data):
    candidate_norm = normalize_text(candidate)

    for item in data:
        if candidate_norm == item["value"]:
            return item
    return None


def find_best_column(query_part: str, columns):

    # 🔥 RULE BASED
    rule_map = {
        "speed": "chi_so_tai_toc_do",
        "tốc độ": "chi_so_tai_toc_do",

        "load": "chi_so_tai_toc_do",
        "tải": "chi_so_tai_toc_do",

        "pressure": "noi_ap_tieu_chuan",
        "áp suất": "noi_ap_tieu_chuan",

        "rim": "duong_kinh_vanh",
        "vành": "duong_kinh_vanh",

        "pattern": "kieu_hoa",
        "hoa": "kieu_hoa"
    }

    for k, v in rule_map.items():
        if k in query_part:
            for col in columns:
                if col["column"] == v:
                    return col, 1.0

    # 🔥 EMBEDDING FALLBACK
    emb = embed_text(query_part)

    best = None
    best_score = -1

    for col in columns:
        sim = cosine_similarity(emb, col["embedding"])

        if sim > best_score:
            best_score = sim
            best = col

    if best_score < 0.6:
        return None, best_score

    return best, best_score


def clean_text(text: str):
    stopwords = [
        "lốp", "tire", "của", "là", "bao nhiêu",
        "là gì", "có", "thuộc", "gì", "là bao nhiêu",
        "cho", "với"
    ]

    for w in stopwords:
        text = text.replace(w, "")

    return text.strip()


def extract_candidates(query: str):
    query = query.lower()

    size_pattern = r"\b\d+(?:\.\d+)?(?:[xX/\\-]\d+(?:\.\d+)?)+\b"
    sizes = re.findall(size_pattern, query)

    text_part = re.sub(size_pattern, "", query)
    text_part = clean_text(text_part)

    candidates = sizes

    if text_part:
        candidates.append(text_part)

    return candidates


class ValueMapper:
    def __init__(self):
        self.store = ValueStore()
        self.store.build()

    def map_query(self, query: str):
        candidates = extract_candidates(query)

        results = []

        for c in candidates:

            # 🔥 1. EXACT MATCH
            exact = find_exact_match(c, self.store.data)

            if exact:
                results.append({
                    "query_part": c,
                    "value": exact["raw_value"],  # 🔥 trả raw
                    "column": exact["column"],
                    "score": 1.0,
                    "type": "exact"
                })
                continue
            
            if re.match(r"\d", c):
                results.append({
                    "query_part": c,
                    "value": c,
                    "column": "Giá trị quy cách",
                    "score": 0.5,
                    "type": "size_fallback"
                })
                continue

            # 🔥 2. COLUMN DETECT
            best_col, col_score = find_best_column(c, self.store.columns)

            if best_col:
                results.append({
                    "query_part": c,
                    "column": self.normalize_column(best_col["column"]),
                    "score": col_score,
                    "type": "column_detect"
                })

        return results
    
    def normalize_column(self, col):
        import unicodedata

        col = col.lower()

        # remove accents chuẩn
        col = unicodedata.normalize('NFD', col)
        col = ''.join(c for c in col if unicodedata.category(c) != 'Mn')

        # fix special cases
        col = col.replace("&", "and")
        col = col.replace("đ", "d")
        col = col.replace(" ", "_")

        return col