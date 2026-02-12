"""Property-based tests for issue severity/type validation."""

import pytest
from hypothesis import given, settings, strategies as st, HealthCheck
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.main import app
from src.db.session import get_db
from src.models.entities import Base, Connection, Project, Issue


# Valid constants
VALID_TYPES = ["BUG", "VULNERABILITY", "CODE_SMELL"]
VALID_SEVERITIES = ["INFO", "MINOR", "MAJOR", "CRITICAL", "BLOCKER"]
VALID_STATUSES = ["OPEN", "CONFIRMED", "REOPENED", "RESOLVED", "CLOSED"]


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


class TestIssueValidationPBT:
    """Property-based tests for issue filtering validation."""

    @given(type_=st.sampled_from(VALID_TYPES))
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=len(VALID_TYPES))
    def test_valid_issue_types(self, client, sample_project, type_):
        """Test all valid issue types are accepted."""
        response = client.get(f"/api/projects/{sample_project.id}/issues?type={type_}")
        assert response.status_code == 200

    @given(severity=st.sampled_from(VALID_SEVERITIES))
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=len(VALID_SEVERITIES))
    def test_valid_severities(self, client, sample_project, severity):
        """Test all valid severities are accepted."""
        response = client.get(f"/api/projects/{sample_project.id}/issues?severity={severity}")
        assert response.status_code == 200

    @given(status=st.sampled_from(VALID_STATUSES))
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=len(VALID_STATUSES))
    def test_valid_statuses(self, client, sample_project, status):
        """Test all valid statuses are accepted."""
        response = client.get(f"/api/projects/{sample_project.id}/issues?status={status}")
        assert response.status_code == 200

    @given(
        type_=st.one_of(st.sampled_from(VALID_TYPES), st.just(None)),
        severity=st.one_of(st.sampled_from(VALID_SEVERITIES), st.just(None)),
        status=st.one_of(st.sampled_from(VALID_STATUSES), st.just(None))
    )
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=20)
    def test_combined_filters(self, client, sample_project, type_, severity, status):
        """Test combining type, severity, and status filters."""
        params = []
        if type_:
            params.append(f"type={type_}")
        if severity:
            params.append(f"severity={severity}")
        if status:
            params.append(f"status={status}")
        
        query = "&".join(params) if params else ""
        url = f"/api/projects/{sample_project.id}/issues"
        if query:
            url += f"?{query}"
        
        response = client.get(url)
        
        assert response.status_code == 200
        data = response.json()
        assert "issues" in data
        assert "pagination" in data

    @given(invalid_type=st.sampled_from(["bug", "vulnerability", "code_smell", "error", "warning"]))
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=5)
    def test_invalid_type_rejected(self, client, sample_project, invalid_type):
        """Test invalid issue types are rejected."""
        response = client.get(f"/api/projects/{sample_project.id}/issues?type={invalid_type}")
        assert response.status_code == 400

    @given(invalid_severity=st.sampled_from(["trivial", "minor", "major", "critical", "blocker", "high", "low", "medium"]))
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=5)
    def test_invalid_severity_rejected(self, client, sample_project, invalid_severity):
        """Test invalid severities are rejected."""
        response = client.get(f"/api/projects/{sample_project.id}/issues?severity={invalid_severity}")
        assert response.status_code == 400

    @given(invalid_status=st.sampled_from(["new", "open", "closed", "fixed", "active", "inactive"]))
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=5)
    def test_invalid_status_rejected(self, client, sample_project, invalid_status):
        """Test invalid statuses are rejected."""
        response = client.get(f"/api/projects/{sample_project.id}/issues?status={invalid_status}")
        assert response.status_code == 400
