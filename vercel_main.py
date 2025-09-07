"""Simplified Vercel main FastAPI application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import logging
from app.core.vercel_config import settings
from app.api import auth, content, quiz
from app.api.vercel_chat import router as chat_router

# Configure logging
logging.basicConfig(level=getattr(logging, settings.log_level))
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="AI Tutoring Assistant",
    version="1.0.0",
    description="A personalized tutoring assistant",
    docs_url="/docs"
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


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "AI Tutoring Assistant API",
        "version": "1.0.0",
        "status": "running",
        "platform": "Vercel"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "platform": "Vercel"
    }