from enum import Enum
from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class ErrorType(str, Enum):
    """Error types for the application."""
    
    # General errors
    INTERNAL_SERVER_ERROR = "internal_server_error"
    NOT_FOUND = "not_found"
    INVALID_INPUT_FORMAT = "invalid_input_format"
    UNAUTHORIZED = "unauthorized"
    FORBIDDEN = "forbidden"
    
    # Domain-specific errors
    DATABASE_ERROR = "database_error"
    EMAIL_PROCESSING_ERROR = "email_processing_error"
    AI_SERVICE_ERROR = "ai_service_error"
    AUTHENTICATION_ERROR = "authentication_error"
    GMAIL_API_ERROR = "gmail_api_error"

class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """Middleware for handling errors."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Any:
        """Handle errors."""
        try:
            return await call_next(request)
        except Exception as e:
            # Log the error
            logger.exception(f"Unhandled exception: {str(e)}")
            
            # Create a standardized error response
            error_response = {
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "error": ErrorType.INTERNAL_SERVER_ERROR,
                "detail": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=error_response
            )

async def http_exception_handler(request: Request, exc: Exception):
    """
    Handle HTTP exceptions and return standardized format
    """
    # Create a standardized error response
    error_response = {
        "status_code": exc.status_code,
        "error": exc.detail if hasattr(exc, "error_type") else "http_error",
        "detail": exc.detail,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    logger.error(f"HTTP error {exc.status_code}: {exc.detail}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response
    ) 