# Data Model: Visualizador de Reportes de SonarQube

**Feature**: 001-sonarqube-report-viewer  
**Date**: 12 de febrero de 2026

---

## Entities

### 1. SonarQube Connection

Represents a configured connection to a SonarQube server.

| Field        | Type     | Required | Description                                                |
| ------------ | -------- | -------- | ---------------------------------------------------------- |
| `id`         | UUID     | Yes      | Primary key                                                |
| `name`       | String   | Yes      | User-friendly name for this connection                     |
| `url`        | String   | Yes      | SonarQube server URL (e.g., https://sonarqube.example.com) |
| `token`      | String   | Yes      | API token (encrypted at rest)                              |
| `created_at` | DateTime | Yes      | Creation timestamp (UTC)                                   |
| `updated_at` | DateTime | Yes      | Last update timestamp (UTC)                                |
| `is_default` | Boolean  | No       | Is this the default connection                             |

**Validation Rules:**

- `url` must be valid URL format
- `name` must be 1-100 characters
- `token` must not be empty

---

### 2. Project

Represents a project fetched from SonarQube.

| Field                | Type     | Required | Description                         |
| -------------------- | -------- | -------- | ----------------------------------- |
| `id`                 | UUID     | Yes      | Primary key                         |
| `connection_id`      | UUID     | Yes      | Foreign key to SonarQube Connection |
| `sonar_key`          | String   | Yes      | SonarQube project key               |
| `name`               | String   | Yes      | Project name                        |
| `visibility`         | String   | Yes      | "public" or "private"               |
| `last_analysis_date` | DateTime | No       | Last analysis timestamp             |
| `created_at`         | DateTime | Yes      | When record was created (UTC)       |
| `updated_at`         | DateTime | Yes      | Last update timestamp (UTC)         |

**Relationships:**

- One Connection has many Projects
- One Project has many MetricsSnapshots

---

### 3. MetricsSnapshot

Represents a point-in-time snapshot of project metrics.

| Field                      | Type     | Required | Description                           |
| -------------------------- | -------- | -------- | ------------------------------------- |
| `id`                       | UUID     | Yes      | Primary key                           |
| `project_id`               | UUID     | Yes      | Foreign key to Project                |
| `snapshot_date`            | DateTime | Yes      | When this snapshot was taken (UTC)    |
| `bugs`                     | Integer  | No       | Number of bugs                        |
| `vulnerabilities`          | Integer  | No       | Number of vulnerabilities             |
| `code_smells`              | Integer  | No       | Number of code smells                 |
| `coverage`                 | Float    | No       | Code coverage percentage              |
| `ncloc`                    | Integer  | No       | Lines of code                         |
| `duplicated_lines_density` | Float    | No       | Duplicated lines percentage           |
| `alert_status`             | String   | No       | Quality gate status (OK, WARN, ERROR) |
| `sqale_index`              | Integer  | No       | Technical debt in minutes             |
| `created_at`               | DateTime | Yes      | When record was created (UTC)         |

**Validation Rules:**

- `snapshot_date` must not be in the future
- Numeric values must be >= 0
- `coverage` and `duplicated_lines_density` must be 0-100

---

### 4. Issue

Represents an issue (bug, vulnerability, code smell) from SonarQube.

| Field        | Type     | Required | Description                                 |
| ------------ | -------- | -------- | ------------------------------------------- |
| `id`         | UUID     | Yes      | Primary key                                 |
| `project_id` | UUID     | Yes      | Foreign key to Project                      |
| `sonar_key`  | String   | Yes      | SonarQube issue key                         |
| `type`       | String   | Yes      | BUG, VULNERABILITY, CODE_SMELL              |
| `severity`   | String   | Yes      | INFO, MINOR, MAJOR, CRITICAL, BLOCKER       |
| `status`     | String   | Yes      | OPEN, CONFIRMED, REOPENED, RESOLVED, CLOSED |
| `message`    | String   | No       | Issue message/description                   |
| `rule`       | String   | No       | Rule that triggered this issue              |
| `component`  | String   | No       | File/component path                         |
| `line`       | Integer  | No       | Line number                                 |
| `effort`     | Integer  | No       | Effort to fix in minutes                    |
| `created_at` | DateTime | Yes      | When record was created (UTC)               |
| `updated_at` | DateTime | Yes      | Last update timestamp (UTC)                 |

**Validation Rules:**

- `type` must be one of: BUG, VULNERABILITY, CODE_SMELL
- `severity` must be one of: INFO, MINOR, MAJOR, CRITICAL, BLOCKER
- `status` must be one of: OPEN, CONFIRMED, REOPENED, RESOLVED, CLOSED

---

## Database Schema (SQLite)

```sql
-- Connections table
CREATE TABLE connections (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    url TEXT NOT NULL,
    token TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    is_default INTEGER DEFAULT 0
);

-- Projects table
CREATE TABLE projects (
    id TEXT PRIMARY KEY,
    connection_id TEXT NOT NULL,
    sonar_key TEXT NOT NULL,
    name TEXT NOT NULL,
    visibility TEXT NOT NULL,
    last_analysis_date TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (connection_id) REFERENCES connections(id)
);

-- Metrics snapshots table
CREATE TABLE metrics_snapshots (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    snapshot_date TEXT NOT NULL,
    bugs INTEGER,
    vulnerabilities INTEGER,
    code_smells INTEGER,
    coverage REAL,
    ncloc INTEGER,
    duplicated_lines_density REAL,
    alert_status TEXT,
    sqale_index INTEGER,
    created_at TEXT NOT NULL,
    FOREIGN KEY (project_id) REFERENCES projects(id)
);

-- Issues table
CREATE TABLE issues (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    sonar_key TEXT NOT NULL,
    type TEXT NOT NULL,
    severity TEXT NOT NULL,
    status TEXT NOT NULL,
    message TEXT,
    rule TEXT,
    component TEXT,
    line INTEGER,
    effort INTEGER,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (project_id) REFERENCES projects(id)
);

-- Indexes for performance
CREATE INDEX idx_projects_connection ON projects(connection_id);
CREATE INDEX idx_metrics_project_date ON metrics_snapshots(project_id, snapshot_date);
CREATE INDEX idx_issues_project ON issues(project_id);
CREATE INDEX idx_issues_type_severity ON issues(type, severity);
```

---

## State Transitions

### Connection State Machine

```
[DISCONNECTED] --> [CONNECTING] --> [CONNECTED]
                                    |
                                    v
                              [ERROR] --> [DISCONNECTED]
```

### Issue Status Transitions

```
OPEN --> CONFIRMED --> RESOLVED --> CLOSED
   |         |            |
   v         v            v
REOPENED   REOPENED    REOPENED
```

---

## API Data Transfer Objects (DTOs)

### ConnectionDTO

```json
{
  "id": "uuid",
  "name": "My SonarQube",
  "url": "https://sonarqube.example.com",
  "is_default": false,
  "created_at": "2026-02-12T10:00:00Z",
  "updated_at": "2026-02-12T10:00:00Z"
}
```

### ProjectDTO

```json
{
  "id": "uuid",
  "sonar_key": "my-project",
  "name": "My Project",
  "visibility": "public",
  "last_analysis_date": "2026-02-10T15:30:00Z"
}
```

### MetricsDTO

```json
{
  "project_id": "uuid",
  "bugs": 5,
  "vulnerabilities": 2,
  "code_smells": 150,
  "coverage": 75.5,
  "ncloc": 10000,
  "duplicated_lines_density": 3.2,
  "alert_status": "OK",
  "sqale_index": 480,
  "snapshot_date": "2026-02-12T10:00:00Z"
}
```

### IssueDTO

```json
{
  "id": "uuid",
  "sonar_key": "AXabc123",
  "type": "BUG",
  "severity": "MAJOR",
  "status": "OPEN",
  "message": "Remove this unused import",
  "rule": "python:S1064",
  "component": "src/main.py",
  "line": 5,
  "effort": 10
}
```

---

## Notes

- All timestamps are stored in UTC
- Connection tokens are encrypted at rest usingFernet (symmetric encryption)
- Issues are synced on-demand, not automatically
- Metrics snapshots are created each time user refreshes data
- Historical data is kept indefinitely (user can delete manually)
