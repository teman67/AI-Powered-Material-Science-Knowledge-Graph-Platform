# AI-Powered Material Science Knowledge Graph Platform

## Implementation Plan (MVP to Production)

This plan translates the product vision in Claude.md into an execution roadmap with concrete milestones, technical decisions, and delivery checkpoints.

## Progress snapshot

- Completed: Phase 0 scaffold (backend app shell, frontend app shell, docker-compose, environment templates, health endpoint)
- Completed in Phase 1 (backend): document upload endpoint, PDF extraction, cleaning/chunking, vector storage schema, semantic chat query endpoint
- Completed in Phase 2 (backend foundation): entity extraction service, PMDcore mapping service, RDF generation, SHACL validation, and `/rdf/export/{document_id}` endpoint
- Completed in Phase 3 (backend foundation): Neo4j graph ingestion service, graph read endpoints (`/graph/materials`, `/graph/relations`), and hybrid chat retrieval with graph evidence
- Completed in Phase 3 hardening: intent-aware GraphRAG ranking over graph facts using relation intent and lexical relevance scoring
- Completed in Phase 4 (backend foundation): JWT authentication with `/auth/register` and `/auth/login`, secure password hashing, and token issuance
- Completed in Phase 4 hardening (backend): auth guards applied to protected endpoints and basic API rate limiting middleware
- Completed in Phase 4 hardening (backend): Celery async document processing flow with Redis broker, worker service, and queue dispatch fallback
- Completed in Phase 4 hardening (backend): request tracing middleware with correlation IDs and structured request logs
- Completed in Phase 4 hardening (devops): GitHub Actions backend CI workflow for dockerized pytest and image build validation
- Completed in Phase 4 (frontend): dashboard, graph view, and RDF viewer pages wired to secured backend endpoints with session token flow
- Completed in Phase 4 (frontend): secured chat page with semantic and graph citation contexts
- Completed in Phase 4 (backend/frontend): authenticated documents listing endpoint and server-backed dashboard status table
- Completed in Phase 4 hardening (backend): Prometheus metrics middleware and `/metrics` endpoint
- Completed in Phase 4 hardening (runtime): FastAPI lifespan-based startup initialization (deprecated startup event removed)
- Completed in Phase 4 hardening (devops): Prometheus + Grafana services added to Docker Compose monitoring stack
- Completed in Phase 4 hardening (devops): automated GHCR image publish workflow on main branch
- Completed in Phase 4 hardening (devops): lint coverage automation in CI (backend Ruff + frontend ESLint)
- Current focus: Phase 5 advanced capabilities backlog prioritization

## 1) Scope and Delivery Strategy

### Primary objective
Deliver an end-to-end platform that can:
1. ingest PDF papers,
2. extract and structure material science knowledge,
3. persist vectors and graph facts,
4. answer user questions using hybrid retrieval,
5. expose results in a usable web interface.

### Delivery approach
Build in vertical slices so each phase is demonstrable:
- Phase A: Upload -> extract -> chunk -> embed -> query (basic RAG)
- Phase B: Entity extraction -> ontology mapping -> RDF export
- Phase C: Graph storage + graph retrieval in QA
- Phase D: Auth, async tasks, hardening, CI/CD

## 2) Architecture Baseline

### Runtime components
- Frontend: Next.js + TypeScript + Tailwind
- Backend API: FastAPI (Python 3.12)
- Relational + vectors: PostgreSQL + pgvector
- Graph: Neo4j
- Queue: Celery + Redis
- AI/NLP: sentence-transformers + spaCy + optional LLM integration
- RDF stack: rdflib + pySHACL

### Service boundaries
- `backend/app/api`: REST endpoints and request validation
- `backend/app/services`: orchestration services
- `backend/app/extraction`: PDF/text/entity extraction
- `backend/app/embeddings`: embedding generation and vector retrieval
- `backend/app/rdf`: RDF triple generation and SHACL validation
- `backend/app/graph`: Neo4j write/read and graph retrieval
- `backend/app/rag`: context assembly and answer generation
- `backend/app/tasks`: Celery jobs

## 3) Initial Repository Buildout Plan

Create this structure first:

```text
backend/
  app/
    api/
    core/
    services/
    models/
    extraction/
    embeddings/
    rdf/
    graph/
    rag/
    tasks/
    ontologies/
    main.py
  tests/
frontend/
docker/
docs/
docker-compose.yml
```

## 4) Phased Milestones

## Phase 0: Foundation (Days 1-3)

### Goals
- Project scaffolding for backend and frontend
- Local dockerized infra up (postgres, redis, neo4j)
- Basic health endpoint and environment management

### Deliverables
- FastAPI app with `/health`
- Next.js app shell with dashboard placeholder
- `docker-compose.yml` with service networking
- `.env.example` and config loader

### Exit criteria
- All services run with one command
- Backend reachable from frontend

## Phase 1: Document Ingestion + Basic RAG (Week 1)

### Goals
- Upload PDF
- Extract and clean text
- Chunk text and store chunks
- Generate/store embeddings in pgvector
- Query endpoint returns answer from retrieved chunks

