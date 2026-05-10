# AI-Powered-Material-Science-Knowledge-Graph-Platform

Initial scaffold for a full-stack AI platform that ingests material science PDFs, builds an ontology-aware knowledge graph, and supports hybrid RAG question answering.

## Current status

- Backend: auth, upload/chunk/embed pipeline, RDF export, GraphRAG retrieval, Celery processing, request tracing, Prometheus metrics
- Frontend: Dashboard, Chat, Graph View, RDF Viewer (secured token session)
- CI: backend/frontend lint + test/build workflows and GHCR image publish workflow
- Observability stack: Prometheus + Grafana services in Docker Compose

## Quick start

1. Copy `.env.example` to `.env`
2. Run:

```bash
docker compose up --build
```

3. Open:

- Frontend: http://localhost:3000
- Backend health: http://localhost:8000/health
- Backend metrics: http://localhost:8000/metrics
- Neo4j Browser: http://localhost:7474
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3001

## Project roadmap

See `IMPLEMENTATION_PLAN.md` for phased implementation details.
