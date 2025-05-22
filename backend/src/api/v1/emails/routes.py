from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional, Dict, Any
from datetime import datetime
from bson import ObjectId

from src.models.email import Email, EmailCreate
from src.services.mail.core.mail_factory import MailServiceFactory
from src.repositories.email_repository import EmailRepository
# from src.core.auth import get_current_user

router = APIRouter(prefix="/emails", tags=["emails"])

@router.get("/", response_model=List[Email])
async def list_emails(
    show_processed: bool = Query(True, description="Show processed emails"),
    show_unprocessed: bool = Query(True, description="Show unprocessed emails"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    # current_user: Dict = Depends(get_current_user)
):
    """
    List emails with optional filtering.
    """
    try:
        # Build filter
        filter_dict = {}
        if show_processed and not show_unprocessed:
            filter_dict["processed"] = True
        elif not show_processed and show_unprocessed:
            filter_dict["processed"] = False

        email_repository = EmailRepository()
        emails = email_repository.find_all(filter_dict=filter_dict, skip=skip, limit=limit)
        return emails
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{email_id}", response_model=Email)
async def get_email(
    email_id: str,
    # current_user: Dict = Depends(get_current_user)
):
    """
    Get a specific email by ID.
    """
    try:
        email_repository = EmailRepository()
        email = email_repository.find_by_id(email_id)
        if not email:
            raise HTTPException(status_code=404, detail="Email not found")
        return email
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sync")
async def sync_emails(
    query: str = Query("isRead eq false", description="Email query filter"),
    max_results: int = Query(20, ge=1, le=100),
    folder: str = Query("inbox", description="Email folder to sync"),
    include_spam_trash: bool = Query(True, description="Include spam and trash"),
    only_recent: bool = Query(True, description="Only sync recent emails"),
    # current_user: Dict = Depends(get_current_user)
):
    """
    Sync emails from the email service.
    """
    try:
        mail_service = MailServiceFactory.create_default_outlook_facade()
        result = mail_service.fetch_and_process_emails(
            query=query,
            max_results=max_results,
            folder=folder,
            include_spam_trash=include_spam_trash,
            only_recent=only_recent
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{email_id}/process")
async def process_email(
    email_id: str,
    # current_user: Dict = Depends(get_current_user)
):
    """
    Process an email into a proposal.
    """
    try:
        from src.services.proposal.core.proposal_factory import ProposalServiceFactory
        from src.repositories.proposal_repository import ProposalRepository
        from src.repositories.email_repository import EmailRepository
        from src.services.mail.core.mail_factory import MailServiceFactory

        # Initialize services
        email_repository = EmailRepository()
        proposal_repository = ProposalRepository()
        mail_service = MailServiceFactory.create_default_outlook_facade()
        
        # Create proposal service
        proposal_service = ProposalServiceFactory.create_proposal_facade(
            proposal_repository=proposal_repository,
            email_repository=email_repository,
            sent_email_repository=None,  # Not needed for processing
            mail_service=mail_service
        )

        # Process email
        proposal_id = proposal_service.analyze_email(email_id)
        if not proposal_id:
            raise HTTPException(status_code=400, detail="Failed to generate proposal")

        return {"proposal_id": str(proposal_id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats/summary")
async def get_email_stats(
    # current_user: Dict = Depends(get_current_user)
):
    """
    Get email statistics summary.
    """
    try:
        email_repository = EmailRepository()
        
        # Get total emails
        total_emails = len(email_repository.find_all(filter_dict={}, skip=0, limit=1000))
        
        # Get unprocessed emails
        unprocessed_emails = len(email_repository.find_all(
            filter_dict={"processing_status": "pending"}, 
            skip=0, 
            limit=1000
        ))

        return {
            "total_emails": total_emails,
            "unprocessed_emails": unprocessed_emails
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
