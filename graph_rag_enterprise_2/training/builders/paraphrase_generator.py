import random

class ParaphraseGenerator:

    def __init__(self):
        self.synonyms = {
            "lốp": ["lop", "vỏ xe"],
            "tốt": ["ổn", "ok", "xịn"],
            "không": ["ko", "kh"],
            "bao nhiêu": ["bn", "bao nhiu"],
            "đánh giá": ["review", "nhận xét"]
        }

    def paraphrase(self, text, n=2):
        results = []

        for _ in range(n):
            new_text = text

            for k, vals in self.synonyms.items():
                if k in new_text and random.random() < 0.5:
                    new_text = new_text.replace(k, random.choice(vals))

            results.append(new_text.lower())

        return list(set(results))