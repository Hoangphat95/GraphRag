import unicodedata
import os
import pickle

import sys
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from db.neo4j_client import Neo4jClient

CACHE_FILE = r"E:\KG\graph_rag_enterprise\mapper\value_store.pkl"

# =========================
# NORMALIZE TEXT
# =========================
def normalize_text(text: str):
    if text is None:
        return ""

    text = str(text).lower().strip()

    # remove dấu
    text = unicodedata.normalize('NFD', text)
    text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')

    text = text.replace("đ", "d")

    return text


# =========================
# VALUE STORE FROM NEO4J
# =========================
class ValueStore:

    def __init__(self):
        self.client = Neo4jClient()
        self.data = []
        self.columns = []

    def build(self):

        # ======================
        # LOAD CACHE
        # ======================
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, "rb") as f:
                data = pickle.load(f)
                self.data = data["data"]
                self.columns = data["columns"]
                print("⚡ Loaded ValueStore from cache")
                return

        print("🚀 Building ValueStore from Neo4j...")

        # ======================
        # 1. GET ALL PROPERTIES
        # ======================
        schema_query = """
        MATCH (t:Tire)
        WITH keys(t) AS props
        UNWIND props AS prop
        RETURN DISTINCT prop
        """

        props = self.client.query(schema_query)

        prop_list = [p["prop"] for p in props]

        # ======================
        # 2. SAVE COLUMNS
        # ======================
        for p in prop_list:
            self.columns.append({
                "column": p
            })

        # ======================
        # 3. GET VALUES
        # ======================
        for prop in prop_list:

            query = f"""
            MATCH (t:Tire)
            WHERE t.{prop} IS NOT NULL
            RETURN DISTINCT t.{prop} AS value
            LIMIT 1000
            """

            try:
                rows = self.client.query(query)
            except:
                continue

            for r in rows:
                raw_val = str(r["value"]).strip()
                norm_val = normalize_text(raw_val)

                if not norm_val:
                    continue

                self.data.append({
                    "value": norm_val,
                    "raw_value": raw_val,
                    "column": prop
                })

        # ======================
        # SAVE CACHE
        # ======================
        with open(CACHE_FILE, "wb") as f:
            pickle.dump({
                "data": self.data,
                "columns": self.columns
            }, f)

        print(f"✅ Loaded {len(self.data)} values from Neo4j")
        print(f"✅ Loaded {len(self.columns)} properties")
        print("💾 Saved cache")


# =========================
# TEST
# =========================
if __name__ == "__main__":
    store = ValueStore()
    store.build()

    print("\n=== SAMPLE ===")
    for item in store.data[:10]:
        print(item)