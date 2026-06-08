import sys
import types
import os


def make_fake_opentelemetry(with_otlp=True):
    # top-level package
    top = types.ModuleType("opentelemetry")
    # trace module with set_tracer_provider
    trace_mod = types.SimpleNamespace(set_tracer_provider=lambda p: None)
    top.trace = trace_mod

    # Resource
    resources_mod = types.ModuleType("opentelemetry.sdk.resources")
    class Resource:
        @staticmethod
        def create(d):
            return d
    resources_mod.Resource = Resource

    # TracerProvider and SDK trace module
    sdk_trace_mod = types.ModuleType("opentelemetry.sdk.trace")
    class TracerProvider:
        def __init__(self, resource=None, sampler=None):
            self._resource = resource
        def add_span_processor(self, proc):
            self._proc = proc
    sdk_trace_mod.TracerProvider = TracerProvider

    # export module
    export_mod = types.ModuleType("opentelemetry.sdk.trace.export")
    class SpanExportResult:
        SUCCESS = 0
    class ConsoleSpanExporter:
        def export(self, spans):
            return SpanExportResult.SUCCESS
    class BatchSpanProcessor:
        def __init__(self, exporter):
            self.exporter = exporter
    export_mod.SpanExportResult = SpanExportResult
    export_mod.ConsoleSpanExporter = ConsoleSpanExporter
    export_mod.BatchSpanProcessor = BatchSpanProcessor

    # OTLP exporter module (may be missing)
    otlp_mod = types.ModuleType("opentelemetry.exporter.otlp.proto.http.trace_exporter")
    if with_otlp:
        class OTLPSpanExporter:
            def __init__(self, endpoint=None, headers=None):
                self.endpoint = endpoint
                self.headers = headers
        otlp_mod.OTLPSpanExporter = OTLPSpanExporter
    else:
        otlp_mod = None

    # instrumentation.fastapi
    instr_fastapi = types.ModuleType("opentelemetry.instrumentation.fastapi")
    class FastAPIInstrumentor:
        @staticmethod
        def instrument_app(app):
            return None
    instr_fastapi.FastAPIInstrumentor = FastAPIInstrumentor

    fake_pkg = {
        "opentelemetry": top,
        "opentelemetry.trace": trace_mod,
        "opentelemetry.instrumentation.fastapi": instr_fastapi,
        "opentelemetry.sdk.resources": resources_mod,
        "opentelemetry.sdk.trace": sdk_trace_mod,
        "opentelemetry.sdk.trace.export": export_mod,
        "opentelemetry.exporter.otlp.proto.http.trace_exporter": otlp_mod,
    }

    return fake_pkg


def test_init_tracing_without_otlp(monkeypatch):
    # Inject fake opentelemetry where OTLP exporter is absent
    fake = make_fake_opentelemetry(with_otlp=False)
    for name, module in fake.items():
        if module is None:
            # ensure import will fail
            monkeypatch.setitem(sys.modules, name, None)
        else:
            monkeypatch.setitem(sys.modules, name, module)

    # import the function under test
    from infra.tracing import init_tracing

    # should return False (no opentelemetry available) or True but not raise
    res = init_tracing()
    assert res in (False, True)


def test_init_tracing_with_otlp_and_headers(monkeypatch):
    fake = make_fake_opentelemetry(with_otlp=True)
    for name, module in fake.items():
        if module is None:
            monkeypatch.setitem(sys.modules, name, None)
        else:
            monkeypatch.setitem(sys.modules, name, module)

    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://otel:4318/v1/traces")
    monkeypatch.setenv("OTEL_API_KEY", "abc123")

    from infra.tracing import init_tracing
    res = init_tracing()
    assert res is True
