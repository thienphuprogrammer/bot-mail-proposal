from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from api.v1.auth.routes import get_current_user
from core.config import settings
import logging
import uuid

router = APIRouter()
logger = logging.getLogger(__name__)

# Proposal status enum (could be in a separate file)
class ProposalStatus(str):
    DRAFT = "draft"
    READY = "ready"
    SENT = "sent"
    ACCEPTED = "accepted"
    REJECTED = "rejected"

# Proposal models
class ProposalBase(BaseModel):
    title: str
    client_name: str
    client_email: str
    content: str
    
class ProposalCreate(ProposalBase):
    email_id: str
    
class Proposal(ProposalBase):
    id: str
    email_id: str
    status: str = ProposalStatus.DRAFT
    created_at: datetime
    updated_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    
    class Config:
        orm_mode = True

# Mock proposal data - replace with database calls in production
proposals_db = []

@router.get("/", response_model=List[Proposal])
async def get_proposals(
    skip: int = 0, 
    limit: int = 10, 
    status: Optional[str] = None,
    current_user = Depends(get_current_user)
):
    """
    Get all proposals, with optional filtering by status.
    """
    if status:
        filtered_proposals = [p for p in proposals_db if p["status"] == status]
    else:
        filtered_proposals = proposals_db
        
    return filtered_proposals[skip:skip+limit]

@router.get("/{proposal_id}", response_model=Proposal)
async def get_proposal(
    proposal_id: str,
    current_user = Depends(get_current_user)
):
    """
    Get a specific proposal by ID.
    """
    for proposal in proposals_db:
        if proposal["id"] == proposal_id:
            return proposal
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Proposal with ID {proposal_id} not found"
    )

@router.post("/", response_model=Proposal)
async def create_proposal(
    proposal: ProposalCreate,
    current_user = Depends(get_current_user)
):
    """
    Create a new proposal.
    """
    now = datetime.utcnow()
    new_proposal = {
        "id": str(uuid.uuid4()),
        **proposal.dict(),
        "status": ProposalStatus.DRAFT,
        "created_at": now,
        "updated_at": now,
        "sent_at": None
    }
    
    proposals_db.append(new_proposal)
    return new_proposal

@router.put("/{proposal_id}", response_model=Proposal)
async def update_proposal(
    proposal_id: str,
    proposal_update: ProposalBase,
    current_user = Depends(get_current_user)
):
    """
    Update a proposal.
    """
    for proposal in proposals_db:
        if proposal["id"] == proposal_id:
            # Update the proposal
            proposal.update(proposal_update.dict())
            proposal["updated_at"] = datetime.utcnow()
            return proposal
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Proposal with ID {proposal_id} not found"
    )

@router.post("/{proposal_id}/send", response_model=Proposal)
async def send_proposal(
    proposal_id: str,
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_user)
):
    """
    Send a proposal to the client.
    """
    # Find the proposal
    proposal = None
    for p in proposals_db:
        if p["id"] == proposal_id:
            proposal = p
            break
    
    if not proposal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Proposal with ID {proposal_id} not found"
        )
    
    if proposal["status"] == ProposalStatus.SENT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Proposal with ID {proposal_id} has already been sent"
        )
    
    # Schedule the proposal to be sent
    background_tasks.add_task(send_proposal_email, proposal_id)
    
    # Update proposal status
    proposal["status"] = ProposalStatus.READY
    proposal["updated_at"] = datetime.utcnow()
    
    return proposal

# Mock function for sending proposal by email
async def send_proposal_email(proposal_id: str):
    """Send a proposal by email."""
    logger.info(f"Sending proposal {proposal_id} by email...")
    
    # Find the proposal
    for proposal in proposals_db:
        if proposal["id"] == proposal_id:
            # In production, this would:
            # 1. Generate an email with the proposal content
            # 2. Send the email using Gmail API or SMTP
            # 3. Update the proposal status
            
            # Update the proposal
            proposal["status"] = ProposalStatus.SENT
            proposal["sent_at"] = datetime.utcnow()
            proposal["updated_at"] = datetime.utcnow()
            
            logger.info(f"Proposal {proposal_id} sent successfully")
            break 