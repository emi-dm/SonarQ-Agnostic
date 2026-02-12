"""Database models for SonarQube Visualizer."""

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


class Connection(Base):
    """SonarQube connection configuration."""

    __tablename__ = "connections"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    token: Mapped[str] = mapped_column(Text, nullable=False)
    organization: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)  # For SonarCloud
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    projects: Mapped[list["Project"]] = relationship(
        "Project",
        back_populates="connection",
        cascade="all, delete-orphan"
    )


class Project(Base):
    """Project fetched from SonarQube."""

    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    connection_id: Mapped[str] = mapped_column(String(36), ForeignKey("connections.id"), nullable=False)
    sonar_key: Mapped[str] = mapped_column(String(200), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    visibility: Mapped[str] = mapped_column(String(20), nullable=False)
    last_analysis_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    connection: Mapped["Connection"] = relationship("Connection", back_populates="projects")
    metrics_snapshots: Mapped[list["MetricsSnapshot"]] = relationship(
        "MetricsSnapshot",
        back_populates="project",
        cascade="all, delete-orphan"
    )
    issues: Mapped[list["Issue"]] = relationship(
        "Issue",
        back_populates="project",
        cascade="all, delete-orphan"
    )


class MetricsSnapshot(Base):
    """Point-in-time snapshot of project metrics."""

    __tablename__ = "metrics_snapshots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id"), nullable=False)
    snapshot_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    bugs: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    vulnerabilities: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    code_smells: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    coverage: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ncloc: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    duplicated_lines_density: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    alert_status: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    sqale_index: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="metrics_snapshots")


class Issue(Base):
    """Issue (bug, vulnerability, code smell) from SonarQube."""

    __tablename__ = "issues"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id"), nullable=False)
    sonar_key: Mapped[str] = mapped_column(String(200), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    rule: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    component: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    line: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    effort: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="issues")


# Database indexes for performance
__table_args__ = (
    Index("idx_projects_connection", "connection_id"),
    Index("idx_metrics_project_date", "project_id", "snapshot_date"),
    Index("idx_issues_project", "project_id"),
    Index("idx_issues_type_severity", "type", "severity"),
)
