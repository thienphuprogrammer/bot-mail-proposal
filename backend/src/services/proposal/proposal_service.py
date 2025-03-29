from typing import Optional, List, Dict, Tuple
import os
from datetime import datetime
from bson import ObjectId

from src.core.config import settings
from src.models.email import Email, EmailCreate
from src.models.proposal import ProposalCreate, Proposal, ExtractedData
from src.models.email import SentEmailCreate, SentEmail
from src.services.gmail.gmail_service import GmailService
from src.services.model.langchain_service import LangChainService
from src.services.model.azure_service import AzureDeepseekService
from src.repositories.base_repository import BaseRepository
from src.services.base_service import ProposalProcessingService

class ProposalService(ProposalProcessingService):
    """Service for proposal operations."""
    
    def __init__(
        self,
        email_repository: BaseRepository,
        proposal_repository: BaseRepository,
        sent_email_repository: BaseRepository
    ):
        """Initialize the proposal service."""
        self.email_repository = email_repository
        self.proposal_repository = proposal_repository
        self.sent_email_repository = sent_email_repository
        self.gmail_service = GmailService()
        
        # Initialize AI service based on configuration
        if settings.USE_AZURE_AI:
            self.ai_service = AzureDeepseekService()
        else:
            self.ai_service = LangChainService()
        
        # Create temp directory for PDFs if it doesn't exist
        os.makedirs("temp", exist_ok=True)
    
    def process_new_emails(self, max_emails: int = 10) -> List[Tuple[Email, Optional[Proposal]]]:
        """Fetch new emails and process them."""
        # Fetch new emails
        email_creates = self.gmail_service.fetch_emails(query="is:unread", max_results=max_emails)
        results = []
        
        for email_create in email_creates:
            # Check if email already exists
            existing_emails = self.email_repository.find_all({"gmail_id": email_create.gmail_id})
            if existing_emails:
                continue
            
            # Save email to database
            email = self.email_repository.create(email_create)
            
            # Process email to extract requirements and generate proposal
            proposal_id = self._process_email(str(email.id))
            
            # Mark as read in Gmail
            self.gmail_service.mark_as_read(email.gmail_id)
            
            # Get proposal if it was created
            proposal = None
            if proposal_id:
                proposal = self.proposal_repository.find_by_id(proposal_id)
            
            # Add to results
            results.append((email, proposal))
        
        return results
    
    def _process_email(self, email_id: str) -> Optional[str]:
        """Process an email to extract requirements and generate proposal."""
        # Get email
        email = self.email_repository.find_by_id(email_id)
        if not email:
            return None
        
        # Extract requirements using AI service
        extracted_data = self.ai_service.extract_requirements(email.body)
            
        if not extracted_data:
            return None
        
        # Generate proposal using AI service
        proposal_html = self.ai_service.generate_proposal(extracted_data)
            
        if not proposal_html:
            return None
        
        # Create proposal
        proposal_create = ProposalCreate(
            email_id=ObjectId(email_id),
            extracted_data=extracted_data,
            proposal_html=proposal_html,
            status="pending"
        )
        
        proposal = self.proposal_repository.create(proposal_create)
        
        # Update email as processed
        self.email_repository.update(email_id, {"processed": True})
        
        return str(proposal.id)
    
    def approve_proposal(self, proposal_id: str) -> bool:
        """Approve a proposal."""
        proposal = self.proposal_repository.find_by_id(proposal_id)
        if not proposal or proposal.status != "pending":
            return False
        
        # Update proposal
        update_data = {
            "status": "approved",
            "updated_at": datetime.utcnow()
        }
        
        updated_proposal = self.proposal_repository.update(proposal_id, update_data)
        return updated_proposal is not None
    
    def generate_pdf(self, proposal_id: str, output_dir: str = "temp") -> Optional[str]:
        """Generate PDF for a proposal."""
        proposal = self.proposal_repository.find_by_id(proposal_id)
        if not proposal:
            return None
        
        # Set output path
        output_path = f"{output_dir}/proposal_{proposal_id}.pdf"
        
        # Generate PDF using AI service
        success = self.ai_service.generate_pdf(
            html_content=proposal.proposal_html,
            output_path=output_path
        )
        
        if success and os.path.exists(output_path):
            # Update proposal with PDF path
            self.proposal_repository.update(
                proposal_id,
                {
                    "pdf_path": output_path,
                    "updated_at": datetime.utcnow()
                }
            )
            return output_path
        
        return None
    
    def send_proposal_to_customer(self, proposal_id: str) -> bool:
        """Send a proposal to the customer."""
        proposal = self.proposal_repository.find_by_id(proposal_id)
        if not proposal or proposal.status != "approved":
            return False
        
        # Get email
        email = self.email_repository.find_by_id(str(proposal.email_id))
        if not email:
            return False
        
        # Generate PDF if not already generated
        pdf_path = proposal.pdf_path
        if not pdf_path or not os.path.exists(pdf_path):
            pdf_path = self.generate_pdf(proposal_id)
            if not pdf_path:
                return False
        
        # Prepare email
        recipient = email.sender
        subject = f"Proposal for {proposal.extracted_data.project_name}"
        body = f"""
        <html>
        <body>
            <p>Dear Valued Customer,</p>
            <p>Thank you for your inquiry. Please find attached our proposal for <strong>{proposal.extracted_data.project_name}</strong>.</p>
            <p>If you have any questions or would like to discuss further, please don't hesitate to contact us.</p>
            <p>Best regards,<br>Your Company</p>
        </body>
        </html>
        """
        
        # Send email
        success = self.gmail_service.send_email(
            to=recipient,
            subject=subject,
            body=body,
            attachment_path=pdf_path
        )
        
        if not success:
            return False
        
        # Create sent email record
        sent_email_create = SentEmailCreate(
            proposal_id=ObjectId(proposal_id),
            recipient=recipient,
            subject=subject,
            body=body,
            attachment=pdf_path
        )
        
        sent_email = self.sent_email_repository.create(sent_email_create)
        
        # Update proposal
        self.proposal_repository.update(
            proposal_id,
            {
                "status": "sent",
                "sent_email_id": ObjectId(sent_email.id),
                "updated_at": datetime.utcnow()
            }
        )
        
        return True
        
    def get_email_with_proposal(self, email_id: str) -> Tuple[Optional[Email], Optional[Proposal]]:
        """Get email and its associated proposal."""
        email = self.email_repository.find_by_id(email_id)
        if not email:
            return None, None
            
        # Find associated proposal
        proposals = self.proposal_repository.find_all({"email_id": ObjectId(email_id)})
        proposal = proposals[0] if proposals else None
            
        return email, proposal 