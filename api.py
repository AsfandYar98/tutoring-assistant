"""API entry point for Vercel deployment."""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
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

# Import and include routers
try:
    from app.api import auth, content, quiz
    from app.api.chat import router as chat_router
    
    app.include_router(auth.router)
    app.include_router(chat_router)
    app.include_router(quiz.router)
    app.include_router(content.router)
    
    logger.info("Successfully imported and included all routers")
except Exception as e:
    logger.error(f"Error importing routers: {e}")

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint - redirect to frontend."""
    from fastapi.responses import RedirectResponse
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