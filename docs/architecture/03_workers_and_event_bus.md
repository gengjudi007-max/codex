# 03 Workers and Event Bus

## Worker Cluster

The production runtime should split responsibilities into specialized workers.

### Connector Worker

Responsibilities:

- Exchange announcements
- Land transaction systems
- Policy crawlers
- Bond prospectuses
- Retry/backoff/cache
- Anti-bot adaptation

### OCR / PDF Worker

Responsibilities:

- OCR
- Table extraction
- Annual report parsing
- Prospectus parsing
- Confidence scoring

### Intelligence Worker

Responsibilities:

- Graph rebuild/update
- Autonomous intelligence
- Strategic intelligence
- Executive intelligence
- Alert escalation

### Editorial Worker

Responsibilities:

- Topic generation
- Assignment suggestions
- Fact-check queue generation
- Publication gate validation

### Publishing Worker

Responsibilities:

- Article packaging
- CMS export
- Newsletter package
- Archive generation
- Post-publication monitoring

---

## Event Bus

### Redis

Used for:

- lightweight queue
- runtime cache
- locks
- rate limits
- runtime state

### Kafka / Redpanda

Used for:

- event streams
- replay
- audit streams
- alert streams
- publishing streams
- graph update streams

---

## Unified Event Envelope

```json
{
  "event_id": "uuid",
  "event_type": "connector.source.changed",
  "priority": 5,
  "source": "hkex",
  "payload": {},
  "trace_id": "uuid",
  "created_at": "iso8601"
}
```

## Runtime Guarantees

The event layer should eventually support:

- retries
- dead-letter queue
- idempotency
- event replay
- audit trail
- event traceability
- worker heartbeat
- runtime observability
