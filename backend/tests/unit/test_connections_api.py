"""Unit tests for connection API endpoints."""

import pytest
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


class TestConnectionEndpoints:
    """Tests for connection API endpoints."""

    def test_list_connections_empty(self, client):
        """Test listing connections when none exist."""
        response = client.get("/api/connections")
        assert response.status_code == 200
        assert response.json() == []

    def test_create_connection(self, client):
        """Test creating a new connection."""
        payload = {
            "name": "Test Connection",
            "url": "https://sonarcloud.io",
            "token": "test-token",
            "organization": "test-org",
            "is_default": True
        }
        response = client.post("/api/connections", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Connection"
        assert data["url"] == "https://sonarcloud.io"
        assert data["organization"] == "test-org"
        assert data["is_default"] is True
        assert "id" in data
        assert "token" not in data

    def test_create_connection_validation_error(self, client):
        """Test creating connection with invalid data."""
        payload = {"name": "Test"}
        response = client.post("/api/connections", json=payload)
        assert response.status_code == 422

    def test_create_connection_sets_default(self, client):
        """Test creating default connection unsets others."""
        payload1 = {
            "name": "Connection 1",
            "url": "https://sonarcloud.io",
            "token": "token1",
            "is_default": True
        }
        client.post("/api/connections", json=payload1)

        payload2 = {
            "name": "Connection 2",
            "url": "https://sonarqube.com",
            "token": "token2",
            "is_default": True
        }
        response = client.post("/api/connections", json=payload2)
        assert response.status_code == 201

        connections = client.get("/api/connections").json()
        assert len(connections) == 2
        conn1 = next(c for c in connections if c["name"] == "Connection 1")
        conn2 = next(c for c in connections if c["name"] == "Connection 2")
        assert conn1["is_default"] is False
        assert conn2["is_default"] is True

    def test_get_connection(self, client):
        """Test getting a specific connection."""
        create_resp = client.post("/api/connections", json={
            "name": "Test",
            "url": "https://sonarcloud.io",
            "token": "test"
        })
        conn_id = create_resp.json()["id"]

        response = client.get(f"/api/connections/{conn_id}")
        assert response.status_code == 200
        assert response.json()["name"] == "Test"

    def test_get_connection_not_found(self, client):
        """Test getting non-existent connection."""
        fake_id = str(uuid4())
        response = client.get(f"/api/connections/{fake_id}")
        assert response.status_code == 404

    def test_update_connection(self, client):
        """Test updating a connection."""
        create_resp = client.post("/api/connections", json={
            "name": "Test",
            "url": "https://sonarcloud.io",
            "token": "test"
        })
        conn_id = create_resp.json()["id"]

        response = client.put(f"/api/connections/{conn_id}", json={
            "name": "Updated Name",
            "is_default": True
        })
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["is_default"] is True

    def test_update_connection_not_found(self, client):
        """Test updating non-existent connection."""
        fake_id = str(uuid4())
        response = client.put(f"/api/connections/{fake_id}", json={"name": "Test"})
        assert response.status_code == 404

    def test_delete_connection(self, client):
        """Test deleting a connection."""
        create_resp = client.post("/api/connections", json={
            "name": "Test",
            "url": "https://sonarcloud.io",
            "token": "test"
        })
        conn_id = create_resp.json()["id"]

        response = client.delete(f"/api/connections/{conn_id}")
        assert response.status_code == 204

        response = client.get(f"/api/connections/{conn_id}")
        assert response.status_code == 404

    def test_delete_connection_not_found(self, client):
        """Test deleting non-existent connection."""
        fake_id = str(uuid4())
        response = client.delete(f"/api/connections/{fake_id}")
        assert response.status_code == 404


class TestConnectionValidation:
    """Property-based tests for connection validation."""

    def test_connection_name_length_limits(self, client):
        """Test connection name length validation."""
        response = client.post("/api/connections", json={
            "name": "x" * 101,
            "url": "https://test.com",
            "token": "test"
        })
        assert response.status_code == 422

        response = client.post("/api/connections", json={
            "name": "",
            "url": "https://test.com",
            "token": "test"
        })
        assert response.status_code == 422

    def test_url_validation(self, client):
        """Test URL validation."""
        response = client.post("/api/connections", json={
            "name": "Test",
            "url": "",
            "token": "test"
        })
        assert response.status_code == 422

    def test_token_required(self, client):
        """Test token is required."""
        response = client.post("/api/connections", json={
            "name": "Test",
            "url": "https://test.com",
            "token": ""
        })
        assert response.status_code == 422
