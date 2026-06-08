"""Intent classifier — lightweight ML model for fallback intent detection.

Uses SentenceTransformer + LogisticRegression.
"""
import os
import json
import pickle
import numpy as np

# ── lazy imports ─────────────────────────────────────────────────────────────
def _get_embedder():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer("all-MiniLM-L6-v2")


def _get_lr():
    from sklearn.linear_model import LogisticRegression
    return LogisticRegression(max_iter=500, class_weight="balanced", C=5.0)


# ── training data ────────────────────────────────────────────────────────────
TRAINING_DATA = {
    "SINGLE": [
        "lốp 120/70-17 thông số thế nào",
        "lốp 2.50-17 có những thông số gì",
        "cho mình biết thông tin lốp 100/90-18",
        "lốp 110/80-14 chiều rộng bao nhiêu",
        "thông số kỹ thuật lốp 2.75-17",
    ],
    "SPEED": [
        "tốc độ tối đa của lốp 120/70-17",
        "lốp 100/80-14 chạy được bao nhiêu km/h",
        "tốc độ lốp 90/90-14",
        "lốp nào nhanh nhất",
        "lốp 110/70-14 tốc độ bao nhiêu",
    ],
    "LOAD": [
        "tải trọng lốp 120/70-17",
        "lốp 2.50-17 chịu tải bao nhiêu kg",
        "lốp 100/90-18 tải trọng tối đa",
        "lốp nào chịu tải cao nhất",
        "lốp 110/80-14 chở được bao nhiêu kg",
    ],
    "PRICE": [
        "giá lốp 120/70-17 bao nhiêu",
        "lốp 100/80-14 giá bao nhiêu tiền",
        "báo giá lốp 2.50-17",
        "lốp rẻ nhất",
        "lốp 3.00-18 giá",
    ],
    "COMPARE": [
        "so sánh lốp 120/70-17 và 110/70-17",
        "lốp 2.50-17 vs 2.75-17",
        "khác nhau giữa lốp 90/90-14 và 100/80-14",
        "nên mua lốp 120/70-17 hay 110/70-17",
        "so sánh 2.50 và 2.75",
    ],
    "PRESSURE": [
        "áp suất lốp 120/70-17",
        "bơm lốp 100/80-14 bao nhiêu kg",
        "áp suất tiêu chuẩn lốp 2.50-17",
        "lốp 90/90-14 bơm bao nhiêu psi",
    ],
    "BRAND": [
        "lốp DPLUS có tốt không",
        "thương hiệu lốp nào bền nhất",
        "lốp IRC giá bao nhiêu",
        "lốp MAXXIS chất lượng",
        "các hãng lốp xe máy",
    ],
}


class IntentClassifier:
    """Lightweight ML intent classifier.  Trains on first use."""

    def __init__(self, model_dir: str = None):
        self.model_dir = model_dir or os.path.join(
            os.path.dirname(__file__), "models", "intent_classifier"
        )
        self._model = None
        self._embedder = None
        self._label_encoder = None
        self._labels = []
        self._fitted = False

    def _ensure_fitted(self):
        if self._fitted:
            return

        # Try loading cached model from disk
        model_path = os.path.join(self.model_dir, "model.pkl")
        if os.path.exists(model_path):
            try:
                with open(model_path, "rb") as f:
                    data = pickle.load(f)
                self._model = data["model"]
                self._labels = data["labels"]
                self._embedder = _get_embedder()
                self._fitted = True
                return
            except Exception:
                pass

        # Train on-the-fly
        self._embedder = _get_embedder()
        X_text, y = [], []
        for intent, examples in TRAINING_DATA.items():
            for ex in examples:
                X_text.append(ex)
                y.append(intent)

        X = self._embedder.encode(X_text)
        self._labels = sorted(set(y))
        label_to_int = {l: i for i, l in enumerate(self._labels)}
        y_int = [label_to_int[l] for l in y]

        self._model = _get_lr()
        self._model.fit(X, y_int)

        # persist
        os.makedirs(self.model_dir, exist_ok=True)
        with open(model_path, "wb") as f:
            pickle.dump({"model": self._model, "labels": self._labels}, f)

        self._fitted = True

    def predict(self, query: str) -> dict:
        self._ensure_fitted()
        emb = self._embedder.encode([query])
        probs = self._model.predict_proba(emb)[0]
        best_idx = int(np.argmax(probs))
        return {
            "intent": self._labels[best_idx],
            "confidence": float(probs[best_idx]),
            "probabilities": {self._labels[i]: float(probs[i]) for i in range(len(self._labels))},
        }
