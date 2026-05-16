from router.ml_router import MLRouter

class QueryRouter:

    def __init__(self):
        self.ml = MLRouter()

    def route(self, query: str, mapped):
        q = query.lower()

        has_size = any(r.get("type") in ["exact", "size_fallback"] for r in mapped)
        has_property = any(r.get("type") == "column_detect" for r in mapped)

        size_count = sum(1 for r in mapped if r.get("type") in ["exact", "size_fallback"])

        # RULE chắc chắn
        if has_size and has_property and size_count == 1:
            return "RULE"

        # ML fallback
        pred = self.ml.predict(query)

        return pred