# Vulnerability Monitor Service


## Architecture

```mermaid
flowchart TD
    Client[Client]
    FlaskAPI[Flask API]
    VulnerabilityService[VulnerabilityService]
    Database[(PostgreSQL)]

    Client --> FlaskAPI
    FlaskAPI --> VulnerabilityService
    VulnerabilityService --> Database
```

The service receives HTTP requests (mainly vulnerability snapshot submissions and queries) via a Flask API. All validation, comparison, and database operations are handled synchronously in the API and service layer.

### Key Points

- All logic is handled synchronously in the Flask API and service layer.
- No background queue, thread pool, or worker process is used.
- The `VulnerabilityService` handles validation, deduplication, snapshot comparison, and DB writes.

## Vulnerability Snapshot Submission Flow

```mermaid
sequenceDiagram
    participant C as Client
    participant API as Flask API
    participant S as VulnerabilityService
    participant DB as Database

    C->>API: POST /snapshots (snapshot data)
    API->>S: validate & process snapshot
    S->>DB: store snapshot & findings
    S->>DB: compare with previous snapshot
    API-->>C: 201 Created / result
```

### Flow Details

- Client submits a vulnerability snapshot via HTTP POST.
- API validates input and checks for duplicates.
- Service compares with the previous snapshot for the same product/version/source.
- New snapshot and findings are stored in the database.
- Change summary is calculated and stored.

## Test & Development

- Tests are implemented using pytest in the `tests/` directory.
- For development environment setup, refer to requirements.txt and Dockerfile.

---

For detailed API usage, refer to the code and comments.
