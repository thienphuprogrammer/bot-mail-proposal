from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any, Tuple

from src.models.email import Email
from src.models.proposal import ExtractedData, Proposal


class AIService(ABC):
    """Base interface for AI services."""
    
    @abstractmethod
    def extract_requirements(self, email_body: str) -> Optional[ExtractedData]:
        """Extract requirements from email body."""
        pass
    
    @abstractmethod
    def generate_proposal(self, extracted_data: ExtractedData) -> Optional[str]:
        """Generate a proposal from extracted data."""
        pass
    
    @abstractmethod
    def generate_pdf(self, html_content: str, output_path: str) -> bool:
        """Generate a PDF from HTML content."""
        pass


class EmailService(ABC):
    """Base interface for email services."""
    
    @abstractmethod
    def fetch_emails(self, query: str = "", max_results: int = 10) -> List[Email]:
        """Fetch emails from the email provider."""
        pass
    
    @abstractmethod
    def mark_as_read(self, email_id: str) -> bool:
        """Mark an email as read."""
        pass
    
    @abstractmethod
    def send_email(self, to: str, subject: str, body: str, 
                  attachment_path: Optional[str] = None) -> bool:
        """Send an email with optional attachment."""
        pass


class ProposalProcessingService(ABC):
    """Base interface for proposal processing services."""
    
    @abstractmethod
    def process_new_emails(self, max_emails: int = 10) -> List[Tuple[Email, Optional[Proposal]]]:
        """Process new emails and create proposals."""
        pass
    
    @abstractmethod
    def approve_proposal(self, proposal_id: str) -> bool:
        """Approve a proposal."""
        pass
    
    @abstractmethod
    def generate_pdf(self, proposal_id: str, output_dir: str = "temp") -> Optional[str]:
        """Generate a PDF for a proposal."""
        pass
    
    @abstractmethod
    def send_proposal_to_customer(self, proposal_id: str) -> bool:
        """Send a proposal to the customer."""
        pass
        
    @abstractmethod
    def get_email_with_proposal(self, email_id: str) -> Tuple[Optional[Email], Optional[Proposal]]:
        """Get an email and its associated proposal."""
        pass


class AuthenticationService(ABC):
    """Base interface for authentication services."""
    
    @abstractmethod
    def authenticate_user(self, username: str, password: str) -> Optional[Any]:
        """Authenticate a user with username and password."""
        pass
    
    @abstractmethod
    def create_access_token(self, user_id: str, expires_delta: Optional[Any] = None) -> str:
        """Create an access token for a user."""
        pass
    
    @abstractmethod
    def get_current_user(self, token: str) -> Optional[Any]:
        """Get the current user from a token."""
        pass
    
    @abstractmethod
    def register_user(self, user_data: Any) -> Optional[Any]:
        """Register a new user."""
        pass 