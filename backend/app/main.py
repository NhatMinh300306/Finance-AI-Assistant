"""
FinMate — AI Personal Finance Assistant
Main FastAPI application entry point.
"""

import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import get_settings
from app.db.database import init_db, SessionLocal
from app.api import transactions, chat, analytics, users
from app.utils.helpers import seed_demo_data

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

settings = get_settings()

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database and seed demo data on startup."""
    # Ensure data directory exists
    data_dir = Path(settings.DATABASE_URL.replace("sqlite:///", "")).parent
    data_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Initializing database...")
    init_db()

    logger.info("Seeding demo data...")
    db = SessionLocal()
    try:
        seed_demo_data(db)
    finally:
        db.close()

    logger.info(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION} started")
    yield

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-powered Personal Finance Management Assistant",
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

# Register API routers
app.include_router(transactions.router)
app.include_router(chat.router)
app.include_router(analytics.router)
app.include_router(users.router)


@app.get("/api/health", tags=["health"])
def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }


# Serve frontend static files
# Mount after API routes so API routes take precedence
frontend_path = Path(__file__).resolve().parent.parent.parent / "frontend"
if frontend_path.exists():
    app.mount("/", StaticFiles(directory=str(frontend_path), html=True), name="frontend")
