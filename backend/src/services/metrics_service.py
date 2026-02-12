"""Metrics service for fetching and calculating metrics."""

import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import desc

from ..models.entities import MetricsSnapshot, Project

logger = logging.getLogger(__name__)


class MetricsService:
    """Service for managing metrics."""

    def __init__(self, db: Session):
        """Initialize metrics service.
        
        Args:
            db: Database session
        """
        self.db = db

    def get_current_metrics(self, project_id: str) -> Optional[MetricsSnapshot]:
        """Get the most recent metrics snapshot for a project.
        
        Args:
            project_id: Project ID
            
        Returns:
            Most recent metrics snapshot or None
        """
        return self.db.query(MetricsSnapshot).filter(
            MetricsSnapshot.project_id == project_id
        ).order_by(desc(MetricsSnapshot.snapshot_date)).first()

    def get_metrics_by_date_range(
        self,
        project_id: str,
        from_date: datetime,
        to_date: datetime
    ) -> list[MetricsSnapshot]:
        """Get metrics snapshots within a date range.
        
        Args:
            project_id: Project ID
            from_date: Start date
            to_date: End date
            
        Returns:
            List of metrics snapshots
        """
        return self.db.query(MetricsSnapshot).filter(
            MetricsSnapshot.project_id == project_id,
            MetricsSnapshot.snapshot_date >= from_date,
            MetricsSnapshot.snapshot_date <= to_date
        ).order_by(MetricsSnapshot.snapshot_date).all()

    def get_trends(
        self,
        project_id: str,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None
    ) -> dict:
        """Get trend data for a project.
        
        Args:
            project_id: Project ID
            from_date: Start date (default: 30 days ago)
            to_date: End date (default: now)
            
        Returns:
            Dict of metric trends
        """
        if to_date is None:
            to_date = datetime.now(timezone.utc)
        if from_date is None:
            from_date = to_date - timedelta(days=30)
        
        snapshots = self.get_metrics_by_date_range(project_id, from_date, to_date)
        
        # Build trend data
        trends = {
            "bugs": [],
            "vulnerabilities": [],
            "code_smells": [],
            "coverage": [],
        }
        
        for snapshot in snapshots:
            date_str = snapshot.snapshot_date.strftime("%Y-%m-%d")
            if snapshot.bugs is not None:
                trends["bugs"].append({"date": date_str, "value": snapshot.bugs})
            if snapshot.vulnerabilities is not None:
                trends["vulnerabilities"].append({"date": date_str, "value": snapshot.vulnerabilities})
            if snapshot.code_smells is not None:
                trends["code_smells"].append({"date": date_str, "value": snapshot.code_smells})
            if snapshot.coverage is not None:
                trends["coverage"].append({"date": date_str, "value": snapshot.coverage})
        
        return trends

    def is_stale(self, project_id: str, hours: int = 24) -> tuple[bool, Optional[datetime]]:
        """Check if project data is stale.
        
        Args:
            project_id: Project ID
            hours: Number of hours to consider stale (default: 24)
            
        Returns:
            Tuple of (is_stale, last_updated)
        """
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project or not project.last_analysis_date:
            return True, None
        
        now = datetime.now(timezone.utc)
        last_updated = project.last_analysis_date
        
        if last_updated.tzinfo is None:
            last_updated = last_updated.replace(tzinfo=timezone.utc)
        
        hours_since_update = (now - last_updated).total_seconds() / 3600
        is_stale = hours_since_update > hours
        
        return is_stale, last_updated
