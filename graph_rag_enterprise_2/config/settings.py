import os
from infra.secrets import get_secret

# Read Neo4j connection info from environment or secret manager
# Example: export NEO4J_URI=neo4j://127.0.0.1:7687
NEO4J_URI = os.environ.get("NEO4J_URI", "neo4j://127.0.0.1:7687")
NEO4J_USER = os.environ.get("NEO4J_USER", "neo4j")
# Prefer secret manager resolution, fall back to env default
NEO4J_PASSWORD = get_secret("NEO4J_PASSWORD", default=os.environ.get("NEO4J_PASSWORD", ""))