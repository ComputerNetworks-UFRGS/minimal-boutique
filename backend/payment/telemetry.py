import os
import platform
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from flask import Flask
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor

def configure_telemetry(app: Flask, service_name: str):
    # Identificador da instância compatível com Windows/Linux
    instance_id = platform.node()

    # Configura o recurso do serviço
    resource = Resource(attributes={
        "service.name": service_name,
        "service.instance.id": instance_id,
    })

    # Configura o tracer provider
    tracer_provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(tracer_provider)

    # Configura retry para o OTLP exporter
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[500, 502, 503, 504],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)

    http_session = requests.Session()
    http_session.mount("http://", adapter)
    http_session.mount("https://", adapter)

    # Configura o exportador OTLP (HTTP)
    exporter = OTLPSpanExporter(
        endpoint="http://collector:4321/v1/traces",
        session=http_session
    )

    span_processor = BatchSpanProcessor(exporter)
    tracer_provider.add_span_processor(span_processor)

    # Instrumenta Flask e Requests
    FlaskInstrumentor().instrument_app(app)
    RequestsInstrumentor().instrument()

    print(f"OpenTelemetry configurado com sucesso para o serviço: {service_name}")
