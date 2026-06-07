import re

class RuleRouter:
    def __init__(self):
        self.size_pattern = re.compile(
            r"\b\d{2,3}/\d{2}-\d{2}\b|\b\d\.\d{2}-\d{2}\b"
        )

        self.recommend_keywords = [
            "nên dùng", "tư vấn", "chọn lốp", "gợi ý"
        ]

        self.ask_info_keywords = [
            "xe tôi", "dùng xe", "đi xe"
        ]

    def route(self, query):
        q = query.lower()

        # 🔥 RECOMMEND
        if any(k in q for k in self.recommend_keywords):
            if any(k in q for k in self.ask_info_keywords):
                return {
                    "route": "ASK_INFO",
                    "source": "RULE"
                }
            return {
                "route": "RECOMMEND",
                "source": "RULE"
            }

        # 🔥 SIZE → RULE
        if self.size_pattern.search(q):
            return {
                "route": "RULE",
                "source": "RULE"
            }

        return None