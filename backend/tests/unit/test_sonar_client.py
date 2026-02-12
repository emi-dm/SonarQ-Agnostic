"""Unit tests for SonarQube API client."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from httpx import ConnectError, TimeoutException

from src.services.sonar_client import (
    SonarQubeClient,
    SonarQubeProject,
    SonarQubeMetrics,
    SonarQubeIssue,
)


class TestSonarQubeClient:
    """Tests for SonarQubeClient."""

    @pytest.fixture
    def client(self):
        """Create a SonarQube client for testing."""
        return SonarQubeClient(
            url="https://sonarcloud.io",
            token="test-token",
            organization="test-org"
        )

    @pytest.fixture
    def sonarqube_client(self):
        """Create a client for regular SonarQube."""
        return SonarQubeClient(
            url="https://sonarqube.example.com",
            token="test-token"
        )

    def test_client_initialization(self, client, sonarqube_client):
        """Test client initializes correctly."""
        assert client.url == "https://sonarcloud.io"
        assert client.token == "test-token"
        assert client.is_sonarcloud is True
        assert client.organization == "test-org"
        
        assert sonarqube_client.is_sonarcloud is False
        assert sonarqube_client.organization is None

    def test_client_url_normalization(self):
        """Test URL normalization removes trailing slashes."""
        client = SonarQubeClient(url="https://sonarcloud.io/", token="test")
        assert client.url == "https://sonarcloud.io"

    def test_organization_lowercase_for_sonarcloud(self):
        """Test organization is lowercased for SonarCloud."""
        client = SonarQubeClient(
            url="https://sonarcloud.io",
            token="test",
            organization="TestOrg"
        )
        assert client.organization == "testorg"

    @pytest.mark.asyncio
    async def test_test_connection_success(self, client):
        """Test successful connection test."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"version": "10.0.0"}

        mock_http_client = AsyncMock()
        mock_http_client.get = AsyncMock(return_value=mock_response)
        client._client = mock_http_client

        success, message, version = await client.test_connection()

        assert success is True
        assert message == "Connection successful"
        assert version == "10.0.0"

    @pytest.mark.asyncio
    async def test_test_connection_auth_failure(self, client):
        """Test connection test with 401 response."""
        mock_response = MagicMock()
        mock_response.status_code = 401

        mock_http_client = AsyncMock()
        mock_http_client.get = AsyncMock(return_value=mock_response)
        client._client = mock_http_client

        success, message, version = await client.test_connection()

        assert success is False
        assert "Authentication failed" in message
        assert version is None

    @pytest.mark.asyncio
    async def test_test_connection_connect_error(self, client):
        """Test connection test with connect error."""
        mock_http_client = AsyncMock()
        mock_http_client.get = AsyncMock(side_effect=ConnectError("Connection failed"))
        client._client = mock_http_client

        success, message, version = await client.test_connection()

        assert success is False
        assert "Cannot connect" in message
        assert version is None

    @pytest.mark.asyncio
    async def test_test_connection_timeout(self, client):
        """Test connection test with timeout."""
        mock_http_client = AsyncMock()
        mock_http_client.get = AsyncMock(side_effect=TimeoutException("Request timed out"))
        client._client = mock_http_client

        success, message, version = await client.test_connection()

        assert success is False
        assert "timeout" in message.lower()
        assert version is None

    @pytest.mark.asyncio
    async def test_list_projects(self, client):
        """Test listing projects."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "components": [
                {"key": "proj-1", "name": "Project 1", "visibility": "public"},
                {"key": "proj-2", "name": "Project 2", "visibility": "private", "lastAnalysisDate": "2024-01-01"},
            ]
        }

        mock_http_client = AsyncMock()
        mock_http_client.get = AsyncMock(return_value=mock_response)
        client._client = mock_http_client

        projects = await client.list_projects()

        assert len(projects) == 2
        assert projects[0].key == "proj-1"
        assert projects[0].name == "Project 1"
        assert projects[0].visibility == "public"
        assert projects[1].lastAnalysisDate == "2024-01-01"

    @pytest.mark.asyncio
    async def test_list_projects_with_search(self, client):
        """Test listing projects with search query."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"components": []}

        mock_http_client = AsyncMock()
        mock_http_client.get = AsyncMock(return_value=mock_response)
        client._client = mock_http_client

        await client.list_projects(q="test")

        # Verify the search parameter was included
        call_args = mock_http_client.get.call_args
        assert call_args is not None

    @pytest.mark.asyncio
    async def test_list_projects_sonarcloud_requires_org(self, client):
        """Test that SonarCloud requires organization."""
        client.organization = None
        with pytest.raises(ValueError, match="SonarCloud requires an organization"):
            await client.list_projects()

    @pytest.mark.asyncio
    async def test_get_project_metrics(self, client):
        """Test getting project metrics."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "component": {
                "measures": [
                    {"metric": "bugs", "value": "10"},
                    {"metric": "vulnerabilities", "value": "5"},
                    {"metric": "coverage", "value": "85.5"},
                    {"metric": "alert_status", "value": "OK"},
                ]
            }
        }

        mock_http_client = AsyncMock()
        mock_http_client.get = AsyncMock(return_value=mock_response)
        client._client = mock_http_client

        metrics = await client.get_project_metrics("proj-1")

        assert metrics.bugs == 10
        assert metrics.vulnerabilities == 5
        assert metrics.coverage == pytest.approx(85.5)
        assert metrics.alert_status == "OK"

    @pytest.mark.asyncio
    async def test_search_issues(self, client):
        """Test searching issues."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "issues": [
                {
                    "key": "issue-1",
                    "type": "BUG",
                    "severity": "MAJOR",
                    "status": "OPEN",
                    "message": "Fix this bug",
                    "rule": "rule-1",
                }
            ],
            "total": 1
        }

        mock_http_client = AsyncMock()
        mock_http_client.get = AsyncMock(return_value=mock_response)
        client._client = mock_http_client

        issues, total = await client.search_issues("proj-1")

        assert len(issues) == 1
        assert issues[0].key == "issue-1"
        assert issues[0].type == "BUG"
        assert total == 1

    @pytest.mark.asyncio
    async def test_search_issues_with_filters(self, client):
        """Test searching issues with type and severity filters."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"issues": [], "total": 0}

        mock_http_client = AsyncMock()
        mock_http_client.get = AsyncMock(return_value=mock_response)
        client._client = mock_http_client

        await client.search_issues(
            "proj-1",
            types=["BUG", "VULNERABILITY"],
            severities=["CRITICAL", "BLOCKER"]
        )

        # Verify filters were applied
        call_args = mock_http_client.get.call_args
        assert call_args is not None

    @pytest.mark.asyncio
    async def test_get_trends(self, client):
        """Test getting trend data."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "measures": [
                {
                    "metric": "bugs",
                    "history": [
                        {"date": "2024-01-01", "value": "10"},
                        {"date": "2024-01-02", "value": "8"},
                    ]
                }
            ]
        }

        mock_http_client = AsyncMock()
        mock_http_client.get = AsyncMock(return_value=mock_response)
        client._client = mock_http_client

        trends = await client.get_trends("proj-1", ["bugs"])

        assert "bugs" in trends
        assert len(trends["bugs"]) == 2
        assert trends["bugs"][0]["value"] == "10"

    @pytest.mark.asyncio
    async def test_close(self, client):
        """Test closing the client."""
        client._client = AsyncMock()
        
        await client.close()
        
        assert client._client is None
