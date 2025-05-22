from fastapi import FastAPI, status, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

import logging
import os
import time
from src.api.v1.router import router as api_router
from src.utils.error_handlers import ErrorType, ErrorHandlerMiddleware, http_exception_handler
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create FastAPI app with OpenAPI configuration
app = FastAPI(
    title="Bot Mail Proposal API",
    description="API for Automated Email Proposal System",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    swagger_ui_parameters={
        "persistAuthorization": True,
        "docExpansion": "none",
        "filter": True
    },
    openapi_version="3.0.2"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add our custom error handler middleware
app.add_middleware(ErrorHandlerMiddleware)

# Register the HTTP exception handler
app.add_exception_handler(HTTPException, http_exception_handler)

# Middleware for request logging and timing
@app.middleware("http")
async def log_and_time_requests(request: Request, call_next):
    """Log request details and timing"""
    start_time = time.time()
    
    response = await call_next(request)
    process_time = time.time() - start_time
    
    # Log request timing
    logger.info(
        f"Request: {request.method} {request.url.path} "
        f"Status: {response.status_code} Time: {process_time:.3f}s"
    )
    return response

# Handle validation errors
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handle validation errors and return standardized format
    """
    error_details = exc.errors()
    error_messages = []
    
    for error in error_details:
        location = " -> ".join(str(loc) for loc in error["loc"])
        message = error["msg"]
        error_messages.append(f"{location}: {message}")
    
    error_response = {
        "status_code": status.HTTP_422_UNPROCESSABLE_ENTITY,
        "error": ErrorType.INVALID_INPUT_FORMAT,
        "detail": error_messages,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    logger.error(f"Validation error: {error_messages}")
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_response
    )

# Include API router with prefix
app.include_router(api_router, prefix="/api/v1")

@app.on_event("shutdown")
def shutdown_event():
    """Close database connections on shutdown."""
    logger.info("Application shutting down")
    # Using asyncio.run could cause issues as it creates a new event loop
    # We'll keep the existing close_mongodb_connection call in lifespan instead

if __name__ == "__main__":
    import uvicorn
    
    # Get configuration from environment or use defaults
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    reload_enabled = os.getenv("API_RELOAD", "true").lower() == "true"
    
    logger.info(f"Starting application on {host}:{port} (reload: {reload_enabled})")
    uvicorn.run(
        "main:app", 
        host=host, 
        port=port, 
        reload=reload_enabled,
        log_level="info"
    )