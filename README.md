# Minimal Boutique

Minimal Boutique is a testing application inspired by Google's Online Boutique. It is a microservices-based e-commerce application designed primarily to generate observability metrics and traces for analysis and profiling of a distributed system.

## Overview

The application features a modular architecture where each service mimics a specific e-commerce capability. Built using Python, Flask, and SQLAlchemy, the system uses **OpenTelemetry (OTel)** to automatically instrument traces and help evaluate distributed system performance.

### Services and Components

- **backend**: Acts as an API Gateway and Authentication service. It authenticates users, manages sessions, and routes requests to appropriate microservices.
- **products**: Manages the product catalog and handles inventory limits (transactional reserve/release of stock).
- **cart**: Manages the user's shopping cart. It operates primarily as a transient state manager and depends on the `products` service to check for live inventory and pricing via simple caching.
- **checkout**: A stateless orchestrator that validates cart items against the product catalog and establishes pending orders.
- **payment**: Simulates an external payment gateway. It interacts with the `orders` service to confirm payments and the `backend`/`cart` services to clear purchased items, introducing extra network hubs to enrich distributed traces.
- **orders**: Acts as the immutable register for persisting historical transaction and order data.
- **frontend**: A web interface for users to directly interact with the minimal boutique.
- **loadgenerator**: A Python component using the Locust framework that simulates asynchronous, non-deterministic user sessions (such as browsing the catalog, adding items to the cart, and completing checkouts). This component provides the steady and necessary traffic load to spawn telemetry traces for analysis.
- **Observability Stack**: Bundles OpenTelemetry Collector for receiving the trace events and Jaeger for visualizing the trace spans.

---

## Deployment

You can run Minimal Boutique locally using **Docker Compose** or deploy it across a **Kubernetes** cluster. Both configurations will lift the microservices, the web frontend, the simulated load generator, and the distributed tracing systems.

### Option 1: Docker Compose (Recommended for Local Dev)

A `docker-compose.yml` file is provided at the root to effortlessly spin up the environment:

1. Ensure you have Docker and Docker Compose installed.
2. From the root directory of the repository, execute:
   ```bash
   docker-compose up -d --build
   ```
3. Once running, you can access:
   - **Frontend UI:** `http://localhost:5173`
   - **Jaeger UI (Tracing Analysis):** `http://localhost:16686`

To gracefully shut down the environment:
```bash
docker-compose down
```

### Option 2: Kubernetes

A comprehensive set of manifest files is provided within the `kubernetes-manifests/` directory.

1. Ensure your local or remote Kubernetes cluster is running and `kubectl` is configured.
2. Set up the namespaces and apply the entire suite of manifestations:
   ```bash
   kubectl apply -f kubernetes-manifests/
   ```
   *(Note: The manifest descriptors provide fine-grained control for services individually like `deploy_backend.yml`, or alternatively bundled via `deploy_all.yml`. Review these carefully as some may provision components into default specific namespaces like `minimal-boutique`).*

To inspect tracing in Kubernetes, utilize `kubectl port-forward` directly mapped to your Jaeger service instances.

A pre-built set of Docker images is available on Docker Hub at https://hub.docker.com/u/momosuke07 in case you don't want to build them yourself.
