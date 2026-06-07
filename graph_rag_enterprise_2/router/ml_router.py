import os
import pickle
import numpy as np
from mapper.model_manager import get_model


class MLRouter:
    def __init__(self):
        model_path = os.getenv(
            "MODEL_PATH",
            "training/models/multitask_model.pkl"
        )

        if not os.path.exists(model_path):
            raise FileNotFoundError(f"❌ Model not found at {model_path}")

        with open(model_path, "rb") as f:
            data = pickle.load(f)

        self.intent_clf = data["intent"]
        self.route_clf = data["route"]

        self.embedder = get_model()

    # =========================
    # RULE OVERRIDE (🔥 QUAN TRỌNG)
    # =========================
    def rule_override(self, query: str):
        q = query.lower()

        # 🔥 RECOMMEND
        if any(k in q for k in ["đường dài", "đi xa", "touring"]):
            return {
                "intent": "LONG_TRIP",
                "route": "RECOMMEND",
                "confidence": 1.0,
                "source": "RULE"
            }

        if any(k in q for k in ["đi phố", "trong phố", "city"]):
            return {
                "intent": "CITY",
                "route": "RECOMMEND",
                "confidence": 1.0,
                "source": "RULE"
            }

        # 🔥 EVALUATE
        if any(k in q for k in ["tốt không", "bền không", "ổn không"]):
            return {
                "intent": "EVALUATE",
                "route": "RULE",
                "confidence": 0.9,
                "source": "RULE"
            }

        return None

    # =========================
    def predict(self, query: str):

        # 🔥 RULE FIRST
        rule = self.rule_override(query)
        if rule:
            return rule

        # ======================
        # ML PREDICT
        # ======================
        vec = self.embedder.encode([query])

        intent = self.intent_clf.predict(vec)[0]
        route = self.route_clf.predict(vec)[0]

        try:
            intent_probs = self.intent_clf.predict_proba(vec)[0]
            route_probs = self.route_clf.predict_proba(vec)[0]

            intent_conf = float(np.max(intent_probs))
            route_conf = float(np.max(route_probs))

            confidence = float((intent_conf + route_conf) / 2)

        except:
            confidence = 0.7

        return {
            "intent": intent,
            "route": route,
            "confidence": confidence,
            "source": "ML"
        }