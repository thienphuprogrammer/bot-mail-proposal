from abc import ABC, abstractmethod
from typing import Optional, List, Any

class EmailService(ABC):
    """Base interface for email services."""
    
    @abstractmethod
    def fetch_emails(self, max_results: int = 10, query: str = "") -> List[Any]:
        """Fetch emails from the email provider."""
        pass
    
    @abstractmethod
    def mark_as_read(self, email_id: str) -> bool:
        """Mark an email as read."""
        pass
    
    @abstractmethod
    def send_email(self, to: str, subject: str, body: str, attachment_path: Optional[str] = None) -> Optional[str]:
        """Send an email."""
        pass
