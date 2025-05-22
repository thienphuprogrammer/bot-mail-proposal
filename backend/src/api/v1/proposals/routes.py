from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Query
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
# from src.api.v1.auth.routes import get_current_user
from src.core.config import settings
import logging
import uuid
from bson import ObjectId

from src.models.proposal import Proposal
from src.repositories.proposal_repository import ProposalRepository
from src.repositories.email_repository import EmailRepository
from src.repositories.sent_email_repository import SentEmailRepository
from src.services.proposal.core.proposal_factory import ProposalServiceFactory
from src.services.mail.core.mail_factory import MailServiceFactory
# from src.core.auth import get_current_user

router = APIRouter(prefix="/proposals", tags=["proposals"])
logger = logging.getLogger(__name__)

# Initialize repositories and services
proposal_repository = ProposalRepository()
email_repository = EmailRepository()
sent_email_repository = SentEmailRepository()
mail_service = MailServiceFactory.create_default_outlook_facade()
proposal_service = ProposalServiceFactory.create_proposal_facade(
    proposal_repository=proposal_repository,
    email_repository=email_repository,
    sent_email_repository=sent_email_repository,
    mail_service=mail_service
)

# Proposal models
class ProposalBase(BaseModel):
    project_name: str
    description: Optional[str] = None
    
class ProposalResponse(BaseModel):
    id: str
    email_id: str
    project_name: str
    description: Optional[str] = None
    current_status: str
    created_at: datetime
    
    class Config:
        orm_mode = True

@router.get("/", response_model=List[Proposal])
async def list_proposals(
    status: Optional[str] = Query(None, description="Filter by proposal status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    # current_user: Dict = Depends(get_current_user)
):
    """
    List proposals with optional status filtering.
    """
    try:
        filter_dict = {}
        if status:
            filter_dict["status"] = status

        proposals = proposal_repository.find_all(filter_dict=filter_dict, skip=skip, limit=limit)
        return proposals
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{proposal_id}", response_model=Proposal)
async def get_proposal(
    proposal_id: str,
    # current_user: Dict = Depends(get_current_user)
):
    """
    Get a specific proposal by ID.
    """
    try:
        proposal = proposal_repository.find_by_id(proposal_id)
        if not proposal:
            raise HTTPException(status_code=404, detail="Proposal not found")
        return proposal
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{proposal_id}/generate")
async def generate_proposal(
    proposal_id: str,
    # current_user: Dict = Depends(get_current_user)
):
    """
    Generate a proposal document.
    """
    try:
        # Create proposal service
        proposal_service = ProposalServiceFactory.create_proposal_facade(
            proposal_repository=proposal_repository,
            email_repository=email_repository,
            sent_email_repository=None,  # Not needed for generation
            mail_service=mail_service
        )

        # Generate proposal
        result = proposal_service.generate_proposal(proposal_id)
        if not result:
            raise HTTPException(status_code=400, detail="Failed to generate proposal document")

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{proposal_id}/send")
async def send_proposal(
    proposal_id: str,
    recipient_email: str = Query(..., description="Email address of the recipient"),
    # current_user: Dict = Depends(get_current_user)
):
    """
    Send a proposal to a recipient.
    """
    try:
        # Create proposal service
        proposal_service = ProposalServiceFactory.create_proposal_facade(
            proposal_repository=proposal_repository,
            email_repository=email_repository,
            sent_email_repository=sent_email_repository,
            mail_service=mail_service
        )

        # Send proposal
        result = proposal_service.send_proposal(proposal_id, recipient_email)
        if not result:
            raise HTTPException(status_code=400, detail="Failed to send proposal")

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats/summary")
async def get_proposal_stats(
    # current_user: Dict = Depends(get_current_user)
):
    """
    Get proposal statistics summary.
    """
    try:
        # Get total proposals
        total_proposals = len(proposal_repository.find_all(filter_dict={}, skip=0, limit=1000))
        
        # Get proposals by status
        status_counts = {}
        for status in ["draft", "sent", "accepted", "rejected"]:
            count = len(proposal_repository.find_all(
                filter_dict={"status": status}, 
                skip=0, 
                limit=1000
            ))
            status_counts[status] = count

        return {
            "total_proposals": total_proposals,
            "status_counts": status_counts
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{proposal_id}/approve", response_model=Dict[str, Any])
async def approve_proposal(
    proposal_id: str,
    approval_notes: Optional[str] = None,
    # current_user = Depends(get_current_user)
):
    """
    Approve a proposal.
    
    - **proposal_id**: ID of the proposal to approve
    - **approval_notes**: Optional notes about the approval decision
    """
    try:
        proposal = proposal_repository.find_by_id(proposal_id)
        if not proposal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Proposal with ID {proposal_id} not found"
            )
            
        if proposal.current_status != "under_review":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Proposal with ID {proposal_id} is not under review and cannot be approved"
            )
            
        # Approve the proposal
        success = proposal_service.approve_proposal(
            proposal_id=proposal_id,
            user_id=current_user["id"],
            decision="approved",  # Using string directly instead of enum
            notes=approval_notes
        )
        
        if success:
            # Get updated proposal after approval
            updated_proposal = proposal_repository.find_by_id(proposal_id)
            return {
                "status": "success", 
                "message": "Proposal approved successfully",
                "proposal_id": proposal_id,
                "current_status": updated_proposal.current_status if updated_proposal else "approved"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to approve proposal"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error approving proposal {proposal_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error approving proposal: {str(e)}"
        )

