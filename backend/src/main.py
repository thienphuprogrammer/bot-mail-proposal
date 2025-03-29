import os
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional, Dict, Any, Tuple
from datetime import timedelta

from src.core.config import settings
from src.database.mongodb import init_db
from src.models.user import User, UserCreate
from src.models.email import Email, SentEmail
from src.models.proposal import Proposal
from src.repositories.user_repository import UserRepository
from src.repositories.email_repository import EmailRepository
from src.repositories.proposal_repository import ProposalRepository
from src.repositories.sent_email_repository import SentEmailRepository
from src.services.gmail.gmail_service import GmailService
from src.services.model.langchain_service import LangChainService
from src.services.model.azure_service import AzureDeepseekService
from src.services.proposal.proposal_service import ProposalService
from src.services.authentication.auth_service import AuthService

# Initialize FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="API for automated proposal generation system"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Initialize repositories
user_repository = UserRepository()
email_repository = EmailRepository()
proposal_repository = ProposalRepository()
sent_email_repository = SentEmailRepository()

# Initialize services
auth_service = AuthService(user_repository=user_repository)
proposal_service = ProposalService(
    email_repository=email_repository,
    proposal_repository=proposal_repository,
    sent_email_repository=sent_email_repository
)

# Authentication
def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """Get current user from token."""
    user = auth_service.get_current_user(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

# Routes
@app.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login and get access token."""
    user = auth_service.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth_service.create_access_token(
        user_id=str(user.id),
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/users", response_model=User)
async def register_user(user_create: UserCreate):
    """Register a new user."""
    user = auth_service.register_user(user_create)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    
    return user

@app.get("/users/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    """Get current user information."""
    return current_user

@app.post("/emails/process")
async def process_emails(
    max_emails: int = 10,
    current_user: User = Depends(get_current_user)
):
    """Process new emails."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    # Process emails
    results = proposal_service.process_new_emails(max_emails=max_emails)
    
    # Format response
    processed_data = []
    for email, proposal in results:
        processed_data.append({
            "email_id": str(email.id),
            "proposal_id": str(proposal.id) if proposal else None,
            "subject": email.subject
        })
    
    return {"processed_emails": processed_data, "count": len(processed_data)}

@app.get("/emails", response_model=List[Email])
async def get_emails(
    skip: int = 0,
    limit: int = 10,
    current_user: User = Depends(get_current_user)
):
    """Get all emails."""
    return email_repository.find_all(filter_dict={}, skip=skip, limit=limit)

@app.get("/proposals", response_model=List[Proposal])
async def get_proposals(
    skip: int = 0,
    limit: int = 10,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get all proposals."""
    filter_dict = {}
    if status:
        filter_dict["status"] = status
    
    return proposal_repository.find_all(filter_dict=filter_dict, skip=skip, limit=limit)

@app.post("/proposals/{proposal_id}/approve")
async def approve_proposal(
    proposal_id: str,
    current_user: User = Depends(get_current_user)
):
    """Approve a proposal."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    success = proposal_service.approve_proposal(proposal_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Proposal not found or not in pending status",
        )
    
    return {"status": "approved"}

@app.post("/proposals/{proposal_id}/generate-pdf")
async def generate_pdf(
    proposal_id: str,
    current_user: User = Depends(get_current_user)
):
    """Generate PDF for a proposal."""
    pdf_path = proposal_service.generate_pdf(proposal_id)
    if not pdf_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Proposal not found or error generating PDF",
        )
    
    return {"pdf_path": pdf_path}

@app.post("/proposals/{proposal_id}/send")
async def send_proposal(
    proposal_id: str,
    current_user: User = Depends(get_current_user)
):
    """Send a proposal to the customer."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    success = proposal_service.send_proposal_to_customer(proposal_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Proposal not found or not in approved status",
        )
    
    return {"status": "sent"}

@app.get("/emails/{email_id}", response_model=Email)
async def get_email(
    email_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get email by ID."""
    email = email_repository.find_by_id(email_id)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email not found",
        )
    return email

@app.get("/proposals/{proposal_id}", response_model=Proposal)
async def get_proposal(
    proposal_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get proposal by ID."""
    proposal = proposal_repository.find_by_id(proposal_id)
    if not proposal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Proposal not found",
        )
    return proposal

@app.get("/workflow/{email_id}")
async def get_complete_workflow(
    email_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get complete workflow information for an email."""
    email, proposal = proposal_service.get_email_with_proposal(email_id)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email not found",
        )
    
    workflow_info = {
        "email": email,
        "proposal": proposal
    }
    
    return workflow_info

@app.get("/api/status")
async def get_api_status():
    """Get API status."""
    return {
        "status": "online",
        "version": settings.APP_VERSION,
        "using_azure": settings.USE_AZURE_AI,
        "model": "deepseek" if settings.USE_AZURE_AI else settings.LANGCHAIN_MODEL
    }

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    # Initialize database
    init_db()
    
    # Create admin user if not exists
    admin_email = os.getenv("ADMIN_EMAIL", "admin@example.com")
    admin_password = os.getenv("ADMIN_PASSWORD", "adminpassword")
    
    existing_admin = user_repository.find_by_email(admin_email)
    if not existing_admin:
        admin_user = UserCreate(
            email=admin_email,
            password=admin_password,
            full_name="Admin User",
            role="admin"
        )
        user_repository.create_user(admin_user)
        print(f"Created admin user: {admin_email}")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Close connections on shutdown."""
    from src.database.mongodb import MongoDB
    MongoDB.disconnect()

# Main entry point
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True) 