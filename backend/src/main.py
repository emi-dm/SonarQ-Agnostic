"""FastAPI application entry point."""

import os
import logging
import sys
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from .api.connections import router as connections_router
from .api.projects import router as projects_router
from .api.issues import router as issues_router
from .api.trends import router as trends_router
from .config import get_settings
from .db.session import init_db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    logger.info("Starting SonarQube Visualizer...")
    init_db()
    logger.info("Database initialized")
    yield
    # Shutdown
    logger.info("Shutting down SonarQube Visualizer...")


app = FastAPI(
    title="SonarQube Visualizer",
    description="Web-based visualizer for SonarQube quality reports",
    version="1.0.0",
    lifespan=lifespan,
)

# Include API routers
app.include_router(connections_router)
app.include_router(projects_router)
app.include_router(issues_router)
app.include_router(trends_router)

# Serve static files
frontend_path = os.path.join(os.path.dirname(
    os.path.dirname(os.path.dirname(__file__))), "frontend")
app.mount(
    "/css", StaticFiles(directory=os.path.join(frontend_path, "css")), name="css")
app.mount("/js", StaticFiles(directory=os.path.join(frontend_path, "js")), name="js")

# Root route - serve index.html


@app.get("/")
async def root():
    """Serve the main HTML page."""
    from fastapi.responses import FileResponse
    return FileResponse(os.path.join(frontend_path, "index.html"))


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    timestamp: datetime


@app.get("/api/health")
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(timezone.utc)
    )


# Error handling middleware
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Global exception handler for consistent error responses."""
    logger.error(
        "Unhandled exception",
        extra={
            "path": str(request.url),
            "method": request.method,
            "error": str(exc),
            "error_type": type(exc).__name__,
        }
    )
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error. Please check logs for more information."
        }
    )
