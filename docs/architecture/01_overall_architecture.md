# 01 Overall Production Architecture

Newsroom OS 的生产级目标，是从本地房地产财经 AI 工具升级为云端化、长期运行、多用户协同的媒体与战略情报基础设施。

## Target Architecture

```text
Web UI / Control Center
        ↓
API Gateway / Auth / RBAC
        ↓
Event Bus / Queue Layer
        ↓
Worker Cluster
        ↓
PostgreSQL + Vector DB + Object Storage
        ↓
Knowledge Graph + Strategic Intelligence Runtime
        ↓
Collaboration OS + Publishing OS + Executive Intelligence
```

## Core Principles

1. All collection, parsing, verification, intelligence, and publishing actions should be event-driven.
2. Every editorial conclusion must preserve source, evidence, version, and approval history.
3. SQLite and asyncio remain the local development fallback.
4. Production should use PostgreSQL, Redis/Kafka, distributed workers, Web UI, and cloud deployment.
5. Long-term memory is a first-class product requirement, not a by-product of logs.

## Production System Goals

- 24/7 real-time source monitoring.
- Long-term policy, city, company, land, property service, and risk memory.
- Strategic and executive-level intelligence synthesis.
- Multi-role editorial collaboration.
- Fact-check and publication gates.
- CMS distribution and post-publication monitoring.
- Observability, auditability, and recovery.