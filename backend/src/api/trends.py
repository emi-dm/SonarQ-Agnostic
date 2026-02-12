"""Trends API endpoints."""

import logging
from datetime import datetime
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..db.session import get_db
from ..models.entities import Project
from ..services.metrics_service import MetricsService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["trends"])


# Pydantic schemas
class TrendDataPoint(BaseModel):
    """Schema for a trend data point."""
    date: str
    value: Optional[float] = None


class TrendMetric(BaseModel):
    """Schema for a trend metric."""
    metric: str
    data_points: List[TrendDataPoint]


class TrendsResponse(BaseModel):
    """Schema for trends response."""
    project_id: str
    metrics: List[TrendMetric]


@router.get("/projects/{project_id}/trends", response_model=TrendsResponse)
async def get_trends(
    project_id: UUID,
    metrics: Optional[str] = Query(
        "bugs,vulnerabilities,code_smells,coverage",
        description="Comma-separated list of metrics"
    ),
    from_date: Optional[datetime] = Query(None, description="Start date (ISO format)"),
    to_date: Optional[datetime] = Query(None, description="End date (ISO format)"),
    db: Session = Depends(get_db)
) -> TrendsResponse:
    """Get historical trends for a project."""
    project = db.query(Project).filter(Project.id == str(project_id)).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Parse metrics list
    metric_list = [m.strip() for m in metrics.split(",") if m.strip()]
    valid_metrics = {"bugs", "vulnerabilities", "code_smells", "coverage"}
    
    for metric in metric_list:
        if metric not in valid_metrics:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid metric: {metric}. Valid metrics: {valid_metrics}"
            )
    
    metrics_service = MetricsService(db)
    trends_data = metrics_service.get_trends(str(project_id), from_date, to_date)
    
    # Build response
    result_metrics = []
    for metric in metric_list:
        data_points = trends_data.get(metric, [])
        result_metrics.append(TrendMetric(
            metric=metric,
            data_points=[TrendDataPoint(**dp) for dp in data_points]
        ))
    
    return TrendsResponse(
        project_id=str(project_id),
        metrics=result_metrics
    )
