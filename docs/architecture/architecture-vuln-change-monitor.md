# Architecture: Vulnerability Change Monitor

Version: 1.1.0
Last Updated: 2026-06-16
Scenario: C - Reverse Engineering

---

## 1. Executive Summary

Vulnerability Change Monitor is a Flask REST API that ingests vulnerability snapshots and computes changes against the previous snapshot for the same product/version/source.

The service supports both synchronous and asynchronous snapshot creation and provides endpoints to read snapshot metadata and detailed change records.

Key capabilities:
- Snapshot validation and normalization
- Delta computation: new, resolved, severity_changed, status_changed, cvss_changed, unchanged
- Persistent storage in PostgreSQL
- Optional idempotency behavior using in-memory cache
- Async job polling with in-memory job status map
- OpenAPI documentation served through Flasgger

---

## 2. System Context

Actors and dependencies:
- API client submits snapshot payloads and queries results.
- Flask application hosts API, business logic, validation, and diff engine.
- PostgreSQL persists snapshots, findings, and change events.

See diagram: [diagrams/system-context-vuln-change-monitor.puml](diagrams/system-context-vuln-change-monitor.puml)

---

## 3. Container Architecture

Primary containers:
- app container (python:3.11-slim): Flask app, SQLAlchemy, service logic
- db container (postgres:15): relational persistence

Runtime notes:
- App startup runs `flask db upgrade` before launching server.
- Flask runs threaded mode on port 8080.

See diagram: [diagrams/container-vuln-change-monitor.puml](diagrams/container-vuln-change-monitor.puml)

---

## 4. Component Architecture

### 4.1 Components

- App factory: app initialization, config load, DB init, migrations, blueprint registration, health endpoint
- API layer: HTTP routing and response marshalling
- Service layer: input validation, snapshot diffing, persistence, idempotency cache, async job orchestration
- Error handler: unified JSON error contract
- Logger: request id assignment and structured request logging
- Data model layer: SQLAlchemy entities for snapshots/findings/changes

### 4.2 Component Responsibilities

- `app/api/vulnerability_api.py`
  - POST `/snapshots`
  - POST `/snapshots/async`
  - GET `/snapshots/<job_id>/status`
  - GET `/snapshots/<job_id>/result`
  - GET `/products/<product_name>/versions/<product_version>/snapshots`
  - GET `/snapshots/<snapshot_id>`
  - GET `/snapshots/<snapshot_id>/changes`

- `app/service/vulnerability_service.py`
  - Validates payload schema and semantic rules
  - Normalizes numeric fields (`cvss_score`, optional `epss_score`)
  - Finds previous snapshot and computes diff sets by finding key
  - Persists snapshot, findings, and change rows in one transaction
  - Supports sync return and async background processing via thread
  - Stores idempotency and async job state in process memory

- `app/error_handler.py`
  - Maps app exceptions to stable JSON error shape

- `app/logger.py`
  - Adds and returns `X-Request-ID`
  - Logs request metadata and latency as JSON

- `app/db/models.py`
  - Defines snapshot/finding/change entities
  - Applies enum, unique, check, and FK cascade constraints

See diagram: [diagrams/component-vuln-change-monitor.puml](diagrams/component-vuln-change-monitor.puml)

---

## 5. Interface Architecture

### 5.1 Endpoints

- POST `/snapshots`
  - Request: snapshot payload JSON
  - Header: optional `Idempotency-Key`
  - Response: `201` with snapshot summary, or `200` on idempotent replay

- POST `/snapshots/async`
  - Request: snapshot payload JSON
  - Header: optional `Idempotency-Key`
  - Response: `202` with `job_id`

- GET `/snapshots/<job_id>`
  - Response: `200` with `{ "status": "processing|completed|failed" }`

- GET `/snapshots/<job_id>/result`
  - Response: `200` with stored async result object

- GET `/health`
  - Response: `200` when DB connectivity check succeeds, else `500`

- GET `/products/<product_name>/versions/<product_version>/snapshots`
  - Query: `limit`, `offset`
  - Response: paged snapshot list

- GET `/snapshots/<snapshot_id>`
  - Response: snapshot summary and linkage to previous snapshot

- GET `/snapshots/<snapshot_id>/changes`
  - Query filters: `change_type`, `severity`, `component_name`, optional `limit`/`offset`
  - Response: change list including previous/current values and severity direction

### 5.2 Error Contract

Error shape:

```json
{
  "request_id": "uuid",
  "error": {
    "code": "validation_error|not_found|conflict|internal_error",
    "message": "text",
    "details": []
  }
}
```

---

## 6. Data Architecture

### 6.1 Entities

- `vulnerability_snapshots`
  - Snapshot metadata and summary counts
  - Self-reference to previous snapshot
  - Unique constraint on `(product_name, product_version, source, snapshot_time)`
  - Indexed columns for `product_name`, `product_version`, `source`, `snapshot_time`
  - Non-negative check constraints for finding/summary counters

- `vulnerability_findings`
  - Findings belonging to a snapshot
  - Unique finding key per snapshot on `(snapshot_id, vulnerability_id, component_name, component_version)`
  - Enum constraints for `severity` and `affected_status`
  - Optional risk fields `epss_score`, `known_exploited`

