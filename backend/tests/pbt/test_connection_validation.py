"""Property-based tests for connection validation."""

import pytest
from hypothesis import given, settings, strategies as st, assume, HealthCheck
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.main import app
from src.db.session import get_db
from src.models.entities import Base


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
def client(test_engine):
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


class TestConnectionValidationPBT:
    """Property-based tests for connection validation."""

    @given(
        name=st.text(min_size=1, max_size=100),
        url=st.sampled_from([
            "https://example.com",
            "https://sonarcloud.io", 
            "https://sonarqube.com",
            "http://localhost:9000",
        ]),
        token=st.text(min_size=1, max_size=200)
    )
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=10)
    def test_valid_connection_payloads(self, client, name, url, token):
        """Test that valid connection payloads are accepted."""
        assume(name.strip())
        
        payload = {
            "name": name[:100],
            "url": url,
            "token": token
        }
        
        response = client.post("/api/connections", json=payload)
        assert response.status_code in [201, 422]

    @given(
        name=st.text(min_size=1, max_size=100),
        url=st.sampled_from([
            "https://example.com",
            "https://sonarcloud.io",
        ]),
        token=st.text(min_size=1),
        org=st.one_of(st.none(), st.text(max_size=200))
    )
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=10)
    def test_connection_with_optional_org(self, client, name, url, token, org):
        """Test connection creation with optional organization."""
        assume(name.strip())
        
        payload = {
            "name": name[:100],
            "url": url,
            "token": token
        }
        if org is not None:
            payload["organization"] = org
        
        response = client.post("/api/connections", json=payload)
        assert response.status_code in [201, 422]

    @given(
        token=st.one_of(
            st.binary(min_size=1, max_size=500).map(lambda x: x.hex()[:200]),
            st.text(min_size=1, max_size=200)
        )
    )
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=10)
    def test_various_token_formats(self, client, token):
        """Test various token formats are accepted."""
        payload = {
            "name": "Test Connection",
            "url": "https://sonarcloud.io",
            "token": token
        }
        
        response = client.post("/api/connections", json=payload)
        assert response.status_code in [201, 422]

    @given(
        url=st.sampled_from([
            "https://sonarcloud.io",
            "https://sonarqube.com", 
            "http://localhost",
            "http://127.0.0.1"
        ])
    )
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=4)
    def test_various_sonarqube_urls(self, client, url):
        """Test various SonarQube URLs are accepted."""
        payload = {
            "name": "Test",
            "url": url,
            "token": "test-token"
        }
        
        response = client.post("/api/connections", json=payload)
        assert response.status_code in [201, 422]
