"""Issues API endpoints."""

import logging
from typing import Optional, List, Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..db.session import get_db
from ..models.entities import Issue, Project

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["issues"])

# Valid values
VALID_TYPES = ["BUG", "VULNERABILITY", "CODE_SMELL"]
VALID_SEVERITIES = ["INFO", "MINOR", "MAJOR", "CRITICAL", "BLOCKER"]
VALID_STATUSES = ["OPEN", "CONFIRMED", "REOPENED", "RESOLVED", "CLOSED"]


# Pydantic schemas
class IssueResponse(BaseModel):
    """Schema for issue response."""
    id: str
    project_id: str
    sonar_key: str
    type: str
    severity: str
    status: str
    message: Optional[str] = None
    rule: Optional[str] = None
    component: Optional[str] = None
    line: Optional[int] = None
    effort: Optional[int] = None

    class Config:
        from_attributes = True


class PaginationResponse(BaseModel):
    """Schema for pagination response."""
    page: int
    page_size: int
    total: int
    total_pages: int


class IssuesListResponse(BaseModel):
    """Schema for issues list response."""
    issues: List[IssueResponse]
    pagination: PaginationResponse


def issue_to_response(issue: Issue) -> IssueResponse:
    """Convert database issue to response schema."""
    return IssueResponse(
        id=issue.id,
        project_id=issue.project_id,
        sonar_key=issue.sonar_key,
        type=issue.type,
        severity=issue.severity,
        status=issue.status,
        message=issue.message,
        rule=issue.rule,
        component=issue.component,
        line=issue.line,
        effort=issue.effort,
    )


@router.get("/projects/{project_id}/issues")
async def list_issues(
    project_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    type: Optional[str] = Query(None, description="Issue type: BUG, VULNERABILITY, CODE_SMELL"),
    severity: Optional[str] = Query(None, description="Issue severity: INFO, MINOR, MAJOR, CRITICAL, BLOCKER"),
    status: Optional[str] = Query(None, description="Issue status: OPEN, CONFIRMED, REOPENED, RESOLVED, CLOSED"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=500, description="Results per page")
) -> IssuesListResponse:
    """Search issues for a project."""
    project = db.query(Project).filter(Project.id == str(project_id)).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Validate filters
    if type and type not in VALID_TYPES:
        raise HTTPException(status_code=400, detail=f"Invalid type. Must be one of: {VALID_TYPES}")
    if severity and severity not in VALID_SEVERITIES:
        raise HTTPException(status_code=400, detail=f"Invalid severity. Must be one of: {VALID_SEVERITIES}")
    if status and status not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {VALID_STATUSES}")
    
    # Build query
    query = db.query(Issue).filter(Issue.project_id == str(project_id))
    
    if type:
        query = query.filter(Issue.type == type)
    if severity:
        query = query.filter(Issue.severity == severity)
    if status:
        query = query.filter(Issue.status == status)
    
    # Get total count
    total = query.count()
    total_pages = (total + page_size - 1) // page_size
    
    # Paginate
    offset = (page - 1) * page_size
    issues = query.offset(offset).limit(page_size).all()
    
    return IssuesListResponse(
        issues=[issue_to_response(i) for i in issues],
        pagination=PaginationResponse(
            page=page,
            page_size=page_size,
            total=total,
            total_pages=total_pages,
        )
    )


@router.get("/issues/{issue_id}")
async def get_issue(
    issue_id: UUID,
    db: Annotated[Session, Depends(get_db)]
) -> IssueResponse:
    """Get issue details."""
    issue = db.query(Issue).filter(Issue.id == str(issue_id)).first()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    return issue_to_response(issue)
