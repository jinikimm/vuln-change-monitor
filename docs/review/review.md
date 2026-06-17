## Review Summary

| Summary of review feedback with clear actions and update tracking.


----

### 260615-Update

---


### 1. Directory Layout Consistency

**Q. Why does this repo have a different layout than other projects?**

**Action**

- Update layout to the same layout as the `archive-file-extractor` repo

**Updates**

  (updated layout)
  - `service/` — Business logic implementation
  - `api/` — HTTP request/response handling
  - `db/` — Domain data models
  - `__init__.py`
  - `config.py` — Global configuration
  - `error_handler.py` — Exception handling
  - `logger.py` — Logging initialization
  - `main.py`

---

### 2. Exception Handling Coverage

**Q. Why are exception handling mechanisms incomplete in this repo?**


**Action**

- Expand into detailed scenario documentation
- Update additional detailed exception handling

**Updates**

- [docs/api/swagger.yaml](../../docs/api/swagger.yaml): API v1.2.0 - Add detailed error scenario and reponse examples to all endpoints (total 8 endpoints, 10+ error scenario)

---

### 3. Duplicate Endpoint Design

**Q. Why are `/snapshots` and `/snapshots/async` both declared? Are both intentional?**

**Answer**

- The requirements demand both synchronous and asynchronous execution for the same task.

**Action**

- N.A

**Updates**

- N.A

---

### 4. Route Path Simplification

**Q. Should `GET /products/<product_name>/versions/<product_version>/snapshots` be refactored to `/prod_versions/{prod_version}/snapshots`?**

**Answer**

- Current api path design was explicitly defined in project requirements specification


**Action**

- N.A

**Updates**

- N.A

---

### 4. API Routing

**Q. Why use Flask Blueprint? What are alternatives?**

**Answer**
- Blueprint is used to modularize and group routes, and here it is combined with API classes to centralize routing logic.

**Action**
- Refactor API routing by adopting PSA's class-based API pattern with centralized route registration.

**Updates**
- [app/api/](https://github.com/jinikimm/vuln-change-monitor/tree/main/app/api) ([99ad20a
](https://github.com/jinikimm/vuln-change-monitor/commit/99ad20a8f508520ac49e9a7537dbc905c99e6bb8) ) : Refactored API routing to class-based structure with centralized add_url_rules() registration for consistency.
