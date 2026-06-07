# Tracing (OpenTelemetry)

This project supports tracing via OpenTelemetry Collector (OTLP) or local console exporter.

Environment variables supported:

- `ENABLE_OTEL` (true|false) — enable tracing at FastAPI startup. Default: false in CI/tests.
- `OTEL_EXPORTER_OTLP_ENDPOINT` — OTLP HTTP exporter endpoint (e.g. `http://otel-collector:4318/v1/traces`).
- `OTEL_API_KEY` — optional API key; when set we'll add `Authorization: Bearer <key>` to OTLP requests.
- `OTEL_EXPORTER_OTLP_HEADERS` — optional comma-separated headers `k1=v1,k2=v2` to send to OTLP.
- `OTEL_SAMPLE_PROB` — optional probability sampler (0.0-1.0). Example `0.05` for 5% sampling.

Notes:
- Tracing is only initialized during FastAPI `startup` to prevent background threads during test collection.
- CI workflow runs with `ENABLE_OTEL=false` to avoid external dependencies.

Collector example (docker-compose) should expose an OTLP HTTP receiver and Prometheus exporter. See `infra/otel-collector-config.yaml`.
