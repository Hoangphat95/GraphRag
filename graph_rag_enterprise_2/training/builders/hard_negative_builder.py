import random

class HardNegativeBuilder:

    def __init__(self):
        pass

    def build(self, sizes):
        data = []

        # 🔥 CASE 1: ambiguous RULE vs LLM
        for size in sizes:
            data.append({
                "text": f"lốp {size} tốt không",
                "intent": "ask_feature",
                "route": "LLM"
            })

            data.append({
                "text": f"tốc độ lốp {size}",
                "intent": "ask_property",
                "route": "RULE"
            })

        # 🔥 CASE 2: tricky recommend
        data.extend([
            {
                "text": "lốp nào tốt",
                "intent": "recommend",
                "route": "RECOMMEND"
            },
            {
                "text": "nên chọn loại lốp nào",
                "intent": "recommend",
                "route": "RECOMMEND"
            }
        ])

        return data