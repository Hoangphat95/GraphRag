import re
import unicodedata
from mapper.value_store import ValueStore, normalize_text

def normalize_query(text: str):
    text = text.lower().strip()

    text = unicodedata.normalize('NFD', text)
    text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')

    return text


# =========================
# EXACT MATCH
# =========================
def find_exact_match(candidate: str, data):

    candidate_norm = normalize_text(candidate)

    for item in data:
        if candidate_norm == item["value"]:
            return item

    return None


# =========================
# RULE-BASED COLUMN DETECT
# =========================
def find_best_column(query_part: str, columns):

    q = normalize_query(query_part)
    q_tokens = q.split()

    rule_map = [
        ("toc do toi da", "toc_do_toi_da", False),
        ("toc do", "toc_do_toi_da", False),

        ("chiu tai", "tai_trong_lon_nhat", False),
        ("tai", "tai_trong_lon_nhat", True),

        ("ap suat", "noi_ap_tieu_chuan", False),

        ("duong kinh vanh", "duong_kinh_vanh", False),
        ("vanh", "duong_kinh_vanh", True),

        ("duong kinh ngoai", "duong_kinh_ngoai", False),

        ("pattern", "kieu_hoa", True),
        ("hoa", "kieu_hoa", True),

        ("gia ban", "gia_ban_co_vat", False),
        ("gia", "gia_ban_co_vat", True),
        ("price", "gia_ban_co_vat", True),
        ("giam", "gia_ban_co_vat", True),
    ]

    for k, v, token_only in rule_map:
        if token_only:
            if k in q_tokens:
                if k == "tai" and "hien tai" in q:
                    continue
                for col in columns:
                    if col["column"] == v:
                        return col, 1.0
        else:
            if k in q:
                for col in columns:
                    if col["column"] == v:
                        return col, 1.0

    return None, 0.0


# =========================
# CLEAN TEXT
# =========================
def clean_text(text: str):

    stopwords = [
        "lop", "lốp", "tire",
        "cua", "của",
        "la", "là",
        "bao nhieu", "bao nhiêu",
        "la gi", "là gì",
        "co", "có",
        "thuoc", "thuộc",
        "cho", "voi", "với",
        "moi", "mọi",
        "ban", "bạn"
    ]

    remove_phrases = [
        "mau nay", "mẫu này",
        "cai nay", "cái này",
        "hien tai", "hiện tại"
    ]

    text_norm = normalize_query(text)

    for phrase in remove_phrases:
        text_norm = text_norm.replace(phrase, " ")

    tokens = re.split(r"\W+", text_norm)
    tokens = [t for t in tokens if t and t not in stopwords]

    return " ".join(tokens).strip()


# =========================
# EXTRACT
# =========================
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


# =========================
# MAIN
# =========================
class ValueMapper:

    def __init__(self):
        self.store = ValueStore()
        self.store.build()

    def map_query(self, query: str):

        candidates = extract_candidates(query)
        results = []

        for c in candidates:

            # EXACT
            exact = find_exact_match(c, self.store.data)

            if exact:
                results.append({
                    "query_part": c,
                    "value": exact["raw_value"],
                    "column": "size",
                    "score": 1.0,
                    "type": "exact"
                })
                continue

            # SIZE FALLBACK
            if re.match(r"\d", c):
                results.append({
                    "query_part": c,
                    "value": c.strip(),
                    "column": "size",
                    "score": 0.6,
                    "type": "size_fallback"
                })
                continue

            # COLUMN
            best_col, score = find_best_column(c, self.store.columns)

            if best_col:
                results.append({
                    "query_part": c,
                    "column": best_col["column"],
                    "score": score,
                    "type": "column_detect"
                })

        return results