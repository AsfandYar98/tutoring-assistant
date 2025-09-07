"""Main FastAPI application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import logging
from app.core.config import settings
from app.api import auth, content, quiz
from app.api.chat import router as chat_router
from app.core.database import engine, Base

# Configure logging
logging.basicConfig(level=getattr(logging, settings.log_level))
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="A personalized tutoring assistant with AI capabilities",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/frontend", StaticFiles(directory="frontend"), name="frontend")

# Include routers
app.include_router(auth.router)
app.include_router(chat_router)
app.include_router(quiz.router)
app.include_router(content.router)


@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    logger.info("Starting AI Tutoring Assistant API")
    
    # Create database tables
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        # Don't raise in production, just log the error
        pass


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "AI Tutoring Assistant API",
        "version": settings.app_version,
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": settings.app_version
    }