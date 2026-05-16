import json
from typing import List, Dict
from property_normalizer import PropertyNormalizer


class CypherBuilder:

    def __init__(self, schema_path="graph_schema.json"):
        with open(schema_path, "r", encoding="utf-8") as f:
            self.schema = json.load(f)

        self.properties = self.schema["properties"]
        self.normalizer = PropertyNormalizer(self.properties)

        self.prop_to_node = {
            p: node
            for node, props in self.properties.items()
            for p in props
        }

        self.valid_props = {
            p for props in self.properties.values() for p in props
        }

        self.property_keywords = {
            "tốc độ": "toc_do_toi_da",
            "tốc độ tối đa": "toc_do_toi_da",
            "chịu tải": "tai_trong_lon_nhat",
            "tải": "tai_trong_lon_nhat",
            "áp suất": "noi_ap_tieu_chuan",
            "rim": "duong_kinh_vanh",
            "đường kính vành": "duong_kinh_vanh",
            "vành": "duong_kinh_vanh",
            "đường kính ngoài": "duong_kinh_ngoai",
            "ngoài": "duong_kinh_ngoai",
            "pattern": "kieu_hoa",
            "hoa": "kieu_hoa"
        }

    # ======================
    def detect_intent(self, mapped, query):
        q = query.lower()

        has_property = any(r.get("type") == "column_detect" for r in mapped)
        has_size = any(r.get("type") in ["exact", "size_fallback"] for r in mapped)

        if "ruột" in q or "tube" in q:
            return "TUBE_QUERY"

        if "hãng" in q:
            return "BRAND_QUERY"

        if "công ty" in q:
            return "COMPANY_QUERY"

        if "tiêu chuẩn" in q:
            return "STANDARD_QUERY"
        
        if "pattern" in q or "hoa" in q:
            return "PATTERN_QUERY"

        if any(k in q for k in ["thông số", "thông tin", "chi tiết", "spec"]):
            return "FULL_INFO_QUERY"

        if has_property and has_size:
            return "PROPERTY_QUERY"

        if has_size:
            return "SIZE_QUERY"

        if has_property:
            return "PROPERTY_ONLY_QUERY"

        return "GENERAL_QUERY"

    # ======================
    def build(self, mapped_results: List[Dict], query: str):

        intent = self.detect_intent(mapped_results, query)

        size_value = None
        target_property = None

        # ======================
        # extract
        # ======================
        for r in mapped_results:

            if r.get("type") in ["exact", "size_fallback"]:
                if r.get("column") == "Giá trị quy cách":
                    size_value = r.get("value")

            if r.get("type") == "column_detect":
                target_property = self.normalizer.get_real_property(r.get("column"))

        # ======================
        # PRIORITY RULE (fix sai semantic)
        # ======================
        q = query.lower()

        if "đường kính vành" in q:
            target_property = "duong_kinh_vanh"

        elif "đường kính ngoài" in q:
            target_property = "duong_kinh_ngoai"

        # ======================
        # extract semantic (chỉ khi chưa có)
        # ======================
        if not target_property:
            for r in mapped_results:
                if r.get("type") == "column_detect":
                    target_property = self.normalizer.get_real_property(r.get("column"))

        # ======================
        # fallback keyword
        # ======================
        if not target_property:
            for k, v in sorted(self.property_keywords.items(), key=lambda x: -len(x[0])):
                if k in q:
                    target_property = v
                    break

        # ======================
        # SAFE CHECK
        # ======================
        if target_property and target_property not in self.valid_props:
            raise ValueError(f"Invalid property: {target_property}")

        # ======================
        # PATTERN
        # ======================
        if intent == "PATTERN_QUERY":

            if size_value:
                return f"""
                MATCH (t:Tire)-[:CÓ_HOA]->(p:TirePattern)
                WHERE t.size = "{size_value}"
                RETURN COLLECT(DISTINCT p.pattern) AS result
                LIMIT 1
                """

            return """
            MATCH (t:Tire)-[:CÓ_HOA]->(p:TirePattern)
            RETURN COLLECT(DISTINCT p.pattern) AS result
            LIMIT 1
            """

        # ======================
        # SIZE QUERY
        # ======================
        if intent == "SIZE_QUERY":

            if not size_value:
                return """
                MATCH (t:Tire)
                RETURN DISTINCT t.size AS result
                LIMIT 20
                """

            if target_property:
                return f"""
                MATCH (t:Tire)
                WHERE t.size = "{size_value}"
                RETURN t.{target_property} AS result
                LIMIT 1
                """

            return f"""
            MATCH (t:Tire)
            WHERE t.size = "{size_value}"
            RETURN 
                t.toc_do_toi_da AS speed,
                t.tai_trong_lon_nhat AS load,
                t.noi_ap_tieu_chuan AS pressure
            LIMIT 1
            """

        # ======================
        # PROPERTY QUERY
        # ======================
        if intent == "PROPERTY_QUERY" and target_property:

            q = "MATCH (t:Tire)\n"

            if size_value:
                q += f'WHERE t.size = "{size_value}"\n'

            q += f"RETURN t.{target_property} AS result LIMIT 1"
            return q

        # ======================
        # PROPERTY ONLY
        # ======================
        if intent == "PROPERTY_ONLY_QUERY":

            if not target_property:
                return """
                MATCH (t:Tire)
                RETURN t.size AS result
                LIMIT 10
                """

            if size_value:
                return f"""
                MATCH (t:Tire)
                WHERE t.size = "{size_value}"
                RETURN t.{target_property} AS result
                LIMIT 1
                """

            return f"""
            MATCH (t:Tire)
            RETURN DISTINCT t.{target_property} AS result
            LIMIT 20
            """

        # ======================
        # BRAND
        # ======================
        if intent in ["BRAND_QUERY", "COMPANY_QUERY"] and size_value:
            return f"""
            MATCH (t:Tire)
            WHERE t.size = "{size_value}"
            RETURN t.brand AS result
            LIMIT 1
            """

        # ======================
        # FULL INFO (FINAL CLEAN)
        # ======================
        if intent == "FULL_INFO_QUERY" and size_value:
            return f"""
            MATCH (t:Tire)
            WHERE t.size = "{size_value}"

            OPTIONAL MATCH (t)-[:CÓ_HOA]->(p:TirePattern)

            WITH t, COLLECT(DISTINCT p.pattern) AS patterns

            RETURN 
                t.size AS size,
                t.brand AS brand,
                t.toc_do_toi_da AS max_speed,
                t.tai_trong_lon_nhat AS max_load,
                t.noi_ap_tieu_chuan AS pressure,
                t.duong_kinh_ngoai AS diameter,
                t.duong_kinh_vanh AS rim,
                t.chieu_rong_toan_bo AS width,
                t.chieu_sau_hoa AS tread_depth,
                t.rong_vanh_tieu_chuan AS std_rim,
                t.rong_vanh_thich_hop AS fit_rim,
                t.so_lop_bo AS ply_rating,
                t.chi_so_tai_toc_do AS load_speed_index,
                t.phan_loai_tai AS load_type,
                t.nhom_lop AS category,
                t.vehicle_type AS vehicle,
                t.kieu_quy_cach AS spec_type,
                t.cau_truc_lop AS structure,
                CASE 
                    WHEN t.co_sam = true THEN "Có săm"
                    ELSE "Không săm"
                END AS tube_type,
                patterns AS pattern
            LIMIT 1
            """

        # ======================
        # TUBE QUERY (FINAL)
        # ======================
        if intent == "TUBE_QUERY":

            if not size_value:
                return """
                MATCH (t:Tire)
                OPTIONAL MATCH (tu:Tube)-[:DÙNG_CHO]->(t)
                RETURN DISTINCT t.size,
                    CASE 
                        WHEN t.co_sam = false THEN "Lốp không săm"
                        WHEN tu.vehicle_type IS NULL THEN "Lốp có săm"
                        ELSE "Lốp có săm: " + tu.vehicle_type
                    END AS result
                LIMIT 20
                """

            return f"""
            MATCH (t:Tire)
            WHERE t.size = "{size_value}"
            OPTIONAL MATCH (tu:Tube)-[:DÙNG_CHO]->(t)
            RETURN 
                CASE 
                    WHEN t.co_sam = false THEN "Lốp không săm"
                    WHEN tu.vehicle_type IS NULL THEN "Lốp có săm"
                    ELSE "Lốp có săm: " + tu.vehicle_type
                END AS result
            LIMIT 1
            """

        # ======================
        # DEFAULT
        # ======================
        return """
        MATCH (t:Tire)
        RETURN t.size AS result
        LIMIT 10
        """