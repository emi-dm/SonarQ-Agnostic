"""Connection API endpoints."""

import logging
from typing import Optional, Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..db.session import get_db
from ..models.entities import Connection
from ..services.sonar_client import SonarQubeClient

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/connections", tags=["connections"])


# Pydantic schemas
class ConnectionCreate(BaseModel):
    """Schema for creating a connection."""
    name: str = Field(..., min_length=1, max_length=100)
    url: str = Field(..., min_length=1)
    token: str = Field(..., min_length=1)
    organization: Optional[str] = Field(None, description="SonarCloud organization (required for sonarcloud.io)")
    is_default: bool = False


class ConnectionUpdate(BaseModel):
    """Schema for updating a connection."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    url: Optional[str] = Field(None, min_length=1)
    token: Optional[str] = Field(None, min_length=1)
    organization: Optional[str] = Field(None)
    is_default: Optional[bool] = None


class ConnectionResponse(BaseModel):
    """Schema for connection response (excludes token)."""
    id: str
    name: str
    url: str
    organization: Optional[str] = None
    is_default: bool
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class ConnectionTestResponse(BaseModel):
    """Schema for connection test response."""
    success: bool
    message: str
    version: Optional[str] = None


def connection_to_response(conn: Connection) -> ConnectionResponse:
    """Convert database connection to response schema."""
    return ConnectionResponse(
        id=conn.id,
        name=conn.name,
        url=conn.url,
        organization=conn.organization,
        is_default=conn.is_default,
        created_at=conn.created_at.isoformat(),
        updated_at=conn.updated_at.isoformat(),
    )


@router.get("")
async def list_connections(db: Annotated[Session, Depends(get_db)]) -> list[ConnectionResponse]:
    """List all SonarQube connections."""
    connections = db.query(Connection).all()
    return [connection_to_response(c) for c in connections]


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_connection(
    data: ConnectionCreate,
    db: Annotated[Session, Depends(get_db)]
) -> ConnectionResponse:
    """Create a new SonarQube connection."""
    # If this is set as default, unset other defaults
    if data.is_default:
        db.query(Connection).update({"is_default": False})
    
    connection = Connection(
        name=data.name,
        url=data.url,
        token=data.token,
        organization=data.organization,
        is_default=data.is_default,
    )
    db.add(connection)
    db.commit()
    db.refresh(connection)
    
    logger.info(f"Created connection: {connection.id}")
    return connection_to_response(connection)


@router.get("/{connection_id}")
async def get_connection(
    connection_id: UUID,
    db: Annotated[Session, Depends(get_db)]
) -> ConnectionResponse:
    """Get a specific connection."""
    connection = db.query(Connection).filter(Connection.id == str(connection_id)).first()
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")
    return connection_to_response(connection)


@router.put("/{connection_id}")
async def update_connection(
    connection_id: UUID,
    data: ConnectionUpdate,
    db: Annotated[Session, Depends(get_db)]
) -> ConnectionResponse:
    """Update a connection."""
    connection = db.query(Connection).filter(Connection.id == str(connection_id)).first()
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")
    
    # If setting as default, unset other defaults
    if data.is_default and not connection.is_default:
        db.query(Connection).filter(Connection.id != str(connection_id)).update({"is_default": False})
    
    # Update fields
    if data.name is not None:
        connection.name = data.name
    if data.url is not None:
        connection.url = data.url
    if data.token is not None:
        connection.token = data.token
    if data.organization is not None:
        connection.organization = data.organization
    if data.is_default is not None:
        connection.is_default = data.is_default
    
    db.commit()
    db.refresh(connection)
    
    logger.info(f"Updated connection: {connection.id}")
    return connection_to_response(connection)


@router.delete("/{connection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_connection(
    connection_id: UUID,
    db: Annotated[Session, Depends(get_db)]
) -> None:
    """Delete a connection."""
    connection = db.query(Connection).filter(Connection.id == str(connection_id)).first()
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")
    
    db.delete(connection)
    db.commit()
    
    logger.info(f"Deleted connection: {connection_id}")


@router.post("/{connection_id}/test")
async def test_connection(
    connection_id: UUID,
    db: Annotated[Session, Depends(get_db)]
) -> ConnectionTestResponse:
    """Test connection to SonarQube."""
    connection = db.query(Connection).filter(Connection.id == str(connection_id)).first()
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")
    
    client = SonarQubeClient(url=connection.url, token=connection.token, organization=connection.organization)
    try:
        success, message, version = await client.test_connection()
        return ConnectionTestResponse(
            success=success,
            message=message,
            version=version,
        )
    finally:
        await client.close()
