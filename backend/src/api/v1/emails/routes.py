from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional, Dict, Any
from datetime import datetime
from bson import ObjectId

from src.models.email import Email, EmailCreate
from src.services.mail.core.mail_factory import MailServiceFactory
from src.services.mail.core.mail_facade import MailServiceFacade
from src.repositories.email_repository import EmailRepository
# from src.core.auth import get_current_user

router = APIRouter(prefix="/emails", tags=["emails"])

mail_service = MailServiceFactory.create_default_outlook_facade()

@router.get("/", response_model=List[Email])
async def list_emails(
    show_processed: bool = Query(True, description="Show processed emails"),
    show_unprocessed: bool = Query(True, description="Show unprocessed emails"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    mail_service: MailServiceFacade = Depends(MailServiceFactory.create_default_outlook_facade)
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

        # Get emails from the mail service
        email_repository = EmailRepository()
        mail_service = MailServiceFacade(
            email_repository=email_repository,
            mail_service=mail_service
        )
        emails = mail_service.get_emails(
            filter_dict=filter_dict, skip=skip, limit=limit)
        return emails
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{email_id}", response_model=Email)
async def get_email(
    email_id: str,
    mail_service: MailServiceFacade = Depends(MailServiceFactory.create_default_outlook_facade)
    # current_user: Dict = Depends(get_current_user)
):
    """
    Get a specific email by ID.
    """
    try:
        email_repository = EmailRepository()
        mail_service = MailServiceFacade(
            email_repository=email_repository,
            mail_service=mail_service
        )
        email = mail_service.get_email(email_id)
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
    mail_service: MailServiceFacade = Depends(MailServiceFactory.create_default_outlook_facade)
    # current_user: Dict = Depends(get_current_user)
):
    """
    Sync emails from the email service.
    """
    try:
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

