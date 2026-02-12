# SonarQube Visualizer

Web-based visualizer for SonarQube or SonarCloud quality reports. Connect to your SonarQube server or SonarCloud account, view project metrics, explore issues, and track trends over time.

## Features

- **Connection Management**: Configure multiple SonarQube server or SonarCloud connections
- **Project Dashboard**: View key metrics (bugs, vulnerabilities, code smells, coverage)
- **Issue Browser**: Search and filter issues by type and severity
- **Trends Analysis**: Visualize historical trends with interactive charts
- **Offline Storage**: Data is stored locally in SQLite for offline viewing
- **Responsive Design**: Works on desktop, tablet, and mobile

## Supported Sources

- **SonarCloud**: https://sonarcloud.io
- **SonarQube**: Self-hosted SonarQube servers

## Quick Start

### Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) (recommended) or pip

### Installation

1. **Clone and enter project**

   ```bash
   cd SonarQ-Agnostic/backend
   ```

2. **Install dependencies**

   ```bash
   uv sync --extra dev
   ```

3. **Configure environment**

   ```bash
   cp .env.example .env
   # Edit .env and add your SonarCloud/SonarQube URL and token
   ```

4. **Start the server**

   ```bash
   uv run uvicorn src.main:app --reload
   ```

5. **Open in browser**

   Navigate to: http://localhost:8000

## Usage

### Adding a SonarCloud Connection

1. Generate a token in SonarCloud:
   - Go to https://sonarcloud.io/account/security/
   - Create a new token
2. Click **+ Add Connection** in the sidebar
3. Enter `https://sonarcloud.io` as the URL
4. Enter your SonarCloud API token
5. Click **Test Connection** to verify
6. Click **Save**

### Adding a SonarQube Connection (Self-Hosted)

1. Generate a token in SonarQube:
   - Go to My Account → Security → Generate Tokens
2. Click **+ Add Connection** in the sidebar
3. Enter your SonarQube URL (e.g., `https://sonarqube.example.com`)
4. Enter your SonarQube API token
5. Click **Test Connection** to verify
6. Click **Save**

### Viewing Projects

1. Select a connection from the dropdown
2. Click **Sync Projects** to fetch from SonarQube
3. Click on any project card to view detailed metrics

### Exploring Issues

1. From a project detail view, scroll to the Issues section
2. Filter by type (Bug, Vulnerability, Code Smell)
3. Filter by severity (Blocker, Critical, Major, Minor, Info)

### Viewing Trends

1. From a project detail view, view the Trends section
2. The chart shows historical data for bugs, vulnerabilities, code smells, and coverage

## API Endpoints

| Endpoint                          | Description              |
| --------------------------------- | ------------------------ |
| `GET /api/health`                 | Health check             |
| `GET /api/connections`            | List all connections     |
| `POST /api/connections`           | Create a connection      |
| `POST /api/connections/{id}/test` | Test connection          |
| `GET /api/projects`               | List all cached projects |
| `POST /api/projects/{id}/refresh` | Refresh metrics          |
| `GET /api/projects/{id}/issues`   | List issues              |
| `GET /api/projects/{id}/trends`   | Get trends               |

## Troubleshooting

### Cannot connect to SonarQube

- Verify URL is correct (must include `https://`)
- Check token has proper permissions
- Ensure SonarQube server is accessible

### No projects shown

- Click **Sync Projects** to fetch from SonarQube
- Check user has access to projects in SonarQube

### Data appears stale

- Click **Refresh** on project to fetch latest data
- Stale indicator shows when data is older than 24 hours

See `specs/001-sonarqube-report-viewer/quickstart.md` for full documentation.
