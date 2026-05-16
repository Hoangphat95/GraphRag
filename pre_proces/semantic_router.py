import re
from typing import Dict, List


class SemanticRouter:

    def __init__(self):

        # intent keywords
        self.intent_keywords = {
            "TUBE_QUERY": ["ruột", "săm", "tube"],
            "BRAND_QUERY": ["hãng", "thương hiệu"],
            "COMPANY_QUERY": ["công ty", "sản xuất"],
            "PATTERN_QUERY": ["pattern", "hoa", "gai"],
            "CO_SAM_QUERY": ["có ruột", "dùng ruột", "có săm", "không săm", "ruột hay không"]
        }

        # property mapping
        self.property_map = {
            "tốc độ": "toc_do_toi_da",
            "tốc độ tối đa": "toc_do_toi_da",
            "chịu tải": "tai_trong_lon_nhat",
            "tải": "tai_trong_lon_nhat",
            "áp suất": "noi_ap_tieu_chuan",
            "vành": "duong_kinh_vanh",
            "rim": "duong_kinh_vanh",
            "pattern": "kieu_hoa"
        }

    # =========================
    # 1. INTENT DETECTION
    # =========================
    def detect_intent(self, query: str) -> str:
        q = query.lower()

        for intent, kws in self.intent_keywords.items():
            if any(k in q for k in kws):
                return intent

        return "PROPERTY_QUERY"

    # =========================
    # 2. SIZE EXTRACTION
    # =========================
    def extract_size(self, query: str):
        match = re.search(r"\d+\.\d+[-/]\d+|\d+/\d+[-/]\d+|\d+x\d+\.\d+", query)
        return match.group() if match else None

    # =========================
    # 3. PROPERTY EXTRACTION
    # =========================
    def extract_property(self, query: str):
        q = query.lower()

        for k, v in self.property_map.items():
            if k in q:
                return v

        return None

    # =========================
    # 4. MAIN ROUTER
    # =========================
    def route(self, query: str) -> Dict:

        intent = self.detect_intent(query)
        size = self.extract_size(query)
        prop = self.extract_property(query)

        # =========================
        # SPECIAL CASE: co_sam
        # =========================
        if intent == "CO_SAM_QUERY":

            return {
                "intent": "CO_SAM_QUERY",
                "size": size
            }

        # =========================
        # NORMAL PROPERTY QUERY
        # =========================
        return {
            "intent": intent,
            "size": size,
            "property": prop
        }