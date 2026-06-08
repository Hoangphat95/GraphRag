OpenTelemetry Collector (local tracing)

This repo includes a pre-configured OpenTelemetry Collector for local development.

Start the collector with docker-compose:

```bash
docker-compose up -d otel-collector
```

Environment vars for the service to export traces to the collector (HTTP OTLP):

- `OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318/v1/traces`
- `OTEL_EXPORTER_OTLP_METRICS_ENDPOINT=http://localhost:4318/v1/metrics`

Usage notes:
- The collector is configured to log traces (for local debugging) and expose metrics on `:8889` for Prometheus scraping.
- To see traces in a UI, configure an exporter (Jaeger/Tempo) in `infra/otel-collector-config.yaml` and restart the collector.
