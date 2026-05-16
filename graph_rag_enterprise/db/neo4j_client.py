from neo4j import GraphDatabase
from config.settings import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD


class Neo4jClient:

    def __init__(self):
        self.driver = GraphDatabase.driver(
            NEO4J_URI,
            auth=(NEO4J_USER, NEO4J_PASSWORD)
        )

    def query(self, cypher: str):

        print("\n===== EXECUTE CYPHER =====")
        print(cypher)

        with self.driver.session() as session:
            result = session.run(cypher)
            data = [r.data() for r in result]

            print("\n===== RAW DB DATA =====")
            print(data)

            return data