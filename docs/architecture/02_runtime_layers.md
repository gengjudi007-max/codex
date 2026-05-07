# 02 Runtime Layers

## Connector Layer

Responsible for connecting the newsroom to the external world.

Sources include:

- HKEX
- SSE
- SZSE
- Natural resources departments
- Land transaction systems
- Bond prospectuses
- Policy documents
- Company IR pages
- Research reports

## Ingestion Layer

Normalizes all external content into unified records.

Core fields:

- source_type
- title
- content
- city
- company
- source credibility
- content hash
- diff status
- collected_at

## Persistence Layer

### Development

- SQLite

### Production

- PostgreSQL
- pgvector
- object storage

Persistent objects:

- sources
- claims
- alerts
- assignments
- graph nodes
- graph edges
- article versions
- approvals
- audit logs

## Intelligence Layer

Responsible for:

- knowledge graph updates
- anomaly detection
- trend detection
- autonomous intelligence
- strategic intelligence
- executive intelligence

## Editorial Layer

Responsible for:

- assignment workflow
- review queue
- verification queue
- publication gate
- approval chain

## Publishing Layer

Responsible for:

- article packaging
- versioning
- CMS distribution
- archive
- post-publication monitoring

## Runtime Philosophy

```text
new information
  ↓
connector event
  ↓
queue/event bus
  ↓
workers
  ↓
knowledge graph
  ↓
intelligence synthesis
  ↓
editorial workflow
  ↓
publishing
  ↓
institutional memory update
```
