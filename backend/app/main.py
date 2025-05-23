import os
import logging
from fastapi import FastAPI, Depends, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

# Import logging configuration first
from app.core.logging_config import setup_logging
from app.api.endpoints import leads as leads_router
from app.db.base import Base, engine

# Initialize logging
setup_logging()
logger = logging.getLogger(__name__)

# Create database tables
Base.metadata.create_all(bind=engine)

# Create uploads directory if it doesn't exist
os.makedirs("uploads/resumes", exist_ok=True)

app = FastAPI(
    title="Alma API",
    description="Backend API for the Alma application",
    version="0.1.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
    on_startup=[],
    on_shutdown=[]
)

# Add middleware to log requests
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Request: {request.method} {request.url}")
    try:
        response = await call_next(request)
        logger.info(f"Response: {request.method} {request.url} - Status: {response.status_code}")
        return response
    except Exception as e:
        logger.error(f"Error processing request {request.method} {request.url}: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": "Internal server error", "details": str(e)}
        )

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React and Vite dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Trusted Host Middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"],  # In production, replace with your domain
)

# Mount static files for uploaded resumes
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


# Include API router
from app.api.endpoints import router as api_router
app.include_router(api_router, prefix="/api")

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

@app.get("/api/")
async def read_root():
    """Root endpoint."""
    return {"message": "Welcome to Alma API"}
