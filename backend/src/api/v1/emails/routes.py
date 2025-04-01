from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from api.v1.auth.routes import get_current_user
from core.config import settings
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

# Email models
class EmailBase(BaseModel):
    subject: str
    sender: str
    sender_email: str
    received_at: datetime
    body_text: str
    body_html: Optional[str] = None
    
class EmailCreate(EmailBase):
    gmail_id: str
    
class Email(EmailBase):
    id: str
    gmail_id: str
    is_processed: bool = False
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        orm_mode = True

# Mock email data - replace with database calls in production
emails_db = []

@router.get("/", response_model=List[Email])
async def get_emails(
    skip: int = 0, 
    limit: int = 10, 
    processed: Optional[bool] = None,
    current_user = Depends(get_current_user)
):
    """
    Get all emails, with optional filtering by processed status.
    """
    if processed is not None:
        filtered_emails = [email for email in emails_db if email["is_processed"] == processed]
    else:
        filtered_emails = emails_db
        
    return filtered_emails[skip:skip+limit]

@router.get("/{email_id}", response_model=Email)
async def get_email(
    email_id: str,
    current_user = Depends(get_current_user)
):
    """
    Get a specific email by ID.
    """
    for email in emails_db:
        if email["id"] == email_id:
            return email
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Email with ID {email_id} not found"
    )

@router.post("/sync")
async def sync_emails(
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_user)
):
    """
    Trigger email synchronization with Gmail (async background task).
    """
    # This would normally use a background task to sync emails from Gmail
    background_tasks.add_task(fetch_emails_from_gmail)
    return {"status": "Email synchronization started"}

@router.post("/process/{email_id}")
async def process_email(
    email_id: str,
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_user)
):
    """
    Process a specific email to generate a proposal.
    """
    # Find the email
    email = None
    for e in emails_db:
        if e["id"] == email_id:
            email = e
            break
    
    if not email:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Email with ID {email_id} not found"
        )
    
    if email["is_processed"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Email with ID {email_id} has already been processed"
        )
    
    # This would normally use a background task to process the email
    background_tasks.add_task(process_email_task, email_id)
    return {"status": f"Processing started for email {email_id}"}

# Mock function for email fetching (would use Gmail API in production)
async def fetch_emails_from_gmail():
    """Fetch emails from Gmail."""
    logger.info("Fetching emails from Gmail...")
    # In production, this would use the Gmail API
    # Add some mock data for now
    if not emails_db:
        emails_db.append({
            "id": "1",
            "gmail_id": "msg123",
            "subject": "Website Development Inquiry",
            "sender": "John Smith",
            "sender_email": "john@example.com",
            "received_at": datetime.utcnow(),
            "body_text": "Hello, I'm interested in developing a website for my business. Can you help?",
            "body_html": "<p>Hello, I'm interested in developing a website for my business. Can you help?</p>",
            "is_processed": False,
            "created_at": datetime.utcnow(),
            "updated_at": None
        })
        emails_db.append({
            "id": "2",
            "gmail_id": "msg456",
            "subject": "App Development Quote",
            "sender": "Jane Doe",
            "sender_email": "jane@example.com",
            "received_at": datetime.utcnow(),
            "body_text": "Hi, we need a mobile app for our startup. Please send a quote for development.",
            "body_html": "<p>Hi, we need a mobile app for our startup. Please send a quote for development.</p>",
            "is_processed": False,
            "created_at": datetime.utcnow(),
            "updated_at": None
        })
    logger.info(f"Fetched {len(emails_db)} emails")

# Mock function for email processing
async def process_email_task(email_id: str):
    """Process an email to generate a proposal."""
    logger.info(f"Processing email {email_id}...")
    
    # Find the email
    for email in emails_db:
        if email["id"] == email_id:
            # Mark as processed
            email["is_processed"] = True
            email["updated_at"] = datetime.utcnow()
            
            # In production, this would:
            # 1. Analyze the email content using AI
            # 2. Generate a proposal based on the content
            # 3. Create a proposal record in the database
            
            logger.info(f"Email {email_id} processed successfully")
            break
