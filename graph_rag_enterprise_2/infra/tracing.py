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
    """Initialize OpenTelemetry tracing. If OTLP endpoint is specified via
    `OTEL_EXPORTER_OTLP_ENDPOINT` we'll try to use OTLP exporter; otherwise
    fall back to console exporter. Instrument FastAPI app if provided.
    """
    if ot_trace is None:
        return False

    resource = Resource.create({"service.name": "graph_rag_service"})

    # Configure sampler: support a probability sampler via env var
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

    if sampler is not None:
        provider = TracerProvider(resource=resource, sampler=sampler)
    else:
        provider = TracerProvider(resource=resource)

    otlp_endpoint = None
    try:
        otlp_endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT") or os.environ.get("OTLP_ENDPOINT")
    except Exception:
        otlp_endpoint = None

    if OTLPSpanExporter is not None and otlp_endpoint:
        # Allow simple API key header via OTEL_API_KEY or OTEL_EXPORTER_OTLP_HEADERS
        headers = None
        try:
            key = os.environ.get("OTEL_API_KEY")
            if key:
                headers = {"Authorization": f"Bearer {key}"}
            else:
                hdrs = os.environ.get("OTEL_EXPORTER_OTLP_HEADERS")
                if hdrs:
                    # expected format: key1=val1,key2=val2
                    headers = {}
                    for kv in hdrs.split(','):
                        if '=' in kv:
                            k, v = kv.split('=', 1)
                            headers[k.strip()] = v.strip()
        except Exception:
            headers = None

        try:
            if headers:
                exporter = OTLPSpanExporter(endpoint=otlp_endpoint, headers=headers)
            else:
                exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
        except TypeError:
            # older OTLP exporter may not accept headers arg
            exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
    else:
        # Console exporter may fail in test harnesses where stdout is closed; wrap safely
        class SafeConsoleExporter(ConsoleSpanExporter):
            def export(self, spans):
                try:
                    return super().export(spans)
                except Exception:
                    return SpanExportResult.SUCCESS

        exporter = SafeConsoleExporter()

    processor = BatchSpanProcessor(exporter)
    provider.add_span_processor(processor)
    ot_trace.set_tracer_provider(provider)

    if app is not None:
        try:
            FastAPIInstrumentor().instrument_app(app)
        except Exception:
            pass

    return True


import time


def trace(func):
    def wrapper(*args, **kwargs):
        start = time.time()
        res = func(*args, **kwargs)
        print(f"[TRACE] {func.__name__}: {time.time()-start:.3f}s")
        return res
    return wrapper