"""Project API endpoints."""

import logging
from typing import Optional, Annotated
from uuid import UUID

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..db.session import get_db
from ..models.entities import Connection, Project
from ..services.metrics_service import MetricsService
from ..services.sync_service import SyncService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["projects"])


# Pydantic schemas
class ProjectResponse(BaseModel):
    """Schema for project response."""
    id: str
    connection_id: str
    sonar_key: str
    name: str
    visibility: str
    last_analysis_date: Optional[str] = None

    class Config:
        from_attributes = True


class ProjectWithMetrics(BaseModel):
    """Schema for project with metrics."""
    project: ProjectResponse
    metrics: Optional[dict]
    staleness: Optional[dict]


class ProjectSyncResponse(BaseModel):
    """Schema for project sync response."""
    synced_count: int
    message: str


class MetricsResponse(BaseModel):
    """Schema for metrics response."""
    project_id: str
    bugs: Optional[int] = None
    vulnerabilities: Optional[int] = None
    code_smells: Optional[int] = None
    coverage: Optional[float] = None
    ncloc: Optional[int] = None
    duplicated_lines_density: Optional[float] = None
    alert_status: Optional[str] = None
    sqale_index: Optional[int] = None
    snapshot_date: str


def project_to_response(proj: Project) -> ProjectResponse:
    """Convert database project to response schema."""
    return ProjectResponse(
        id=proj.id,
        connection_id=proj.connection_id,
        sonar_key=proj.sonar_key,
        name=proj.name,
        visibility=proj.visibility,
        last_analysis_date=proj.last_analysis_date.isoformat() if proj.last_analysis_date else None,
    )


@router.get("/connections/{connection_id}/projects")
async def list_projects(
    connection_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    q: Optional[str] = None,
) -> list[ProjectResponse]:
    """List projects from a SonarQube connection."""
    connection = db.query(Connection).filter(Connection.id == str(connection_id)).first()
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")
    
    query = db.query(Project).filter(Project.connection_id == str(connection_id))
    
    if q:
        query = query.filter(Project.name.ilike(f"%{q}%"))
    
    projects = query.all()
    return [project_to_response(p) for p in projects]


@router.post("/connections/{connection_id}/projects")
async def sync_projects(
    connection_id: UUID,
    db: Annotated[Session, Depends(get_db)]
) -> ProjectSyncResponse:
    """Sync projects from SonarQube to local database."""
    connection = db.query(Connection).filter(Connection.id == str(connection_id)).first()
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")
    
    sync_service = SyncService(db)
    try:
        synced_count = await sync_service.sync_projects(str(connection_id))
        return ProjectSyncResponse(
            synced_count=synced_count,
            message=f"Successfully synced {synced_count} projects"
        )
    except Exception as e:
        logger.exception("Error syncing projects")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects")
async def list_all_projects(
    db: Annotated[Session, Depends(get_db)],
    connection_id: Optional[UUID] = None,
    search: Optional[str] = None,
) -> list[ProjectResponse]:
    """List all cached projects."""
    query = db.query(Project)
    
    if connection_id:
        query = query.filter(Project.connection_id == str(connection_id))
    
    if search:
        query = query.filter(Project.name.ilike(f"%{search}%"))
    
    projects = query.all()
    return [project_to_response(p) for p in projects]


@router.get("/projects/{project_id}")
async def get_project(
    project_id: UUID,
    db: Annotated[Session, Depends(get_db)]
) -> ProjectWithMetrics:
    """Get project details with current metrics."""
    project = db.query(Project).filter(Project.id == str(project_id)).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    metrics_service = MetricsService(db)
    metrics = metrics_service.get_current_metrics(str(project_id))
    is_stale, last_updated = metrics_service.is_stale(str(project_id))
    
    metrics_dict = None
    if metrics:
        metrics_dict = {
            "project_id": metrics.project_id,
            "bugs": metrics.bugs,
            "vulnerabilities": metrics.vulnerabilities,
            "code_smells": metrics.code_smells,
            "coverage": metrics.coverage,
            "ncloc": metrics.ncloc,
            "duplicated_lines_density": metrics.duplicated_lines_density,
            "alert_status": metrics.alert_status,
            "sqale_index": metrics.sqale_index,
            "snapshot_date": metrics.snapshot_date.isoformat(),
        }
    
    staleness_dict = {
        "is_stale": is_stale,
        "last_updated": last_updated.isoformat() if last_updated else None,
        "hours_since_update": int((datetime.now(timezone.utc) - last_updated).total_seconds() / 3600) if last_updated else None,
    }
    
    return ProjectWithMetrics(
        project=project_to_response(project),
        metrics=metrics_dict,
        staleness=staleness_dict,
    )


@router.post("/projects/{project_id}/refresh")
async def refresh_project_metrics(
    project_id: UUID,
    db: Annotated[Session, Depends(get_db)]
) -> MetricsResponse:
    """Refresh project metrics from SonarQube."""
    project = db.query(Project).filter(Project.id == str(project_id)).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    sync_service = SyncService(db)
    try:
        snapshot = await sync_service.sync_metrics(str(project_id))
        if not snapshot:
            raise HTTPException(status_code=500, detail="Failed to sync metrics")
        
        return MetricsResponse(
            project_id=snapshot.project_id,
            bugs=snapshot.bugs,
            vulnerabilities=snapshot.vulnerabilities,
            code_smells=snapshot.code_smells,
            coverage=snapshot.coverage,
            ncloc=snapshot.ncloc,
            duplicated_lines_density=snapshot.duplicated_lines_density,
            alert_status=snapshot.alert_status,
            sqale_index=snapshot.sqale_index,
            snapshot_date=snapshot.snapshot_date.isoformat(),
        )
    except Exception as e:
        logger.exception("Error refreshing metrics")
        raise HTTPException(status_code=500, detail=str(e))

