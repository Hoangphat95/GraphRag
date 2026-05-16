import sys
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(BASE_DIR)

import json
import random
from collections import defaultdict

from db.kg_loader import KGLoader


class DataBuilder:

    def __init__(self):
        self.kg = KGLoader()
        self.ctx = self.kg.get_full_context()

        # fallback props nếu KG thiếu
        self.props = [
            "tải trọng",
            "tốc độ",
            "độ bền",
            "độ bám",
            "áp suất"
        ]

        self.typo_map = {
            "lốp": ["lop"],
            "không": ["ko", "k"],
            "bao nhiêu": ["bn"],
            "tốt": ["tot"],
            "đánh giá": ["dg"]
        }

    # =========================
    # UTILS
    # =========================
    def typo(self, text):
        for k, v in self.typo_map.items():
            if k in text and random.random() < 0.4:
                text = text.replace(k, random.choice(v))
        return text

    def shuffle_text(self, text):
        if random.random() < 0.2:
            return text.lower()
        return text

    def augment(self, text):
        text = self.typo(text)
        text = self.shuffle_text(text)
        return text

    # =========================
    # BUILD
    # =========================
    def build(self, output_path="training/dataset_train/multitask_dataset.json"):

        sizes = self.ctx.get("sizes", [])
        brands = self.ctx.get("brands", [])
        vehicles = self.ctx.get("vehicles", [])

        data = []

        # =========================
        # 1. ASK INFO
        # =========================
        for size in sizes:
            for _ in range(20):
                text = random.choice([
                    f"lốp {size}",
                    f"thông tin lốp {size}",
                    f"lop {size} la gi",
                    f"{size} là loại gì"
                ])
                data.append(self.sample(text, "ask_info", "RULE"))

        # =========================
        # 2. ASK PROPERTY
        # =========================
        for size in sizes:
            for prop in self.props:
                for _ in range(10):
                    text = random.choice([
                        f"{prop} của lốp {size}",
                        f"lốp {size} có {prop} bao nhiêu",
                        f"{size} {prop}",
                        f"cho tôi {prop} của {size}"
                    ])
                    data.append(self.sample(text, "ask_property", "RULE"))

        # =========================
        # 3. FEATURE / LLM
        # =========================
        for size in sizes:
            for prop in self.props:
                for _ in range(10):
                    text = random.choice([
                        f"{size} {prop} có tốt không",
                        f"lốp {size} có {prop} ổn không",
                        f"đánh giá {prop} của {size}"
                    ])
                    data.append(self.sample(text, "ask_feature", "LLM"))

        # =========================
        # 4. COMPARE
        # =========================
        for _ in range(1000):
            s1, s2 = random.sample(sizes, 2)
            text = random.choice([
                f"so sánh {s1} và {s2}",
                f"{s1} vs {s2} cái nào tốt hơn",
                f"{s1} với {s2}"
            ])
            data.append(self.sample(text, "compare", "LLM"))

        # =========================
        # 5. BRAND
        # =========================
        for brand in brands:
            for _ in range(50):
                text = random.choice([
                    f"lốp {brand} có tốt không",
                    f"hãng {brand} bền không",
                    f"đánh giá hãng {brand}"
                ])
                data.append(self.sample(text, "brand", "LLM"))

        # =========================
        # 6. RECOMMEND (CONTEXT)
        # =========================
        for _ in range(1500):
            v = random.choice(vehicles) if vehicles else "xe máy"
            text = random.choice([
                f"xe {v} nên dùng lốp nào",
                f"tôi đi {v} nên chọn lốp gì",
                f"gợi ý lốp cho {v}",
                f"xe tôi nên dùng loại nào"
            ])
            data.append(self.sample(text, "recommend", "RECOMMEND"))

        # =========================
        # 7. AMBIGUOUS (🔥 QUAN TRỌNG)
        # =========================
        for _ in range(1000):
            text = random.choice([
                "xe tôi nên dùng gì",
                "loại nào tốt",
                "cái này ổn không",
                "tư vấn giúp tôi"
            ])
            data.append(self.sample(text, "recommend", "RECOMMEND"))

        # =========================
        # 8. HARD NEGATIVE
        # =========================
        for _ in range(1000):
            text = random.choice([
                "thời tiết hôm nay thế nào",
                "giá vàng bao nhiêu",
                "ăn gì ngon",
                "python là gì"
            ])
            data.append(self.sample(text, "other", "LLM"))

        # =========================
        # CLEAN + SHUFFLE
        # =========================
        random.shuffle(data)

        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"✅ DONE: {len(data)} samples → {output_path}")

    def sample(self, text, intent, route):
        return {
            "text": self.augment(text),
            "intent": intent,
            "route": route
        }


if __name__ == "__main__":
    builder = DataBuilder()
    builder.build()