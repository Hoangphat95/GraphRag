import json
import os


class AutoLearner:

    def __init__(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))

        self.log_path = os.path.join(base_dir, "logs.json")
        self.train_path = os.path.join(base_dir, "train_data.json")
        self.model_path = os.path.join(base_dir, "intent_model.pkl")

        # 🔥 đảm bảo folder tồn tại
        os.makedirs(base_dir, exist_ok=True)

        # 🔥 tạo file log nếu chưa có
        if not os.path.exists(self.log_path):
            with open(self.log_path, "w", encoding="utf-8") as f:
                json.dump([], f)

    # ======================
    # 🔥 SAVE QUERY LOG
    # ======================
    def log(self, query, route, mapped):
        record = {
            "query": query,
            "label": None,
            "predicted": route,
            "mapped": mapped
        }

        with open(self.log_path, "r+", encoding="utf-8") as f:
            data = json.load(f)
            data.append(record)
            f.seek(0)
            json.dump(data, f, ensure_ascii=False, indent=2)

    # ======================
    # 🔥 MERGE LOG → TRAIN DATA
    # ======================
    def merge_and_retrain(self):
        if not os.path.exists(self.log_path):
            return

        with open(self.log_path, "r", encoding="utf-8") as f:
            logs = json.load(f)

        if len(logs) < 200:
            print("⚠️ Not enough new data to retrain")
            return

        # load train_data
        if not os.path.exists(self.train_path):
            train_data = []
        else:
            with open(self.train_path, "r", encoding="utf-8") as f:
                train_data = json.load(f)

        # merge
        new_data = [
            {"query": l["query"], "label": l["label"]}
            for l in logs
            if l.get("label") in ["RULE", "LLM"]
        ]
        
        if len(new_data) < 100:
            print("⚠️ Not enough labeled data → skip retrain")
            return
        
        merged = train_data + new_data

        with open(self.train_path, "w", encoding="utf-8") as f:
            json.dump(merged, f, ensure_ascii=False, indent=2)

        # clear logs
        with open(self.log_path, "w") as f:
            json.dump([], f)

        print(f"🔥 Retraining with {len(merged)} samples...")

        # xóa model cũ để train lại
        if os.path.exists(self.model_path):
            os.remove(self.model_path)

        print("✅ Ready for retrain on next run")