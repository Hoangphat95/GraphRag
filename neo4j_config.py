import os
from neo4j import GraphDatabase

class Neo4jConnection:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
    
    def run_query(self, query, parameters=None):
        """Run a Cypher query and return results"""
        session = self.driver.session()
        try:
            result = session.run(query, parameters or {})
            data = result.data()
            return data
        except Exception as e:
            print(f"Neo4j query error: {e}")
            return []
        finally:
            session.close()
    
    def close(self):
        self.driver.close()
