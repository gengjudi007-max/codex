# Installation Guide

## Current Packaging Status

Newsroom OS currently ships as a Python package.

Supported environments:

- macOS
- Windows
- Linux

Python 3.11+ is recommended.

---

## Install from Source

```bash
git clone https://github.com/gengjudi007-max/codex.git
cd codex
pip install -e .
```

---

## Core Commands

### Health Check

```bash
codex health
```

### Run Scheduler Once

```bash
codex run-once
```

### Start API Gateway

```bash
python -m codex.api_gateway
```

Then open:

```text
http://localhost:8000/health
http://localhost:8000/control-center
```

---

## Docker

Build image:

```bash
docker build -t newsroom-os .
```

Run container:

```bash
docker run -p 8000:8000 newsroom-os
```

---

## Package Builds

GitHub Actions automatically builds:

- wheel (.whl)
- source distribution (.tar.gz)

Artifacts are uploaded to GitHub Actions.

---

## Current Limitations

The project is currently a production-grade newsroom runtime prototype.

Still planned:

- PostgreSQL migration
- Redis/Kafka integration
- FastAPI backend
- Dashboard UI
- OCR/PDF production pipeline
- Kubernetes deployment
- Cloud runtime

---

## Recommended Local Stack

### Development

- Python 3.11
- SQLite
- local runtime

### Production Target

- PostgreSQL
- Redis
- Docker/Kubernetes
- Prometheus/Grafana/Loki
