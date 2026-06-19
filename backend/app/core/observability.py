from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

from app.core.config import Settings

# ---------------------------------------------------------------------------
# PII fields that MUST be sanitized from logs, traces, and error responses.
# C-02: email (siempre estuvo)
# C-07: dni, cuil, cbu, alias_cbu
# ---------------------------------------------------------------------------
PII_FIELDS_TO_SANITIZE: frozenset[str] = frozenset({
    "email",
    "password",
    "email_encrypted",
    "password_hash",
    "dni",
    "cuil",
    "cbu",
    "alias_cbu",
    "dni_encrypted",
    "cuil_encrypted",
    "cbu_encrypted",
    "alias_cbu_encrypted",
})


def setup_observability(app, settings: Settings) -> None:
    resource = Resource.create({"service.name": settings.otel_service_name})
    provider = TracerProvider(resource=resource)

    if settings.otel_exporter_otlp_endpoint:
        exporter = OTLPSpanExporter(endpoint=settings.otel_exporter_otlp_endpoint)
    else:
        exporter = ConsoleSpanExporter()

    processor = BatchSpanProcessor(exporter)
    provider.add_span_processor(processor)
    trace.set_tracer_provider(provider)

    FastAPIInstrumentor.instrument_app(app)
