"""API entry point for Vercel deployment."""

import os
import sys
from pathlib import Path

# Add the current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, JSONResponse
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="AI Tutoring Assistant",
    version="1.0.0",
    description="A personalized tutoring assistant with AI capabilities"
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

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint - redirect to frontend."""
    return RedirectResponse(url="/frontend/index.html")

# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "platform": "Vercel"
    }

# Simple API endpoints for testing
@app.get("/api/test")
async def test_api():
    """Test API endpoint."""
    return {"message": "API is working!", "status": "success"}

# Try to import and include routers, but don't fail if they don't work
try:
    from app.api import auth, content, quiz
    from app.api.chat import router as chat_router
    
    # Include routers (they already have their own prefixes)
    app.include_router(auth.router)
    app.include_router(chat_router)
    app.include_router(quiz.router)
    app.include_router(content.router)
    
    logger.info("Successfully imported and included all routers with /api/v1 prefix")
except Exception as e:
    logger.error(f"Error importing routers: {e}")
    # Create a simple fallback endpoint
    @app.get("/api/fallback")
    async def fallback():
        return {"message": "Some features may not be available", "error": str(e)}