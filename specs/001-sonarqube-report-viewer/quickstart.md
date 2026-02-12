# Quickstart: SonarQube Visualizer

**Feature**: 001-sonarqube-report-viewer  
**Date**: 12 de febrero de 2026

---

## Prerequisites

- Python 3.11+
- uv (recommended) or pip

---

## Setup (5 steps or less)

### Step 1: Clone and enter project

```bash
git clone https://github.com/your-org/SonarQ-Agnostic.git
cd SonarQ-Agnostic
```

### Step 2: Install dependencies with uv

```bash
uv sync
```

### Step 3: Configure environment

```bash
cp .env.example .env
# Edit .env and add your SonarQube URL and token
```

### Step 4: Start the server

```bash
uv run uvicorn src.main:app --reload
```

### Step 5: Open in browser

Navigate to: http://localhost:8000

---

## Usage

### Add a SonarQube Connection

1. Click "Add Connection" in the web UI
2. Enter your SonarQube URL (e.g., https://sonarqube.example.com)
3. Enter your API token (generate at User → My Account → Security → Generate Tokens)
4. Click "Test Connection" to verify
5. Click "Save"

### View Projects

1. Select a connection from the sidebar
2. Click "Sync Projects" to fetch from SonarQube
3. Click on any project to view metrics

### Explore Issues

1. From a project dashboard, click "Issues"
2. Filter by type (Bug, Vulnerability, Code Smell)
3. Filter by severity (INFO, MINOR, MAJOR, CRITICAL, BLOCKER)
4. Click on any issue for details

### View Trends

1. From a project dashboard, click "Trends"
2. Select metrics to display
3. Choose date range

---

## Development

### Run tests

```bash
# Unit tests
uv run pytest tests/unit -v

# Property-Based Tests
uv run pytest tests/pbt -v

# All tests
uv run pytest tests/ -v
```

### Lint and format

```bash
uv run ruff check .
uv run ruff format .
```

---

## Troubleshooting

**Cannot connect to SonarQube**

- Verify URL is correct (must include https://)
- Check token has proper permissions
- Ensure SonarQube server is accessible

**No projects shown**

- Click "Sync Projects" to fetch from SonarQube
- Check user has access to projects in SonarQube

**Data appears stale**

- Click "Refresh" on project to fetch latest data
- Stale indicator shows when data is older than 24 hours
