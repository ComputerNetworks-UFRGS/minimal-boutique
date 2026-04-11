import os
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
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

def configure_telemetry(app: Flask, service_name: str):
    resource = Resource(attributes={"service.name": service_name, "service.instance.id": os.uname().nodename,})
    trace.set_tracer_provider(TracerProvider(resource=resource))
    tracer_provider = trace.get_tracer_provider()

    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[500, 502, 503, 504],
    )

    adapter = HTTPAdapter(max_retries=retry_strategy)

    http_session = requests.Session()
    http_session.mount("http://", adapter)
    http_session.mount("https://", adapter)

    exporter = OTLPSpanExporter(
        endpoint="http://collector:4321/v1/traces",
        session=http_session
    )

    span_processor = BatchSpanProcessor(exporter)
    tracer_provider.add_span_processor(span_processor)

    FlaskInstrumentor().instrument_app(app)

    RequestsInstrumentor().instrument()

    from database import db 

    with app.app_context():
        SQLAlchemyInstrumentor().instrument(engine=db.engine)

    print(f"Opentelemetry configurado com sucesso para o serviço: {service_name}")