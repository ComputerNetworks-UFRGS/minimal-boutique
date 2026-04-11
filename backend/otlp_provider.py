from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace.export import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.trace.sampling import TraceIdRationBased
import os



def traces_provider(resource):
    traces_endpoint = os.getenv("TRACES_ENDPOINT", "http://collector:4321/v1/traces")

    provider = TracerProvider(resource=resource, sampler=TraceIdRationBased(1.0))
    processor = BatchSpanProcessor(OTLPSpanExporter(endpoint=traces_endpoint))
    provider.add_span_processor(processor)
    trace.set_tracer_provider(provider)

    return trace.get_tracer(provider)
