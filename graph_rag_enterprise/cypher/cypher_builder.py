import re

class CypherBuilder:

    def __init__(self):
        pass

    def _safe(self, val):
        if val is None:
            return None
        return re.sub(r'[^a-zA-Z0-9./\-]', '', str(val))

    # =========================
    # FULL INFO
    # =========================
    def _build_full(self, size):
        return f"""
        MATCH (t:Tire)
        WHERE t.size = "{size}"
        OPTIONAL MATCH (t)-[:CÓ_HOA]->(p:TirePattern)
        RETURN 
            t.size AS size,
            t.brand AS brand,
            t.toc_do_toi_da AS speed,
            t.tai_trong_lon_nhat AS load,
            t.noi_ap_tieu_chuan AS pressure,
            t.gia_ban_co_vat AS price,
            t.duong_kinh_ngoai AS diameter,
            t.duong_kinh_vanh AS rim,
            t.cau_truc_lop AS structure,
            COLLECT(DISTINCT p.pattern) AS pattern
        LIMIT 1
        """

    # =========================
    # BUILD MAIN
    # =========================
    def build(self, plan):

        if not plan or "type" not in plan:
            return self._fallback()

        plan_type = plan.get("type")
        sizes = [self._safe(s) for s in plan.get("sizes", []) if s]

        # =========================
        # NO MATCH
        # =========================
        if plan_type == "NO_MATCH":
            return None

        # =========================
        # MAX LOAD
        # =========================
        if plan_type == "MAX_LOAD":

            if sizes:
                return f"""
                MATCH (t:Tire)
                WHERE t.size = "{sizes[0]}" AND t.tai_trong_lon_nhat IS NOT NULL
                RETURN t.size AS size, t.tai_trong_lon_nhat AS load
                LIMIT 1
                """
            
            return """
            MATCH (t:Tire)
            WHERE t.tai_trong_lon_nhat IS NOT NULL

            WITH MAX(t.tai_trong_lon_nhat) AS max_load

            MATCH (t:Tire)
            WHERE t.tai_trong_lon_nhat = max_load

            RETURN 
                t.size AS size,
                t.brand AS brand,
                t.tai_trong_lon_nhat AS load
            LIMIT 10
            """

        # =========================
        # MAX SPEED
        # =========================
        if plan_type == "MAX_SPEED":

            if sizes:
                return f"""
                MATCH (t:Tire)
                WHERE t.size = "{sizes[0]}" AND t.toc_do_toi_da IS NOT NULL
                RETURN t.size AS size, t.toc_do_toi_da AS speed
                LIMIT 1
                """

            return """
            MATCH (t:Tire)
            WHERE t.toc_do_toi_da IS NOT NULL

            WITH MAX(t.toc_do_toi_da) AS max_speed

            MATCH (t:Tire)
            WHERE t.toc_do_toi_da = max_speed

            RETURN 
                t.size AS size,
                t.brand AS brand,
                t.toc_do_toi_da AS speed
            LIMIT 10
            """

        # =========================
        # MAX PRICE (🔥 NEW)
        # =========================
        if plan_type == "MAX_PRICE":

            if sizes:
                return f"""
                MATCH (t:Tire)
                WHERE t.size = "{sizes[0]}" AND t.gia_ban_co_vat IS NOT NULL
                RETURN t.size AS size, t.gia_ban_co_vat AS price
                LIMIT 1
                """

            return """
            MATCH (t:Tire)
            WHERE t.gia_ban_co_vat IS NOT NULL
            WITH MAX(t.gia_ban_co_vat) AS max_price
            MATCH (t:Tire)
            WHERE t.gia_ban_co_vat = max_price
            RETURN t.size AS size, t.brand AS brand, t.gia_ban_co_vat AS price
            LIMIT 10
            """
        
        # =========================
        # LOAD (🔥 NEW - FIX semantic)
        # =========================
        if plan_type == "LOAD":

            if not sizes:
                return None

            return f"""
            MATCH (t:Tire)
            WHERE t.size = "{sizes[0]}"
            RETURN t.size AS size, t.tai_trong_lon_nhat AS load
            LIMIT 1
            """

        # =========================
        # SPEED (🔥 NEW - FIX semantic)
        # =========================
        if plan_type == "SPEED":

            if not sizes:
                return None

            return f"""
            MATCH (t:Tire)
            WHERE t.size = "{sizes[0]}"
            RETURN t.size AS size, t.brand AS brand, t.toc_do_toi_da AS speed
            LIMIT 1
            """

        # =========================
        # PRICE (🔥 NEW)
        # =========================
        if plan_type == "PRICE":

            if not sizes:
                return None

            return f"""
            MATCH (t:Tire)
            WHERE t.size = "{sizes[0]}"
            RETURN t.size AS size, t.gia_ban_co_vat AS price
            LIMIT 1
            """

        # =========================
        # PRESSURE (🔥 NEW)
        # =========================
        if plan_type == "PRESSURE":

            if not sizes:
                return None

            return f"""
            MATCH (t:Tire)
            WHERE t.size = "{sizes[0]}"
            RETURN t.size AS size, t.noi_ap_tieu_chuan AS pressure
            LIMIT 1
            """

        # =========================
        # MULTI HOP
        # =========================
        if plan_type == "MULTI_HOP":

            if not sizes:
                return self._fallback()

            size = sizes[0]
            path = plan.get("path", [])

            if path == ["Tire", "Company"]:
                return f"""
                MATCH (c:Company)-[:CO_SP]->(t:Tire)
                WHERE t.size = "{size}"
                RETURN c.name AS company
                LIMIT 1
                """

            if path == ["Tire", "QualityStandard"]:
                return f"""
                MATCH (t:Tire)-[:ĐẠT_CHUẨN]->(q:QualityStandard)
                WHERE t.size = "{size}"
                RETURN DISTINCT q.name AS standard
                LIMIT 5
                """

            if path == ["Tire", "Tube", "Van"]:
                return f"""
                MATCH (t:Tire)<-[:DÙNG_CHO]-(tu:Tube)-[:DÙNG_VAN]->(v:Van)
                WHERE t.size = "{size}"
                RETURN DISTINCT v.name AS valve
                LIMIT 5
                """

            return self._build_full(size)

        # =========================
        # COMPARE
        # =========================
        if plan_type == "COMPARE":

            if len(sizes) < 2:
                return None

            size_list = ", ".join([f'"{s}"' for s in sizes])

            return f"""
            MATCH (t:Tire)
            WHERE t.size IN [{size_list}]
            OPTIONAL MATCH (t)-[:CÓ_HOA]->(p:TirePattern)
            RETURN 
                t.size AS size,
                t.brand AS brand,
                t.tai_trong_lon_nhat AS load,
                t.toc_do_toi_da AS speed,
                t.noi_ap_tieu_chuan AS pressure,
                t.duong_kinh_ngoai AS diameter,
                t.duong_kinh_vanh AS rim,
                t.cau_truc_lop AS structure,
                COLLECT(DISTINCT p.pattern) AS pattern
            LIMIT 20
            """

        # =========================
        # SINGLE
        # =========================
        if plan_type == "SINGLE":

            if not sizes:
                return None

            return self._build_full(sizes[0])

        return self._fallback()

    # =========================
    # FALLBACK
    # =========================
    def _fallback(self):
        return """
        MATCH (t:Tire)
        RETURN t.size AS size, t.brand AS brand
        LIMIT 20
        """