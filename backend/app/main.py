"""FastAPI application main entry point."""
import logging
from contextlib import asynccontextmanager
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.config import settings
from app.api.v1 import users, events, ai, telegram_webhook
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


# Frontend assets directory (mounted at /app/static by docker-compose)
# Use absolute path to avoid /app/app/static mistake
FRONTEND_DIR = "/app/static"
INDEX_FILE = os.path.join(FRONTEND_DIR, "index.html")

# Create FastAPI app
app = FastAPI(
    title="Telegram Calendar Bot API",
    description="AI-powered calendar assistant for Telegram Mini App",
    version="1.0.0",
    lifespan=lifespan,
)

# Serve static frontend if available
if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

# CORS middleware
# In development, allow all origins; in production, use configured origins
cors_origins = ["*"] if settings.DEBUG else settings.CORS_ORIGINS
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(users.router, prefix="/api/v1")
app.include_router(events.router, prefix="/api/v1")
app.include_router(ai.router, prefix="/api/v1")
app.include_router(telegram_webhook.router)


@app.get("/", include_in_schema=False)
async def root():
    """Serve frontend index if present; otherwise show API info."""
    if os.path.exists(INDEX_FILE):
        return FileResponse(INDEX_FILE)
    return {"message": "Telegram Calendar Bot API", "version": "1.0.0"}


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/{full_path:path}", include_in_schema=False)
async def spa_fallback(full_path: str):
    """
    Serve the frontend index.html for non-API routes (SPA fallback).
    """
    # Do not hijack API or docs routes
    if full_path.startswith(("api", "docs", "openapi", "health", "redoc")):
        raise HTTPException(status_code=404)
    if os.path.exists(INDEX_FILE):
        return FileResponse(INDEX_FILE)
    raise HTTPException(status_code=404)


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

