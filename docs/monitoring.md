**Monitoring & Alerting**

- **Prometheus metrics:** the app exposes metrics at `/metrics` using `infra.metrics_prometheus.init_metrics()`.
  - Key metrics:
    - `grag_requests_total{endpoint}` — request counts
    - `grag_pipeline_latency_seconds` — pipeline latency histogram
    - `grag_neo4j_queries_total{success}` — neo4j query counts
    - `grag_neo4j_query_failures_total` — neo4j failures
    - `grag_llm_calls_total{success}` — LLM calls

- **Kubernetes Alerting:**
  - `k8s/prometheus-rules.yaml` contains sample `PrometheusRule` resources for `HighPipelineLatency`, `Neo4jQueryFailures`, `HighLLMErrorRate`, and request spikes.
  - Apply to cluster with `kubectl apply -f k8s/prometheus-rules.yaml` (requires Prometheus Operator / kube-prometheus stack).

- **Docker Compose / Local:**
  - `docker/prometheus/prometheus.yml` is a template for local Prometheus with sample scrape targets and rule path. Use it with a `prometheus` container and mount `./docker/prometheus` into `/etc/prometheus`.

- **Alertmanager:**
  - Configure Alertmanager to route critical alerts to pager/Slack/email. Example config is out of scope but typical Alertmanager config lives in `docker/alertmanager` or k8s Secret for production.

- **Grafana Dashboards:**
  - Create dashboards showing:
    - Request rate (`grag_requests_total`)
    - 95th/99th percentile pipeline latency (use `histogram_quantile` on `grag_pipeline_latency_seconds_bucket`)
    - Neo4j errors and query rates
    - FAISS index health (if surfaced as gauge)

- **Best practices:**
  - Keep `ENABLE_OTEL=false` in CI to avoid background threads.
  - Add alert runbooks for critical alerts (Neo4j down, high latency, LLM failures).

