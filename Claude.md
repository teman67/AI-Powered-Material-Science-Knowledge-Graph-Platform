# AI-Powered Material Science Knowledge Graph Platform

## Full Implementation Guide for AI Coding Agents

---

# 1. Project Overview

## Goal

Build a full-stack AI platform that:

1. Accepts material science papers (PDFs)
2. Extracts scientific knowledge
3. Maps extracted information to the PMDcore ontology
4. Generates RDF triples
5. Stores data in a Knowledge Graph
6. Performs semantic search using RAG
7. Answers scientific questions using LLMs
8. Visualizes relationships between materials, properties, and processes

---

# 2. Main Features

## Core Features

- PDF Upload
- Scientific Text Extraction
- Chunking Pipeline
- Embedding Generation
- Vector Search
- LLM-based Question Answering
- Ontology-aware Entity Extraction
- RDF Triple Generation
- SHACL Validation
- Knowledge Graph Visualization
- Authentication
- Async Processing
- API Endpoints
- Graph-based Retrieval

---

# 3. Target Architecture

```text
Frontend (Next.js)
        |
        v
FastAPI Backend
        |
        +----------------------+
        |                      |
        v                      v
PostgreSQL + pgvector     Neo4j / GraphDB
        |                      |
        v                      v
Vector Retrieval         RDF Knowledge Graph
        |
        v
LLM + RAG Pipeline
```

---

# 4. Recommended Tech Stack

## Backend

- FastAPI
- Python 3.12

## Frontend

- Next.js
- TypeScript
- TailwindCSS

## Databases

### Relational Database

- PostgreSQL

### Vector Database

- pgvector

### Knowledge Graph

- Neo4j
- GraphDB

## AI / NLP

- LangChain
- LlamaIndex
- sentence-transformers
- Instructor Embeddings
- spaCy
- SciBERT

## RDF / Ontology

- rdflib
- pySHACL
- owlready2

## Queue System

- Celery
- Redis

## DevOps

- Docker
- Docker Compose
- GitHub Actions

---

# 5. Folder Structure

```text
project-root/
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── services/
│   │   ├── models/
│   │   ├── ontologies/
│   │   ├── rdf/
│   │   ├── rag/
│   │   ├── extraction/
│   │   ├── graph/
│   │   ├── embeddings/
│   │   ├── tasks/
│   │   └── main.py
│   │
│   ├── tests/
│   └── requirements.txt
│
├── frontend/
│
├── docker/
│
├── docs/
│
└── docker-compose.yml
```

---

# 6. PMDcore Ontology Integration

## Ontology Source

Use PMDcore ontology as the primary semantic schema.

## Required Tasks

### Load Ontology

- Load PMDcore OWL/Turtle files
- Parse ontology classes
- Parse object properties
- Parse data properties

### Store Ontology Metadata

Create internal mappings:

```python
{
  "Material": "pmd:Material",
  "Process": "pmd:Process",
  "Property": "pmd:Property"
}
```

### Ontology Matching

Map extracted entities to PMDcore concepts.

### Example

```text
"bandgap" -> pmd:ElectricalProperty
"conductivity" -> pmd:TransportProperty
```

---

# 7. PDF Processing Pipeline

## Step 1 — Upload PDF

Create endpoint:

```http
POST /documents/upload
```

### Requirements

- Accept PDF files
- Store metadata
- Save file locally or object storage

---

## Step 2 — Extract Text

Use:

- PyMuPDF
- pdfplumber

Extract:

- Title
- Abstract
- Sections
- References

---

## Step 3 — Clean Text

Remove:

- Broken lines
- References
- Headers/footers
- Figure captions

---

## Step 4 — Chunking

### Chunk Size

```text
800-1200 tokens
```

### Overlap

```text
100-200 tokens
```

Store chunks in PostgreSQL.

---

# 8. Embedding Pipeline

## Embedding Model

Recommended:

```text
BAAI/bge-large-en
```

Alternative:

```text
hkunlp/instructor-xl
```

---

## Generate Embeddings

For every chunk:

```python
embedding = model.encode(chunk)
```

Store vectors in pgvector.

---

# 9. Entity Extraction Pipeline

## Goal

Extract:

- Materials
- Properties
- Units
- Processes
- Crystal structures
- Applications

---

## Example

### Input

```text
MoS2 exhibits a direct bandgap of 1.8 eV.
```

### Output

```json
{
  "material": "MoS2",
  "property": "bandgap",
  "value": "1.8",
  "unit": "eV"
}
```

---

## Extraction Methods

### Hybrid Approach

Combine:

- Rule-based extraction
- spaCy NER
- SciBERT
- LLM extraction

---

# 10. RDF Triple Generation

## Goal

Convert extracted knowledge into RDF.

---

## Example RDF

```ttl
@prefix pmd: <http://example.org/pmd#> .

:MoS2 rdf:type pmd:Material .
:MoS2 pmd:hasBandgap "1.8"^^xsd:float .
:MoS2 pmd:hasApplication :Nanoelectronics .
```

---

## Requirements

- Generate valid RDF
- Use PMDcore classes
- Use PMDcore predicates
- Support Turtle serialization

