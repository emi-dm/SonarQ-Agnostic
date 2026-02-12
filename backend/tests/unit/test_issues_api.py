"""Unit tests for issues API endpoints."""

import pytest
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.main import app
from src.db.session import get_db
from src.models.entities import Base, Connection, Project, Issue


@pytest.fixture(scope="function")
def test_engine():
    """Create a fresh in-memory database for each test."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(test_engine):
    """Create a database session for each test."""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    db = TestingSessionLocal()
    yield db
    db.close()


@pytest.fixture(scope="function")
def client(db_session, test_engine):
    """Create test client with database override."""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def sample_project(db_session):
    """Create a sample project for testing."""
    conn = Connection(
        id=str(uuid4()),
        name="Test Conn",
        url="https://sonarcloud.io",
        token="test-token"
    )
    db_session.add(conn)
    
    project = Project(
        id=str(uuid4()),
        connection_id=conn.id,
        sonar_key="test-project",
        name="Test Project",
        visibility="public"
    )
    db_session.add(project)
    db_session.commit()
    return project


class TestIssuesEndpoints:
    """Tests for issues API endpoints."""

    def test_list_issues_empty(self, client, sample_project):
        """Test listing issues when none exist."""
        response = client.get(f"/api/projects/{sample_project.id}/issues")
        assert response.status_code == 200
        data = response.json()
        assert data["issues"] == []
        assert data["pagination"]["total"] == 0

    def test_list_issues_project_not_found(self, client):
        """Test listing issues for non-existent project."""
        fake_id = str(uuid4())
        response = client.get(f"/api/projects/{fake_id}/issues")
        assert response.status_code == 404

    def test_list_issues_with_pagination(self, client, db_session, sample_project):
        """Test issues pagination."""
        for i in range(10):
            issue = Issue(
                id=str(uuid4()),
                project_id=sample_project.id,
                sonar_key=f"issue-{i}",
                type="BUG",
                severity="MAJOR",
                status="OPEN",
                message=f"Issue {i}"
            )
            db_session.add(issue)
        db_session.commit()

        response = client.get(f"/api/projects/{sample_project.id}/issues?page=1&page_size=5")
        assert response.status_code == 200
        data = response.json()
        assert len(data["issues"]) == 5
        assert data["pagination"]["total"] == 10
        assert data["pagination"]["total_pages"] == 2

    def test_list_issues_filter_by_type(self, client, db_session, sample_project):
        """Test filtering issues by type."""
        for issue_type in ["BUG", "VULNERABILITY", "CODE_SMELL"]:
            issue = Issue(
                id=str(uuid4()),
                project_id=sample_project.id,
                sonar_key=f"issue-{issue_type}",
                type=issue_type,
                severity="MAJOR",
                status="OPEN"
            )
            db_session.add(issue)
        db_session.commit()

        response = client.get(f"/api/projects/{sample_project.id}/issues?type=BUG")
        assert response.status_code == 200
        data = response.json()
        assert len(data["issues"]) == 1
        assert data["issues"][0]["type"] == "BUG"

    def test_list_issues_filter_by_severity(self, client, db_session, sample_project):
        """Test filtering issues by severity."""
        for severity in ["INFO", "MINOR", "CRITICAL"]:
            issue = Issue(
                id=str(uuid4()),
                project_id=sample_project.id,
                sonar_key=f"issue-{severity}",
                type="BUG",
                severity=severity,
                status="OPEN"
            )
            db_session.add(issue)
        db_session.commit()

        response = client.get(f"/api/projects/{sample_project.id}/issues?severity=CRITICAL")
        assert response.status_code == 200
        data = response.json()
        assert len(data["issues"]) == 1
        assert data["issues"][0]["severity"] == "CRITICAL"

    def test_list_issues_filter_by_status(self, client, db_session, sample_project):
        """Test filtering issues by status."""
        for status in ["OPEN", "CLOSED"]:
            issue = Issue(
                id=str(uuid4()),
                project_id=sample_project.id,
                sonar_key=f"issue-{status}",
                type="BUG",
                severity="MAJOR",
                status=status
            )
            db_session.add(issue)
        db_session.commit()

        response = client.get(f"/api/projects/{sample_project.id}/issues?status=OPEN")
        assert response.status_code == 200
        data = response.json()
        assert len(data["issues"]) == 1
        assert data["issues"][0]["status"] == "OPEN"

    def test_list_issues_invalid_type(self, client, sample_project):
        """Test filtering with invalid type returns 400."""
        response = client.get(f"/api/projects/{sample_project.id}/issues?type=INVALID")
        assert response.status_code == 400
        assert "Invalid type" in response.json()["detail"]

    def test_list_issues_invalid_severity(self, client, sample_project):
        """Test filtering with invalid severity returns 400."""
        response = client.get(f"/api/projects/{sample_project.id}/issues?severity=INVALID")
        assert response.status_code == 400
        assert "Invalid severity" in response.json()["detail"]

    def test_list_issues_invalid_status(self, client, sample_project):
        """Test filtering with invalid status returns 400."""
        response = client.get(f"/api/projects/{sample_project.id}/issues?status=INVALID")
        assert response.status_code == 400
        assert "Invalid status" in response.json()["detail"]

    def test_get_issue(self, client, db_session, sample_project):
        """Test getting a specific issue."""
        issue = Issue(
            id=str(uuid4()),
            project_id=sample_project.id,
            sonar_key="test-issue",
            type="BUG",
            severity="MAJOR",
            status="OPEN",
            message="Test issue"
        )
        db_session.add(issue)
        db_session.commit()

        response = client.get(f"/api/issues/{issue.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["sonar_key"] == "test-issue"
        assert data["message"] == "Test issue"

    def test_get_issue_not_found(self, client):
        """Test getting non-existent issue."""
        fake_id = str(uuid4())
        response = client.get(f"/api/issues/{fake_id}")
        assert response.status_code == 404


class TestIssuesFilteringLogic:
    """Tests for issue filtering validation logic."""

    VALID_TYPES = ["BUG", "VULNERABILITY", "CODE_SMELL"]
    VALID_SEVERITIES = ["INFO", "MINOR", "MAJOR", "CRITICAL", "BLOCKER"]
    VALID_STATUSES = ["OPEN", "CONFIRMED", "REOPENED", "RESOLVED", "CLOSED"]

    def test_all_valid_types_accepted(self, client, sample_project):
        """Test all valid issue types are accepted."""
        for issue_type in self.VALID_TYPES:
            response = client.get(f"/api/projects/{sample_project.id}/issues?type={issue_type}")
            assert response.status_code == 200, f"Type {issue_type} should be valid"

    def test_all_valid_severities_accepted(self, client, sample_project):
        """Test all valid severities are accepted."""
        for severity in self.VALID_SEVERITIES:
            response = client.get(f"/api/projects/{sample_project.id}/issues?severity={severity}")
            assert response.status_code == 200, f"Severity {severity} should be valid"

    def test_all_valid_statuses_accepted(self, client, sample_project):
        """Test all valid statuses are accepted."""
        for status in self.VALID_STATUSES:
            response = client.get(f"/api/projects/{sample_project.id}/issues?status={status}")
            assert response.status_code == 200, f"Status {status} should be valid"

    def test_combined_filters(self, client, db_session, sample_project):
        """Test combining multiple filters."""
        issues = [
            Issue(id=str(uuid4()), project_id=sample_project.id, sonar_key=f"bug-critical-{i}",
                  type="BUG", severity="CRITICAL", status="OPEN")
            for i in range(3)
        ]
        issues.extend([
            Issue(id=str(uuid4()), project_id=sample_project.id, sonar_key=f"bug-major-{i}",
                  type="BUG", severity="MAJOR", status="OPEN")
            for i in range(2)
        ])
        for issue in issues:
            db_session.add(issue)
        db_session.commit()

        response = client.get(
            f"/api/projects/{sample_project.id}/issues?type=BUG&severity=CRITICAL"
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["issues"]) == 3
