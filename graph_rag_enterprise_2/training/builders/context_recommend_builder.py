# training/builders/context_recommend_builder.py

import random


class ContextRecommendBuilder:

    def __init__(self, kg):
        self.kg = kg
        self.ctx = self.kg.get_full_context()

    # ======================
    # TEMPLATE BANK
    # ======================
    def templates(self):
        return [
            "xe {vehicle} nên dùng lốp nào",
            "tôi đi {vehicle} nên chọn lốp gì",
            "xe {vehicle} đi {usage} nên dùng loại lốp nào",
            "đi {usage} nên chọn lốp gì",
            "lốp nào phù hợp cho xe {vehicle}",
            "tư vấn lốp cho xe {vehicle}",
            "xe {vehicle} chạy {usage} nên dùng lốp nào",
            "gợi ý lốp cho xe {vehicle} đi {usage}"
        ]

    # ======================
    # BUILD FROM KG
    # ======================
    def build(self):
        data = []

        vehicles = self.ctx.get("vehicle_types", [])
        sizes = self.ctx.get("sizes", [])
        brands = self.ctx.get("brands", [])

        # fallback nếu KG thiếu
        if not vehicles:
            vehicles = ["motorcycle", "scooter"]

        usages = [
            "đi phố",
            "đi đường dài",
            "chở nặng",
            "đi mưa",
            "đi offroad"
        ]

        # ======================
        # 1. VEHICLE-BASED
        # ======================
        for v in vehicles:
            for temp in self.templates():
                if "{usage}" not in temp:
                    data.append({
                        "text": temp.format(vehicle=v),
                        "intent": "recommend",
                        "route": "RECOMMEND",
                        "context": {
                            "vehicle": v
                        }
                    })

        # ======================
        # 2. VEHICLE + USAGE
        # ======================
        for v in vehicles:
            for u in usages:
                for temp in self.templates():
                    if "{vehicle}" in temp and "{usage}" in temp:
                        data.append({
                            "text": temp.format(vehicle=v, usage=u),
                            "intent": "recommend",
                            "route": "RECOMMEND",
                            "context": {
                                "vehicle": v,
                                "usage": u
                            }
                        })

        # ======================
        # 3. USAGE ONLY
        # ======================
        for u in usages:
            data.append({
                "text": f"tôi thường {u} nên dùng lốp nào",
                "intent": "recommend",
                "route": "RECOMMEND",
                "context": {
                    "usage": u
                }
            })

        # ======================
        # 4. SIZE-AWARE RECOMMEND
        # ======================
        for s in random.sample(sizes, min(10, len(sizes))):
            data.append({
                "text": f"size {s} nên chọn lốp nào",
                "intent": "recommend",
                "route": "RECOMMEND",
                "context": {
                    "size": s
                }
            })

        # ======================
        # 5. BRAND-AWARE
        # ======================
        for b in brands:
            data.append({
                "text": f"lốp hãng {b} có nên dùng không",
                "intent": "recommend",
                "route": "RECOMMEND",
                "context": {
                    "brand": b
                }
            })

        print(f"🧠 Context recommend generated: {len(data)} samples")

        return data