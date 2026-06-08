import re
from .limits import SINGLE_LIMIT, MULTI_LIMIT

class CypherBuilder:

    def __init__(self):
        pass

    def _safe(self, val):
        if val is None:
            return None

        s = str(val).strip()

        # Allow common size characters (digits, letters, dot, slash, dash)
        # Examples: 205/55R16, 205.55, 205-55
        if re.match(r'^[0-9A-Za-z./\-]+$', s):
            return s

        # If value contains disallowed characters, try to remove them conservatively
        cleaned = re.sub(r'[^0-9A-Za-z./\-]', '', s)
        if cleaned:
            return cleaned

        return None

    # =========================
    # FULL INFO
    # =========================
    def _build_full(self, size_param_name="$size"):
        # return cypher string using parameter placeholder
        return f"""
        MATCH (t:Tire)
        WHERE t.size = {size_param_name}
        OPTIONAL MATCH (t)-[:CÓ_HOA]->(p:TirePattern)
        RETURN 
            t.size AS size,
            t.brand AS brand,
            t.toc_do_toi_da AS max_speed,
            t.tai_trong_lon_nhat AS max_load,
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
    def build(self, plan_or_mapped, query=None):

        # Support two calling styles for backward compatibility:
        # - build(plan: dict)
        # - build(mapped: list, query: str)

        plan = None
        if isinstance(plan_or_mapped, dict):
            plan = plan_or_mapped
        elif isinstance(plan_or_mapped, list):
            # simple conversion: pick first size if present
            mapped = plan_or_mapped
            sizes = [m.get('value') for m in mapped if m.get('column') == 'size' and m.get('value')]
            if sizes:
                plan = {'type': 'SINGLE', 'sizes': sizes}
            else:
                plan = {'type': 'SINGLE', 'sizes': []}
        else:
            return None, None

        plan_type = plan.get("type")
        # sanitize sizes and filter out invalid/None values
        sizes = [s for s in (self._safe(x) for x in plan.get("sizes", [])) if s]

        # =========================
        # NO MATCH
        # =========================
        if plan_type == "NO_MATCH":
            return None, None

        # =========================
        # MAX LOAD
        # =========================
        if plan_type == "MAX_LOAD":

            if sizes:
                cy = """
                MATCH (t:Tire)
                WHERE t.size = $size AND t.tai_trong_lon_nhat IS NOT NULL
                RETURN t.size AS size, t.tai_trong_lon_nhat AS max_load
                LIMIT 1
                """
                return cy, {"size": sizes[0]}
            
            cy = """
            MATCH (t:Tire)
            WHERE t.tai_trong_lon_nhat IS NOT NULL

            WITH MAX(t.tai_trong_lon_nhat) AS max_load

            MATCH (t:Tire)
                WHERE t.tai_trong_lon_nhat = max_load

                RETURN 
                    t.size AS size,
                    t.brand AS brand,
                    t.tai_trong_lon_nhat AS max_load
                LIMIT 10
            """
            return cy, None

        # =========================
        # MAX SPEED
        # =========================
        if plan_type == "MAX_SPEED":

            if sizes:
                cy = """
                MATCH (t:Tire)
                WHERE t.size = $size AND t.toc_do_toi_da IS NOT NULL
                RETURN t.size AS size, t.toc_do_toi_da AS max_speed
                LIMIT 1
                """
                return cy, {"size": sizes[0]}

            cy = """
            MATCH (t:Tire)
            WHERE t.toc_do_toi_da IS NOT NULL

            WITH MAX(t.toc_do_toi_da) AS max_speed

            MATCH (t:Tire)
                WHERE t.toc_do_toi_da = max_speed

                RETURN 
                    t.size AS size,
                    t.brand AS brand, 
                    t.toc_do_toi_da AS max_speed
                LIMIT 10
            """
            return cy, None

        # =========================
        # MAX PRICE (🔥 NEW)
        # =========================
        if plan_type == "MAX_PRICE":

            if sizes:
                cy = """
                MATCH (t:Tire)
                WHERE t.size = $size AND t.gia_ban_co_vat IS NOT NULL
                RETURN t.size AS size, t.gia_ban_co_vat AS price
                LIMIT 1
                """
                return cy, {"size": sizes[0]}

            cy = """
            MATCH (t:Tire)
            WHERE t.gia_ban_co_vat IS NOT NULL
            WITH MAX(t.gia_ban_co_vat) AS max_price
            MATCH (t:Tire)
                WHERE t.gia_ban_co_vat = max_price
                RETURN t.size AS size, t.brand AS brand, t.gia_ban_co_vat AS price
                LIMIT 10
            """
            return cy, None
        
        # =========================
        # LOAD (🔥 NEW - FIX semantic)
        # =========================
        if plan_type == "LOAD":

            if not sizes:
                return None, None

            cy = """
            MATCH (t:Tire)
            WHERE t.size = $size
            RETURN t.size AS size, t.tai_trong_lon_nhat AS max_load
            LIMIT 1
            """
            return cy, {"size": sizes[0]}

        # =========================
        # SPEED (🔥 NEW - FIX semantic)
        # =========================
        if plan_type == "SPEED":

            if not sizes:
                return None, None

            cy = """
            MATCH (t:Tire)
            WHERE t.size = $size
            RETURN t.size AS size, t.brand AS brand, t.toc_do_toi_da AS max_speed
            LIMIT 1
            """
            return cy, {"size": sizes[0]}

        # =========================
        # PRICE (🔥 NEW)
        # =========================
        if plan_type == "PRICE":

            if not sizes:
                return None, None

            cy = """
            MATCH (t:Tire)
            WHERE t.size = $size
            RETURN t.size AS size, t.gia_ban_co_vat AS price
            LIMIT 1
            """
            return cy, {"size": sizes[0]}

        # =========================
        # PRESSURE (🔥 NEW)
        # =========================
        if plan_type == "PRESSURE":

            if not sizes:
                return None, None

            cy = """
            MATCH (t:Tire)
            WHERE t.size = $size
            RETURN t.size AS size, t.noi_ap_tieu_chuan AS pressure
            LIMIT 1
            """
            return cy, {"size": sizes[0]}

        # =========================
        # MULTI HOP
        # =========================
        if plan_type == "MULTI_HOP":

            if not sizes:
                return self._fallback()

            size = sizes[0]
            path = plan.get("path", [])

            if path == ["Tire", "Company"]:
                cy = """
                MATCH (c:Company)-[:CO_SP]->(t:Tire)
                WHERE t.size = $size
                RETURN c.name AS company
                LIMIT 1
                """
                return cy, {"size": size}

            if path == ["Tire", "QualityStandard"]:
                cy = """
                MATCH (t:Tire)-[:ĐẠT_CHUẨN]->(q:QualityStandard)
                WHERE t.size = $size
                RETURN DISTINCT q.name AS standard
                LIMIT 10
                """
                return cy, {"size": size}

            if path == ["Tire", "Tube", "Van"]:
                cy = """
                MATCH (t:Tire)<-[:DÙNG_CHO]-(tu:Tube)-[:DÙNG_VAN]->(v:Van)
                WHERE t.size = $size
                RETURN DISTINCT v.name AS valve
                LIMIT 10
                """
                return cy, {"size": size}

            return self._build_full("$size"), {"size": size}

        # =========================
        # COMPARE
        # =========================
        if plan_type == "COMPARE":

            if len(sizes) < 2:
                return None, None

            # use parameterized list
            cy = """
            MATCH (t:Tire)
            WHERE t.size IN $sizes
            OPTIONAL MATCH (t)-[:CÓ_HOA]->(p:TirePattern)
            RETURN 
                t.size AS size,
                t.brand AS brand,
                t.tai_trong_lon_nhat AS max_load,
                t.toc_do_toi_da AS max_speed,
                t.noi_ap_tieu_chuan AS pressure,
                t.duong_kinh_ngoai AS diameter,
                t.duong_kinh_vanh AS rim,
                t.cau_truc_lop AS structure,
                COLLECT(DISTINCT p.pattern) AS pattern
            LIMIT 10
            """
            return cy, {"sizes": sizes}

        # =========================
        # SINGLE
        # =========================
        if plan_type == "SINGLE":

            if not sizes:
                return None, None

            cy = self._build_full("$size")
            return cy, {"size": sizes[0]}

        cy = self._fallback()
        return cy, None

    # =========================
    # FALLBACK
    # =========================
    def _fallback(self):
        return f"""
        MATCH (t:Tire)
        RETURN t.size AS size, t.brand AS brand
        LIMIT {MULTI_LIMIT}
        """