import os
import re
import json


class CypherValidator:

    def __init__(self):
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        schema_path = os.path.join(BASE_DIR, "../cypher/graph_schema.json")

        with open(schema_path, "r", encoding="utf-8") as f:
            self.schema = json.load(f)

        self.valid_labels = set(self.schema.get("nodes", []))
        self.valid_relationships = set(self.schema.get("relationships", []))

        self.valid_props = {
            p for props in self.schema["properties"].values() for p in props
        }

    # =========================
    # REMOVE STRING LITERALS
    # =========================
    def _remove_strings(self, cypher: str):
        cypher = re.sub(r'"[^"]*"', '', cypher)
        cypher = re.sub(r"'[^']*'", '', cypher)
        return cypher

    # =========================
    # MAIN VALIDATE
    # =========================
    def validate(self, cypher: str):
        print("\n===== VALIDATING CYPHER =====")
        print(cypher)

        if not cypher or len(cypher.strip()) == 0:
            return self._fail("Empty query")

        cypher_upper = cypher.upper()
        clean_cypher = self._remove_strings(cypher)

        # =========================
        # 1. BLOCK DANGEROUS
        # =========================
        danger_keywords = ["DELETE", "CREATE", "MERGE", "SET", "DROP", "CALL"]
        for kw in danger_keywords:
            if kw in cypher_upper:
                return self._fail(f"Dangerous keyword: {kw}")

        # =========================
        # 2. BASIC STRUCTURE
        # =========================
        if "MATCH" not in cypher_upper:
            return self._fail("Missing MATCH")

        if "RETURN" not in cypher_upper:
            return self._fail("Missing RETURN")

        if "LIMIT" not in cypher_upper:
            return self._fail("Missing LIMIT")

        # =========================
        # 3. LABEL CHECK
        # =========================
        labels = re.findall(r"\((?:\w+):(\w+)\)", clean_cypher)
        for label in labels:
            if label not in self.valid_labels:
                return self._fail(f"Invalid label: {label}")

        # =========================
        # 4. RELATIONSHIP CHECK
        # =========================
        rels = re.findall(r"\[:([^\]]+)\]", clean_cypher)
        for rel in rels:
            if rel not in self.valid_relationships:
                return self._fail(f"Invalid relationship: {rel}")

        # =========================
        # 5. PROPERTY CHECK
        # =========================
        props = re.findall(r"\b\w+\.(\w+)\b", clean_cypher)

        for p in props:
            if p not in self.valid_props:
                return self._fail(f"Invalid property: {p}")

        # =========================
        # 6. ANTI FULL SCAN (🔥 FIX)
        # =========================
        if "MATCH (t:Tire)" in clean_cypher and "WHERE" not in cypher_upper:

            # ✅ cho phép query ranking / aggregation
            if "ORDER BY" in cypher_upper or "LIMIT" in cypher_upper:
                pass
            elif "DISTINCT" in cypher_upper:
                pass
            else:
                return self._fail("Full scan Tire without filter")

        # =========================
        # 7. BLOCK MULTI QUERY
        # =========================
        if ";" in cypher:
            return self._fail("Multiple query detected")

        print("✅ CYPHER OK")
        return True

    def _fail(self, msg):
        print(f"❌ INVALID: {msg}")
        return False