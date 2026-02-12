"""SonarQube API client service."""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

# SonarCloud configuration
SONARCLOUD_URL = "https://sonarcloud.io"
SONARCLOUD_API_PATH = "/api"


@dataclass
class SonarQubeVersion:
    """SonarQube server version info."""
    version: str


@dataclass
class SonarQubeProject:
    """SonarQube project data."""
    key: str
    name: str
    visibility: str
    lastAnalysisDate: Optional[str] = None


@dataclass
class SonarQubeMetrics:
    """SonarQube project metrics."""
    bugs: Optional[int] = None
    vulnerabilities: Optional[int] = None
    code_smells: Optional[int] = None
    coverage: Optional[float] = None
    ncloc: Optional[int] = None
    duplicated_lines_density: Optional[float] = None
    alert_status: Optional[str] = None
    sqale_index: Optional[int] = None


@dataclass
class SonarQubeIssue:
    """SonarQube issue data."""
    key: str
    type: str
    severity: str
    status: str
    message: Optional[str] = None
    rule: Optional[str] = None
    component: Optional[str] = None
    line: Optional[int] = None
    effort: Optional[int] = None


class SonarQubeClient:
    """Client for interacting with SonarQube or SonarCloud REST API."""

    def __init__(self, url: str, token: str, organization: Optional[str] = None):
        """Initialize SonarQube client.
        
        Args:
            url: SonarQube server URL (e.g., https://sonarqube.example.com or https://sonarcloud.io)
            token: API token for authentication
            organization: SonarCloud organization (required for sonarcloud.io)
        """
        # Normalize URL - remove trailing slash
        self.url = url.rstrip("/")
        
        # Detect if using SonarCloud
        self.is_sonarcloud = "sonarcloud.io" in self.url.lower()
        
        # Store organization (for SonarCloud) - normalize to lowercase
        # SonarCloud organization keys are case-insensitive but must be lowercase in API calls
        self.organization = organization.lower() if organization and self.is_sonarcloud else organization
        
        # For SonarCloud, use the base URL (API path is added per-request)
        # For SonarQube, use the base URL as-is
        self.api_base = self.url
        
        self.token = token
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def client(self) -> httpx.AsyncClient:
        """Get or create async HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.api_base,
                timeout=30.0,
                headers={
                    "Authorization": f"Bearer {self.token}",
                }
            )
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def test_connection(self) -> tuple[bool, str, Optional[str]]:
        """Test connection to SonarQube server.
        
        Returns:
            Tuple of (success, message, version)
        """
        try:
            response = await self.client.get("/api/system/status")
            if response.status_code == 200:
                data = response.json()
                version = data.get("version")
                return True, "Connection successful", version
            elif response.status_code == 401:
                return False, "Authentication failed. Check your token.", None
            else:
                return False, f"Unexpected status: {response.status_code}", None
        except httpx.ConnectError:
            return False, "Cannot connect to SonarQube server. Check URL.", None
        except httpx.TimeoutException:
            return False, "Connection timeout. Server may be unreachable.", None
        except Exception as e:
            logger.exception("Error testing connection")
            return False, f"Error: {str(e)}", None

    async def get_version(self) -> Optional[str]:
        """Get SonarQube server version."""
        try:
            response = await self.client.get("/api/system/status")
            if response.status_code == 200:
                return response.json().get("version")
        except Exception:
            pass
        return None

    async def list_projects(
        self,
        q: Optional[str] = None,
        page: int = 1,
        page_size: int = 100
    ) -> list[SonarQubeProject]:
        """List projects from SonarQube or SonarCloud.
        
        Args:
            q: Search query for project name/key
            page: Page number
            page_size: Results per page
            
        Returns:
            List of projects
        """
        params = {
            "p": page,
            "ps": page_size,
        }
        
        # SonarCloud requires organization parameter
        if self.is_sonarcloud and self.organization:
            params["organization"] = self.organization
        elif self.is_sonarcloud:
            raise ValueError("SonarCloud requires an organization. Please set the organization in connection settings.")
        
        if q:
            params["q"] = q

        response = await self.client.get("/api/projects/search", params=params)
        response.raise_for_status()
        
        data = response.json()
        projects = []
        
        for component in data.get("components", []):
            projects.append(SonarQubeProject(
                key=component["key"],
                name=component["name"],
                visibility=component.get("visibility", "public"),
                lastAnalysisDate=component.get("lastAnalysisDate"),
            ))
        
        return projects

    async def get_project_metrics(self, project_key: str) -> SonarQubeMetrics:
        """Get metrics for a specific project.
        
        Args:
            project_key: SonarQube project key
            
        Returns:
            Project metrics
        """
        # SonarQube uses component measures API
        response = await self.client.get(
            "/api/measures/component",
            params={
                "component": project_key,
                "metricKeys": "bugs,vulnerabilities,code_smells,coverage,ncloc,duplicated_lines_density,sqale_index,alert_status"
            }
        )
        response.raise_for_status()
        
        data = response.json()
        metrics_map = {}
        
        for measure in data.get("component", {}).get("measures", []):
            metric_key = measure["metric"]
            value = measure.get("value")
            
            # alert_status is a string, not a number
            if metric_key == "alert_status":
                metrics_map[metric_key] = value
            # Parse value based on metric type
            elif metric_key in ("coverage", "duplicated_lines_density"):
                metrics_map[metric_key] = float(value) if value is not None else None
            else:
                metrics_map[metric_key] = int(value) if value is not None else None
        
        return SonarQubeMetrics(
            bugs=metrics_map.get("bugs"),
            vulnerabilities=metrics_map.get("vulnerabilities"),
            code_smells=metrics_map.get("code_smells"),
            coverage=metrics_map.get("coverage"),
            ncloc=metrics_map.get("ncloc"),
            duplicated_lines_density=metrics_map.get("duplicated_lines_density"),
            alert_status=metrics_map.get("alert_status"),
            sqale_index=metrics_map.get("sqale_index"),
        )

    async def search_issues(
        self,
        project_key: str,
        types: Optional[list[str]] = None,
        severities: Optional[list[str]] = None,
        statuses: Optional[list[str]] = None,
        page: int = 1,
        page_size: int = 50
    ) -> tuple[list[SonarQubeIssue], int]:
        """Search issues for a project.
        
        Args:
            project_key: SonarQube project key
            types: Issue types (BUG, VULNERABILITY, CODE_SMELL)
            severities: Issue severities (INFO, MINOR, MAJOR, CRITICAL, BLOCKER)
            statuses: Issue statuses
            page: Page number
            page_size: Results per page
            
        Returns:
            Tuple of (issues, total count)
        """
        params = {
            "componentKeys": project_key,
            "p": page,
            "ps": page_size,
        }
        
        if types:
            params["types"] = ",".join(types)
        if severities:
            params["severities"] = ",".join(severities)
        if statuses:
            params["statuses"] = ",".join(statuses)
        
        response = await self.client.get("/api/issues/search", params=params)
        response.raise_for_status()
        
        data = response.json()
        issues = []
        
        for issue_data in data.get("issues", []):
            # Parse effort (time to fix)
            effort = None
            if issue_data.get("effort"):
                try:
                    effort = int(float(issue_data["effort"]))
                except (ValueError, TypeError):
                    pass
            
            issues.append(SonarQubeIssue(
                key=issue_data["key"],
                type=issue_data["type"],
                severity=issue_data["severity"],
                status=issue_data["status"],
                message=issue_data.get("message"),
                rule=issue_data.get("rule"),
                component=issue_data.get("component"),
                line=issue_data.get("line"),
                effort=effort,
            ))
        
        total = data.get("total", 0)
        return issues, total

    async def get_trends(
        self,
        project_key: str,
        metrics: list[str],
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None
    ) -> dict[str, list[dict]]:
        """Get historical trend data for a project.
        
        Args:
            project_key: SonarQube project key
            metrics: List of metrics to fetch
            from_date: Start date for trends
            to_date: End date for trends
            
        Returns:
            Dict mapping metric names to list of data points
        """
        # Map our metric names to SonarQube metric keys
        metric_mapping = {
            "bugs": "bugs",
            "vulnerabilities": "vulnerabilities",
            "code_smells": "code_smells",
            "coverage": "coverage",
        }
        
        sonar_metrics = [metric_mapping.get(m, m) for m in metrics]
        
        params = {
            "component": project_key,
            "metrics": ",".join(sonar_metrics),
        }
        
        if from_date:
            params["from"] = from_date.strftime("%Y-%m-%d")
        if to_date:
            params["to"] = to_date.strftime("%Y-%m-%d")
        
        response = await self.client.get("/api/measures/search_history", params=params)
        response.raise_for_status()
        
        data = response.json()
        trends = {}
        
        for metric_data in data.get("measures", []):
            metric_name = metric_data.get("metric")
            # Reverse mapping
            our_name = next((k for k, v in metric_mapping.items() if v == metric_name), metric_name)
            
            points = []
            for dp in metric_data.get("history", []):
                points.append({
                    "date": dp.get("date"),
                    "value": dp.get("value"),
                })
            
            trends[our_name] = points
        
        return trends
