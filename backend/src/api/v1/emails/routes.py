from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from api.v1.auth.routes import get_current_user
from core.config import settings
import logging
from bson import ObjectId
from models.email import Email as EmailModel
from services.mail.core.mail_factory import MailServiceFactory
from repositories.email_repository import EmailRepository

router = APIRouter()
logger = logging.getLogger(__name__)

# Email models
class EmailBase(BaseModel):
    subject: str
    sender: str
    body: str
    
class EmailResponse(EmailBase):
    id: str
    received_at: datetime
    processed: bool
    
    class Config:
        orm_mode = True

# Initialize repositories and services
email_repository = EmailRepository()
mail_service = MailServiceFactory.create_default_outlook_facade()

@router.get("/", response_model=List[EmailResponse])
async def get_emails(
    skip: int = 0, 
    limit: int = 20, 
    processed: Optional[bool] = None,
    current_user = Depends(get_current_user)
):
    """
    Get all emails, with optional filtering by processed status.
    """
    filter_dict = {}
    if processed is not None:
        filter_dict["processed"] = processed
        
    emails = email_repository.find_all(
        filter_dict=filter_dict,
        skip=skip,
        limit=limit
    )
    
    # Convert to API response format
    results = []
    for email in emails:
        results.append({
            "id": str(email.id),
            "subject": email.subject,
            "sender": email.sender,
            "body": email.body,
            "received_at": email.received_at,
            "processed": email.processed
        })
    
    return results

@router.get("/{email_id}", response_model=Dict[str, Any])
async def get_email(
    email_id: str,
    current_user = Depends(get_current_user)
):
    """
    Get a specific email by ID.
    """
    try:
        email = email_repository.find_by_id(email_id)
        if not email:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Email with ID {email_id} not found"
            )
        
        # Convert to dictionary with string ID
        email_dict = email.__dict__
        email_dict["id"] = str(email_dict["id"])
        
        return email_dict
    except Exception as e:
        logger.error(f"Error retrieving email {email_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving email: {str(e)}"
        )

@router.post("/sync")
async def sync_emails(
    background_tasks: BackgroundTasks,
    max_results: int = 20,
    current_user = Depends(get_current_user)
):
    """
    Trigger email synchronization with Outlook (async background task).
    """
    try:
        background_tasks.add_task(
            fetch_emails_task,
            max_results=max_results
        )
        return {"status": "Email synchronization started"}
    except Exception as e:
        logger.error(f"Error triggering email sync: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error triggering email sync: {str(e)}"
        )

@router.post("/process/{email_id}")
async def process_email(
    email_id: str,
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_user)
):
    """
    Process a specific email to generate a proposal.
    """
    try:
        email = email_repository.find_by_id(email_id)
        if not email:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Email with ID {email_id} not found"
            )
        
        if email.processed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Email with ID {email_id} has already been processed"
            )
        
        # Add task to process email
        from services.proposal.core.proposal_factory import ProposalServiceFactory
        from repositories.proposal_repository import ProposalRepository
        from repositories.sent_email_repository import SentEmailRepository
        
        # Initialize required services
        proposal_repository = ProposalRepository()
        sent_email_repository = SentEmailRepository()
        
        # Create proposal service
        proposal_service = ProposalServiceFactory.create_proposal_facade(
            proposal_repository=proposal_repository,
            email_repository=email_repository,
            sent_email_repository=sent_email_repository,
            mail_service=mail_service
        )
        
        # Process in background
        background_tasks.add_task(
            process_email_task,
            email_id=email_id,
            proposal_service=proposal_service
        )
        
        return {"status": f"Processing started for email {email_id}"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing email {email_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing email: {str(e)}"
        )

# Actual function for email fetching
async def fetch_emails_task(max_results: int = 20):
    """Fetch emails from Outlook."""
    logger.info(f"Fetching up to {max_results} emails from Outlook...")
    try:
        result = mail_service.fetch_and_process_emails(
            query="isRead eq false",
            max_results=max_results,
            folder="inbox",
            include_spam_trash=True,
            only_recent=True
        )
        
        if isinstance(result, dict):
            fetched_count = result.get("fetched", 0)
            processed_count = result.get("processed", 0)
            logger.info(f"Fetched {fetched_count} emails, processed {processed_count}")
        elif isinstance(result, list):
            logger.info(f"Processed {len(result)} emails")
        else:
            logger.info("Email fetch completed")
    except Exception as e:
        logger.error(f"Error fetching emails: {str(e)}")
        raise

# Actual function for email processing
async def process_email_task(email_id: str, proposal_service: Any):
    """Process an email to generate a proposal."""
    logger.info(f"Processing email {email_id}...")
    try:
        proposal_id = proposal_service.analyze_email(email_id)
        if proposal_id:
            logger.info(f"Email {email_id} processed successfully, proposal {proposal_id} created")
        else:
            logger.error(f"Failed to generate proposal for email {email_id}")
    except Exception as e:
        logger.error(f"Error processing email {email_id}: {str(e)}")
        raise
