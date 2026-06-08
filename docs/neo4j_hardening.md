Neo4j Hardening & Migration
===========================

Environment variables (add to deployment env or .env; never commit secrets):

- `NEO4J_URI` (default `neo4j://127.0.0.1:7687`) — use `neo4j+s://` for TLS.
- `NEO4J_USER` (default `neo4j`)
- `NEO4J_PASSWORD` (no default; required in production)
- `NEO4J_MAX_RETRIES` (default `2`)
- `NEO4J_QUERY_TIMEOUT` (seconds, default `30`)
- `NEO4J_MAX_CONN_LIFETIME` (seconds, default `3600`)

Quick migration steps:

1. Rotate any exposed credentials and remove them from `config/settings.py`.
2. Set the required environment variables in your deployment/CI.
3. Ensure Neo4j is reachable and `NEO4J_URI` uses secure scheme (neo4j+s://).
4. Run the health-check helper in `graph_rag_enterprise.db.neo4j_client.Neo4jClient.check_indexes()` on startup; add CI check to fail if critical indexes missing.
5. Update callers that built Cypher by string concatenation to pass `params` into `Neo4jClient.query(cypher, params=...)`.
6. Confirm logging/metrics are configured (module logs and `infra.metrics` integration) and secrets are not printed.

Notes:
- The repo now reads Neo4j credentials from environment variables; do not reintroduce hardcoded secrets.
- Tests in `graph_rag_enterprise/tests/test_neo4j_client.py` mock the driver to validate behavior locally.
