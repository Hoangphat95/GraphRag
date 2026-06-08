"""Cypher query validator — ensures queries are safe before execution."""
import os
import re
import json


class CypherValidator:
    def __init__(self):
        base = os.path.dirname(os.path.abspath(__file__))
        schema_path = os.path.join(base, "graph_schema.json")
        with open(schema_path, "r", encoding="utf-8") as f:
            self.schema = json.load(f)

        self.valid_labels = set(self.schema.get("nodes", []))
        self.valid_relationships = set(self.schema.get("relationships", []))
        self.valid_props = {p for props in self.schema["properties"].values() for p in props}

    # ── public ───────────────────────────────────────────────────────────

    def validate(self, cypher: str, params: dict = None):
        if not cypher or not cypher.strip():
            return False, "Empty query"

        # Block dangerous keywords
        cypher_upper = cypher.upper()
        for kw in ("DELETE", "CREATE", "MERGE", "SET", "DROP", "CALL"):
            if kw in cypher_upper:
                return False, f"Dangerous keyword: {kw}"

        # If no params, reject raw string literals
        if params is None:
            if re.search(r"['\"]", cypher):
                return False, "Raw string literal detected; use query parameters"

        # Validate parameter placeholders match supplied params
        placeholders = re.findall(r"\$([A-Za-z_]\w*)", cypher)
        if placeholders:
            if not params:
                return False, "Parameterized query missing params"
            missing = [p for p in placeholders if p not in params]
            if missing:
                return False, f"Missing params for placeholders: {missing}"

        # Optional: check node labels & relationship types
        clean = self._remove_strings(cypher)
        found_labels = re.findall(r"(?i)\bMATCH\s*\(:\s*([A-Za-z_]\w*)", clean)
        for lbl in found_labels:
            if lbl not in self.valid_labels:
                return False, f"Unknown node label: {lbl}"

        return True, ""

    # ── internal ─────────────────────────────────────────────────────────

    def _remove_strings(self, cypher: str):
        cypher = re.sub(r'"[^"\\]*(?:\\.[^"\\]*)*"', "", cypher)
        cypher = re.sub(r"'[^'\\]*(?:\\.[^'\\]*)*'", "", cypher)
        cypher = re.sub(r"`[^`]*`", "", cypher)
        cypher = re.sub(r"//.*", "", cypher)
        cypher = re.sub(r"/\*.*?\*/", "", cypher, flags=re.S)
        return cypher
