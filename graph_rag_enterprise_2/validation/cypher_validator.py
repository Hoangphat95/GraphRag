import os
import re
import json
try:
    from cypher import metrics as cy_metrics
except Exception:
    cy_metrics = None


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
        # remove double-quoted and single-quoted string literals
        cypher = re.sub(r'"[^"\\]*(?:\\.[^"\\]*)*"', '', cypher)
        cypher = re.sub(r"'[^'\\]*(?:\\.[^'\\]*)*'", '', cypher)

        # remove backtick quoted identifiers
        cypher = re.sub(r'`[^`]*`', '', cypher)

        # remove single-line comments //...
        cypher = re.sub(r'//.*', '', cypher)

        # remove block comments /* ... */
        cypher = re.sub(r'/\*.*?\*/', '', cypher, flags=re.S)

        return cypher

    # =========================
    # MAIN VALIDATE
    # =========================
    def validate(self, cypher: str, params: dict = None):
        print("\n===== VALIDATING CYPHER =====")
        print(cypher)

        if not cypher or len(cypher.strip()) == 0:
            return False, "Empty query"

        # If caller did not supply parameters, reject queries that contain
        # raw string literals (likely user interpolation). This forces
        # callers to use parameterized queries and prevents injection.
        if params is None:
            # detect any single- or double-quoted literal
            if re.search(r"(['\"]).+?\1", cypher):
                if cy_metrics:
                    try:
                        cy_metrics.increment('validator.invalid.raw_literal')
                    except Exception:
                        pass
                return False, "Raw string literal detected; use query parameters"

        # If the query uses parameter placeholders like $size, ensure params
        # dict contains corresponding keys. If params is None and placeholders
        # exist, reject.
        placeholders = re.findall(r"\$([A-Za-z_]\w*)", cypher)
        if placeholders:
            if not params:
                if cy_metrics:
                    try:
                        cy_metrics.increment('validator.invalid.missing_params')
                    except Exception:
                        pass
                return False, "Parameterized query missing params"
            missing = [p for p in placeholders if p not in params]
            if missing:
                if cy_metrics:
                    try:
                        cy_metrics.increment('validator.invalid.missing_params')
                    except Exception:
                        pass
                return False, f"Missing params for placeholders: {missing}"

        cypher_upper = cypher.upper()
        clean_cypher = self._remove_strings(cypher)

        # =========================
        # 1. BLOCK DANGEROUS
        # =========================
        danger_keywords = ["DELETE", "CREATE", "MERGE", "SET", "DROP", "CALL"]
        for kw in danger_keywords:
            if kw in cypher_upper:
                return False, f"Dangerous keyword: {kw}"

        # =========================
        # 2. BASIC STRUCTURE
        # =========================
        if "MATCH" not in cypher_upper:
            return False, "Missing MATCH"

        if "RETURN" not in cypher_upper:
            return False, "Missing RETURN"

        if "LIMIT" not in cypher_upper:
            return False, "Missing LIMIT"

        # =========================
        # 3. LABEL CHECK
        # =========================
        labels = re.findall(r"\((?:\w+):(\w+)\)", clean_cypher)
        for label in labels:
            if label not in self.valid_labels:
                return False, f"Invalid label: {label}"

        # =========================
        # 4. RELATIONSHIP CHECK
        # =========================
        rels = re.findall(r"\[:([^\]]+)\]", clean_cypher)
        for rel in rels:
            if rel not in self.valid_relationships:
                return False, f"Invalid relationship: {rel}"

        # =========================
        # 5. PROPERTY CHECK
        # =========================
        props = re.findall(r"\b\w+\.(\w+)\b", clean_cypher)

        for p in props:
            if p not in self.valid_props:
                return False, f"Invalid property: {p}"

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
                return False, "Full scan Tire without filter"

        # =========================
        # 7. BLOCK MULTI QUERY
        # =========================
        if ";" in cypher:
            return False, "Multiple query detected"
        if cy_metrics:
            try:
                cy_metrics.increment('validator.valid')
            except Exception:
                pass

        print("✅ CYPHER OK")
        return True, "OK"

    def _fail(self, msg):
        print(f"❌ INVALID: {msg}")
        return False, msg