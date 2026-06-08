"""Prometheus metrics initialisation (standalone).

Import once at app startup to register all metrics.
"""
try:
    from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
except Exception:
    Counter = None
    Histogram = None
    generate_latest = None
    CONTENT_TYPE_LATEST = None

# ── metric references (set after init_metrics()) ─────────────────────────────
request_counter = None
query_latency = None
pipeline_latency = None
llm_latency = None
llm_call_counter = None
neo4j_query_counter = None
neo4j_query_failures = None
retriever_matches = None
neo4j_rows = None


def init_metrics():
    """Initialise all Prometheus metrics. Call once at startup."""
    global request_counter, query_latency, pipeline_latency
    global llm_latency, llm_call_counter, retriever_matches, neo4j_rows
    global neo4j_query_counter, neo4j_query_failures

    if Counter is None:
        return False

    request_counter = Counter("grag_requests_total", "Total GraphRAG requests", ["endpoint"])
    query_latency = Histogram("grag_query_latency_seconds", "Neo4j query latency seconds")
    pipeline_latency = Histogram("grag_pipeline_latency_seconds", "Pipeline run latency seconds")
    llm_latency = Histogram("grag_llm_latency_seconds", "LLM call latency seconds")
    llm_call_counter = Counter("grag_llm_calls_total", "LLM calls", ["success"])
    retriever_matches = Counter("grag_retriever_matches_total", "Retriever match counts", ["strategy"])
    neo4j_rows = Histogram("grag_neo4j_rows_returned", "Rows returned by Neo4j query")
    neo4j_query_counter = Counter("grag_neo4j_queries_total", "Total Neo4j queries", ["success"])
    neo4j_query_failures = Counter("grag_neo4j_query_failures_total", "Neo4j query failures")
    return True


def metrics_response():
    """Return (bytes, content_type) for the /metrics endpoint."""
    if generate_latest is None:
        return None, "text/plain"
    return generate_latest(), CONTENT_TYPE_LATEST
