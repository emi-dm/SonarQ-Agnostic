"""Project sync service."""

import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from ..models.entities import Connection, MetricsSnapshot, Project
from ..services.sonar_client import SonarQubeClient

logger = logging.getLogger(__name__)


class SyncService:
    """Service for syncing data from SonarQube."""

    def __init__(self, db: Session):
        """Initialize sync service.
        
        Args:
            db: Database session
        """
        self.db = db

    async def sync_projects(self, connection_id: str) -> int:
        """Sync projects from SonarQube to local database.
        
        Args:
            connection_id: Connection ID
            
        Returns:
            Number of projects synced
        """
        # Get connection
        connection = self.db.query(Connection).filter(Connection.id == connection_id).first()
        if not connection:
            raise ValueError(f"Connection not found: {connection_id}")
        
        # Create SonarQube client
        client = SonarQubeClient(
            url=connection.url, 
            token=connection.token,
            organization=connection.organization
        )
        
        try:
            # Fetch projects from SonarQube
            sq_projects = await client.list_projects()
            
            synced_count = 0
            for sq_project in sq_projects:
                # Check if project already exists
                existing = self.db.query(Project).filter(
                    Project.connection_id == connection_id,
                    Project.sonar_key == sq_project.key
                ).first()
                
                if existing:
                    # Update existing project
                    existing.name = sq_project.name
                    existing.visibility = sq_project.visibility
                    if sq_project.lastAnalysisDate:
                        existing.last_analysis_date = datetime.fromisoformat(
                            sq_project.lastAnalysisDate.replace("Z", "+00:00")
                        )
                else:
                    # Create new project
                    project = Project(
                        connection_id=connection_id,
                        sonar_key=sq_project.key,
                        name=sq_project.name,
                        visibility=sq_project.visibility,
                        last_analysis_date=datetime.fromisoformat(
                            sq_project.lastAnalysisDate.replace("Z", "+00:00")
                        ) if sq_project.lastAnalysisDate else None,
                    )
                    self.db.add(project)
                
                synced_count += 1
            
            self.db.commit()
            logger.info(f"Synced {synced_count} projects for connection {connection_id}")
            return synced_count
            
        finally:
            await client.close()

    async def sync_metrics(self, project_id: str) -> Optional[MetricsSnapshot]:
        """Sync metrics for a project from SonarQube.
        
        Args:
            project_id: Project ID
            
        Returns:
            Created metrics snapshot
        """
        # Get project
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise ValueError(f"Project not found: {project_id}")
        
        # Get connection
        connection = self.db.query(Connection).filter(Connection.id == project.connection_id).first()
        if not connection:
            raise ValueError(f"Connection not found: {project.connection_id}")
        
        # Create SonarQube client
        client = SonarQubeClient(
            url=connection.url, 
            token=connection.token,
            organization=connection.organization
        )
        
        try:
            # Fetch metrics from SonarQube
            sq_metrics = await client.get_project_metrics(project.sonar_key)
            
            # Create snapshot
            snapshot = MetricsSnapshot(
                project_id=project_id,
                snapshot_date=datetime.now(timezone.utc),
                bugs=sq_metrics.bugs,
                vulnerabilities=sq_metrics.vulnerabilities,
                code_smells=sq_metrics.code_smells,
                coverage=sq_metrics.coverage,
                ncloc=sq_metrics.ncloc,
                duplicated_lines_density=sq_metrics.duplicated_lines_density,
                alert_status=sq_metrics.alert_status,
                sqale_index=sq_metrics.sqale_index,
            )
            
            self.db.add(snapshot)
            self.db.commit()
            self.db.refresh(snapshot)
            
            # Update project's last_analysis_date
            project.last_analysis_date = datetime.now(timezone.utc)
            self.db.commit()
            
            logger.info(f"Synced metrics for project {project_id}")
            return snapshot
            
        finally:
            await client.close()
