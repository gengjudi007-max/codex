# Production Roadmap for Newsroom OS

This document tracks the next engineering phase required to turn the local Newsroom OS into a production-grade, cloud-running, multi-user real estate financial newsroom platform.

## 1. Queue and Event Streaming

### Current

- Runtime queue uses local `asyncio.PriorityQueue`.
- Good for local smoke tests and single-process execution.

### Target

- Redis for lightweight task queue and cache.
- Kafka or Redpanda for event streaming, connector events, alert events, and long-running newsroom history.

### Milestones

1. Add Redis connection settings and queue abstraction.
2. Add event envelope schema.
3. Add Kafka/Redpanda adapter.
4. Keep asyncio runtime as local fallback.

---

## 2. PostgreSQL Persistence

### Current

- SQLite is the default persistence layer.
- Good for local development and single-user mode.

### Target

- PostgreSQL for production.
- SQLAlchemy or equivalent repository abstraction.
- Migration tool such as Alembic.

### Milestones

1. Introduce database URL config.
2. Add repository abstraction over SQLite/Postgres.
3. Add Postgres schema migration.
4. Add connection pooling.

---

## 3. Distributed Workers

### Current

- Single-process workers in `async_runtime.py`.

### Target

- Worker service for connectors.
- Worker service for OCR/PDF parsing.
- Worker service for intelligence synthesis.
- Worker service for publishing/package export.

### Milestones

1. Split runtime tasks into worker categories.
2. Add worker heartbeat.
3. Add retry/dead-letter queue.
4. Add worker metrics.

---

## 4. Web UI

### Current

- Control center returns JSON payload.

### Target

- Web dashboard for:
  - Live control center
  - Alerts
  - Topic pool
  - Assignments
  - Claims/fact-check queue
  - Knowledge graph explorer
  - Publishing board

### Milestones

1. Add FastAPI API layer.
2. Add `/health`, `/control-center`, `/alerts`, `/assignments`, `/publishing`, `/graph` endpoints.
3. Add frontend scaffold.
4. Add role-based access.

---

## 5. OCR / PDF Pipeline

### Current

- Basic PDF parser through `pypdf`.

### Target

- Robust OCR and table extraction.
- Support scanned PDFs, annual reports, bond prospectuses, land notices.

### Milestones

1. Add PDF job model.
2. Add OCR adapter interface.
3. Add table extraction adapter.
4. Add parser confidence and human verification queue.

---

## 6. Real Exchange Connectors and Anti-bot Adaptation

### Current

- Generic HTTP connector framework.

### Target

- Dedicated connectors for:
  - HKEX
  - SSE
  - SZSE
  - Company IR pages
  - Natural resources / land transaction sites
  - Bond prospectus sources

### Milestones

1. Build connector contract and fixtures.
2. Add per-source rate limits.
3. Add retries, backoff, user-agent, cache, and checksum diff.
4. Add manual review for captcha/protected pages.

---

## 7. Vector Database and Embedding Retrieval

### Current

- SQLite keyword retrieval and knowledge graph.

### Target

- Embedding retrieval for long-form reports, annual reports, policies, interviews, and historical articles.

### Milestones

1. Add embedding provider abstraction.
2. Add vector store interface.
3. Support pgvector or Qdrant/Milvus.
4. Add hybrid retrieval: keyword + vector + graph.

---

## 8. Multi-user Permissions

### Current

- Single-user local mode.

### Target

- Roles:
  - Reporter
  - Editor
  - Fact checker
  - Legal reviewer
  - Chief editor
  - Admin

### Milestones

1. Add user and role schema.
2. Add auth layer.
3. Add permission checks around assignment, verification, approval, and publishing.
4. Add audit log.

---

## 9. CMS Publishing Interface

### Current

- Publishing OS packages article output locally.

### Target

- Connect to actual CMS or export formats.

### Milestones

1. Add CMS adapter interface.
2. Add local markdown/html/json export.
3. Add approval gate enforcement before external publish.
4. Add post-publication correction tracking.

---

## 10. Docker / Kubernetes / Cloud Runtime

### Current

- Local Python package.

### Target

- Docker Compose for local production-like stack.
- Kubernetes deployment for cloud.

### Milestones

1. Add Dockerfile.
2. Add docker-compose with app, Postgres, Redis, Redpanda optional.
3. Add environment variable config.
4. Add K8s manifests or Helm chart.
5. Add cloud deployment guide.

---

## Suggested Implementation Order

1. Docker Compose + environment config.
2. Postgres-compatible persistence abstraction.
3. Redis queue abstraction.
4. FastAPI control-center API.
5. Worker split.
6. OCR/PDF pipeline.
7. Vector retrieval.
8. Real connectors.
9. Multi-user permissions.
10. CMS publishing.
11. K8s/cloud deployment.
