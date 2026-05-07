# 06 Cloud Runtime and Observability

## 24/7 Cloud Runtime

The production system should support continuous newsroom operation.

Required components:

- scheduler
- distributed queue
- worker orchestration
- retries and dead-letter queue
- runtime health checks
- automatic restart
- backup and recovery
- cloud logging

## Runtime Schedule

Suggested cadence:

```text
minute-level connector polling
hourly signal synthesis
daily newsroom brief
weekly executive intelligence
monthly strategic memory update
```

## Kubernetes Direction

### Services

- api-service
- connector-worker
- ocr-worker
- intelligence-worker
- editorial-worker
- publishing-worker
- scheduler
- web-ui

### Infrastructure

- PostgreSQL
- Redis
- Kafka/Redpanda
- vector database
- object storage

## Observability Stack

### Prometheus

Metrics collection:

- connector latency
- queue depth
- worker failures
- OCR latency
- publishing failures
- alert counts

### Grafana

Dashboards:

- runtime health
- newsroom alerts
- connector activity
- publishing pipeline
- strategic intelligence overview

### Loki

Centralized logs:

- connector logs
- worker logs
- runtime logs
- publishing logs
- audit logs

## Traceability

Every major action should include:

- trace_id
- event_id
- source_id
- article_id
- assignment_id
- worker_id

## Reliability Goals

The production system should eventually support:

- event replay
- idempotency
- graceful degradation
- rollback
- auditability
- disaster recovery
