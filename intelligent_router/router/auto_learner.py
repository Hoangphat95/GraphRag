# import json
# import os
# from router.intent_model import IntentModel


# class AutoLearner:

#     def __init__(self):
#         self.log_path = "router/logs.json"
#         self.model = IntentModel()

#     def log(self, query, intent):
#         data = []

#         if os.path.exists(self.log_path):
#             with open(self.log_path, "r", encoding="utf-8") as f:
#                 data = json.load(f)

#         data.append({"query": query, "intent": intent})

#         with open(self.log_path, "w", encoding="utf-8") as f:
#             json.dump(data, f, indent=2, ensure_ascii=False)

#     def retrain_if_needed(self, threshold=20):
#         if not os.path.exists(self.log_path):
#             return

#         with open(self.log_path, "r", encoding="utf-8") as f:
#             data = json.load(f)

#         if len(data) < threshold:
#             return

#         print("🔥 Auto retraining model...")

#         texts = [x["query"] for x in data]
#         labels = [1 if x["intent"] == "LLM" else 0 for x in data]

#         X = self.model.embedder.encode(texts)

#         self.model.clf.fit(X, labels)

#         print("✅ Retrained from logs")