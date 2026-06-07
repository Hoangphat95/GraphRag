import re

class ContextParser:

    def parse(self, query: str):
        q = query.lower()

        context = {
            "vehicle": None,
            "usage": None,
            "priority": None
        }

        # vehicle
        if any(k in q for k in ["vision", "air blade"]):
            context["vehicle"] = "scooter"

        if any(k in q for k in ["exciter", "winner"]):
            context["vehicle"] = "motorcycle"

        # usage
        if "đường dài" in q:
            context["usage"] = "long_trip"

        if "đi phố" in q:
            context["usage"] = "city"

        if "chở nặng" in q:
            context["usage"] = "heavy_load"

        # priority
        if "bền" in q:
            context["priority"] = "durability"

        if "êm" in q:
            context["priority"] = "comfort"

        if "bám" in q:
            context["priority"] = "grip"

        return context