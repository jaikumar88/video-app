"""
Main FastAPI application entry point.
Handles both local development and production deployment modes.
"""

import os
import logging
import sys


from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
import uvicorn

from app.core.config import get_settings
from app.core.database import create_tables, initialize_database
from app.api.auth import router as auth_router
from app.api.admin import router as admin_router
from app.api.meetings import router as meetings_router
from app.api.users import router as users_router
from app.api.websocket import router as websocket_router


# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logging.getLogger().setLevel(logging.INFO)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    # Startup
    logger.info("Starting Video Calling Platform...")
    settings = get_settings()
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Database: {settings.DATABASE_URL}")

    # Initialize database connection
    initialize_database()

    # Initialize database tables
    await create_tables()
    logger.info("Database initialized successfully")
    
    # Create default admin user
    from app.core.database import get_db_session
    from app.services.auth_service import AuthService
    
    async with get_db_session() as db:
        auth_service = AuthService(db)
        admin_user = await auth_service.create_admin_user_if_not_exists()
        if admin_user:
            logger.info(f"🔧 Admin user available: {admin_user.email}")
        else:
            logger.warning("⚠️ Failed to create admin user")

    yield

    # Shutdown
    logger.info("Shutting down Video Calling Platform...")


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="WorldClass Video Calling Platform",
        description=(
            "A secure, scalable, and high-quality video conferencing platform"
        ),
        version="1.0.0",
        docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
        redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
        lifespan=lifespan,
    )

    # Request logging middleware
    @app.middleware("http")
    async def log_requests(request, call_next):
        logger.info(f"🌐 {request.method} {request.url}")
        logger.info(f"Headers: {dict(request.headers)}")
        response = await call_next(request)
        logger.info(f"Response: {response.status_code}")
        return response

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Allow all origins for development
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(auth_router, prefix="/api/v1/auth", tags=["Authentication"])
    app.include_router(admin_router, prefix="/api/v1/admin", tags=["Admin"])
    app.include_router(users_router, prefix="/api/v1/users", tags=["Users"])
    app.include_router(meetings_router, prefix="/api/v1/meetings", tags=["Meetings"])
    app.include_router(websocket_router, prefix="/ws", tags=["WebSocket"])

    # Static files for uploads and recordings
    if not os.path.exists("uploads"):
        os.makedirs("uploads")
    if not os.path.exists("recordings"):
        os.makedirs("recordings")

    app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
    app.mount("/recordings", StaticFiles(directory="recordings"), name="recordings")
    
    # Serve frontend static files
    if os.path.exists("static"):
        app.mount("/static", StaticFiles(directory="static"), name="static")

    @app.get("/")
    async def root():
        # Serve the frontend index.html for the root path
        if os.path.exists("static/index.html"):
            return FileResponse("static/index.html")
        return {
            "message": "WorldClass Video Calling Platform API",
            "version": "1.0.0",
            "environment": settings.ENVIRONMENT,
            "status": "running",
        }

    @app.get("/health")
    async def health_check():
        """Health check endpoint for load balancers."""
        return {"status": "healthy", "environment": settings.ENVIRONMENT}

    @app.exception_handler(404)
    async def not_found_handler(request, exc):
        # For frontend routes, serve the React app
        if request.url.path.startswith("/api") or request.url.path.startswith("/ws"):
            return JSONResponse(status_code=404, content={"message": "Resource not found"})
        # Serve React app for all other routes
        if os.path.exists("static/index.html"):
            return FileResponse("static/index.html")
        return JSONResponse(status_code=404, content={"message": "Resource not found"})

    @app.exception_handler(500)
    async def internal_server_error_handler(request, exc):
        logger.error(f"Internal server error: {exc}")
        return JSONResponse(
            status_code=500, content={"message": "Internal server error"}
        )

    return app


# Create the FastAPI application
app = create_app()


if __name__ == "__main__":
    settings = get_settings()

    if settings.ENVIRONMENT == "local":
        # Local development server
        uvicorn.run(
            "main:app", host="0.0.0.0", port=8000, reload=True, log_level="info"
        )
    else:
        # Production server (handled by docker-compose with multiple workers)
        uvicorn.run("main:app", host="0.0.0.0", port=8000, log_level="info")
