# vuln-change-monitor

Flask service that stores vulnerability snapshots, compares each new snapshot with the previous one, and exposes change results.

## 1) Build and run locally

Prerequisites:
- Python 3.11+
- PostgreSQL 15+

Install and run:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# optional but recommended for flask cli
export FLASK_APP=app:create_app

# run API
python -m app.main
```

Default API port: 8080

## 2) Run with Docker / docker-compose

Docker only (db + app):

```bash
docker build -t vuln-change-monitor .

docker run -d \
  --name db_local \
  -e POSTGRES_DB=vuln_db \
  -e POSTGRES_USER=vuln_user \
  -e POSTGRES_PASSWORD=vuln_pass \
  -p 5432:5432 \
  postgres:15

docker run --rm -p 8080:8080 \
    -e DB_HOST=host.docker.internal \
    -e DB_PORT=5432 \
    -e DB_NAME=vuln_db \
    -e DB_USER=vuln_user \
    -e DB_PASSWORD=vuln_pass \
    vuln-change-monitor
```

docker-compose (db + app):

```bash
docker compose up --build
```

compose app startup command runs DB migration first:
- flask db upgrade
- python -m app.main

## 3) Required environment variables and defaults

Variables used by app:
- DB_HOST: localhost
- DB_PORT: 5432
- DB_NAME: vuln_db
- DB_USER: vuln_user
- DB_PASSWORD: vuln_pass
- PORT: 8080

In docker-compose, DB_HOST is set to db.

## 4) Database setup / migration

This project uses Flask-Migrate (Alembic), and migration files are included in this repo.

Apply schema:

```bash
export FLASK_APP=app:create_app
flask db upgrade
```

If you only need quick local testing, tests use in-memory SQLite and do not require PostgreSQL.

## 5) Run tests

```bash
pytest -q
```

Main tests are in tests/test_vulnerability_api.py.

## 6) Matching-key explanation

A snapshot is identified by:
- product_name
- product_version
- source
- snapshot_time

A finding is identified by:
- vulnerability_id
- component_name
- component_version

Behavior based on this key:
- same snapshot key submitted: rejected (409)
- same finding key in one snapshot: rejected (400)
- same finding key across snapshots: compared for severity/status changes
- different component_version with same CVE/component_name: treated as different findings

## 7) Snapshot ordering, duplicate submission, idempotency

Snapshot ordering:
- for same (product_name, product_version, source), new snapshot_time must be strictly later than previous snapshot_time
- otherwise request is rejected with 409 conflict
- list endpoint returns snapshots in snapshot_time descending order

Duplicate submission:
- exact duplicate snapshot_time for same (product_name, product_version, source) is rejected
- DB unique constraint also prevents duplicate snapshot rows

Idempotency:
- no explicit idempotency key endpoint/header exists
- practical behavior is conflict-based deduplication: repeated same-time submissions return 409 instead of creating extra rows

## 8) Assumptions and shortcuts

- Single service process, synchronous request handling (no queue/worker).
- Snapshot comparison only uses the immediate previous snapshot for the same product/version/source.
- Change detection tracks new/resolved/severity_changed/status_changed/unchanged.
- CVSS value is validated as numeric 0.0 to 10.0.

## 9) Improvements with more time

- Idempotency key support for safe retries and duplicate request handling.
- Database integration tests using a real database or test containers.
- Structured JSON logging with request IDs for better observability.
- Severity ordering helpers for escalation and de-escalation reporting.
- CVSS-specific change tracking or a dedicated `cvss_score_changed` change type.
- Additional fields such as EPSS score or known-exploited indicators in the data model.
- Asynchronous processing with a status endpoint for handling large snapshots.
- Database transaction handling to ensure snapshot, findings, and changes are committed atomically.
- OpenAPI / Swagger specification for clear API documentation.
