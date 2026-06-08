"""OpenTelemetry tracing initialisation (standalone).

Import and call init_tracing(app) when ENABLE_OTEL is set.
"""
import os

try:
    from opentelemetry import trace as ot_trace
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter, SpanExportResult
    try:
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    except Exception:
        OTLPSpanExporter = None
except Exception:
    ot_trace = None


def init_tracing(app=None):
    """Initialise OpenTelemetry tracing with optional FastAPI instrumentation."""
    if ot_trace is None:
        return False

    resource = Resource.create({"service.name": "graph_rag_service"})

    sampler = None
    try:
        samp = os.environ.get("OTEL_SAMPLE_PROB")
        if samp is not None:
            prob = float(samp)
            if 0.0 <= prob <= 1.0:
                from opentelemetry.sdk.trace.sampling import TraceIdRatioBased
                sampler = TraceIdRatioBased(prob)
    except Exception:
        sampler = None

    provider = TracerProvider(resource=resource, sampler=sampler) if sampler else TracerProvider(resource=resource)

    otlp_endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT") or os.environ.get("OTLP_ENDPOINT")

    if OTLPSpanExporter is not None and otlp_endpoint:
        headers = None
        try:
            key = os.environ.get("OTEL_API_KEY")
            if key:
                headers = {"Authorization": f"Bearer {key}"}
            else:
                hdrs = os.environ.get("OTEL_EXPORTER_OTLP_HEADERS")
                if hdrs:
                    headers = {}
                    for kv in hdrs.split(","):
                        if "=" in kv:
                            k, v = kv.split("=", 1)
                            headers[k.strip()] = v.strip()
        except Exception:
            headers = None

        try:
            exporter = OTLPSpanExporter(endpoint=otlp_endpoint, headers=headers) if headers else OTLPSpanExporter(endpoint=otlp_endpoint)
        except TypeError:
            exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
    else:
        class SafeConsoleExporter(ConsoleSpanExporter):
            def export(self, spans):
                try:
                    return super().export(spans)
                except Exception:
                    return SpanExportResult.SUCCESS

        exporter = SafeConsoleExporter()

    provider.add_span_processor(BatchSpanProcessor(exporter))
    ot_trace.set_tracer_provider(provider)

    if app is not None:
        try:
            FastAPIInstrumentor().instrument_app(app)
        except Exception:
            pass

    return True
