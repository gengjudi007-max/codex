# 04 Graph and Vector Retrieval

## Knowledge Graph

The production system should persist and query relationships between:

- companies
- cities
- policies
- risks
- events
- claims
- sources
- articles
- assignments

## Core Graph Questions

The graph layer should help answer:

1. Which companies are linked to a specific city risk?
2. Which policy terms affected a company or market narrative?
3. Which claims are supported by which sources?
4. Which events belong to the same risk propagation chain?
5. Which editorial decisions were made from similar historical signals?

## Vector Retrieval

The production target should support semantic retrieval over:

- annual reports
- bond prospectuses
- policy documents
- land notices
- interview notes
- historical articles
- research reports

## Recommended Stack

Phase 1:

- PostgreSQL + pgvector

Phase 2:

- Qdrant or Milvus if scale requires dedicated vector infrastructure

## Hybrid Retrieval

Final retrieval should combine:

```text
keyword search
+ vector search
+ graph traversal
+ timeline query
+ claim/evidence lookup
```

## Editorial Use Cases

- Retrieve similar historical events before drafting.
- Find contradictory claims across sources.
- Build city/company timelines.
- Support fact-check workflow.
- Support strategic and executive intelligence synthesis.
