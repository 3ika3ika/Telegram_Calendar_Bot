"""FastAPI application main entry point."""
import logging
import os
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from app.config import settings
from app.api.v1 import users, events, ai
from app.workers.scheduler import start_scheduler, stop_scheduler

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown."""
    # Startup
    logger.info("Starting Telegram Calendar Bot API...")
    start_scheduler()
    yield
    # Shutdown
    logger.info("Shutting down Telegram Calendar Bot API...")
    stop_scheduler()


# Create FastAPI app
app = FastAPI(
    title="Telegram Calendar Bot API",
    description="AI-powered calendar assistant for Telegram Mini App",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(users.router, prefix="/api/v1")
app.include_router(events.router, prefix="/api/v1")
app.include_router(ai.router, prefix="/api/v1")

# Include telegram webhook router (no prefix, uses /telegram/webhook)
from app.api.v1 import telegram_webhook
app.include_router(telegram_webhook.router)

# Mount static files (frontend)
static_dir = Path("/app/static")
assets_dir = static_dir / "assets"

if static_dir.exists() and (static_dir / "index.html").exists():
    # Mount assets directory if it exists
    if assets_dir.exists() and assets_dir.is_dir():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")
    
    @app.get("/")
    async def root():
        """Serve frontend index.html."""
        index_path = static_dir / "index.html"
        if index_path.exists():
            return FileResponse(index_path)
        return {"message": "Telegram Calendar Bot API", "version": "1.0.0"}
    
    @app.get("/{path:path}")
    async def serve_frontend(path: str):
        """Serve frontend files, fallback to index.html for SPA routing."""
        # Don't serve API routes as static files
        if path.startswith("api/"):
            return JSONResponse(status_code=404, content={"detail": "Not found"})
        
        # Handle assets
        if path.startswith("assets/"):
            file_path = static_dir / path
            if file_path.exists() and file_path.is_file():
                return FileResponse(file_path)
            return JSONResponse(status_code=404, content={"detail": "Not found"})
        
        # For SPA routing, serve index.html for all non-API routes
        index_path = static_dir / "index.html"
        if index_path.exists():
            return FileResponse(index_path)
        
        return JSONResponse(status_code=404, content={"detail": "Not found"})
else:
    @app.get("/")
    async def root():
        """Root endpoint."""
        return {"message": "Telegram Calendar Bot API", "version": "1.0.0"}


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
    )

