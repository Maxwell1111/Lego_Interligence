"""
FastAPI application for LEGO Architect web interface.
"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

from lego_architect.web.routes import builds, patterns, validation, export


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="LEGO Architect",
        description="Build and visualize LEGO creations with physical validation",
        version="1.0.0",
    )

    # Include routers
    app.include_router(builds.router, prefix="/api/builds", tags=["builds"])
    app.include_router(patterns.router, prefix="/api/patterns", tags=["patterns"])
    app.include_router(validation.router, prefix="/api/validation", tags=["validation"])
    app.include_router(export.router, prefix="/api/export", tags=["export"])

    # Serve static files
    static_dir = Path(__file__).parent / "static"
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    @app.get("/", include_in_schema=False)
    async def root():
        """Serve the main HTML page."""
        index_path = static_dir / "index.html"
        return FileResponse(str(index_path))

    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "healthy", "service": "lego-architect"}

    return app


# Create app instance for uvicorn
app = create_app()
