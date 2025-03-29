from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any

from src.models.proposal import ExtractedData

class ProposalProcessingService(ABC):
    """Base interface for proposal processing services."""
    
    @abstractmethod
    def process_new_emails(self) -> List[str]:
        """Process new emails and create proposals."""
        pass
    
    @abstractmethod
    def approve_proposal(self, proposal_id: str, user_id: str) -> Any:
        """Approve a proposal."""
        pass
    
    @abstractmethod
    def generate_pdf(self, proposal_id: str) -> Optional[str]:
        """Generate a PDF for a proposal."""
        pass
    
    @abstractmethod
    def send_proposal(self, proposal_id: str) -> Optional[str]:
        """Send a proposal to the customer."""
        pass
        
    @abstractmethod
    def get_email_with_proposal(self, proposal_id: str) -> Optional[Dict]:
        """Get both the email and proposal information together."""
        pass 