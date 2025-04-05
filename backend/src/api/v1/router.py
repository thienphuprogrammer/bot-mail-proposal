from fastapi import APIRouter
from api.v1.auth.routes import router as auth_router
from api.v1.emails.routes import router as emails_router
from api.v1.proposals.routes import router as proposals_router
from api.v1.templates.routes import router as templates_router

# Main API router
router = APIRouter(prefix="/api/v1")

# Include all the routers
router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
router.include_router(emails_router, prefix="/emails", tags=["Emails"])
router.include_router(proposals_router, prefix="/proposals", tags=["Proposals"])
router.include_router(templates_router, prefix="/templates", tags=["Templates"])