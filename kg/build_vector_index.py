# kg/build_vector_index.py

from app.neo4j_conn import Neo4jConnection
from pre_proces.embeddings import embed_text


def build_embedding_text(tire):
    return f"""
    size: {tire.get('size')}
    brand: {tire.get('brand')}
    pattern: {tire.get('kieu_hoa')}
    type: {tire.get('nhom_lop')}
    load: {tire.get('tai_trong_lon_nhat')}
    pressure: {tire.get('noi_ap_tieu_chuan')}
    """


def main():
    conn = Neo4jConnection()

    tires = conn.run_query("MATCH (t:Tire) RETURN t")

    for r in tires:
        t = r["t"]
        text = build_embedding_text(t)
        embedding = embed_text(text)

        conn.run_query("""
        MATCH (t:Tire {size: $size, brand: $brand})
        SET t.embedding = $embedding
        """, {
            "size": t["size"],
            "brand": t["brand"],
            "embedding": embedding
        })

    # create vector index
    conn.run_query("""
    CREATE VECTOR INDEX tire_embedding_index
    FOR (t:Tire) ON (t.embedding)
    OPTIONS {
        indexConfig: {
            `vector.dimensions`: 1536,
            `vector.similarity_function`: 'cosine'
        }
    }
    """)

    print("Vector index created!")


if __name__ == "__main__":
    main()