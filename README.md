# AI-Powered-Material-Science-Knowledge-Graph-Platform

Initial scaffold for a full-stack AI platform that ingests material science PDFs, builds an ontology-aware knowledge graph, and supports hybrid RAG question answering.

## Current status

- Phase 0 scaffold complete
- FastAPI backend with `GET /health`
- Next.js frontend shell
- Docker Compose services: backend, frontend, postgres+pgvector, redis, neo4j

## Quick start

1. Copy `.env.example` to `.env`
2. Run:

```bash
docker compose up --build
```

3. Open:

- Frontend: http://localhost:3000
- Backend health: http://localhost:8000/health
- Neo4j Browser: http://localhost:7474

## Project roadmap

See `IMPLEMENTATION_PLAN.md` for phased implementation details.
