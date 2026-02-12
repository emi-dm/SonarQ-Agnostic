# Implementation Plan: Visualizador de Reportes de SonarQube

**Branch**: `001-sonarqube-report-viewer` | **Date**: 12 de febrero de 2026 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-sonarqube-report-viewer/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Web-based visualizer for SonarQube quality reports. The tool connects to SonarQube instances via REST API, fetches project metrics (bugs, vulnerabilities, code coverage, code smells), stores them locally in SQLite for offline viewing, and presents them through a minimalist responsive HTML/CSS/JS interface with interactive visualizations. The Python backend (FastAPI) handles API integration, data persistence, and serves the frontend. Core capabilities include connection management, multi-project dashboard comparisons, trend analysis, and manual data refresh with staleness indicators.

## Technical Context

**Language/Version**: Python 3.11+  
**Primary Dependencies**: FastAPI, SQLAlchemy (SQLite), httpx (async HTTP client), Pydantic, Chart.js or similar for visualizations  
**Storage**: SQLite (local file)  
**Testing**: pytest, pytest-asyncio, hypothesis (for Property-Based Testing per Constitution)  
**Target Platform**: Linux/macOS/Windows (desktop or server)  
**Project Type**: Web application (Python backend + HTML/CSS/JS frontend)  
**Performance Goals**: Response time < 2s for dashboard loads, support 10+ projects, offline-first capability  
**Constraints**: Single-user local tool, data stored locally in SQLite, manual refresh (no polling)  
**Scale/Scope**: Individual developer or small team tool, 10-50 projects, thousands of issues

### UI/UX Decisions (from checklist)

| Decision        | Value                                                                | Source                 |
| --------------- | -------------------------------------------------------------------- | ---------------------- |
| Severity Colors | SonarQube standard (#FF4444, #FF8800, #FFCC00, #4488FF, #888888)     | Checklist + User input |
| Chart Types     | Bar charts for trends                                                | User input             |
| Responsive      | Fully responsive (Desktop ≥1024px, Tablet 768-1023px, Mobile <768px) | User input             |
| Loading States  | Skeleton loaders, 10s timeout                                        | Checklist              |
| Accessibility   | WCAG AA (4.5:1 contrast, keyboard nav, ARIA)                         | Checklist              |

## Constitution Check

_GATE: Must pass before Phase 0 research. Re-check after Phase 1 design._

| Gate                           | Status  | Notes                                                             |
| ------------------------------ | ------- | ----------------------------------------------------------------- |
| Test-First & PBT               | ✅ PASS | pytest + hypothesis for PBT as required by Constitution I         |
| Documentation & Traceability   | ✅ PASS | Changelog, README, docs/ structure per Constitution II            |
| Maintainability & Code Health  | ✅ PASS | Modular structure, linters, type annotations per Constitution III |
| Reproducible Releases & SemVer | ✅ PASS | Will use semantic versioning per Constitution IV                  |
| Observability & Simplicity     | ✅ PASS | Structured logging, KISS approach per Constitution V              |
| Quickstart ≤ 5 steps           | ✅ PASS | Requirement: single command or 5-step setup in README             |

**Gate Result**: ALL GATES PASS - Phase 1 design complete

## Project Structure

### Documentation (this feature)

```text
specs/001-sonarqube-report-viewer/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
│   └── openapi.yaml    # REST API contract
├── checklists/          # Quality checklists
│   ├── requirements.md # Spec quality checklist
│   └── ui.md          # UI/UX requirements quality checklist
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── config.py            # Configuration management
│   ├── models/              # SQLAlchemy models
│   │   ├── __init__.py
│   │   ├── connection.py   # SonarQube connection config
│   │   ├── project.py      # Project entity
│   │   ├── metrics.py      # Metrics entity
│   │   └── issue.py         # Issue entity
│   ├── services/           # Business logic
│   │   ├── __init__.py
│   │   ├── sonar_client.py # SonarQube API client
│   │   ├── sync_service.py # Data synchronization
│   │   └── metrics_service.py # Metrics calculation
│   ├── api/                # FastAPI routes
│   │   ├── __init__.py
│   │   ├── connections.py  # Connection management endpoints
│   │   ├── projects.py     # Project endpoints
│   │   ├── metrics.py      # Metrics endpoints
│   │   └── issues.py       # Issues endpoints
│   └── db/
│       ├── __init__.py
│       └── session.py       # Database session management
├── tests/
│   ├── __init__.py
│   ├── unit/
│   ├── integration/
│   └── pbt/                # Property-Based Tests
├── pyproject.toml
├── uv.lock
└── .env.example

frontend/
├── index.html              # Main HTML entry
├── css/
│   ├── styles.css          # Main styles
│   └── dashboard.css      # Dashboard-specific styles
├── js/
│   ├── app.js             # Main application
│   ├── api.js             # API client
│   ├── charts.js          # Chart.js wrappers
│   └── components/        # UI components
│       ├── header.js
│       ├── project-card.js
│       ├── metrics-panel.js
│       └── issue-list.js
└── tests/
```

**Structure Decision**: Web application with Python FastAPI backend and vanilla HTML/CSS/JS frontend. This architecture ensures:

- Simple deployment (single backend process)
- Easy offline capability (SQLite + frontend served by backend)
- Minimal dependencies for frontend (vanilla JS with Chart.js)
- FastAPI provides automatic OpenAPI documentation

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No complexity violations at this stage. The structure follows the Constitution principles:

- Simple single-user tool with SQLite
- Modular backend with clear separation of concerns
- Minimal frontend dependencies

---

## Phase 0: Research Required

### Unknowns to Research

1. **SonarQube API specifics**: Need to verify exact endpoints for metrics, issues, and historical data
2. **Best practices for offline-first web apps**: Caching strategies, staleness indicators design
3. **Chart.js vs alternatives**: Compare visualization libraries for trend charts

### Best Practices to Investigate

1. **FastAPI + SQLite**: Patterns for async database operations
2. **Property-Based Testing in Python**: Using hypothesis effectively
3. **HTML/CSS/JS architecture**: Component patterns for maintainable vanilla JS

---

## Phase 1: Design Artifacts to Generate

After research, generate:

- `research.md`: Decisions and alternatives evaluated
- `data-model.md`: Entity definitions
- `contracts/openapi.yaml`: REST API specification
- `quickstart.md`: Setup instructions (≤5 steps per Constitution)
