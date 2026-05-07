# Newsroom OS Product Status

## Current Product State

Newsroom OS is evolving from a local AI-assisted newsroom runtime into a downloadable and installable real estate financial strategic intelligence product.

Current capabilities:

- realtime newsroom runtime skeleton
- connector scheduler
- queue + worker runtime
- strategic intelligence runtime
- executive intelligence runtime
- collaboration workflow
- publishing workflow
- API gateway
- desktop launcher
- native desktop packaging workflow
- GitHub Actions CI and release workflows

---

## Supported Platforms

### Current

- macOS
- Windows
- Linux (runtime mode)

### Packaging

Current packaging uses:

- PyInstaller

Future packaging may add:

- Tauri
- Electron

---

## Download and Installation Path

### GitHub Actions Artifacts

Desktop binaries are currently generated through GitHub Actions.

### GitHub Releases

Tagged releases (`v*`) automatically:

- build desktop binaries
- package ZIP artifacts
- upload release assets
- generate release notes

---

## Product Runtime

Current runtime model:

```text
Desktop App
↓
Local Runtime
↓
API Gateway
↓
Dashboard Endpoint
↓
Newsroom OS
```

The desktop launcher automatically:

- creates local data directories
- starts local runtime
- launches dashboard endpoint in browser

---

## Current Product Limitations

The product is still in productionization phase.

Remaining work:

- Dashboard frontend
- realtime WebSocket updates
- PostgreSQL migration
- Redis/Kafka integration
- installer/signing
- auto updater
- cloud sync/runtime
- Kubernetes deployment
- observability stack

---

## Product Vision

The target product is:

> A continuously running real estate financial newsroom and strategic intelligence platform with realtime information collection, institutional memory, collaborative editorial workflow, strategic reasoning, and executive intelligence.
