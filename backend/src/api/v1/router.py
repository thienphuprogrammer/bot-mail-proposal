from fastapi import APIRouter
from src.api.v1.auth.routes import router as auth_router
from src.api.v1.emails.routes import router as emails_router
from src.api.v1.proposals.routes import router as proposals_router
from src.api.v1.templates.routes import router as templates_router

# Create main router
router = APIRouter()

# Include all routers
router.include_router(auth_router)
router.include_router(emails_router)
router.include_router(proposals_router)
router.include_router(templates_router)

# Add health check endpoint
@router.get("/health")
async def health_check():
    """
    Health check endpoint.
    """
    return {"status": "healthy"}