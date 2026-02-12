# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-02-12

### Added

- Initial release of SonarQube Visualizer
- Connection management (create, update, delete, test)
- Project listing and synchronization from SonarQube
- Metrics dashboard with key quality indicators (bugs, vulnerabilities, code smells, coverage)
- Issue browser with filtering by type and severity
- Historical trends visualization with Chart.js
- Responsive web interface
- SonarQube-standard color palette for severity levels
- Loading states and empty states
- Staleness indicator (>24h)
- SQLite database for local storage

### Technical

- Python FastAPI backend
- SQLAlchemy ORM with SQLite
- Vanilla JavaScript frontend with Chart.js
- Pydantic for validation
- httpx for async HTTP requests
- uv for dependency management