### Backend tasks
- `POST /documents/upload`
- PDF extraction (PyMuPDF first, pdfplumber fallback)
- section-aware cleaner
- token chunker (target 1000 tokens, overlap 150)
- embedding pipeline with `BAAI/bge-large-en`
- pgvector similarity search
- `POST /chat/query` (semantic retrieval only)

### Data model (minimum)
- `documents(id, title, authors, abstract, upload_date, file_path, status)`
- `chunks(id, document_id, content, embedding, section, chunk_index)`

### Exit criteria
- Uploading a PDF makes it searchable through `/chat/query`

## Phase 2: Entity Extraction + Ontology Mapping + RDF (Week 2)

### Goals
- Extract entities (material, property, value, unit, process, application)
- Map to PMDcore classes/properties
- Generate RDF triples and export Turtle
- Validate triples with SHACL

### Backend tasks
- PMDcore loader in `app/ontologies`
- hybrid extractor:
  - regex/rule patterns for property-value-unit pairs
  - spaCy NER for scientific entities
  - optional LLM fallback for low-confidence spans
- ontology mapping service
- RDF generator (`rdflib`)
- SHACL validator (`pySHACL`)
- `GET /rdf/export/{document_id}`

### Data model additions
- `extracted_entities(id, document_id, entity_type, entity_value, ontology_mapping, confidence)`
- `rdf_artifacts(id, document_id, ttl_content, is_valid, validation_report)`

### Exit criteria
- RDF export works for uploaded docs and passes baseline shape checks

## Phase 3: Knowledge Graph + Hybrid Retrieval (Week 3)

### Goals
- Persist extracted knowledge in Neo4j
- Add graph retrieval to QA pipeline
- Start GraphRAG traversal patterns

### Backend tasks
- Neo4j writer for nodes/edges:
  - `Material`, `Property`, `Process`, `Application`
  - relationships like `HAS_PROPERTY`, `PRODUCED_BY`, `USED_IN`
- graph query services
- `GET /graph/materials`, `GET /graph/relations`
- Hybrid retriever in `app/rag`:
  - vector top-k chunks
  - graph neighborhood expansion
  - context merger and citation metadata

### Exit criteria
- `/chat/query` combines semantic and graph evidence in answers

## Phase 4: Productization (Week 4)

### Goals
- auth + async processing + observability + CI/CD

### Backend tasks
- JWT auth (`/auth/register`, `/auth/login`)
- Celery tasks for upload pipeline stages
- request logging + error handling
- rate limiting and file validation

### Frontend tasks
- Dashboard: upload list + processing status + stats
- Chat page: question input + cited contexts
- Graph page: interactive graph view
- RDF page: Turtle viewer + validation status

### DevOps tasks
- GitHub Actions: lint, tests, docker build
- production-ready Dockerfiles

### Exit criteria
- Stable authenticated app with background processing and CI checks

## 5) API Contract (MVP-first)

Implement in this order:
1. `POST /documents/upload`
2. `GET /documents/{id}`
3. `POST /chat/query`
4. `GET /rdf/export/{document_id}`
5. `GET /graph/materials`
6. `GET /graph/relations`
7. `POST /auth/register`
8. `POST /auth/login`

## 6) Testing Plan

### Unit tests
- chunker boundaries and overlap
- ontology mapper deterministic mappings
- RDF serializer output shape
- SHACL validator behavior

### Integration tests
- upload -> extraction -> embeddings pipeline
- RDF generation from extracted entities
- neo4j insertion and retrieval
- chat query end-to-end (vector + graph)

### Smoke tests
- docker-compose startup
- health checks for backend, postgres, redis, neo4j

## 7) Key Risks and Mitigations

- Extraction quality risk:
  - Mitigation: rule-based baseline first, then add model-assisted extraction
- Ontology mapping ambiguity:
  - Mitigation: confidence scores + unresolved bucket + manual override table
- Cost/latency in embedding + LLM:
  - Mitigation: async pipelines, caching, and configurable model providers
- Data consistency across stores:
  - Mitigation: document status state machine and idempotent task design

## 8) Immediate Next Tasks (Start Now)

1. Scaffold backend FastAPI app and dependency management.
2. Add docker-compose for postgres, redis, neo4j, backend, frontend.
3. Implement `/health` and config module.
4. Create DB models/migrations for `documents` and `chunks`.
5. Implement `POST /documents/upload` with file validation.
6. Add PDF extraction + cleaner + chunker services.
7. Integrate embedding model and pgvector storage.
8. Implement `POST /chat/query` with semantic retrieval.
9. Create frontend upload + chat MVP pages.
10. Add baseline tests and CI workflow.

## 9) Definition of Done for MVP

MVP is done when:
- a user uploads a PDF,
- the system extracts/chunks/embeds content,
- the user asks a question and receives a contextual answer,
- extracted entities are mapped to ontology terms,
- RDF export is available and validated,
- graph relations are viewable in UI.

## 10) Suggested Execution Rhythm

- Daily: build one vertical slice and verify end-to-end.
- Every 2-3 days: integration checkpoint and bug fix pass.
- Weekly: milestone demo with measurable acceptance criteria.
