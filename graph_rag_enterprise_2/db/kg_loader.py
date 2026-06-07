from db.neo4j_client import Neo4jClient
from functools import lru_cache


class KGLoader:
    def __init__(self):
        self.client = Neo4jClient()

    # =========================
    # LOAD ALL SIZES
    # =========================
    @lru_cache(maxsize=1)
    def get_all_sizes(self):
        query = """
        MATCH (t:Tire)
        WHERE t.size IS NOT NULL
        RETURN DISTINCT t.size AS size
        """
        result = self.client.query(query)
        return [r["size"] for r in result if r["size"]]

    # =========================
    # LOAD ALL BRANDS
    # =========================
    @lru_cache(maxsize=1)
    def get_all_brands(self):
        query = """
        MATCH (t:Tire)
        WHERE t.brand IS NOT NULL
        RETURN DISTINCT t.brand AS brand
        """
        result = self.client.query(query)
        return [r["brand"] for r in result if r["brand"]]

    # =========================
    # LOAD ALL TYPES
    # =========================
    @lru_cache(maxsize=1)
    def get_all_types(self):
        query = """
        MATCH (t:Tire)-[:THUỘC_NHÓM]->(tt:TireType)
        RETURN DISTINCT tt.name AS type
        """
        result = self.client.query(query)
        return [r["type"] for r in result if r["type"]]

    # =========================
    # LOAD ALL PATTERNS
    # =========================
    @lru_cache(maxsize=1)
    def get_all_patterns(self):
        query = """
        MATCH (t:Tire)-[:CÓ_HOA]->(tp:TirePattern)
        RETURN DISTINCT tp.pattern AS pattern
        """
        result = self.client.query(query)
        return [r["pattern"] for r in result if r["pattern"]]

    # =========================
    # LOAD ALL VEHICLES
    # =========================
    @lru_cache(maxsize=1)
    def get_all_vehicle_types(self):
        query = """
        MATCH (t:Tire)
        WHERE t.vehicle_type IS NOT NULL
        RETURN DISTINCT t.vehicle_type AS vehicle
        """
        result = self.client.query(query)
        return [r["vehicle"] for r in result if r["vehicle"]]

    # =========================
    # 🔥 NEW: LOAD PROPERTIES (QUAN TRỌNG)
    # =========================
    @lru_cache(maxsize=1)
    def get_properties(self):
        query = """
        MATCH (t:Tire)
        RETURN keys(t) AS props
        LIMIT 1
        """
        result = self.client.query(query)

        if not result:
            return []

        props = result[0]["props"]

        # ❌ loại bỏ field không cần
        blacklist = {"id"}
        props = [p for p in props if p not in blacklist]

        return props

    # =========================
    # FULL CONTEXT
    # =========================
    def get_full_context(self):
        return {
            "sizes": self.get_all_sizes(),
            "brands": self.get_all_brands(),
            "types": self.get_all_types(),
            "patterns": self.get_all_patterns(),
            "vehicle_types": self.get_all_vehicle_types(),  # 🔥 rename cho đồng bộ
            "properties": self.get_properties()  # 🔥 QUAN TRỌNG
        }