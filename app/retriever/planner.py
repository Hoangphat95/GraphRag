"""Query planner — rule-based, with optional ML intent classification fallback."""
import os

from app.intent_classifier import IntentClassifier


class QueryPlanner:
    def __init__(self):
        model_path = os.path.join(os.path.dirname(__file__), "..", "models", "intent_classifier")
        if os.path.exists(model_path):
            try:
                self.classifier = IntentClassifier(model_path)
                self.use_ml = True
                print("[OK] Intent Classifier loaded - using ML for intent detection")
            except Exception as e:
                print(f"[WARN] Failed to load Intent Classifier: {e}")
                self.classifier = None
                self.use_ml = False
        else:
            self.classifier = None
            self.use_ml = False
            print("[INFO] Intent Classifier not found - using rule-based planning")

    def plan(self, query, mapped):
        q = query.lower()
        sizes = [r["value"] for r in mapped if r.get("column") == "size"]

        rule_plan = self._rule_based_plan(q, sizes, mapped)
        if rule_plan["type"] != "NO_MATCH":
            return rule_plan

        if self.use_ml:
            ml_result = self.classifier.predict(query)
            intent = ml_result["intent"]
            confidence = ml_result["confidence"]
            print(f"[ML] Intent: {intent} (confidence: {confidence:.2f})")
            if confidence > 0.7:
                return self._ml_to_plan(intent, sizes, mapped)

        return rule_plan

    def _rule_based_plan(self, q: str, sizes: list, mapped: list) -> dict:
        print("[PLAN] Using rule-based planning")
        columns = [r.get("column") for r in mapped]

        if not sizes and any(phrase in q for phrase in ["mẫu này", "mau nay", "cái này", "cai nay"]):
            return {"type": "NO_MATCH", "reason": "Referent missing size or model"}

        # ── LOAD signals ─────────────────────────────────────────────────
        if "tai_trong_lon_nhat" in columns:
            if sizes:
                if not any(phrase in q for phrase in ["cao nhất", "cao nhat", "tốt nhất", "max", "lớn nhất", "nhiều nhất"]):
                    return {"type": "LOAD", "sizes": sizes}
                return {"type": "MAX_LOAD", "sizes": sizes}
            if any(phrase in q for phrase in ["chịu tải", "chiu tai", "tải nặng", "tai nang", "chở hàng", "cho hang", ">400", "400kg", "400 kg"]):
                return {"type": "MAX_LOAD", "sizes": sizes}
            if any(phrase in q for phrase in ["cao nhất", "cao nhat", "tốt nhất", "max", "lớn nhất", "nhiều nhất"]):
                return {"type": "MAX_LOAD", "sizes": sizes}
            return {"type": "ATTRIBUTE_SEARCH", "attribute": "high_load", "sizes": sizes, "query": q}

        # ── SPEED signals ────────────────────────────────────────────────
        if "toc_do_toi_da" in columns:
            if sizes:
                if not any(phrase in q for phrase in ["cao nhất", "cao nhat", "tốt nhất", "max", "lớn nhất", "nhiều nhất"]):
                    return {"type": "SPEED", "sizes": sizes}
                return {"type": "MAX_SPEED", "sizes": sizes}
            if any(phrase in q for phrase in ["cao nhất", "cao nhat", "tốt nhất", "max", "lớn nhất", "nhiều nhất"]):
                return {"type": "MAX_SPEED", "sizes": sizes}
            return {"type": "NO_MATCH", "reason": "Need a specific size or a stronger speed signal"}

        # ── PRICE signals ────────────────────────────────────────────────
        if "gia_ban_co_vat" in columns:
            if sizes and "cao nhất" not in q:
                return {"type": "PRICE", "sizes": sizes}
            if any(phrase in q for phrase in ["giam gia", "giảm giá", "khuyen mai", "khuyến mại", "loc", "lọc", "tang dan", "tăng dần", "sap xep", "sắp xếp", "hang x", "hãng x"]):
                return {"type": "ATTRIBUTE_SEARCH", "attribute": "discount", "sizes": sizes, "query": q}
            if any(phrase in q for phrase in ["cao nhất", "cao nhat", "tốt nhất", "max", "lớn nhất", "nhiều nhất"]):
                return {"type": "MAX_PRICE", "sizes": sizes}
            return {"type": "ATTRIBUTE_SEARCH", "attribute": "price", "sizes": sizes, "query": q}

        # ── direct keyword signals ───────────────────────────────────────
        if ("cao nhất" in q and "tải" in q) or "chịu tải" in q:
            return {"type": "MAX_LOAD", "sizes": sizes}
        if "giá" in q and sizes and "cao nhất" not in q:
            return {"type": "PRICE", "sizes": sizes}
        if "công ty" in q:
            return {"type": "MULTI_HOP", "path": ["Tire", "Company"], "sizes": sizes}
        if "tiêu chuẩn" in q:
            return {"type": "MULTI_HOP", "path": ["Tire", "QualityStandard"], "sizes": sizes}
        if "van" in q:
            return {"type": "MULTI_HOP", "path": ["Tire", "Tube", "Van"], "sizes": sizes}
        if "so sánh" in q:
            if sizes:
                return {"type": "COMPARE", "sizes": sizes}
            return {"type": "NO_MATCH", "reason": "Need specific tires or sizes to compare"}
        if "giá" in q and "cao nhất" in q:
            return {"type": "MAX_PRICE", "sizes": sizes}
        if sizes:
            return {"type": "SINGLE", "sizes": sizes}

        # ── attribute map ────────────────────────────────────────────────
        attr_map = [
            ("drainage", ["thoat nuoc", "thoát nước", "mua", "mưa"]),
            ("noise", ["it on", "ít ồn", "ồn", "on"]),
            ("durability", ["do ben", "độ bền", "ben", "bền"]),
            ("warranty", ["bao hanh", "bảo hành"]),
            ("tube", ["sam", "săm", "tube"]),
            ("price", ["gia", "giá", "gia ban"]),
            ("road_trip", ["duong truong", "đường trường", "chạy đường trường", "duong dai"]),
            ("high_load", [">400", "400kg", "400 kg", "chiu tai >400", "chịu tải >400"]),
            ("service", ["dat lich", "đặt lịch", "phi lap", "phí lắp", "lắp đặt"]),
            ("discount", ["giam gia", "khuyen mai", "giảm giá"]),
            ("compatibility", ["tuong thich", "tương thích", "vành", "mâm"]),
        ]
        for attr_key, keywords in attr_map:
            for kw in keywords:
                if kw in q:
                    return {"type": "ATTRIBUTE_SEARCH", "attribute": attr_key, "sizes": sizes, "query": q}

        return {"type": "NO_MATCH", "reason": "No signal detected"}

    def _ml_to_plan(self, intent: str, sizes: list, mapped: list) -> dict:
        if intent == "SINGLE":
            return {"type": "SINGLE", "sizes": sizes}
        if intent == "COMPARE":
            return {"type": "COMPARE", "sizes": sizes}
        if intent == "SPEED":
            return {"type": "SPEED", "sizes": sizes}
        if intent == "LOAD":
            return {"type": "LOAD", "sizes": sizes}
        if intent == "PRICE":
            return {"type": "PRICE", "sizes": sizes}
        if intent == "PRESSURE":
            return {"type": "PRESSURE", "sizes": sizes}
        if intent == "BRAND":
            return {"type": "MULTI_HOP", "path": ["Tire", "Brand"], "sizes": sizes}
        return {"type": "NO_MATCH", "reason": "ML intent not recognised"}
