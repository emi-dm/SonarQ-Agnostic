# Research: Visualizador de Reportes de SonarQube

**Feature**: 001-sonarqube-report-viewer  
**Date**: 12 de febrero de 2026

---

## 1. SonarQube API Research

### Authentication

**Decision**: Bearer authentication scheme (recommended by SonarQube docs)

```http
Authorization: Bearer YOUR_API_TOKEN
```

Alternative: X-Sonar-Passcode for specific endpoints.

**Token Generation**: User → My Account → Security → Generate Tokens

### Key Endpoints

| Endpoint                           | Method | Purpose                              |
| ---------------------------------- | ------ | ------------------------------------ |
| `/api/components/search`           | GET    | List all projects user has access to |
| `/api/measures/component`          | GET    | Get metrics for a specific project   |
| `/api/measures/search_history`     | GET    | Get historical data for trends       |
| `/api/issues/search`               | GET    | Search issues with filters           |
| `/api/qualitygates/project_status` | GET    | Get quality gate status              |

### Endpoint Details

**GET /api/components/search**

- Parameters: `q` (query), `p` (page), `ps` (page size), `qualifiers` (TRK for projects)
- Returns: List of components with key, name, visibility

**GET /api/measures/component**

- Parameters: `component` (project key), `metricKeys` (comma-separated), `branch`
- Common metrics: `bugs`, `vulnerabilities`, `code_smells`, `coverage`, `ncloc`, `duplicated_lines_density`, `alert_status`

**GET /api/measures/search_history**

- Parameters: `component`, `metrics`, `from`, `to`
- Returns: Time series data for trend charts

**GET /api/issues/search**

- Parameters: `projectKeys`, `types` (BUG, VULNERABILITY, CODE_SMELL), `severities` (INFO, MINOR, MAJOR, CRITICAL, BLOCKER), `p`, `ps`

### Response Format

- Default: JSON
- Use `Content-Type: application/x-www-form-urlencoded` for POST requests
- Pagination via `p` and `ps` parameters

---

## 2. Technology Decisions

### Backend: Python + FastAPI

**Decision**: FastAPI over Flask/Django

**Rationale**:

- Built-in OpenAPI documentation
- Async support for API calls
- Pydantic for data validation
- Type annotations support

**Alternative rejected**: Django - Too heavy for single-user tool

### Database: SQLite

**Decision**: SQLite with SQLAlchemy

**Rationale**:

- Zero configuration
- Single file storage (portable)
- Offline capability
- Sufficient for single-user

**Alternative rejected**: PostgreSQL - Overkill for single-user local tool

### HTTP Client: httpx

**Decision**: httpx over requests

**Rationale**:

- Async support
- Modern API
- Better for concurrent operations

### Frontend: Vanilla JS + Chart.js

**Decision**: Vanilla JS with Chart.js

**Rationale**:

- No build step required
- Lightweight
- Good visualization options
- Easy to serve from FastAPI

**Alternative rejected**: React/Vue - Requires build step, too complex for this use case

### Testing: pytest + hypothesis

**Decision**: pytest with hypothesis for Property-Based Testing

**Rationale**:

- Required by Constitution (Principle I)
- hypothesis finds edge cases standard tests miss

---

## 3. Best Practices Applied

### Error Handling

- All API errors must be caught and transformed to user-friendly messages
- No empty exception handlers
- Log context before re-raising exceptions

### Input Validation

- Validate all user inputs (URL format, token format)
- Sanitize data from SonarQube API before display

### Time Handling

- Store timestamps with timezone (UTC)
- Display in local timezone with indicator

### Offline-First

- Store all fetched data in SQLite
- Show staleness indicator when data is old
- Allow manual refresh

---

## 4. Architecture Summary

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend                              │
│  (HTML/CSS/JS + Chart.js)                                   │
│  - Dashboard                                               │
│  - Project details                                          │
│  - Issue browser                                            │
│  - Trend charts                                             │
└─────────────────────┬───────────────────────────────────────┘
                      │ HTTP JSON
┌─────────────────────▼───────────────────────────────────────┐
│                     Backend (FastAPI)                       │
│  - /api/connections    (CRUD for SonarQube configs)        │
│  - /api/projects       (list, metrics)                     │
│  - /api/issues        (search, filter)                     │
│  - /api/trends        (historical data)                    │
│  - Static files (frontend/)                                 │
└─────────────────────┬───────────────────────────────────────┘
                      │ httpx
┌─────────────────────▼───────────────────────────────────────┐
│                  SonarQube API                              │
│  (External)                                                │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────▼───────────────────────────────────────┐
│                   SQLite Database                           │
│  - connections table                                       │
│  - projects table                                           │
│  - metrics table                                           │
│  - issues table                                            │
│  - snapshots table (for trends)                            │
└─────────────────────────────────────────────────────────────┘
```

---

## 5. Next Steps

After this research, proceed to:

1. Generate `data-model.md` with entity definitions
2. Generate `contracts/openapi.yaml` with API specification
3. Generate `quickstart.md` with setup instructions
