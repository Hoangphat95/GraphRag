try:
    from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
except Exception:
    Counter = None
    Histogram = None
    generate_latest = None
    CONTENT_TYPE_LATEST = None

request_counter = None
query_latency = None
neo4j_query_counter = None
neo4j_query_failures = None
llm_call_counter = None
llm_latency = None
pipeline_latency = None
retriever_matches = None
neo4j_rows = None

def init_metrics():
    global request_counter, query_latency
    if Counter is None:
        return False
    request_counter = Counter('grag_requests_total', 'Total GraphRAG requests', ['endpoint'])
    query_latency = Histogram('grag_query_latency_seconds', 'Neo4j query latency seconds')
    # track request-level latency
    global pipeline_latency, llm_latency
    pipeline_latency = Histogram('grag_pipeline_latency_seconds', 'Pipeline run latency seconds')
    llm_latency = Histogram('grag_llm_latency_seconds', 'LLM call latency seconds')
    # retriever and LLM counters
    global llm_call_counter, retriever_matches, neo4j_rows
    llm_call_counter = Counter('grag_llm_calls_total', 'LLM calls', ['success'])
    retriever_matches = Counter('grag_retriever_matches_total', 'Retriever match counts', ['strategy'])
    neo4j_rows = Histogram('grag_neo4j_rows_returned', 'Rows returned by Neo4j query')
    # Neo4j specific metrics
    global neo4j_query_counter, neo4j_query_failures
    neo4j_query_counter = Counter('grag_neo4j_queries_total', 'Total Neo4j queries', ['success'])
    neo4j_query_failures = Counter('grag_neo4j_query_failures_total', 'Neo4j query failures')
    return True

def metrics_response():
    if generate_latest is None:
        return None, 'text/plain'
    data = generate_latest()
    return data, CONTENT_TYPE_LATEST
