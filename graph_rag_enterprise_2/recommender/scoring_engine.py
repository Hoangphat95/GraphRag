class ScoringEngine:

    def score(self, tire, context):
        score = 0
        reasons = []

        # ======================
        # LOAD
        # ======================
        load = tire.get("max_load") or tire.get("tai_trong_lon_nhat") or tire.get("load") or 0
        score += load * 0.3
        reasons.append(f"Tải trọng cao ({load})")

        # ======================
        # SPEED
        # ======================
        speed = tire.get("max_speed") or tire.get("toc_do_toi_da") or tire.get("speed") or 0
        score += speed * 0.2
        reasons.append(f"Tốc độ cao ({speed})")

        # ======================
        # VEHICLE MATCH
        # ======================
        if context.get("vehicle"):
            if tire.get("vehicle_type") == context["vehicle"]:
                score += 20
                reasons.append("Phù hợp loại xe")

        # ======================
        # PRIORITY
        # ======================
        if context.get("priority") == "durability":
            score += load * 0.2
            reasons.append("Ưu tiên độ bền")

        if context.get("priority") == "grip":
            score += 15
            reasons.append("Độ bám tốt")

        return score, reasons