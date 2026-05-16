class ContextManager:

    def __init__(self):
        self.history = []

    def add_context(self, query, mapped, plan, data):
        self.history.append({
            "query": query,
            "mapped": mapped,
            "plan": plan,
            "data": data
        })

    def get_last(self):
        return self.history[-1] if self.history else None

    def get_last_sizes(self, n=2):
        sizes = []
        for entry in self.history:
            for m in entry.get("mapped", []):
                if m.get("column") == "size":
                    value = m.get("value")
                    if value and value not in sizes:
                        sizes.append(value)
        return sizes[-n:]

    def get_last_size(self):
        sizes = self.get_last_sizes(1)
        return sizes[0] if sizes else None

    def get_last_brand(self):
        last = self.get_last()
        if not last:
            return None

        brands = [m.get("value") for m in last.get("mapped", []) if m.get("column") == "brand"]
        return brands[-1] if brands else None