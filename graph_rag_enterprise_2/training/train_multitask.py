import json
import pickle
import os
from datetime import datetime
from sentence_transformers import SentenceTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report


class MultiTaskModel:
    def __init__(self):
        self.embedder = SentenceTransformer("all-MiniLM-L6-v2")

        self.intent_clf = LogisticRegression(max_iter=300, class_weight="balanced")
        self.route_clf = LogisticRegression(max_iter=300, class_weight="balanced")

    def load_data(self, path):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        texts = [d["text"] for d in data]
        intents = [d["intent"] for d in data]
        routes = [d["route"] for d in data]

        return texts, intents, routes

    def train(self, path="training/dataset_train/multitask_dataset.json"):
        texts, intents, routes = self.load_data(path)

        print(f"🚀 Training MultiTask Model on {len(texts)} samples...")

        X = self.embedder.encode(texts)

        X_train, X_test, y_int_train, y_int_test, y_route_train, y_route_test = train_test_split(
            X, intents, routes, test_size=0.2, random_state=42
        )

        # train
        self.intent_clf.fit(X_train, y_int_train)
        self.route_clf.fit(X_train, y_route_train)

        # eval
        print("\n🎯 Intent Report:")
        print(classification_report(y_int_test, self.intent_clf.predict(X_test)))

        print("\n🎯 Route Report:")
        print(classification_report(y_route_test, self.route_clf.predict(X_test)))

        # ensure folder
        os.makedirs("training/models", exist_ok=True)

        # versioning
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        model_path = f"training/models/multitask_model_{timestamp}.pkl"

        with open(model_path, "wb") as f:
            pickle.dump({
                "intent": self.intent_clf,
                "route": self.route_clf
            }, f)

        # latest symlink (optional)
        latest_path = "training/models/multitask_model.pkl"
        with open(latest_path, "wb") as f:
            pickle.dump({
                "intent": self.intent_clf,
                "route": self.route_clf
            }, f)

        print(f"✅ Saved: {model_path}")
        print(f"✅ Updated latest: {latest_path}")


if __name__ == "__main__":
    model = MultiTaskModel()
    model.train()