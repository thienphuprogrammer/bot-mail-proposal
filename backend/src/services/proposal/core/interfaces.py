"""
Base Proposal Service Interfaces
===============================

This module defines the core interfaces that all proposal service implementations must follow.
The design uses the Interface Segregation Principle to separate different concerns:

1. BaseProposalService: Core proposal operations
2. ProposalGenerator: Proposal content generation
3. ProposalRenderer: Proposal rendering for different formats (HTML, PDF)

Each implementation should respect these interfaces to ensure consistent behavior
across different proposal generation and rendering strategies.
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any, Tuple
from src.models.proposal import ExtractedData
from src.models.email import Email


class BaseProposalService(ABC):
    """Base interface for all proposal service providers."""

    @abstractmethod
    def analyze_email(self, email_id: str) -> Optional[str]:
        """
        Analyze an email and generate a proposal.
        
        Args:
            email_id: ID of the email to analyze
            
        Returns:
            ID of the created proposal or None if processing failed
        """
        pass
    
    
    @abstractmethod
    def process_new_emails(self, query: str = "is:unread", max_emails: int = 10) -> List[Any]:
        """
        Process new emails and create proposals from them.
        
        Args:
            max_emails: Maximum number of emails to process
            
        Returns:
            List of processed email and proposal tuples
        """
        pass
    
    @abstractmethod
    def approve_proposal(self, proposal_id: str, user_id: str, comments: str = None) -> bool:
        """
        Approve a proposal.
        
        Args:
            proposal_id: ID of the proposal to approve
            user_id: ID of the user approving the proposal
            comments: Optional comments for the approval
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
    def submit_for_review(self, proposal_id: str) -> bool:
        """
        Submit a proposal for review.
        
        Args:
            proposal_id: ID of the proposal to submit
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
    def send_proposal_to_customer(self, proposal_id: str) -> bool:
        """
        Send a proposal to the customer.
        
        Args:
            proposal_id: ID of the proposal to send
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def get_email_with_proposal(self, email_id: str) -> Tuple[Optional[Any], Optional[Any]]:
        """
        Get both the email and proposal information together.
        
        Args:
            email_id: ID of the email to retrieve
            
        Returns:
            Tuple of (email, proposal) or (None, None) if not found
        """
        pass
    
    @abstractmethod
    def send_proposal(self, proposal_id: str, recipient: str = None, cc: List[str] = None, 
                     subject: str = None, body: str = None) -> Dict[str, Any]:
        """
        Send a proposal by email.
        
        Args:
            proposal_id: ID of the proposal to send
            recipient: Optional recipient email
            cc: Optional CC recipients
            subject: Optional custom subject
            body: Optional custom body
            
        Returns:
            Dictionary with results of the send operation
        """
        pass
    
    @abstractmethod
    def get_health_status(self) -> Dict[str, Any]:
        """
        Check the health status of the proposal service.
        
        Returns:
            Dictionary with status information
        """
        pass


class ProposalGenerator(ABC):
    """Interface for proposal content generation."""
    
    @abstractmethod
    def extract_requirements(self, email: Email) -> Optional[ExtractedData]:
        """
        Extract project requirements from an email.
        
        Args:
            email_id: ID of the email to analyze
            
        Returns:
            ExtractedData object with structured requirements or None if extraction failed
        """
        pass
    
    @abstractmethod
    def generate_proposal(self, requirements: Dict[str, Any]) -> str:
        """
        Generate proposal HTML content from requirements.
        
        Args:
            requirements: Dictionary of extracted requirements
            
        Returns:
            HTML content for the proposal
        """
        pass
    
    @abstractmethod
    def regenerate_proposal(self, proposal_id: str, additional_context: Dict[str, Any] = None) -> str:
        """
        Regenerate proposal content using existing data and additional context.
        
        Args:
            proposal_id: ID of the existing proposal
            additional_context: Optional additional context to consider
            
        Returns:
            Updated HTML content for the proposal
        """
        pass
    
    @abstractmethod
    def review_proposal(self, proposal_html: str) -> Dict[str, Any]:
        """
        Review a proposal for quality, completeness, and errors.
        
        Args:
            proposal_html: HTML content of the proposal to review
            
        Returns:
            Dictionary with review results and suggestions
        """
        pass


class ProposalRenderer(ABC):
    """Interface for proposal rendering to different formats."""
    
    @abstractmethod
    def generate_pdf(self, content: str, output_path: str = None) -> Optional[str]:
        """
        Generate a PDF version of a proposal.
        
        Args:
            proposal_id: ID of the proposal to convert
            output_dir: Directory to save the PDF
            
        Returns:
            Path to the generated PDF file or None if failed
        """
        pass
    
    @abstractmethod
    def generate_docx(self, proposal_id: str, output_dir: str = "temp") -> Optional[str]:
        """
        Generate a DOCX version of a proposal.
        
        Args:
            proposal_id: ID of the proposal to convert
            output_dir: Directory to save the DOCX
            
        Returns:
            Path to the generated DOCX file or None if failed
        """
        pass
