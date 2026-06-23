# vuln-change-monitor

Flask service that stores vulnerability snapshots, compares each new snapshot with the previous one, and exposes change results.

Current package layout:
- app/api
- app/service
- app/db

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
docker-compose (db + app):

```bash
docker compose up --build app db
```

compose app startup command runs DB migration first:
- flask db upgrade
- python -m app.main

### Example usage

```bash

# Synchronous processing
curl -s -X POST http://localhost:8080/snapshots \
	-H "Content-Type: application/json" \
	-d @example/snapshot-day-1.json

curl -s -X POST http://localhost:8080/snapshots \
	-H "Content-Type: application/json" \
	-d @example/snapshot-day-2.json


# Asynchronous processing
curl -s -X POST http://localhost:8080/snapshots/async \
	-H "Content-Type: application/json" \
	-d @example/snapshot-day-3.json

curl -s -X POST http://localhost:8080/snapshots/async \
	-H "Content-Type: application/json" \
	-d @example/snapshot-day-4.json

curl http://localhost:8080/snapshots/<snapshot_id>/status
curl http://localhost:8080/snapshots/<snapshot_id>/result


# get snapshot change results

curl http://localhost:8080/snapshots/<snapshot_id>

curl http://localhost:8080/snapshots/<snapshot_id>/changes
curl http://localhost:8080/snapshots/<snapshot_id>/changes?change_type=severity_changed&limit=20&offset=0
curl http://localhost:8080/snapshots/<snapshot_id>/changes?severity=critical
curl http://localhost:8080/snapshots/<snapshot_id>/changes?component_name=openssl

curl http://localhost:8080/products/demo-app/versions/1.0.0/snapshots?limit=10&offset=0

```


## 3) Required environment variables and defaults

Variables used by app:
- DB_HOST: localhost
- DB_PORT: 5433
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

#### Functional tests are in tests/api_test/test_vulnerability_api.py.

To run functional tests:

```bash
docker compose run --rm test pytest tests/api_test/
```

#### Live integration tests are in tests/integration_test/test_live_vulnerability_api.py.

To run live integration tests:

```bash
docker compose run --rm test pytest tests/integration_test/
```


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
- Idempotency-Key header is supported on POST /snapshots and POST /snapshots/async
- same key replay on sync endpoint returns cached snapshot response (200)
- same key replay on async endpoint returns the same job_id

Async snapshot API:
- POST /snapshots/async returns 202 with job_id
- GET /snapshots/{job_id}/status returns processing/completed/failed
- GET /snapshots/{job_id}/result returns snapshot result or error

API docs:
- OpenAPI source: docs/api/swagger.yaml
- Swagger UI (Flasgger): /apidocs

## 8) Assumptions and shortcuts

- Single service process, async snapshot is handled by in-process thread (no external queue/worker).
- Snapshot comparison only uses the immediate previous snapshot for the same product/version/source.
- Change detection tracks new/resolved/severity_changed/status_changed/unchanged.
- CVSS value is validated as numeric 0.0 to 10.0.
- Optional finding fields epss_score (0.0 to 1.0) and known_exploited (boolean) are supported.

## 9) Improvements with more time
- Ensure more detailed exception handling

## 10) Bonus updates

- Added idempotency support with Idempotency-Key for sync and async snapshot submission.
- Added async snapshot processing endpoints (submit/status/result).
- Added optional finding fields: epss_score and known_exploited.
- Added cvss_changed change type handling.
- Added structured error response shape with request_id.
- Added live integration API tests for running environment.
- Added severity ordering helpers for escalation/de-escalation reporting.
- Added database transaction handling that guarantees data are committed atomically.
- Added OpenAPI specification at docs/api/swagger.yaml and integrated Flasgger UI.
- Refined DB schema using enums, FK cascade rules, and snapshot metadata indexes.