---

# 11. SHACL Validation

## Goal

Validate RDF correctness.

Use:

- pySHACL

---

## Example Shape

```ttl
pmd:MaterialShape
    a sh:NodeShape ;
    sh:targetClass pmd:Material ;
    sh:property [
        sh:path pmd:hasBandgap ;
        sh:datatype xsd:float ;
    ] .
```

---

# 12. Knowledge Graph Storage

## Recommended

Use Neo4j.

---

## Requirements

Store:

- Materials
- Properties
- Processes
- Applications
- Relationships

---

## Example Relationship

```text
(MoS2)-[:HAS_PROPERTY]->(Bandgap)
```

---

# 13. RAG Pipeline

## User Question Flow

1. User asks question
2. Query embedding generated
3. Similar chunks retrieved
4. Graph retrieval executed
5. Context assembled
6. LLM generates final answer

---

# 14. Hybrid Retrieval

## Combine

### Semantic Retrieval

Using pgvector

AND

### Graph Retrieval

Using Neo4j queries

---

## Example

### Question

```text
Which materials have high thermal conductivity?
```

### System Actions

- Retrieve semantic chunks
- Retrieve graph relations
- Merge contexts
- Send to LLM

---

# 15. GraphRAG

## Advanced Goal

Augment RAG with graph traversal.

---

## Example Traversal

```text
Material -> Property -> Application
```

Use graph relationships as additional context.

---

# 16. Backend API Design

# Authentication

## Endpoints

```http
POST /auth/register
POST /auth/login
```

Use JWT authentication.

---

# Documents

```http
POST /documents/upload
GET /documents/{id}
```

---

# Chat

```http
POST /chat/query
```

---

# Graph

```http
GET /graph/materials
GET /graph/relations
```

---

# RDF

```http
GET /rdf/export/{document_id}
```

---

# 17. Async Processing

## Use Celery

Background tasks:

- PDF parsing
- Embedding generation
- RDF generation
- Graph insertion

---

# 18. Frontend Requirements

## Pages

### Dashboard

- Uploaded papers
- Statistics

### Chat Interface

- Scientific QA

### Graph Visualization

- Interactive graph

### RDF Viewer

- Display triples

---

# 19. Graph Visualization

## Recommended Libraries

- Cytoscape.js
- React Flow

---

## Features

- Zoom
- Search nodes
- Filter relationships
- Expand neighbors

---

# 20. Database Schema

## PostgreSQL Tables

### documents

```sql
CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    title TEXT,
    authors TEXT,
    abstract TEXT,
    upload_date TIMESTAMP
);
```

### chunks

```sql
CREATE TABLE chunks (
    id SERIAL PRIMARY KEY,
    document_id INTEGER,
    content TEXT,
    embedding VECTOR(1024)
);
```

### extracted_entities

```sql
CREATE TABLE extracted_entities (
    id SERIAL PRIMARY KEY,
    document_id INTEGER,
    entity_type TEXT,
    entity_value TEXT,
    ontology_mapping TEXT
);
```

---

# 21. Docker Setup

## Services

- backend
- frontend
- postgres
- redis
- neo4j

---

# 22. CI/CD

## GitHub Actions Pipeline

Pipeline should:

- Run tests
- Run linting
- Build Docker images
- Deploy automatically

---

# 23. Testing Requirements

## Unit Tests

Test:

- RDF generation
- Entity extraction
- Embedding pipeline

---

## Integration Tests

Test:

- Upload pipeline
- RAG pipeline
- Graph insertion

---

# 24. Monitoring

## Add

- Logging
- Error tracking
- Request tracing

Recommended:

- Prometheus
- Grafana

---

# 25. Security Requirements

- JWT authentication
- Rate limiting
- File validation
- Secure API keys
- CORS configuration

---

# 26. MVP Milestones

## Phase 1

- PDF upload
- Text extraction
- Chunking
- Embeddings
- Basic RAG

---

## Phase 2

- Entity extraction
- RDF generation
- PMDcore integration

---

## Phase 3

- Knowledge graph
- Graph visualization
- GraphRAG

---

## Phase 4

- Authentication
- Async processing
- Deployment
- CI/CD

---

# 27. Advanced Features

## Future Improvements

- Multi-agent workflows
- Autonomous ontology refinement
- Fine-tuned material science LLM
- Scientific reasoning engine
- Cross-paper knowledge linking
- Recommendation system

---

# 28. Recommended LLM Prompts

## Entity Extraction Prompt

```text
Extract material science entities from the following text.

Return:
- material
- property
- value
- unit
- application
```

---

## RDF Generation Prompt

```text
Convert the extracted entities into RDF triples using PMDcore ontology.
```

---

# 29. Expected Final Result

The platform should allow users to:

- Upload papers
- Query scientific knowledge
- Explore relationships
- Generate RDF automatically
- Validate semantic correctness
- Use ontology-aware AI search

---

# 30. Final Goal

Build a production-grade AI scientific knowledge platform combining:

- AI Engineering
- RAG
- Knowledge Graphs
- Ontologies
- RDF/SHACL
- Scientific NLP
- Backend Engineering
- Graph AI
- DevOps