# Vulnerability Monitor Service

## Operating Model

```mermaid
flowchart LR
  C[Client] --> S[Service API]
  S --> Q[(In-memory Queue)]
  Q --> W1[Worker 1]
  Q --> W2[Worker 2]
  Q --> Wn[Worker N]

  S --> DB[(DB: vulnerabilities/files)]
  S --> FS[(Filesystem: temp files)]

  W1 --> DB
  W2 --> DB
  Wn --> DB

  W1 --> FS
  W2 --> FS
  Wn --> FS
```

The service receives requests, stores job state in the database, and enqueues vulnerability analysis jobs in an in-memory queue.
Workers consume tasks concurrently from the queue, write results to the database, and use the temporary filesystem.

## Architecture

```mermaid
flowchart TD
  Client[Client]
  API[Flask API]
  Q[(In-memory Queue)]
  W[ThreadPool Worker]
  VS[VulnerabilityService]
  DB[(PostgreSQL)]
  FS[(Temp Filesystem)]

  Client --> API
  API --> DB
  API --> Q

  Q --> W

  W --> VS
  VS --> DB
  VS --> FS
```

### Key Points

- The queue is used as a trigger for background jobs.
- Each vulnerability analysis job is enqueued once and fully processed in a single worker flow.
- The analysis logic is centralized in `VulnerabilityService`.

## Vulnerability Analysis Request Flow

```mermaid
sequenceDiagram
  participant C as Client
  participant API as /vulnerabilities
  participant DB as vulnerabilities/files
  participant Q as Queue
  participant W as Worker
  participant VS as VulnerabilityService

  C->>API: POST /vulnerabilities (file, options)
  API->>VS: save_file()
  API->>DB: create VulnerabilityJob(status=pending)
  API->>Q: enqueue vulnerability analysis task (once)
  API-->>C: 202 {job_id}

  Q->>W: consume task
  W->>VS: analyze_task(job_id, file_path, options)
  VS->>DB: status -> running
  VS->>VS: analyze_vulnerabilities()
  VS->>DB: insert results
  VS->>DB: status -> completed
```

## Test & Development

- Tests are implemented using pytest in the `tests/` directory.
- For development environment setup, refer to requirements.txt and Dockerfile.

---

For detailed API usage, refer to the code and comments.
