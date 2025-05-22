"""
Proposal service facade that integrates proposal generation, rendering, and database operations.
"""

import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
import os

from src.services.proposal.core.interfaces import BaseProposalService
from src.services.proposal.generators.ai_generator import AIProposalGenerator
from src.services.proposal.renderers.pdf_renderer import PDFProposalRenderer
from src.services.mail.core.mail_facade import MailServiceFacade
from src.repositories.proposal_repository import ProposalRepository
from src.repositories.email_repository import EmailRepository

from src.models.proposal import (
    Proposal,
    ProposalCreate,
    ProposalUpdate,
    ProposalStatus,
    Priority,
    ApprovalDecision,
    ExtractedData,
    ProposalVersion
)
from src.models.email import Email
from src.models.proposal import ApprovalHistory


logger = logging.getLogger(__name__)

class ProposalServiceFacade(BaseProposalService):
    """Facade for proposal-related operations."""
    
    def __init__(
        self,
        proposal_generator: AIProposalGenerator,
        proposal_renderer: PDFProposalRenderer,
        mail_service: MailServiceFacade,
        proposal_repository: ProposalRepository,
        email_repository: EmailRepository,
        sent_email_repository: Optional[Any] = None
    ):
        """
        Initialize the proposal service facade.
        
        Args:
            proposal_generator: Service for generating proposal content
            proposal_renderer: Service for rendering proposals
            mail_service: Service for handling email operations
            proposal_repository: Repository for proposal data
            email_repository: Repository for email data
            sent_email_repository: Repository for sent email data
        """
        self.proposal_generator = proposal_generator
        self.proposal_renderer = proposal_renderer
        self.mail_service = mail_service
        self.proposal_repository = proposal_repository
        self.email_repository = email_repository
        self.sent_email_repository = sent_email_repository
        
        logger.info("Initialized proposal service facade")
    
    def analyze_email(self, email_id: str) -> Optional[str]:
        """
        Analyze an email to extract proposal requirements.
        
        Args:
            email_id: ID of the email to analyze
            
        Returns:
            ID of the created proposal or None if analysis failed
        """
        logger.info(f"Analyzing email {email_id}")
        
        try:    
            # Get email details
            email = self.email_repository.find_by_id(email_id)
            if not email:
                logger.error(f"Email not found: {email_id}")
                return None
                
            # Extract requirements using AI
            extracted_data = self.proposal_generator.extract_requirements(email=email)
            if not extracted_data:
                logger.error(f"Failed to extract requirements from email {email_id}")
                return None
            
            # Generate proposal content
            content = self.proposal_generator.generate_proposal(extracted_data)
            if not content:
                logger.error(f"Failed to generate proposal content for email {email_id}")
                return None
            
            proposal_version = ProposalVersion(
                version=1,
                content=content,
                created_at=datetime.utcnow()
            )

            # Check if proposal already exists
            existing_proposal = self.proposal_repository.find_by_email_id(email_id)
            if existing_proposal:
                # Update proposal
                old_proposal_version = existing_proposal.proposal_versions
                if old_proposal_version is None:
                    old_proposal_version = []
                else:
                    version_number = old_proposal_version[-1].version + 1
                    proposal_version.version = version_number
                old_proposal_version.append(proposal_version)

                update = ProposalUpdate(
                    extracted_data=extracted_data,
                    proposal_versions=old_proposal_version,
                    status=ProposalStatus.DRAFT,
                    priority=extracted_data.priority
                )
                proposal_id = existing_proposal.id
                self.proposal_repository.update(proposal_id, update)
            else:
                # Save extracted data to database
                proposal = ProposalCreate(  
                    email_id=email_id,
                    extracted_data=extracted_data,
                    proposal_versions=[proposal_version],
                    status=ProposalStatus.DRAFT,
                    priority=extracted_data.priority,
                    metadata={
                        "client_name": email.sender,
                        "subject": email.subject,
                        "received_at": email.received_at.isoformat()
                    }
                )
                proposal_id = self.proposal_repository.create(proposal)
                
            logger.info(f"Successfully analyzed email {email_id}")
            return proposal_id
            
        except Exception as e:
            logger.error(f"Error analyzing email: {str(e)}")
            raise e
    
    def process_new_emails(self) -> List[str]:
        """
        Process new emails and create proposals.
        
        Returns:
            List of created proposal IDs
        """
        logger.info("Processing new emails")
        
        try:
            # Get unprocessed emails
            unprocessed_emails = self.email_repository.find_unprocessed()
            if not unprocessed_emails:
                logger.info("No new emails to process")
                return []
                
            created_proposals = []
            
            # Process each email
            for email in unprocessed_emails:
                proposal_id = self._process_email(email)
                if proposal_id:
                    created_proposals.append(proposal_id)
                    
            logger.info(f"Processed {len(created_proposals)} new proposals")
            return created_proposals
            
        except Exception as e:
            logger.error(f"Error processing new emails: {str(e)}")
            return []
    
    def _process_email(self, email: Email) -> Optional[str]:
        """
        Process a single email and create a proposal.
        
        Args:
            email: Email details to process
            
        Returns:
            ID of the created proposal or None if processing failed
        """
        try:
            # Extract requirements
            extracted_data = self.proposal_generator.extract_requirements(email.body)
            if not extracted_data:
                logger.error(f"Failed to extract requirements from email {email.id}")
                return None
                
            # Generate proposal content
            html_content = self.proposal_generator.generate_proposal(extracted_data)
            if not html_content:
                logger.error(f"Failed to generate proposal content for email {email.id}")
                return None
                
            # Create proposal version
            version = ProposalVersion(
                version=1,
                html_content=html_content,
                created_at=datetime.utcnow()
            )
            
            # Create proposal
            proposal = ProposalCreate(
                email_id=email.id,
                extracted_data=extracted_data,
                proposal_versions=[version],
                status=ProposalStatus.DRAFT,
                priority=extracted_data.priority,
                metadata={
                    "client_name": email.from_email,
                    "subject": email.subject,
                    "received_at": email.received_at.isoformat()
                }
            )
            
            # Save proposal
            proposal_id = self.proposal_repository.create(proposal)
            if not proposal_id:
                logger.error(f"Failed to save proposal for email {email.id}")
                return None
                
            # Mark email as processed
            self.email_repository.mark_as_processed(email.id)
            
            logger.info(f"Successfully created proposal {proposal_id} from email {email.id}")
            return proposal_id
            
        except Exception as e:
            logger.error(f"Error processing email {email.id}: {str(e)}")
            return None
    
    def approve_proposal(
        self, 
        proposal_id: str, 
        user_id: str, 
        decision: str = "approved",
        notes: str = None
    ) -> Dict[str, Any]:
        """
        Approve or reject a proposal with optional notes.
        
        Args:
            proposal_id: ID of the proposal to approve
            user_id: ID of the approver
            decision: Approval decision (approved, rejected)
            notes: Optional notes/comments for the approval decision
            
        Returns:
            Dictionary with status and details of the operation
        """
        logger.info(f"Processing approval decision '{decision}' for proposal {proposal_id}")
        
        try:
            # Get proposal
            proposal = self.proposal_repository.find_by_id(proposal_id)
            if not proposal:
                logger.error(f"Proposal not found: {proposal_id}")
                return {
                    "success": False,
                    "error": f"Proposal not found: {proposal_id}"
                }
            
            # Validate proposal status for approving
            if proposal.current_status != "under_review":
                return {
                    "success": False,
                    "error": f"Proposal is not under review. Current status: {proposal.current_status}"
                }
                
            # Map string decision to enum if needed
            approval_decision = decision
            if isinstance(decision, str):
                if decision.lower() == "approved":
                    approval_decision = ApprovalDecision.APPROVED
                elif decision.lower() == "rejected":
                    approval_decision = ApprovalDecision.REJECTED
                else:
                    return {
                        "success": False,
                        "error": f"Invalid decision: {decision}. Must be 'approved' or 'rejected'"
                    }
                
            # Create approval history entry
            approval_entry = {
                "approver_id": user_id,
                "decision": approval_decision,
                "timestamp": datetime.utcnow()
            }
            
            # Add notes if provided
            if notes:
                approval_entry["notes"] = notes
                
            # Prepare the update data
            new_status = ProposalStatus.APPROVED if approval_decision == ApprovalDecision.APPROVED else ProposalStatus.REJECTED
            
            # Initialize approval history array if it doesn't exist
            approval_history = []
            if hasattr(proposal, 'approval_history') and proposal.approval_history:
                approval_history = proposal.approval_history
                
            # Prepare the update
            update_data = {
                "current_status": new_status,
                "approval_history": approval_history + [approval_entry],
                "timestamps.approved_at": datetime.utcnow(),
                "timestamps.updated_at": datetime.utcnow()
            }
            
            # Save changes
            success = self.proposal_repository.update(proposal_id, update_data)
            if not success:
                logger.error(f"Failed to update proposal {proposal_id}")
                return {
                    "success": False,
                    "error": f"Failed to update proposal {proposal_id}"
                }
                
            logger.info(f"Successfully processed approval decision for proposal {proposal_id}")
            
            # Get the updated proposal
            updated_proposal = self.proposal_repository.find_by_id(proposal_id)
            
            return {
                "success": True,
                "message": f"Proposal {proposal_id} has been {decision}",
                "proposal_id": proposal_id,
                "status": new_status,
                "approver_id": user_id,
                "approved_at": datetime.utcnow().isoformat(),
                "current_version": len(updated_proposal.proposal_versions) if hasattr(updated_proposal, 'proposal_versions') else 0
            }
            
        except Exception as e:
            logger.error(f"Error approving proposal: {str(e)}")
            return {
                "success": False,
                "error": f"Error approving proposal: {str(e)}"
            }
    
    def regenerate_proposal(self, proposal_id: str, additional_context: Dict[str, Any] = None) -> bool:
        """
        Regenerate a proposal's content.
        
        Args:
            proposal_id: ID of the proposal to regenerate
            additional_context: Optional additional context to consider
            
        Returns:
            True if regeneration was successful, False otherwise
        """
        logger.info(f"Regenerating proposal {proposal_id}")
        
        try:
            # Get proposal
            proposal = self.proposal_repository.find_by_id(proposal_id)
            if not proposal:
                logger.error(f"Proposal not found: {proposal_id}")
                return False
                
            # Generate new content
            html_content = self.proposal_generator.regenerate_proposal(proposal_id, additional_context)
            if not html_content:
                logger.error(f"Failed to regenerate content for proposal {proposal_id}")
                return False
                
            # Create new version
            new_version = ProposalVersion(
                version=len(proposal.proposal_versions) + 1,
                html_content=html_content,
                created_at=datetime.utcnow()
            )
            
            # Update proposal
            update = ProposalUpdate(
                proposal_versions=proposal.proposal_versions + [new_version],
                status=ProposalStatus.DRAFT
            )
            
            # Save changes
            success = self.proposal_repository.update(proposal_id, update)
            if not success:
                logger.error(f"Failed to update proposal {proposal_id}")
                return False
                
            logger.info(f"Successfully regenerated proposal {proposal_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error regenerating proposal: {str(e)}")
            return False
    
    def generate_pdf(self, proposal_id: str) -> Optional[str]:
        """
        Generate PDF version of a proposal.
        
        Args:
            proposal_id: ID of the proposal to generate PDF for
            
        Returns:
            Path to the generated PDF file or None if generation failed
        """
        logger.info(f"Generating PDF for proposal {proposal_id}")
        
        try:
            # Generate PDF
            proposal = self.proposal_repository.find_by_id(proposal_id)
            if not proposal:
                logger.error(f"Proposal not found: {proposal_id}")
                return None
            
            # Ensure temp directory exists
            os.makedirs("temp", exist_ok=True)
            
            # Generate file name based on project name or proposal ID
            if proposal.extracted_data and proposal.extracted_data.project_name:
                safe_name = "".join(c if c.isalnum() else "_" for c in proposal.extracted_data.project_name)
                output_path = os.path.join("temp", f"{safe_name}.pdf")
            else:
                output_path = os.path.join("temp", f"proposal_{proposal_id}.pdf")
                
            content = proposal.proposal_versions[-1].content
            pdf_path = self.proposal_renderer.generate_pdf(content, output_path)
            
            if not pdf_path:
                logger.error(f"Failed to generate PDF for proposal {proposal_id}")
                return None
                
            logger.info(f"Successfully generated PDF for proposal {proposal_id} at {pdf_path}")
            return pdf_path
            
        except Exception as e:
            logger.error(f"Error generating PDF: {str(e)}")
            return None
    
    def apply_template(self, proposal_id: str, template_name: str) -> bool:
        """
        Apply a template to a proposal.
        
        Args:
            proposal_id: ID of the proposal to apply template to
            template_name: Name of the template to apply
            
        Returns:
            True if template application was successful, False otherwise
        """
        logger.info(f"Applying template {template_name} to proposal {proposal_id}")
        
        try:
            # Apply template
            html_content = self.proposal_renderer.apply_template(proposal_id, template_name)
            if not html_content:
                logger.error(f"Failed to apply template to proposal {proposal_id}")
                return False
                
            # Get proposal
            proposal = self.proposal_repository.find_by_id(proposal_id)
            if not proposal:
                logger.error(f"Proposal not found: {proposal_id}")
                return False
                
            # Create new version
            new_version = ProposalVersion(
                version=len(proposal.proposal_versions) + 1,
                html_content=html_content,
                created_at=datetime.utcnow()
            )
            
            # Update proposal
            update = ProposalUpdate(
                proposal_versions=proposal.proposal_versions + [new_version],
                status=ProposalStatus.DRAFT
            )
            
            # Save changes
            success = self.proposal_repository.update(proposal_id, update)
            if not success:
                logger.error(f"Failed to update proposal {proposal_id}")
                return False
                
            logger.info(f"Successfully applied template to proposal {proposal_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error applying template: {str(e)}")
            return False 
        
    def reject_proposal(self, proposal_id: str, user_id: str, comments: str = None) -> bool:
        """
        Reject a proposal.
        
        Args:
            proposal_id: ID of the proposal to reject
            user_id: ID of the user rejecting the proposal
            comments: Optional comments for the rejection
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create rejection history entry
            rejection_entry = ApprovalHistory(
                user_id=user_id,
                decision="rejected",
                comments=comments,
            )
            
            # Update proposal status
            updated = self.proposal_repository.update(
                proposal_id, 
                {
                    "current_status": ProposalStatus.REJECTED,
                    "approval_history": [rejection_entry.model_dump()]
                }
            )
            
            if not updated:
                logger.error(f"Failed to update proposal status: {proposal_id}")
                return False
                
            logger.info(f"Proposal rejected: {proposal_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error rejecting proposal {proposal_id}: {str(e)}")
            return False
    
    def submit_for_review(self, proposal_id: str) -> bool:
        """
        Submit a proposal for review.
        
        Args:
            proposal_id: ID of the proposal to submit
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Update proposal status
            updated = self.proposal_repository.update(
                proposal_id, 
                {"current_status": ProposalStatus.UNDER_REVIEW}
            )
            
            if not updated:
                logger.error(f"Failed to update proposal status: {proposal_id}")
                return False
                
            logger.info(f"Proposal submitted for review: {proposal_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error submitting proposal for review {proposal_id}: {str(e)}")
            return False
    
    def add_proposal_version(self, proposal_id: str, html_content: str, user_id: str) -> bool:
        """
        Add a new version to an existing proposal.
        
        Args:
            proposal_id: ID of the proposal
            html_content: New HTML content for the proposal
            user_id: ID of the user creating the version
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get the proposal
            proposal = self.proposal_repository.find_by_id(proposal_id)
            if not proposal:
                logger.error(f"Proposal not found: {proposal_id}")
                return False
                
            # Get the current versions
            versions = proposal.proposal_versions or []
            
            # Calculate the new version number
            next_version = 1
            if versions:
                next_version = max(v.version for v in versions) + 1
                
            # Create new version
            new_version = ProposalVersion(
                html_content=html_content,
                version=next_version,
                modified_by=user_id
            )
            
            # Add to versions list
            versions.append(new_version)
            
            # Update proposal
            updated = self.proposal_repository.update(
                proposal_id, 
                {"proposal_versions": [v.model_dump() for v in versions]}
            )
            
            if not updated:
                logger.error(f"Failed to add proposal version: {proposal_id}")
                return False
                
            logger.info(f"Added version {next_version} to proposal: {proposal_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding proposal version {proposal_id}: {str(e)}")
            return False
    
    def send_proposal_to_customer(self, proposal_id: str) -> bool:
        """
        Send a proposal to the customer.
        
        Args:
            proposal_id: ID of the proposal to send
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get the proposal
            proposal = self.proposal_repository.find_by_id(proposal_id)
            if not proposal:
                logger.error(f"Proposal not found: {proposal_id}")
                return False
                
            # Get the email
            email = self.email_repository.find_by_id(proposal.email_id)
            if not email:
                logger.error(f"Email not found for proposal: {proposal_id}")
                return False
                
            # Generate PDF
            pdf_path = self.proposal_renderer.generate_pdf(proposal_id)
            if not pdf_path:
                logger.error(f"Failed to generate PDF for proposal: {proposal_id}")
                return False
                
            # Get latest version HTML
            latest_version = max(proposal.proposal_versions, key=lambda v: v.version)
            html_content = latest_version.html_content
            
            # Get client name and project title from metadata
            client_name = proposal.metadata.get("client_name", "Client")
            project_title = proposal.metadata.get("project_title", "Project")
            
            # Prepare email content
            subject = f"Proposal for {project_title}"
            body = f"""
            <p>Dear {client_name},</p>
            
            <p>Thank you for your inquiry. We're pleased to submit our proposal for the {project_title} project.</p>
            
            <p>Please find attached our detailed proposal. We look forward to discussing this further with you.</p>
            
            <p>Best regards,<br>
            Your Company Name</p>
            """
            
            # Send email with attachment
            if not self.mail_service:
                logger.error("Mail service not available for sending proposal")
                return False
                
            result = self.mail_service.send_email(
                to=email.sender,
                subject=subject,
                body=body,
                attachment_path=pdf_path
            )
            
            # Log sent email using the proper Pydantic model
            from src.models.email import SentEmailCreate
            
            sent_email_create = SentEmailCreate(
                proposal_id=proposal_id,
                recipients=[email.sender],
                subject=subject,
                content=body,
                attachments=[{"path": pdf_path, "name": os.path.basename(pdf_path)}],
                gmail_data={
                    "message_id": result.get("message_id", ""),
                    "thread_id": result.get("thread_id", "")
                }
            )
            
            # Save sent email to database
            sent_email = self.sent_email_repository.create(sent_email_create)
            
            # Update proposal status and timestamps
            self.proposal_repository.update(
                proposal_id, 
                {
                    "current_status": ProposalStatus.SENT,
                    "sent_email_id": str(sent_email.id),
                    "timestamps.sent_at": datetime.utcnow()
                }
            )
            
            logger.info(f"Proposal sent to customer: {proposal_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending proposal {proposal_id}: {str(e)}")
            return False
    
    def get_email_with_proposal(self, email_id: str) -> Tuple[Optional[Email], Optional[Proposal]]:
        """
        Get both the email and proposal information together.
        
        Args:
            email_id: ID of the email to retrieve
            
        Returns:
            Tuple of (email, proposal) or (None, None) if not found
        """
        try:
            # Get email
            email = self.email_repository.find_by_id(email_id)
            if not email:
                logger.error(f"Email not found: {email_id}")
                return (None, None)
                
            # Get proposal if linked
            proposal = None
            if hasattr(email, "proposal_id") and email.proposal_id:
                proposal = self.proposal_repository.find_by_id(email.proposal_id)
                
            return (email, proposal)
            
        except Exception as e:
            logger.error(f"Error getting email with proposal {email_id}: {str(e)}")
            return (None, None)
    
    def send_proposal(
        self, 
        proposal_id: str, 
        recipient: str = None, 
        cc: List[str] = None,
        bcc: List[str] = None, 
        subject: str = None, 
        message: str = None,
        importance: str = "normal",
        template_variables: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Send a proposal by email with enhanced options.
        
        Args:
            proposal_id: ID of the proposal to send
            recipient: Optional recipient email
            cc: Optional CC recipients
            bcc: Optional BCC recipients
            subject: Optional custom subject
            message: Optional custom message body
            importance: Email importance (low, normal, high)
            template_variables: Optional variables for templating
            
        Returns:
            Dictionary with results of the send operation
        """
        try:
            # Get the proposal
            proposal = self.proposal_repository.find_by_id(proposal_id)
            if not proposal:
                logger.error(f"Proposal not found: {proposal_id}")
                return {"success": False, "error": "Proposal not found"}
                
            # Get the email if recipient not specified
            email = None
            if not recipient and proposal.email_id:
                email = self.email_repository.find_by_id(proposal.email_id)
                if email:
                    recipient = email.sender
                    
            if not recipient:
                logger.error(f"No recipient specified for proposal: {proposal_id}")
                return {"success": False, "error": "No recipient specified"}
                
            # Generate PDF if not already generated
            pdf_path = None
            if hasattr(proposal, 'proposal_versions') and proposal.proposal_versions and len(proposal.proposal_versions) > 0:
                latest_version = proposal.proposal_versions[-1]
                if hasattr(latest_version, 'pdf_path') and latest_version.pdf_path and os.path.exists(latest_version.pdf_path):
                    pdf_path = latest_version.pdf_path
            
            # Generate new PDF if needed
            if not pdf_path:
                pdf_path = self.proposal_renderer.generate_pdf(proposal_id)
                
            if not pdf_path:
                logger.error(f"Failed to generate PDF for proposal: {proposal_id}")
                return {"success": False, "error": "Failed to generate PDF"}
            
            # Gather proposal data for email template
            project_name = "Project"
            client_name = "Client"
            company_name = settings.COMPANY_NAME if hasattr(settings, 'COMPANY_NAME') else "Your Company"
            
            # Try to extract from proposal data
            if hasattr(proposal, 'extracted_data'):
                if hasattr(proposal.extracted_data, 'project_name'):
                    project_name = proposal.extracted_data.project_name
                    
                if hasattr(proposal.extracted_data, 'client_name'):
                    client_name = proposal.extracted_data.client_name
                    
            # Also check metadata fields
            if hasattr(proposal, 'metadata'):
                if not client_name or client_name == "Client":
                    client_name = proposal.metadata.get("client_name", client_name)
                if not project_name or project_name == "Project":
                    project_name = proposal.metadata.get("project_title", project_name)
                    
            # Default subject and body if not provided
            if not subject:
                subject = f"Proposal for {project_name}"
                
            # Prepare email body (message)
            body = message if message else None
            if not body:
                body = f"""
                <p>Dear {client_name},</p>
                
                <p>Thank you for your inquiry. We're pleased to submit our proposal for the {project_name} project.</p>
                
                <p>Please find attached our detailed proposal. We look forward to discussing this further with you.</p>
                
                <p>Best regards,<br>
                {company_name}</p>
                """
                
            # Send email with attachment
            if not self.mail_service:
                logger.error("Mail service not available for sending proposal")
                return {"success": False, "error": "Mail service not available"}
            
            # Prepare template variables if not provided
            if not template_variables:
                template_variables = {
                    "client_name": client_name,
                    "project_name": project_name,
                    "company_name": company_name
                }
                
                # Add proposal details if available
                if hasattr(proposal, 'extracted_data'):
                    if hasattr(proposal.extracted_data, 'key_features'):
                        template_variables["features"] = proposal.extracted_data.key_features
                    if hasattr(proposal.extracted_data, 'deadline'):
                        template_variables["deadline"] = proposal.extracted_data.deadline
                    if hasattr(proposal.extracted_data, 'budget'):
                        template_variables["budget"] = proposal.extracted_data.budget
                
            # Send using improved email service
            result = self.mail_service.send_email(
                to=recipient,
                subject=subject,
                body=body,
                attachment_paths=[pdf_path] if pdf_path else None,
                cc=cc,
                bcc=bcc,
                is_html=True,
                importance=importance,
                template_variables=template_variables
            )
            
            # Create sent email using the proper Pydantic model
            from src.models.email import SentEmailCreate
            
            # Prepare recipients list (primary + cc + bcc)
            recipients = [recipient]
            if cc:
                recipients.extend(cc)
            if bcc:
                recipients.extend(bcc)
            
            sent_email_create = SentEmailCreate(
                proposal_id=proposal_id,
                recipients=recipients,
                subject=subject,
                content=body,
                attachments=[{"path": pdf_path, "name": os.path.basename(pdf_path)}] if pdf_path else [],
                metadata={
                    "message_id": result.get("message_id", ""),
                    "importance": importance,
                    "template_variables": template_variables
                }
            )
            
            # Save sent email to database
            sent_email = self.sent_email_repository.create(sent_email_create)
            
            # Update proposal status and timestamps
            update_data = {
                "current_status": ProposalStatus.SENT,
                "sent_email_id": str(sent_email.id),
                "timestamps.sent_at": datetime.utcnow()
            }
            
            self.proposal_repository.update(proposal_id, update_data)
            
            logger.info(f"Proposal sent: {proposal_id} to {recipient}")
            return {
                "success": True, 
                "message": f"Proposal sent successfully to {recipient}",
                "sent_email_id": str(sent_email.id),
                "proposal_id": proposal_id,
                "recipient": recipient
            }
            
        except Exception as e:
            logger.error(f"Error sending proposal {proposal_id}: {str(e)}")
            return {"success": False, "error": str(e)}

    def get_health_status(self) -> Dict[str, Any]:
        """
        Check the health status of the proposal service.
        
        Returns:
            Dictionary with status information
        """
        status = {
            "proposal_service": "healthy",
            "proposal_generator": "unknown",
            "proposal_renderer": "unknown",
            "repositories": {
                "email": "unknown",
                "proposal": "unknown",
                "sent_email": "unknown"
            },
            "mail_service": "unknown" if self.mail_service else "not_configured"
        }
        
        # Check proposal generator
        try:
            # Simple check
            if self.proposal_generator:
                status["proposal_generator"] = "healthy"
        except Exception as e:
            status["proposal_generator"] = f"error: {str(e)}"
            
        # Check proposal renderer
        try:
            # Simple check
            if self.proposal_renderer:
                status["proposal_renderer"] = "healthy"
        except Exception as e:
            status["proposal_renderer"] = f"error: {str(e)}"
            
        # Check repositories
        try:
            if self.email_repository:
                status["repositories"]["email"] = "healthy"
        except Exception as e:
            status["repositories"]["email"] = f"error: {str(e)}"
            
        try:
            if self.proposal_repository:
                status["repositories"]["proposal"] = "healthy"
        except Exception as e:
            status["repositories"]["proposal"] = f"error: {str(e)}"
            
        try:
            if self.sent_email_repository:
                status["repositories"]["sent_email"] = "healthy"
        except Exception as e:
            status["repositories"]["sent_email"] = f"error: {str(e)}"
            
        # Check mail service if configured
        if self.mail_service:
            try:
                mail_status = self.mail_service.get_health_status()
                status["mail_service"] = mail_status.get("status", "unknown")
            except Exception as e:
                status["mail_service"] = f"error: {str(e)}"
                
        return status
