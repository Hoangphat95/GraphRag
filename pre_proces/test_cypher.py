# app/test_cypher.py

from value_mapper import ValueMapper
from cypher_builder import CypherBuilder
from neo4j import GraphDatabase

mapper = ValueMapper()
builder = CypherBuilder()

# =========================
# Neo4j CONNECT
# =========================
URI = "bolt://localhost:7687"
AUTH = ("neo4j", "tiredrc2026")  # đổi password của bạn

driver = GraphDatabase.driver(URI, auth=AUTH)


def run_cypher(query):
    """Execute Cypher and return results"""
    with driver.session() as session:
        result = session.run(query)
        return [record.data() for record in result]


# =========================
# TEST QUERIES (DATA-BASED ONLY)
# =========================
queries = [
    "lốp 110/70-14 có tốc độ tối đa bao nhiêu",
    "lốp 110/70-14 chịu tải bao nhiêu",
    "lốp 110/70-14 áp suất bao nhiêu",
    "lốp 110/70-14 có đường kính vành bao nhiêu",

    "lốp 90/80-17 có tốc độ tối đa bao nhiêu",
    "lốp 90/80-17 chịu tải bao nhiêu",
    "lốp 2.75-17 áp suất bao nhiêu",

    "lốp 110/70-14 thuộc hãng nào",
    "lốp 110/70-14 có pattern gì",

    "lốp 70/90-14 dùng ruột hay không",
    "lốp 16x1.75 thuộc loại gì",
    
    "Cho tôi các thông số của lốp 70/90-14"
]


for q in queries:
    print("\n" + "=" * 40)
    print("QUERY:", q)

    # =========================
    # 1. MAP QUERY
    # =========================
    mapped = mapper.map_query(q)
    print("MAPPED:", mapped)

    # =========================
    # 2. BUILD CYPHER
    # =========================
    try:
        cypher = builder.build(mapped, q)

        print("\nCYPHER:")
        print(cypher)

        # =========================
        # 3. RUN ON NEO4J
        # =========================
        results = run_cypher(cypher)

        print("\nRESULT:")
        if results:
            for r in results:
                print(r)
        else:
            print("No data found")

    except Exception as e:
        print("ERROR:", e)