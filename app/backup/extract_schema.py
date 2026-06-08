# app/extract_schema.py

from neo4j import GraphDatabase
import json


class SchemaExtractor:

    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def get_labels(self):
        query = "CALL db.labels()"
        with self.driver.session() as session:
            result = session.run(query)
            return [r["label"] for r in result]

    def get_relationships(self):
        query = "CALL db.relationshipTypes()"
        with self.driver.session() as session:
            result = session.run(query)
            return [r["relationshipType"] for r in result]

    def get_node_properties(self):
        query = """
        MATCH (n)
        UNWIND labels(n) AS label
        RETURN label, keys(n) AS props
        """
        data = {}

        with self.driver.session() as session:
            result = session.run(query)

            for r in result:
                label = r["label"]
                props = r["props"]

                data.setdefault(label, set()).update(props)

        # convert set → list
        return {k: list(v) for k, v in data.items()}

    def get_graph_structure(self):
        query = """
        MATCH (a)-[r]->(b)
        RETURN DISTINCT labels(a)[0] AS from_node,
                        type(r) AS rel,
                        labels(b)[0] AS to_node
        """
        rels = []

        with self.driver.session() as session:
            result = session.run(query)

            for r in result:
                rels.append({
                    "from": r["from_node"],
                    "rel": r["rel"],
                    "to": r["to_node"]
                })

        return rels

    def extract_all(self):

        schema = {
            "nodes": self.get_labels(),
            "relationships": self.get_relationships(),
            "properties": self.get_node_properties(),
            "graph": self.get_graph_structure()
        }

        print("\n=== GRAPH SCHEMA ===")
        print(json.dumps(schema, indent=2, ensure_ascii=False))

        # 🔥 save ra file
        with open("graph_schema.json", "w", encoding="utf-8") as f:
            json.dump(schema, f, indent=2, ensure_ascii=False)

        print("\n✅ Saved to graph_schema.json")

        return schema


if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    load_dotenv()

    extractor = SchemaExtractor(
        uri=os.environ.get("NEO4J_URI", "bolt://localhost:7687").replace("neo4j://", "bolt://"),
        user=os.environ.get("NEO4J_USER", "neo4j"),
        password=os.environ.get("NEO4J_PASSWORD", "")
    )

    extractor.extract_all()
    extractor.close()