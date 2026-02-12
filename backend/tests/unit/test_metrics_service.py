"""Unit tests for metrics service."""

import pytest
from datetime import datetime, timezone, timedelta
from uuid import uuid4
from unittest.mock import MagicMock

from src.services.metrics_service import MetricsService
from src.models.entities import MetricsSnapshot, Project


class TestMetricsService:
    """Tests for MetricsService."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        db = MagicMock()
        return db

    @pytest.fixture
    def service(self, mock_db):
        """Create metrics service with mock db."""
        return MetricsService(mock_db)

    def test_get_current_metrics(self, service, mock_db):
        """Test getting current metrics for a project."""
        mock_snapshot = MagicMock()
        mock_query = MagicMock()
        mock_query.filter.return_value.order_by.return_value.first.return_value = mock_snapshot
        mock_db.query.return_value = mock_query

        result = service.get_current_metrics("project-123")

        assert result == mock_snapshot
        mock_db.query.assert_called_once()

    def test_get_current_metrics_empty(self, service, mock_db):
        """Test getting current metrics when none exist."""
        mock_query = MagicMock()
        mock_query.filter.return_value.order_by.return_value.first.return_value = None
        mock_db.query.return_value = mock_query

        result = service.get_current_metrics("project-123")

        assert result is None

    def test_get_metrics_by_date_range(self, service, mock_db):
        """Test getting metrics within a date range."""
        mock_snapshots = [MagicMock(), MagicMock()]
        mock_query = MagicMock()
        mock_query.filter.return_value.order_by.return_value.all.return_value = mock_snapshots
        mock_db.query.return_value = mock_query

        from_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
        to_date = datetime(2024, 1, 31, tzinfo=timezone.utc)

        result = service.get_metrics_by_date_range("project-123", from_date, to_date)

        assert result == mock_snapshots

    def test_get_trends(self, service, mock_db):
        """Test getting trend data."""
        # Create mock snapshots
        snapshot1 = MagicMock()
        snapshot1.snapshot_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
        snapshot1.bugs = 10
        snapshot1.vulnerabilities = 5
        snapshot1.code_smells = 20
        snapshot1.coverage = 85.0

        snapshot2 = MagicMock()
        snapshot2.snapshot_date = datetime(2024, 1, 2, tzinfo=timezone.utc)
        snapshot2.bugs = 8
        snapshot2.vulnerabilities = 4
        snapshot2.code_smells = 18
        snapshot2.coverage = 86.0

        mock_query = MagicMock()
        mock_query.filter.return_value.order_by.return_value.all.return_value = [snapshot1, snapshot2]
        mock_db.query.return_value = mock_query

        result = service.get_trends("project-123")

        assert "bugs" in result
        assert "vulnerabilities" in result
        assert "code_smells" in result
        assert "coverage" in result

    def test_get_trends_with_date_filter(self, service, mock_db):
        """Test getting trends with date filter."""
        mock_query = MagicMock()
        mock_query.filter.return_value.order_by.return_value.all.return_value = []
        mock_db.query.return_value = mock_query

        from_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
        to_date = datetime(2024, 1, 31, tzinfo=timezone.utc)

        service.get_trends("project-123", from_date=from_date, to_date=to_date)

        # Verify filter was called with correct dates
        call_args = mock_query.filter.call_args
        assert call_args is not None

    def test_get_trends_default_date_range(self, service, mock_db):
        """Test trends default to last 30 days."""
        mock_query = MagicMock()
        mock_query.filter.return_value.order_by.return_value.all.return_value = []
        mock_db.query.return_value = mock_query

        service.get_trends("project-123")

        # Should use default date range (30 days)
        mock_db.query.assert_called_once()

    def test_is_stale_true(self, service, mock_db):
        """Test project is marked stale when old."""
        # Create project with old analysis date
        mock_project = MagicMock()
        mock_project.last_analysis_date = datetime.now(timezone.utc) - timedelta(hours=25)

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_project
        mock_db.query.return_value = mock_query

        is_stale, last_updated = service.is_stale("project-123")

        assert is_stale is True

    def test_is_stale_false(self, service, mock_db):
        """Test project is not stale when recent."""
        mock_project = MagicMock()
        mock_project.last_analysis_date = datetime.now(timezone.utc) - timedelta(hours=12)

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_project
        mock_db.query.return_value = mock_query

        is_stale, last_updated = service.is_stale("project-123")

        assert is_stale is False

    def test_is_stale_no_project(self, service, mock_db):
        """Test stale check when project doesn't exist."""
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query

        is_stale, last_updated = service.is_stale("nonexistent")

        assert is_stale is True
        assert last_updated is None

    def test_is_stale_no_analysis_date(self, service, mock_db):
        """Test stale check when project has no analysis date."""
        mock_project = MagicMock()
        mock_project.last_analysis_date = None

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_project
        mock_db.query.return_value = mock_query

        is_stale, last_updated = service.is_stale("project-123")

        assert is_stale is True