@router.post("/{proposal_id}/generate-pdf", response_model=Dict[str, Any])
async def generate_pdf(
    proposal_id: str,
    background_tasks: BackgroundTasks,
    # current_user = Depends(get_current_user)
):
    """
    Generate PDF for a proposal.
    """
    try:
        proposal = proposal_repository.find_by_id(proposal_id)
        if not proposal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Proposal with ID {proposal_id} not found"
            )
        
        # Check if PDF already exists
        has_pdf = False
        if hasattr(proposal, 'proposal_versions') and proposal.proposal_versions and len(proposal.proposal_versions) > 0:
            latest_version = proposal.proposal_versions[-1]
            if hasattr(latest_version, 'pdf_path') and latest_version.pdf_path:
                has_pdf = True
        
        # Generate PDF in background 
        background_tasks.add_task(
            generate_pdf_task,
            proposal_id=proposal_id,
            proposal_service=proposal_service
        )
        
        return {
            "status": "success", 
            "message": "PDF generation started",
            "already_exists": has_pdf
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating PDF for proposal {proposal_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating PDF: {str(e)}"
        )

class SendProposalRequest(BaseModel):
    custom_subject: Optional[str] = None
    custom_message: Optional[str] = None
    custom_recipient: Optional[str] = None
    cc_recipients: Optional[List[str]] = None
    bcc_recipients: Optional[List[str]] = None

@router.post("/{proposal_id}/send", response_model=Dict[str, Any])
async def send_proposal(
    proposal_id: str,
    send_options: SendProposalRequest = None,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    # current_user = Depends(get_current_user)
):
    """
    Send a proposal to the client.
    
    - **proposal_id**: ID of the proposal to send
    - **send_options**: Optional customization for the email (subject, message, recipients)
    """
    try:
        proposal = proposal_repository.find_by_id(proposal_id)
        if not proposal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Proposal with ID {proposal_id} not found"
            )
        
        if proposal.current_status != "approved":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Proposal with ID {proposal_id} is not approved and cannot be sent"
            )
        
        # Check if we have a PDF
        has_pdf = False
        if hasattr(proposal, 'proposal_versions') and proposal.proposal_versions and len(proposal.proposal_versions) > 0:
            latest_version = proposal.proposal_versions[-1]
            if hasattr(latest_version, 'pdf_path') and latest_version.pdf_path:
                has_pdf = True
        
        if not has_pdf:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot send proposal without generating PDF first"
            )
            
        # Get recipient from email or custom option
        recipient = None
        if send_options and send_options.custom_recipient:
            recipient = send_options.custom_recipient
        else:
            # Get email to determine recipient
            email = None
            if hasattr(proposal, 'email_id') and proposal.email_id:
                try:
                    email = email_repository.find_by_id(str(proposal.email_id))
                except Exception:
                    pass
                    
            if not email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot find original email to determine recipient. Please provide a custom recipient."
                )
                
            recipient = email.sender
                
        # Send in background with custom options
        send_options_dict = {}
        if send_options:
            if send_options.custom_subject:
                send_options_dict["subject"] = send_options.custom_subject
            if send_options.custom_message:
                send_options_dict["message"] = send_options.custom_message
            if send_options.cc_recipients:
                send_options_dict["cc"] = send_options.cc_recipients
            if send_options.bcc_recipients:
                send_options_dict["bcc"] = send_options.bcc_recipients
        
        background_tasks.add_task(
            send_proposal_task,
            proposal_id=proposal_id,
            recipient=recipient,
            proposal_service=proposal_service,
            options=send_options_dict
        )
        
        return {
            "status": "success", 
            "message": "Sending proposal in background",
            "recipient": recipient,
            "proposal_id": proposal_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending proposal {proposal_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error sending proposal: {str(e)}"
        )

# Background tasks for PDF generation
async def generate_pdf_task(proposal_id: str, proposal_service: Any):
    """Generate PDF for a proposal in the background."""
    logger.info(f"Generating PDF for proposal {proposal_id}...")
    try:
        if hasattr(proposal_service.proposal_renderer, 'generate_pdf_from_proposal'):
            pdf_path = proposal_service.proposal_renderer.generate_pdf_from_proposal(proposal_id)
        else:
            pdf_path = proposal_service.generate_pdf(proposal_id)
            
        if pdf_path:
            logger.info(f"PDF generated successfully for proposal {proposal_id}: {pdf_path}")
        else:
            logger.error(f"Failed to generate PDF for proposal {proposal_id}")
    except Exception as e:
        logger.error(f"Error generating PDF for proposal {proposal_id}: {str(e)}")
        raise

# Background task for sending proposal
async def send_proposal_task(proposal_id: str, recipient: str, proposal_service: Any, options: Dict[str, Any] = None):
    """Send a proposal by email in the background."""
    logger.info(f"Sending proposal {proposal_id} to {recipient}...")
    try:
        # Build send parameters
        send_params = {
            "proposal_id": proposal_id,
            "recipient": recipient
        }
        
        # Add custom options if provided
        if options:
            for key, value in options.items():
                send_params[key] = value
        
        result = proposal_service.send_proposal(**send_params)
        
        if result["success"]:
            # Update the proposal status to "sent" if not already done by the service
            try:
                proposal = proposal_repository.find_by_id(proposal_id)
                if proposal and proposal.current_status != "sent":
                    proposal_repository.update(proposal_id, {"current_status": "sent"})
            except Exception as update_error:
                logger.error(f"Error updating proposal status: {str(update_error)}")
                
            logger.info(f"Proposal {proposal_id} sent successfully to {recipient}")
        else:
            logger.error(f"Failed to send proposal {proposal_id}: {result.get('error', 'Unknown error')}")
    except Exception as e:
        logger.error(f"Error sending proposal {proposal_id}: {str(e)}")
        raise 