- `vulnerability_changes`
  - Materialized delta rows between previous and current snapshots
  - Includes prior/current severity, CVSS, affected status
  - Tracks `cvss_changed` as first-class change type
  - FK cascade from `snapshot_id` and `previous_snapshot_id`

See diagram: [diagrams/erd-vuln-change-monitor.puml](diagrams/erd-vuln-change-monitor.puml)

### 6.2 Finding Identity Key

A finding is identified by:
- vulnerability_id
- component_name
- component_version

This key drives set-based diff logic for new/resolved/common findings.

---

## 7. Data Flow

### 7.1 Synchronous Snapshot Flow

1. Client sends payload to POST `/snapshots`
2. Service validates and normalizes payload
3. Service finds previous snapshot for same product/version/source
4. Service compares findings and computes delta sets
5. Service inserts snapshot, findings, and changes in one DB transaction
6. Response returns snapshot id and summary counts

See diagram: [diagrams/seq-sync-snapshot-vuln-change-monitor.puml](diagrams/seq-sync-snapshot-vuln-change-monitor.puml)

### 7.2 Asynchronous Snapshot Flow

1. Client sends payload to POST `/snapshots/async`
2. Service allocates `job_id`, stores `processing` in in-memory jobs map
3. Background thread calls `create_snapshot`
4. Service marks job `completed` or `failed`
5. Client polls status and fetches result

See diagram: [diagrams/seq-async-snapshot-vuln-change-monitor.puml](diagrams/seq-async-snapshot-vuln-change-monitor.puml)

---

## 8. Deployment Architecture

Docker Compose topology:
- db: postgres:15, host port 5433 -> container 5432
- app: Flask service on host port 8080

Startup command:
- `flask db upgrade && python -m app.main`

See diagram: [diagrams/deployment-vuln-change-monitor.puml](diagrams/deployment-vuln-change-monitor.puml)

---

## 9. Requirements Traceability (Inferred)

- REQ-01: Accept vulnerability snapshot payloads
  - Evidence: `app/api/vulnerability_api.py`, `app/service/vulnerability_service.py: create_snapshot`
- REQ-02: Enforce payload validation rules and enums
  - Evidence: `app/service/vulnerability_service.py: normalize_snapshot_input`
- REQ-03: Compute changes against previous snapshot
  - Evidence: `app/service/vulnerability_service.py: compare_snapshots`
- REQ-04: Persist snapshots, findings, and changes
  - Evidence: `app/db/models.py`, `app/service/vulnerability_service.py: create_snapshot`
- REQ-05: Support idempotent behavior via key
  - Evidence: `app/api/vulnerability_api.py`, `app/service/vulnerability_service.py`
- REQ-06: Support async snapshot processing and polling
  - Evidence: `app/service/vulnerability_service.py: submit_snapshot/get_snapshot_status/get_snapshot_result`
- REQ-07: Expose health endpoint with DB connectivity check
  - Evidence: `app/__init__.py: /health`
- REQ-08: Provide machine-readable API spec and Swagger UI
  - Evidence: `docs/api/swagger.yaml`, `app/__init__.py: Swagger(app, template=template)`

---

## 10. Non-Functional Characteristics

- Reliability
  - DB transaction with rollback on snapshot write failure
- Observability
  - Structured logs with request id and latency
- Performance
  - Threaded Flask and async thread path reduce request wait for heavy snapshot processing
- Data Integrity
  - Unique/check constraints, enum-typed status/severity fields, and FK cascade rules protect consistency
- Operability
  - Migrations applied on startup in container command and API schema exposed through Swagger UI

---

## 11. Risks and Mitigations

- RISK-01: In-memory async job state is not durable across process restart
  - Impact: lost job status/result
  - Mitigation: persist jobs in DB or move to durable queue (Celery/RQ)

- RISK-02: In-memory idempotency cache is process-local and bounded
  - Impact: inconsistent replay behavior in multi-instance deployment
  - Mitigation: move idempotency records to shared store (DB/Redis)

- RISK-03: No authentication/authorization layer on snapshot endpoints
  - Impact: unauthorized writes/reads
  - Mitigation: add API auth and per-tenant authorization

- RISK-04: Potential unbounded memory growth for `jobs` map
  - Impact: memory pressure over long uptime
  - Mitigation: add TTL cleanup and retention limits

---

## 12. Architecture Decisions

- ADR-01: Materialize changes in dedicated table
  - Decision: store computed deltas as `vulnerability_changes` rows
  - Tradeoff: faster query vs additional write volume

- ADR-02: Use finding composite key for diff
  - Decision: key = `(vulnerability_id, component_name, component_version)`
  - Tradeoff: simple deterministic comparison, but key changes create resolved+new pair semantics

- ADR-03: Offer both sync and async snapshot ingestion
  - Decision: two write endpoints for different client needs
  - Tradeoff: async uses in-memory lifecycle state, not durable

- ADR-04: Process-local idempotency cache
  - Decision: lightweight OrderedDict with cap for quick replay handling
  - Tradeoff: not safe for horizontal scaling without shared store
